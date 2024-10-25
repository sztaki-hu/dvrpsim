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

from dvrpsim import Model, Vehicle, Location, Order
from dvrpsim import ModelError

from dvrpsim.utils.distances       import manhattan_distance
from dvrpsim.utils.order_providers import order_provider
# from dvrpsim.utils.routing         import create_directory, file_based_routing_via_module_function_call
from dvrpsim.utils.statistics      import collect_vehicle_statistics, collect_order_statistics, print_statistics

from sddp_probdata import read_sddp_probdata
from routing.demo_algorithm import routing

class SDDPVehicle(Vehicle):
    def __init__( self, id:str ) -> None:
        super().__init__(id)

    def travel_distance( self, origin:Location, destination:Location ):
        """
        "(...) we first calculate the Manhattan distance between locations (...)"
        """
        return manhattan_distance( origin.x, origin.y, destination.x, destination.y )
    
    def travel_time( self, origin:Location, destination:Location ):
        return round( 60 * self.travel_distance( origin, destination ) / self.aux['speed'] )
    
class SDDPModel(Model):
    def __init__(self) -> None:
        super().__init__()

    def on_vehicle_arrival( self, vehicle:Vehicle ) -> None:
        """
        "(...) epoch occurs (...) as a result of (...) the following:
            1. a vehicle arrives at the depot (...)"
        """
        # check arrival at the depot from other location
        if vehicle.current_location.id == 'depot' and vehicle.previous_location.id != 'depot':
            self.request_for_routing()

    def on_order_request( self, order:Order ) -> None:
        """
        "(...) epoch occurs (...) as a result of (...) the following:
            2. a new request arrives and at least one vehicle is waiting at the depot."
        """
        if any( vehicle for vehicle in self.vehicles if vehicle.is_idle and vehicle.current_visit.location.id == 'depot' and not vehicle.has_next_visit ):
            self.request_for_routing()

    def init(self):
        # # file-based routing
        # # create data interaction directory for file-based routing
        # interaction_directory = os.path.join( os.path.dirname( __file__ ), 'routing', 'data_interaction' )
        # self.log.info( f'(initialization) creating data interaction directory "{interaction_directory}"' )
        # create_directory( interaction_directory )
        return
    
    def routing_callback(self) -> Any:
        """
        The routing algorithm is implemented in a python module:        
            routing.demo_algorithm.routing_through_files( state_file, decision_file )

        or:
            routing.demo_algorithm.routing( state )
        """
        state = self.get_state()
        state['static'] = self.public_data

        # # a) File-based routing
        # interaction_directory = os.path.join( os.path.dirname( __file__ ), 'routing', 'data_interaction' )
        # state_filepath        = os.path.join( interaction_directory, 'state.json' )
        # decision_filepath     = os.path.join( interaction_directory, 'decision.json' )
        
        # decision = file_based_routing_via_module_function_call( state, state_filepath, decision_filepath,
        #     'routing.demo_algorithm', 'routing_through_files', state_filepath, decision_filepath 
        # )
        
        # b) Direct routing
        decision = routing( state )

        return decision

def build_sddp_model( probdata:Dict[str,dict] ) -> Model:
    # create model
    model = SDDPModel()

    # set private data
    model.private_data = probdata

    # set public data
    model.public_data = probdata.copy()
    del model.public_data['orders']
    
    # create and add locations
    for location_id, location_data in probdata['locations'].items():
        location = Location( location_id )

        # parameters
        location.x = location_data['x']
        location.y = location_data['y']

        model.add_location( location )

    # create and add orders
    orders = []

    for order_id, order_data in probdata['orders'].items():
        order = Order( order_data['id'] )
        order.release_date = order_data['release_date']
        order.pickup_location = model.get_location_by_id( order_data['pickup_location'] )
        order.delivery_location = model.get_location_by_id( order_data['delivery_location'] )
        order.earliest_delivery_start = order_data['earliest_delivery_arrival']
        order.latest_delivery_start = order_data['latest_delivery_arrival']

        if order.pickup_location is None:
            raise ModelError( f'unknown pickup location for order {order_id}: {order_data["pickup_location"]}' )

        if order.delivery_location is None:
            raise ModelError( f'unknown delivery location for order {order_id}: {order_data["delivery_location"]}' )
        
        orders.append( order )

    model.env.process( order_provider( model, orders, decision_point_on_request= False ) )

    # create and add vehicles
    for vehicle_id, vehicle_data in probdata['vehicles'].items():        
        vehicle = SDDPVehicle( vehicle_id )
        vehicle.initial_location = model.get_location_by_id( vehicle_data['initial_location'] )
        vehicle.aux['speed'] = vehicle_data['speed']

        if vehicle.initial_location is None:
            raise ModelError( f'unknown initial location for order {vehicle_id}: {vehicle_data["initial_location"]}' )
        
        model.add_vehicle( vehicle )

    # set callbacks
    model.env.process( depot_deadline( model, probdata['depot_deadline'] ) )

    return model

def depot_deadline( model:Model, deadline:int ):
    yield model.env.high_timeout( deadline )

    model.log.custom( "*** DEPOT DEADLINE HAS PASSED ***" )

if __name__ == '__main__':
    data_directory = os.path.join( os.path.dirname( __file__ ), 'data' )
    orders_file    = os.path.join( data_directory, 'TWr_R_1_het1_2_actual_001.txt' )

    probdata = read_sddp_probdata( orders_file )
    model = build_sddp_model( probdata )
    model.run()

    print_statistics( collect_vehicle_statistics( model ) )
    print_statistics( collect_order_statistics( model ), onebyone= False )
