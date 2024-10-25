def setup_dvrpsim_import():
    import sys, pathlib, importlib.util

    if importlib.util.find_spec( 'dvrpsim' ) is None:
        source_path = str( pathlib.Path(__file__).resolve().parents[2] / 'src' )
        
        if source_path not in sys.path:
            sys.path.insert(0, source_path)
            
        print( f'module "dvrpsim" will be imported from "{source_path}"' )

setup_dvrpsim_import()

from dvrpsim import Model, Location, Order, Vehicle
from dvrpsim.utils.order_providers import order_provider

from typing import Any, Dict

def demo_routing_algorithm( state:Dict[str,Any] ) -> Dict[str,Any]:
    """
    Demo "external" routing algorithm.

    Args: state

    Returns: decision
    """

    # collect unassigned orders
    unassigned_orders = [ order_id for order_id in state['open_orders'].keys()
        if state['open_orders'][order_id]['assigned_vehicle'] is None
    ]

    # if none, there is nothing to do
    if len(unassigned_orders) == 0:
        return { 'vehicles': {}, 'orders': {} }

    # collect idle vehicles at the depot
    idle_vehicles = [ vehicle_id for vehicle_id, vehicle_state in state['vehicles'].items()
        if vehicle_state['status'] == 'IDLE'
        and vehicle_state['current_visit']['location'] == 'DEPOT'
    ]

    # if none, all orders are rejected
    if len(idle_vehicles) == 0:
        return {
            'vehicles': {},
            #'orders': { order_id: { 'status': 'rejected' } for order_id in unassigned_orders }
            'orders': { order_id: { 'status': 'accepted' } for order_id in unassigned_orders }
        }

    # otherwise, orders are accepted and assigned to an idle vehicle
    vehicle_id = idle_vehicles[0]

    vehicle_route = []

    # pickup
    vehicle_route.append( {
        'location': 'DEPOT',
        'pickup_list': unassigned_orders
    } )

    # deliveries
    for order_id in unassigned_orders:
        vehicle_route.append( {
            'location': state['open_orders'][order_id]['delivery_location'],
            'delivery_list': [ order_id ]
        } )

    # depot return
    vehicle_route.append( {
        'location': 'DEPOT',
    } )

    return {
        'vehicles': {
            vehicle_id: {
                'next_visits': vehicle_route
            }
        },
        'orders': { order_id: { 'status': 'accepted' } for order_id in unassigned_orders }
    }

class DemoModel(Model):
    def __init__(self) -> None:
        super().__init__()
    
    # def on_vehicle_arrival( self, vehicle:Vehicle ) -> None:
    #     if vehicle.current_location.id == 'DEPOT' and any( order for order in self.orders.values() if not order.picked_up ):
    #         self.request_for_routing()

    def routing_callback(self):
        state = self.get_state()

        return demo_routing_algorithm( state )        

class Truck(Vehicle):
    def __init__( self, id:str ) -> None:
        super().__init__(id)

    def travel_time( self, origin:Location, destination:Location ) -> int | float:
        return 10
        
    def on_service_finish( self ) -> None:
        if self.current_location.id == 'DEPOT' and any( order for order in self.model.orders if not order.is_picked_up ):
            self.model.request_for_routing()

if __name__ == '__main__':
    model = DemoModel()

    depot = Location( id= 'DEPOT' )
    model.add_location( depot )

    orders_to_request = []

    for i in range(5):
        customer_location = Location( id= f'CUSTOMER {i+1}' )
        model.add_location( customer_location )

        order = Order( id= f'O-{i+1}' )
        order.pickup_location = depot
        order.delivery_location = customer_location
        order.release_date = (i+1)*8
        orders_to_request.append( order )

    model.env.process( order_provider( model, orders_to_request, decision_point_on_request= True ) )

    vehicle = Truck( 'TRUCK' )
    vehicle.initial_location = depot
    model.add_vehicle( vehicle )

    model.run()
