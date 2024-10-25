# A closer look at the routing procedure

Before we create our first routing callback, let's take a closer look at the routing (or decision making) procedure that connects the simulator and the external routing algorithm!

***

## Main overview

The routing procedure consists of the following steps.

1. **State.** The external routing algorithm is provided with the current *state*, which describes all the information available to make a decision.
2. **Routing.** The external routing algorithm is executed.
3. **Decision.** The external routing algorithm returns a *decision* to the simulator.

``` mermaid
sequenceDiagram
    participant A as Simulator
    participant B as External routing algorithm
    A->>+B: state
    Note right of B: routing
    B->>-A: decision
```

!!! note
    States and decisions do not contain objects, but are pure JSON data.
    The reason for this is that the implementation of the external routing algorithm is not tied to Python, but can be implemented in any programming language.
    In the latter case, the simulator and the external routing algorithm can communicate with each other via JSON files, for example.

***

## States

A state describes all the information available to make a decision.
By default, a state consists of the following elements:

- the current simulation time (see ``time``)
- the current status of the vehicles (see ``vehicles``)
- the current status of the orders (see ``open_orders`` and ``canceled_orders``)

!!! tip "Custom states"
    States can also be customized by overriding the corresponding model method (``get_state``).

### Vehicle status

A vehicle is always in one of the following statuses (``status``):

- ``EN_ROUTE``: the vehicle is currently *en route*, i.e., on the way to its next location.
- ``UNDER_SERVICE``: the vehicle is currently *under service*
- ``WAITING_FOR_SERVICE``: the vehicle has arrived at a location and currently *waiting for the service*
- ``IDLE``: the vehicle is at a location and is ready to depart

When the vehicle is en route, its previous visit (``previous_visit``) is given, describing where the vehicle was located (``location``) and when the vehicle departed (``departure_time``).
Otherwise, when the vehicle is at a location, its current visit is given (``current_visit``) as follows.
The location (``location``) refers to the current location, and the arrival time (``arrival_time``) refers to the time when the vehicle arrived.
If the vehicle is waiting for service, the service start time is not set (``None``).
When the vehicle is under service, the service start time is set, but the service finish time is not.
Finally, when the vehicle is idle, only the departure time of the visit is not set.

The list ``next_visits`` describes the tentative route plan that the vehicle is currently following, if any.

### Order status

We say that an order is *open* if it is not rejected, not canceled, and not delivered.
The open orders are given in the dictionary ``open_orders``, which maps order ids to order statuses.
The status of an order contains all the currently available information about the order.

The dictionary ``canceled_orders`` specifies those orders that have been canceled and therefore must not be included in the vehicle routes anymore.

***

## Decisions

The *decision on orders* shows whether the orders are accepted, rejected or postponed.
The *decision on vehicles* describes the updated routes of the vehicles.

### Decision on orders

Orders can be accepted or may be rejected.
The decision on an order may also be postponed until a given time.

```python
# example for decisions on orders

'orders': {
    'O-1': { 'status': 'accepted' },
    'O-2': { 'status': 'rejected' },
    'O-3': { 'status': 'postponed', 'postponed_until': 42 }
}
```

### Decision on vehicles

Updated vehicles must be provided in the decision.
Both the current visit (``current_visit``) and the next visits (``next_visits``) can be modified, if any.
For each visit, the corresponding location (``location``) and the pickup and delivery lists (``pickup_list`` and ``delivery_list``) must be given.
For next visits, an earliest start time (``earliest_start_time``) can also be specified.

!!! warning
    The route of the vehicles can be modified subject to certain reasonable restrictions.

    1. The current visits of a vehicle (i.e., the pickup and delivery lists), if any, cannot be modified if the service has already started.

    2. The location of the next visit of an en route vehicle cannot be modified.

    Moreover, canceled and rejected orders should not be included in the vehicle routes.

!!! tip "Some technical simplifications"

    - If the entire route of a vehicle remains unchanged, the status of the vehicle need not to be provided in the decision.

    - If the current visit of a vehicle waiting for service is not changed, the current visit need not be provided.

    - If none of the next visits of a vehicle waiting for service is changed, the next visists need not be provided.

    - Empty pickup and delivery lists need not be provided.

```python
# example for decisions on vehicles

'vehicles': {
    'VEHICLE-1': None,
    'VEHICLE-2': {
        'next_visits': [
            {
                'location': 'DEPOT',
                'pickup_list': ['O-1']
            },
            {
                'location': 'CUSTOMER 1',
                'delivery_list': ['O-1']
            },
            {
                'location': 'DEPOT'
            }
        ]
    }
}
```

***

## Routing callback

After routing is requested (i.e., a decision point is imposed), the routing procedure is started in a separate process, in which the method ``routing_callback`` of the model is invoked.
Here we can do the connection between the simulator and the external routing algorithm.
Let's look at the "default" routing callback, which rejected all orders!

### Default routing callback

In the case of the default routing callback, there is no external routing algorithm, but a dummy decision procedure is implemented in this callback.
The procedure first gets the current state and then returns a decision that rejects all open orders.

=== "Default callback"

    ```python
    def routing_callback(self) -> Any:
        """
        This callback invokes the external routing algorithm.
        """
        self.log.warning( 'routing callback is not implemented (all orders will be rejected)' )

        state = self.get_state()

        return {
            'vehicles': {},
            'orders': {
                order_id: {
                    'status': 'rejected'
                } for order_id in state['open_orders']
            }
        }
    ```

=== "First state"

    ```python
    {
        'time': 8,
        'vehicles': {},
        'open_orders': {
            'O-1': {
                'id': 'O-1',
                'original_id': 'O-1',
                'quantity': 0,
                'release_date': 8,
                'due_date': None,
                'pickup_location': 'DEPOT',
                'earliest_service_start_pickup': None,
                'latest_service_start_pickup': None,
                'delivery_location': 'CUSTOMER 1',
                'earliest_service_start_delivery': None,
                'latest_service_start_delivery': None,
                'pickup_time': None,
                'pickup_vehicle': None
            }
        },
        'cancelled_orders': [],
        'aux': {}
    }
    ```

=== "First decision"

    ```python
    {
        'vehicles': {},
        'orders': {
            'O-1': {
                'status': 'rejected'
            }
        }
    }
    ```
