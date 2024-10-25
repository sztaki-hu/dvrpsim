from typing import Dict

import json

def __read_state( state_file:str ) -> Dict[str,dict]:
    with open ( state_file, 'r' ) as json_file:
        return json.load( json_file )
    
def __write_decision( routes:dict, decision_file:str ) -> None:
    with open( decision_file, 'w' ) as json_file:
        json.dump( routes, json_file, indent= 2 )
    
def routing( state_file:str, decision_file:str ) -> None:
    state = __read_state( state_file )

    # collect unassigned orders
    unassigned_orders = [ order_id for order_id in state['open_orders'].keys()
        if state['open_orders'][order_id]['assigned_vehicle'] is None
    ]

    # copy current routes into the decision
    decision = {
        'vehicles': {
            vehicle_id : {
                'current_visit': None,
                'next_visits': [ {
                    'location': visit['location'],
                    'pickup_list': visit['pickup_list'],
                    'delivery_list': visit['delivery_list']
                } for visit in vehicle_state['next_visits'] ]
            } for vehicle_id, vehicle_state in state['vehicles'].items()
        },
        'orders': {}
    }

    # primitive assignment
    for order_id in unassigned_orders:
        if state['time'] + 20 < state['open_orders'][order_id]['due_date']:
            decision['orders'][order_id] = {
                'status': 'postponed',
                'postponed_until': state['time'] + 10
            }

        else:            
            decision['orders'][order_id] = { 'status': 'accepted' }

            vehicle_id = sorted( decision['vehicles'].keys(), key= lambda vehicle_id : len(decision['vehicles'][vehicle_id]['next_visits']) )[0]

            decision['vehicles'][vehicle_id]['next_visits'].append( {
                'location': state['open_orders'][order_id]['pickup_location'],
                'pickup_list': [ order_id ]
            } )

            decision['vehicles'][vehicle_id]['next_visits'].append( {
                'location': state['open_orders'][order_id]['delivery_location'],
                'delivery_list': [ order_id ]
            } )

    __write_decision( decision, decision_file )

if __name__ == '__main__':
    import os

    interaction_directory = os.path.join( os.getcwd(), 'examples', 'rmdp', 'routing', 'data_interaction' )
    state_file            = os.path.join( interaction_directory, 'state.json' )
    decision_file         = os.path.join( interaction_directory, 'decision.json' )

    routing( state_file, decision_file )
