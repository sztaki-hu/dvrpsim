# Demo routing algorithm

The demo (external) routing algorithm is also implemented in Python, in the function ``routing`` in the file ``routing/demo_algorithm``.
The simulator (i.e., the routing callback) and the demo routing algorithm interact directly.

``` mermaid
sequenceDiagram
    participant A as Simulator
    participant B as Demo routing algorithm

    A->>+B: state
    Note right of B: routing
    B->>-A: decision
```

***

## Routing callback

The routing callback directly calls the function ``routing``.

```python
from routing.demo_algorithm import routing

class SDDPModel(Model):

    def routing_callback(self) -> Any:
        """
        The routing algorithm is implemented in a python module:
            routing.demo_algorithm.routing( state )
        """
        state = self.get_state()
        state['static'] = self.static_data
        
        decision = routing( state )

        return decision
```

***

## Routing algorithm

The routing algorithm does the following steps:

1. Collects unassigned orders and idle vehicles located at the depot.
2. Attempts to insert the orders one by one into the (possibly newly created) route of the vehicles.
    - If it is too late to deliver the order, it will be rejected.
    - If it is not possible to feasibly insert an order into any of the routes, it will be postponed.
    - Otherwise, the order will be accepted and inserted into the corresponding route.
3. Calculates a maximum delay time for each vehicle located at the depot to delay their departure, if possible.
