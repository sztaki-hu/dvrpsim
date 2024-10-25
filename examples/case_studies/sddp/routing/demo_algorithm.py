from typing import Dict
import json

from dvrpsim.utils.distances import manhattan_distance
    
def __read_state( state_file:str ) -> Dict[str,dict]:
    with open ( state_file, 'r' ) as json_file:
        return json.load( json_file )
    
def __write_decision( routes:dict, decision_file:str ) -> None:
    with open( decision_file, 'w' ) as json_file:
        json.dump( routes, json_file, indent= 2 )

def _travel_time( state, vehicle_id:str, origin_id:str, destination_id:str ):
    travel_time = 60 * manhattan_distance(
        state['static']['locations'][origin_id]['x'],
        state['static']['locations'][origin_id]['y'],
        state['static']['locations'][destination_id]['x'],
        state['static']['locations'][destination_id]['y']
    ) / state['static']['vehicles'][vehicle_id]['speed']

    return round(travel_time)

def _check_route_feasibility( state:dict, vehicle_id:str, route:list ) -> bool:
    if len(route) == 0:
        return True
    
    if len(route) == 1:
        raise Exception( 'unexpected route length' )
    
    assert route[0]['location'] == 'depot', f'the first visit ({route[0]["location"]}) is not the depot!'
       
    current_time = state['time']

    for i in range(len(route)-1):
        curr_visit = route[i]
        next_visit = route[i+1]

        current_time += _travel_time( state, vehicle_id, curr_visit['location'], next_visit['location'] )
        
        current_time = max( current_time, max( (state['open_orders'][order_id]['earliest_delivery_start'] for order_id in next_visit['delivery_list']), default= 0 ) )

        if min( (state['open_orders'][order_id]['latest_delivery_start'] for order_id in next_visit['delivery_list']), default= current_time ) < current_time:
            return False # if the vehicle arrives at the location too late, then the route is infeasible
    
    return current_time <= state['static']['depot_deadline']

def _calculate_maximum_delay_time( state:dict, vehicle_id:str, route:list ):
    D = [0]  # vehicle departure time
    A = [0]  # vehicle arrival time
    W = [0]  # waiting time to begin service
    CW = [0] # cumulative waiting time
    DS = [0] # deadline slack
    mdt = 0

    if len(route) >= 2:
        for j in range(1,len(route)-1):
            prev_visit = route[j-1]
            next_visit = route[j]

            order = state['open_orders'][next_visit['delivery_list'][0]]
            e_j = order['earliest_delivery_start']
            l_j = order['latest_delivery_start']

            A.append( D[j-1] + _travel_time( state, vehicle_id, prev_visit['location'], next_visit['location']) )
            D.append(max(A[j], e_j))
            W.append(max(e_j - A[j], 0))
            CW.append(sum(W[:(j+1)]))
            DS.append(l_j-A[j])

        mdt = min(min(DS[j-1] + CW[j-2] if j > 1 else float('inf'), CW[-1]) for j in range(1, len(DS) + 1))

    return mdt

def _assign_order( state, decision, order_id, vehicle_id ) -> bool:
    current_route = decision['vehicles'][vehicle_id]['next_visits'][:] # copy

    if len(current_route) == 1:
        raise Exception( 'unexpected route length' )

    if len(current_route) == 0:
        current_route.append({
                'location': 'depot',
                'pickup_list': [],
                'delivery_list': []
            } ) # visit to pickup orders
        
        current_route.append({
                'location': 'depot',
                'pickup_list': [],
                'delivery_list': []
            } ) # return to the depot
        
    new_visit = {
        'location': state['open_orders'][order_id]['delivery_location'],
        'pickup_list': [],
        'delivery_list': [ order_id ]
    }

    for i in range(1,len(current_route)):
        current_route[0]['pickup_list'].append( order_id )
        current_route.insert( i, new_visit )

        if _check_route_feasibility( state, vehicle_id, current_route ):
            current_route[0]['earliest_start_time'] = _calculate_maximum_delay_time( state, vehicle_id, current_route )
            decision['vehicles'][vehicle_id]['next_visits'] = current_route

            return True
        
        del current_route[i]
        current_route[0]['pickup_list'].remove( order_id )

    return False        
    
def routing_through_files( state_file:str, decision_file:str ) -> None:
    state  = __read_state( state_file )
    decision = routing( state )
    __write_decision( decision, decision_file )

def routing( state:dict ) -> dict:
    # collect unassigned vehicles
    unassigned_orders = [ order_id for order_id in state['open_orders'].keys()
        if state['open_orders'][order_id]['assigned_vehicle'] is None
    ]

    # collect idle vehicles at the depot
    depot_vehicles = [ vehicle_id for vehicle_id, vehicle_state in state['vehicles'].items()
        if vehicle_state['status'] == 'IDLE'
        and vehicle_state['current_visit']['location'] == 'depot'
    ]
    
    # copy current routed into decision
    decision = {
        'vehicles': {},
        'orders': {},
    }

    decision['vehicles'] = {
        vehicle_id : {
            'next_visits': [
                {
                    'location': visit['location'],
                    'pickup_list': visit['pickup_list'],
                    'delivery_list': visit['delivery_list']
                } for visit in vehicle_state['next_visits']
            ] if vehicle_id in depot_vehicles else None
        } for vehicle_id, vehicle_state in state['vehicles'].items()
    }

    # assign / reject remaining orders
    for order_id in unassigned_orders:
        # if the order is already delayed, we reject it
        if state['time'] > state['open_orders'][order_id]['latest_delivery_start']:
            decision['orders'][order_id] = { 'status': 'rejected' }

        else:
            order_assigned = False

            for vehicle_id in depot_vehicles:
                if _assign_order( state, decision, order_id, vehicle_id ):
                    order_assigned = True
                    break

            if order_assigned:
                decision['orders'][order_id] = { 'status': 'accepted' }

            else:
                decision['orders'][order_id] = {
                    'status': 'postponed',
                    'postponed_until': state['time'] + 60
                }

    return decision
