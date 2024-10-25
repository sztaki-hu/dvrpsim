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
from dpdp_routing import dpdp_module_routing, get_dpdp_state

class DPDPModel(Model):
    def __init__(self) -> None:
        super().__init__()

    def get_state(self) -> Dict[str, Dict]:
        return get_dpdp_state(self)

    def routing_callback(self) -> Any:
        interaction_directory   = os.path.join( os.getcwd(), 'examples', 'dpdp', 'routing', 'data_interaction' )
        vehicle_info_file       = os.path.join( interaction_directory, 'vehicle_info.json' )
        ongoing_orders_file     = os.path.join( interaction_directory, 'ongoing_order_items.json' )
        unallocated_orders_file = os.path.join( interaction_directory, 'unallocated_order_items.json' )
        destination_file        = os.path.join( interaction_directory, 'output_destination.json' )
        routes_file             = os.path.join( interaction_directory, 'output_route.json' )

        state = self.get_state()
        
        decision = dpdp_module_routing(
            self, state,
            vehicle_info_file, unallocated_orders_file, ongoing_orders_file, destination_file, routes_file,
            'routing.demo_algorithm', 'routing', vehicle_info_file, ongoing_orders_file, unallocated_orders_file, destination_file, routes_file
        )

        return decision
```

***

## Routing algorithm

1. The state is read from the corresponding file.
2. The primitive routing algorithm collects the unassigned orders and assigns them to the vehicles cyclically.
The incumbent order is assigned to the end of the chosen vehicle as separates pickup and delivery nodes.
3. The decision is written to the appropriate file.
