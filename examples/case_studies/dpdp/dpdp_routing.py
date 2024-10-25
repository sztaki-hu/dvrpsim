import json
import os

from typing import Dict

from dvrpsim               import Model, Visit, Location
from dvrpsim.utils.routing import call_module_function, call_algorithm_in_subprocess

def calculate_earliest_departure_times_at_location( model:Model, location:Location ):
    vehicles = [ vehicle for vehicle in model.vehicles if vehicle.is_at_location and vehicle.current_location == location ]
    vehicles.sort( key = lambda vehicle : vehicle.current_visit.arrival_time )

    service_ends  = {}
    reservation_list = []

    for vehicle in vehicles:
        if not vehicle.has_previous_visit:
            service_ends[vehicle.id] = 0
            continue # vehicle is at its initial location

        service_time = model.private_data.get( 'docking_time' )
        service_time += sum( model.private_data.get( 'loading_time' ) * order.quantity for order in vehicle.current_visit.pickup_list )
        service_time += sum( model.private_data.get( 'unloading_time' ) * order.quantity for order in vehicle.current_visit.delivery_list )

        if vehicle.current_visit.service_finish_time is not None:
            service_ends[vehicle.id] = vehicle.current_visit.service_finish_time
            
        elif vehicle.current_visit.service_start_time is not None:
            service_ends[vehicle.id] = vehicle.current_visit.service_start_time + service_time
            
        elif len(reservation_list) < location.resource.capacity:
            service_ends[vehicle.id] = vehicle.current_visit.arrival_time + service_time

        else:
            service_started = max( vehicle.current_visit.arrival_time, service_ends[reservation_list[-location.resource.capacity].id] )
            service_ends[vehicle.id] = service_started + service_time

        reservation_list.append( vehicle )
        reservation_list.sort( key = lambda vehicle : service_ends[vehicle.id] )

    return { vehicle.id : max( model.env.now, service_ends[vehicle.id] ) for vehicle in vehicles }

def calculate_earliest_departure_times( model:Model ):
    departure_times = { vehicle.id : None for vehicle in model.vehicles }

    for vehicle in model.vehicles:
        if not vehicle.is_at_location:
            continue

        if departure_times[vehicle.id] is not None:
            continue # already calculated

        departure_times_at_location = calculate_earliest_departure_times_at_location( model, vehicle.current_visit.location )

        for vehicle_id, departure_time in departure_times_at_location.items():
            departure_times[vehicle.id] = departure_time

    return departure_times

def get_dpdp_state( model:Model ) -> Dict:
    state = {
        'vehicle_info':       [],
        'unallocated_orders': [],
        'ongoing_orders':     []
    }

    departure_times = calculate_earliest_departure_times( model )

    for vehicle in model.vehicles:
        expected_arrival_time = 0

        if vehicle.has_next_visit:
            if vehicle.is_at_location:
                expected_arrival_time = departure_times[vehicle.id] + model.private_data.get( 'travel_times' ).get( (vehicle.current_location.id, vehicle.next_location.id ), 0 )
            else:
                expected_arrival_time = vehicle.previous_visit.departure_time + model.private_data.get( 'travel_times' ).get( ( vehicle.previous_location.id, vehicle.next_location.id ), 0 )

        state['vehicle_info'].append( {
            'id':                             vehicle.id,
            'capacity':                       vehicle.capacity,
            'update_time':                    model.env.now,
            'cur_factory_id' :                vehicle.current_visit.location.id  if vehicle.is_at_location else "",
            'arrive_time_at_current_factory': vehicle.current_visit.arrival_time if vehicle.is_at_location else 0,
            'leave_time_at_current_factory':  departure_times[vehicle.id]        if vehicle.is_at_location else 0,
            'carrying_items':                 [ order.id for order in vehicle.loaded_orders_after_current_visit ],
            'destination': {
                'factory_id':         vehicle.next_visit.location.id,
                'delivery_item_list': [ order.id for order in vehicle.next_visit.delivery_list ],
                'pickup_item_list':   [ order.id for order in vehicle.next_visit.pickup_list ],
                'arrive_time':        expected_arrival_time,
                'leave_time':         0
            } if vehicle.has_next_visit else None
        } )

    unallocated_orders = [ order for order in model.open_orders if not order.is_picked_up ]
    ongoing_orders     = list(model.orders_under_delivery)

    for vehicle in model.vehicles:
        if vehicle.is_on_the_way:
            continue

        for order in vehicle.current_visit.delivery_list:
            if order in ongoing_orders:
                ongoing_orders.remove( order )

        for order in vehicle.current_visit.pickup_list:
            if order in unallocated_orders:
                unallocated_orders.remove( order )
                ongoing_orders.append( order )

    for item in unallocated_orders:
        state['unallocated_orders'].append( {
            'id':                        item.id,
            'order_id':                  item.original_id,
            'demand':                    item.quantity,
            'pickup_factory_id':         item.pickup_location.id,
            'delivery_factory_id':       item.delivery_location.id,
            'creation_time':             item.release_date,
            'committed_completion_time': item.due_date,
            'load_time':                 model.private_data['loading_time'] * item.quantity,
            'unload_time':               model.private_data['unloading_time'] * item.quantity,
        } )
        
    for item in ongoing_orders:
        state['ongoing_orders'].append( {
            'id':                        item.id,
            'order_id':                  item.original_id,
            'demand':                    item.quantity,
            'pickup_factory_id':         item.pickup_location.id,
            'delivery_factory_id':       item.delivery_location.id,
            'creation_time':             item.release_date,
            'committed_completion_time': item.due_date,
            'load_time':                 model.private_data['loading_time'] * item.quantity,
            'unload_time':               model.private_data['unloading_time'] * item.quantity,
        } )

    return state

