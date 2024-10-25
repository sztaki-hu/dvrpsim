def setup_dvrpsim_import():
    import sys, pathlib, importlib.util

    if importlib.util.find_spec( 'dvrpsim' ) is None:
        source_path = str( pathlib.Path(__file__).resolve().parents[3] / 'src' )
        
        if source_path not in sys.path:
            sys.path.insert(0, source_path)
            
        print( f'module "dvrpsim" will be imported from "{source_path}"' )

setup_dvrpsim_import()

import os

from typing import Any, Dict

from dvrpsim.model import Model, Vehicle, Location, Order, ModelError

from dvrpsim.utils.order_providers import order_provider
from dvrpsim.utils.routing         import create_directory, file_based_routing_via_direct_function_call
from dvrpsim.utils.statistics      import collect_order_statistics, collect_vehicle_statistics, print_statistics

from dvrpsim.utils.distances import great_circle_distance

from rmdp_problemdata import read_rmdp_problem
from routing.demo_algorithm import routing

class RMDPDriver(Vehicle):
    def __init__( self, id:str ) -> None:
        super().__init__(id)

    def travel_distance( self, origin:Location, destination:Location ) -> float:
        """
        "(...) multiplying Euclidean distances by a factor of 1.4 closely approximates the relationship between Euclidean and street distances."
        """
        return 1.4 * great_circle_distance( origin.x, origin.y, destination.x, destination.y )
    
    def travel_time( self, origin:Location, destination:Location ) -> float:
        """
        "(...) assuming the travel speed over the resulting distances is 40 kilometers per hour."
        """
        travel_time = 60 * self.travel_distance( origin, destination ) / 40.0

        return round( travel_time )
    
    def _preservice(self):
        """
        "(...) the driver may need to wait for the order's completion when arriving to a restaurant."
        """
        waiting_time = max( ( self.model.private_data['orders'][order.id]['ready_time']
            for order in self.current_visit.pickup_list ), default= 0 ) - self.model.env.now

        if 0 < waiting_time:
            self.model.log.custom( 'waiting for food...', vehicle= self )
            yield self.model.env.medium_timeout( waiting_time )

class RMDPModel(Model):
    def __init__( self ) -> None:
        super().__init__()

    def init(self):
        # create data interaction directory for file-based routing
        interaction_directory = os.path.join( os.path.dirname( __file__ ), 'routing', 'data_interaction' )
        self.log.info( f'(initialization) creating data interaction directory "{interaction_directory}"' )
        create_directory( interaction_directory )

    def routing_callback(self) -> Any:
        """
        The external routing algorithm is implemented in a python module:
        
            routing.demo_algorithm.routing( state_file, decision_file )
        """
        interaction_directory = os.path.join( os.path.dirname( __file__ ), 'routing', 'data_interaction' )
        state_filepath        = os.path.join( interaction_directory, 'state.json' )
        decision_filepath     = os.path.join( interaction_directory, 'decision.json' )

        state = self.get_state()

        decision = file_based_routing_via_direct_function_call( state, state_filepath, decision_filepath, routing, state_filepath, decision_filepath )

        return decision

def build_rmdp_model( probdata:Dict[str,dict] ) -> Model:    
    # create model
    model = RMDPModel()
    model.private_data = probdata

    # create and add locations
    for location_id, location_data in probdata['locations'].items():
        location = Location( location_id )
        
        location.x = location_data['lon']
        location.y = location_data['lat']

        model.add_location( location )

    # create and add orders
    orders = []

    for order_id, order_data in probdata['orders'].items():        
        order = Order( order_data['id'] )

        order.release_date      = order_data['release_date']
        order.due_date          = order_data['due_date']
        order.pickup_location   = model.get_location_by_id( order_data['pickup_location'] )
        order.delivery_location = model.get_location_by_id( order_data['delivery_location'] )

        if order.pickup_location is None:
            raise ModelError( f'unknown pickup location for order {order_id}: {order_data["pickup_location"]}' )

        if order.delivery_location is None:
            raise ModelError( f'unknown delivery location for order {order_id}: {order_data["delivery_location"]}' )

        order.pickup_duration   = 2 # "The service time (...) at a restaurant, once the food is ready, is two minutes."        
        order.delivery_duration = 2 # "The service time at a customer (...) is two minutes.
                
        orders.append( order )

    # create and add vehicles
    for vehicle_id, vehicle_data in probdata['vehicles'].items():
        vehicle = RMDPDriver( vehicle_id )
        vehicle.initial_location = model.get_location_by_id( vehicle_data['initial_location'] )
        
        if vehicle.initial_location is None:
            raise ModelError( f'unknown initial location for order {vehicle_id}: {vehicle_data["initial_location"]}' )

        model.add_vehicle( vehicle )

    # set callbacks
    model.env.process( order_provider( model, orders, decision_point_on_request= True ) )

    return model

if __name__ == '__main__':
    data_directory = os.path.join( os.path.dirname( __file__ ), 'data' )

    probdata = read_rmdp_problem(
        os.path.join( data_directory, 'restaurants.txt' ),
        os.path.join( data_directory, 'vehicles.txt' ),
        os.path.join( data_directory, '180_2.txt' ),
        1
    )

    model = build_rmdp_model( probdata )
    model.run()

    print_statistics( collect_vehicle_statistics( model ) )
    print_statistics( collect_order_statistics( model ), onebyone= False )
    