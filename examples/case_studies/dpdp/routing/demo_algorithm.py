
from typing import Tuple, Dict

import json

def __read_state( vehicle_info_file:str, ongoing_order_items_file:str, unallocated_order_items_file:str ) -> Tuple[Dict[str,dict],Dict[str,dict],Dict[str,dict]]:
    """Read state from the corresponding files."""
    vehicle_info            = None
    ongoing_order_items     = None
    unallocated_order_items = None

    with open( vehicle_info_file, 'r' ) as jsonfile:
        vehicle_info = { vehicle['id'] : vehicle for vehicle in json.load( jsonfile ) }

    with open( ongoing_order_items_file, 'r' ) as jsonfile:
        ongoing_order_items = { item['id'] : item for item in json.load( jsonfile ) }

    with open( unallocated_order_items_file, 'r' ) as jsonfile:
        unallocated_order_items = { item['id'] : item for item in json.load( jsonfile ) }

    return vehicle_info, ongoing_order_items, unallocated_order_items

def __run_naive_routing( vehicle_info:Dict[str,dict], ongoing_order_items:Dict[str,dict], unallocated_order_items:Dict[str,dict] ) -> Tuple[Dict[str,dict],Dict[str,list]]:
    """
    Naive routing algorithm.
    
    Vehicle routes will look like: [pickup an order] -> [deliver the order] -> [pickup another order] -> [deliver the order] -> ...

    Orders are assigned to vehicles cyclically.
    """
    dispatched_items = set()

    # 1. Initialize routes
    routes = { vehicle_id : [] for vehicle_id in vehicle_info.keys() }

    for vehicle_id, vehicle in vehicle_info.items():
        destination = vehicle['destination']

        if destination is not None:
            routes[vehicle['id']].append( {
                'factory_id':         destination['factory_id'],
                'arrive_time':        destination['arrive_time'],
                'leave_time':         destination['leave_time'],
                'delivery_item_list': destination['delivery_item_list'],
                'pickup_item_list':   destination['pickup_item_list']
            } )

            dispatched_items = dispatched_items.union( destination['delivery_item_list'] )

            if 0 < len(destination['pickup_item_list']):
                # a new location (deliver the picked up items) is inserted into the route
                delivery_location = unallocated_order_items[destination['pickup_item_list'][0]]['delivery_factory_id'] # NOTE : each item has the same delivery location

                routes[vehicle['id']].append( {
                        'factory_id':         delivery_location,
                        'arrive_time':        0,                                     # leave empty
                        'leave_time':         0,                                     # leave empty
                        'delivery_item_list': destination['pickup_item_list'][::-1], # deliver in reverse order
                        'pickup_item_list':   []                                     # no pickup
                } )

                dispatched_items = dispatched_items.union( destination['pickup_item_list'] )

    # 2. Dispatch further orders

    # collect orders
    orders:Dict[str,list] = {}

    for item_id, item in unallocated_order_items.items():
        if item_id in dispatched_items:
            continue # already dispatched

        if item['order_id'] not in orders.keys():
            orders[item['order_id']] = []
        
        orders[item['order_id']].append( item )

    # assign (small) orders to vehicles, cyclically 
    vehicle_list = [ vehicle for vehicle in vehicle_info.values() ]
    vehicle_idx  = 0

    for order, order_items in orders.items():
        pickup_location   = order_items[0]['pickup_factory_id']
        delivery_location = order_items[0]['delivery_factory_id']

        order_items.sort( key= lambda item : item['demand'], reverse= True )

        small_orders = [ [] ]

        for item in order_items:
            if int(vehicle_list[vehicle_idx]['capacity']) < sum( unallocated_order_items[i]['demand'] for i in small_orders[-1] ) + item['demand']:
                small_orders.append( [] )

            small_orders[-1].append( item['id'] )

        for small_order in small_orders:
            vehicle_id = vehicle_list[vehicle_idx]['id']

            # if the pickup location differs from the last delivery location, insert a new location to the route
            if 0 == len(routes[vehicle_id]) or routes[vehicle_id][-1]['factory_id'] != pickup_location:
                routes[vehicle_list[vehicle_idx]['id']].append( {
                    'factory_id':         pickup_location,
                    'arrive_time':        0,
                    'leave_time':         0,
                    'delivery_item_list': [],
                    'pickup_item_list':   []
                } )

            # set the pickup list at the last location
            routes[vehicle_id][-1]['pickup_item_list'] = small_order[:]

            # insert a new location (deliver the items in reverse order) to the route
            routes[vehicle_id].append( {
                'factory_id':         delivery_location,
                'arrive_time':        0,
                'leave_time':         0,
                'delivery_item_list': small_order[::-1],
                'pickup_item_list':   []
            } )

            vehicle_idx = (vehicle_idx + 1) % len(vehicle_list)

    # split routes into next visits, and future planned visits
    next_visits:Dict[str,dict]    = { vehicle_id : None for vehicle_id in routes.keys() }
    planned_visits:Dict[str,list] = { vehicle_id : []   for vehicle_id in routes.keys() }

    for vehicle_id, route in routes.items():
        vehicle = vehicle_info[vehicle_id]

        assert vehicle['destination'] is None or 0 < len(route), f'destination of vehicle {vehicle_id} has been lost!'
        
        if 0 < len(route):
            next_visits[vehicle_id]    = route[0]
            planned_visits[vehicle_id] = route[1:]

    return next_visits, planned_visits

def __write_decision( next_visits:Dict[str,dict], planned_visits:Dict[str,list], next_visits_file:str, planned_visits_file:str ) -> None:
    """Writes routes (next visits and future planned visits) into the corresponding files."""
    with open( next_visits_file, 'w' ) as jsonfile:
        json.dump( next_visits, jsonfile, indent= 2 )

    with open( planned_visits_file, 'w' ) as jsonfile:
        json.dump( planned_visits, jsonfile, indent= 2 )

def routing( vehicle_info_file:str, ongoing_order_items_file:str, unallocated_order_items_file:str, destination_file:str, routes_file:str ) -> None:
    # read statenext_visits_file
    vehicle_info, ongoing_order_items, unallocated_order_items = __read_state( vehicle_info_file, ongoing_order_items_file, unallocated_order_items_file )

    # initialize vehicle routes
    next_visits, planned_visits = __run_naive_routing( vehicle_info, ongoing_order_items, unallocated_order_items )

    # write decision
    __write_decision( next_visits, planned_visits, destination_file, routes_file )

    # print
    #print( 'SUCCESS' )