def remove_old_dpdp_decision( destination_file:str, route_file:str ) -> None:
    try:
        os.remove( os.path.join( destination_file ) )

    except Exception as exc:
        pass

    try:
        os.remove( os.path.join( route_file ) )
                    
    except Exception as exc:
        pass

def write_dpdp_state( state:Dict, vehicle_info_file:str, unallocated_orders_file:str, ongoing_orders_file:str ) -> None:
    with open( os.path.join( vehicle_info_file ), 'w' ) as jsonfile:
        json.dump( state['vehicle_info'], jsonfile, indent= 2 )

    with open( os.path.join( unallocated_orders_file ), 'w' ) as jsonfile:
        json.dump( state['unallocated_orders'], jsonfile, indent= 2 )

    with open( os.path.join( ongoing_orders_file ), 'w' ) as jsonfile:
        json.dump( state['ongoing_orders'], jsonfile, indent= 2 )

def read_dpdp_decision( destination_file:str, route_file:str ) -> Dict:
    decision = {
        'destinations': {},
        'routes': {}
    }

    with open( os.path.join( destination_file ), 'r' ) as jsonfile:
        decision['destinations'] = json.load( jsonfile )

    with open( os.path.join( route_file ), 'r' ) as jsonfile:
        decision['routes'] = json.load( jsonfile )

    return decision

def transform_dpdp_decision( model:Model, raw_decision:Dict ) -> Dict:
    routes:Dict[str,dict] = { vehicle.id: {} for vehicle in model.vehicles }

    for vehicle_id, raw_visit in raw_decision['destinations'].items():
        routes[vehicle_id] = {
            'current_visit': None,
            'next_visits':   []
        }

        if raw_visit is None:
            continue

        routes[vehicle_id]['next_visits'].append( {
            'location':      raw_visit['factory_id'],
            'pickup_list':   raw_visit['pickup_item_list'][:],
            'delivery_list': raw_visit['delivery_item_list'][:]
        } )

    for vehicle_id, visits in raw_decision['routes'].items():
        for raw_visit in visits:

            routes[vehicle_id]['next_visits'].append( {
                'location':      raw_visit['factory_id'],
                'pickup_list':   raw_visit['pickup_item_list'][:],
                'delivery_list': raw_visit['delivery_item_list'][:]
            } )

    return {
        'vehicles': routes,
        'orders': {
            order.id : { 'status': 'accepted' } for order in model.open_orders
        }
    }

def dpdp_module_routing(
    model:Model, state:dict,
    vehicle_info_file:str, unallocated_orders_file:str, ongoing_orders_file:str,
    destination_file:str, route_file:str,
    module_name:str, function_name:str, *args, **kwargs ):
    
    # delete old decision file, if any
    remove_old_dpdp_decision( destination_file, route_file )

    # write state file
    write_dpdp_state( state, vehicle_info_file, unallocated_orders_file, ongoing_orders_file )

    # call external algorithm
    call_module_function( module_name, function_name, *args, **kwargs )

    # read decision
    raw_decision = read_dpdp_decision( destination_file, route_file )

    # transform decision
    decision = transform_dpdp_decision( model, raw_decision )

    return decision

def dpdp_subprocess_routing(
    model:Model, state:dict,
    vehicle_info_file:str, unallocated_orders_file:str, ongoing_orders_file:str,
    destination_file:str, route_file:str,
    algorithm_calling_command ):
    
    # delete old decision file, if any
    remove_old_dpdp_decision( destination_file, route_file )

    # write state file
    write_dpdp_state( state, vehicle_info_file, unallocated_orders_file, ongoing_orders_file )

    # call external algorithm
    call_algorithm_in_subprocess( algorithm_calling_command )

    # read decision
    raw_decision = read_dpdp_decision( destination_file, route_file )

    # transform decision
    decision = transform_dpdp_decision( model, raw_decision )

    return decision
