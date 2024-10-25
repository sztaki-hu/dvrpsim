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

from simpy.resources.resource import Resource
from dvrpsim.utils.distances import manhattan_distance

from typing import Any, Dict

def demo_routing_algorithm( state:Dict[str,Any] ) -> Dict[str,Any]:
    """
    Demo "external" routing algorithm.

    Args: state

    Returns: decision
    """
    idle_vehicles = [ vehicle_id for vehicle_id, vehicle_state in state['vehicles'].items()
        if vehicle_state['status'] == 'IDLE'
        and vehicle_state['current_visit']['location'] == 'DEPOT'
    ]

    unassigned_orders = [ order_id for order_id in state['open_orders'].keys()
        if state['open_orders'][order_id]['assigned_vehicle'] is None
    ]

    # if there is no vehicle at the depot, orders are rejected
    if len(idle_vehicles) == 0:
        return {
            'vehicles': {},
            'orders': { order_id: { 'status': 'accepted' } for order_id in unassigned_orders }
        }
    
    decision = {
        'vehicles': {},
        'orders': { order_id: { 'status': 'accepted' } for order_id in unassigned_orders }
    }

    # otherwise, orders are accepted and assigned to a vehicle from the depot
    for (order_id,vehicle_id) in zip(unassigned_orders,idle_vehicles):
        vehicle_route = []

        # pickup visit
        vehicle_route.append( {
            'location': 'DEPOT',
            'pickup_list': [ order_id ]
        } )
        
        # delivery visit
        vehicle_route.append( {
            'location': state['open_orders'][order_id]['delivery_location'],
            'delivery_list': [ order_id ]
        } )

        # return visit
        vehicle_route.append( {
            'location': 'DEPOT',
        } )

        decision['vehicles'][vehicle_id] = {
            'next_visits':  vehicle_route
        }

    return decision

class DemoModel(Model):
    def __init__(self) -> None:
        super().__init__()
    
    '''
    def on_vehicle_arrival( self, vehicle:Vehicle ) -> None:
        if vehicle.current_location.id == 'DEPOT' and any( order for order in self.orders.values() if not order.picked_up ):
            self.request_for_routing()
    '''

    def routing_callback(self):
        state = self.get_state()

        return demo_routing_algorithm( state )        

class Truck(Vehicle):
    def __init__( self, id:str ) -> None:
        super().__init__(id)

    def travel_time( self, origin:Location, destination:Location ) -> int | float:
        return manhattan_distance( origin.x, origin.y, destination.x, destination.y )
        
    def on_arrival( self ) -> None:
        if self.current_location.id == 'DEPOT' and any( order for order in self.model.orders if not order.is_picked_up ):
            self.model.request_for_routing()

import random

if __name__ == '__main__':
    random.seed(42)

    model = DemoModel()

    depot = Location( id= 'DEPOT', x= 0, y= 0 )
    depot.resource = Resource( model.env, 1 )
    model.add_location( depot )

    for i in range(5):
        x = random.randint( -10, 10 )
        y = random.randint( -10, 10 )
        customer_location = Location( id= f'CUSTOMER {i+1}', x= x, y= y )
        model.add_location( customer_location )

        order = Order( id= f'O-{i+1}' )
        order.pickup_location = depot
        order.delivery_location = customer_location
        order.release_date = 0
        order.pickup_duration = 2
        order.delivery_duration = 3
        model.request_order( order, decision_point_on_request= True )

    for i in range(2):
        vehicle = Truck( f'TRUCK-{i+1}' )
        vehicle.initial_location = depot
        model.add_vehicle( vehicle )

    model.run()
