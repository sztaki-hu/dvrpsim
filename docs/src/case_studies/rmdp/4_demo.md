# Demo routing algorithm

The demo (external) routing algorithm is also implemented in Python, in the function ``routing`` in the file ``routing/demo_algorithm``.
The simulator (i.e., the routing callback) and the demo routing algorithm interact through files.

``` mermaid
---
title: Routing callback
---
graph TB
    subgraph era[Demo routing algorithm]
        direction LR
        d[read state from file] --> e[routing]
        e --> f[write decision to file]
    end
    a[write state to file] --> era
    era --> c[read decision from file]
```

***

## Routing callback

The routing callback uses function ``file_based_routing_via_direct_function_call`` to communicate with the routing algorithm.

1. The state is written to the appropriate file.
2. The routing algorithm is invoked.
3. The decision is read from the corresponding file.

```python
from routing.demo_algorithm import routing

class RMDPModel(Model):
    def __init__( self ) -> None:
        super().__init__()

    def routing_callback(self) -> Any:
        """
        The external routing algorithm is implemented in a python module:
        
            routing.demo_algorithm.routing( state_file, decision_file )
        """

        state_filepath    = os.path.join( os.getcwd(), 'examples', 'rmdp', 'routing', 'data_interaction', 'state.json' )
        decision_filepath = os.path.join( os.getcwd(), 'examples', 'rmdp', 'routing', 'data_interaction', 'decision.json' )

        state = self.get_state()

        decision = file_based_routing_via_direct_function_call( state, state_filepath, decision_filepath, routing, state_filepath, decision_filepath )

        return decision
```

***

## Routing algorithm

1. The state is read from the corresponding file.
2. This primitive routing algorithm collects the unassigned orders and assigns them to the vehicles.
The incumbent order is assigned to the vehicle with the shortest route (in terms of number of visits).
3. The decision is written to the appropriate file.

```python
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
```
