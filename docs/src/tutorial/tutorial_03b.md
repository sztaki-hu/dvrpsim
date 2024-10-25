# Our first routing callback

It's time to define a simple routing callback for our model!

In this short tutorial we will get familiar with the vehicles, where we will define a custom travel time callback, and we will impose decision points on vehicle arrivals.
We will also define a simple routing callback.

!!! info
    For the sake of simplicity, we also implement our demo routing algorithm in Python (in this file) and use direct interaction with the simulator.

***

## Vehicles

If we want to accept some orders, we need vehicles to deliver them.

!!! example "Example (custom vehicles)"
    Lets' define a custom vehicle class, say ``Truck``!
    Create a single instance and add it to the model.
    Set the depot as the initial location for the vehicle.

```python
from dvrpsim import Vehicle
```

```python
class Truck(Vehicle):
    def __init__( self, id:str ) -> None:
        super().__init__(id)
```

```python
vehicle = Truck( 'TRUCK' )
vehicle.initial_location = depot
model.add_vehicle( vehicle )
```

Now, we can assign orders to the vehicles.

***

## Custom routing policy I.

!!! example "Example (custom routing callback)"
    Let's try the following strange policy!
    If the vehicle is at the depot, we accept all unassigned orders and assign them to the vehicle that will deliver them in a single trip.
    Otherwise, if the vehicle is out of the depot, we reject all unassigned orders.

=== "Demo algorithm"
    ```python
    def demo_routing_algorithm( state:Dict[str,Any] ) -> Dict[str,Any]:
        # collect unassigned orders
        unassigned_orders = [ order_id for order_id in state['open_orders'].keys()
            if state['open_orders'][order_id]['assigned_vehicle'] is None
        ]

        # if none, there is nothing to do
        if len(unassigned_orders) == 0:
            return { 'vehicles': {}, 'orders': {} }

        # collect idle vehicles at the depot
        idle_vehicles = [ vehicle_id for vehicle_id, vehicle_state in state['vehicles'].items()
            if vehicle_state['status'] == 'IDLE'
            and vehicle_state['current_visit']['location'] == 'DEPOT'
        ]

        # if none, all orders are rejected
        if len(idle_vehicles) == 0:
            return {
                'vehicles': {},
                'orders': {
                    order_id: {
                        'status': 'rejected'
                    } for order_id in unassigned_orders
                }
            }

        # otherwise, orders are accepted and assigned to an idle vehicle
        vehicle_id = idle_vehicles[0]

        vehicle_route = []

        # pickup
        vehicle_route.append( {
            'location': 'DEPOT',
            'pickup_list': unassigned_orders
        } )

        # deliveries
        for order_id in unassigned_orders:
            vehicle_route.append( {
                'location': state['open_orders'][order_id]['delivery_location'],
                'delivery_list': [ order_id ]
            } )

        # depot return
        vehicle_route.append( {
            'location': 'DEPOT',
        } )

        return {
            'vehicles': {
                vehicle_id: {
                    'next_visits': vehicle_route
                }
            },
            'orders': {
                order_id: {
                    'status': 'accepted'
                } for order_id in unassigned_orders
            }
        }
    ```

=== "Custom callback"
    ```python
    class DemoModel(Model):
        def __init__(self) -> None:
            super().__init__()

        def routing_callback(self):
            state = self.get_state()

            return demo_routing_algorithm( state )
    ```

=== "Output"
    ```txt
    INFO    :        0.0 | 00:00:00 | START
    INFO    :        8.0 | 00:00:08 | order O-1 is requested (DEPOT -> CUSTOMER 1)
    INFO    :        8.0 | 00:00:08 | <<< routing >>>
    INFO    :        8.0 | 00:00:08 | TRUCK | service is started
    INFO    :        8.0 | 00:00:08 | TRUCK | order O-1 is picked up
    INFO    :        8.0 | 00:00:08 | TRUCK | service is finished
    INFO    :        8.0 | 00:00:08 | TRUCK | departed from DEPOT to CUSTOMER 1
    INFO    :        8.0 | 00:00:08 | TRUCK | arrived at CUSTOMER 1
    INFO    :        8.0 | 00:00:08 | TRUCK | service is started
    INFO    :        8.0 | 00:00:08 | TRUCK | order O-1 is delivered
    INFO    :        8.0 | 00:00:08 | TRUCK | service is finished
    INFO    :        8.0 | 00:00:08 | TRUCK | departed from CUSTOMER 1 to DEPOT
    INFO    :        8.0 | 00:00:08 | TRUCK | arrived at DEPOT
    INFO    :        8.0 | 00:00:08 | TRUCK | service is started
    INFO    :        8.0 | 00:00:08 | TRUCK | service is finished
    ...
    ```

Although we currently have only one vehicle, our algorithm is prepared for multiple vehicles:

1. We collect the open orders that have not yet been assigned to a vehicle.
   If all orders are assigned, there is nothing to do.
2. We collect the idle vehicles that located at the depot.
    1. If there is none, all unassigned orders will be rejected.
    2. Otherwise, all unassigned orders will be accpeted and assigned to a single vehicle to be delivered in one trip.

Our code works, however, the vehicle is currently traveling at the speed of light, which does not seem very realistic.

***

## Travel time callback

!!! example "Example (travel time callback)"
    Let's define a (still unrealistic) travel time callback where the travel time between any two locations is 5 units of time!

=== "Code snippet"
    ```python    
    class Truck(Vehicle):
        def __init__( self, id:str ) -> None:
            super().__init__(id)

        def travel_time(self, origin:Location, destination:Location) -> int | float:
            return 5
    ```

=== "Output"
    ```
    ...
    INFO    :        8.0 | 00:00:08 | TRUCK | departed from DEPOT to CUSTOMER 1
    INFO    :       13.0 | 00:00:13 | TRUCK | arrived at CUSTOMER 1
    INFO    :       13.0 | 00:00:13 | TRUCK | service is started
    INFO    :       13.0 | 00:00:13 | TRUCK | order O-1 is delivered
    INFO    :       13.0 | 00:00:13 | TRUCK | service is finished
    INFO    :       13.0 | 00:00:13 | TRUCK | departed from CUSTOMER 1 to DEPOT
    INFO    :       16.0 | 00:00:16 | order O-2 is requested (DEPOT -> CUSTOMER 2)
    INFO    :       16.0 | 00:00:16 | <<< routing >>>
    INFO    :       16.0 | 00:00:16 | order O-2 is rejected
    INFO    :       18.0 | 00:00:18 | TRUCK | arrived at DEPOT
    ...
    ```

Nice! The travel time between locations is now indeed 5 units of time.
As a result, the second order arrives at a time when the vehicle is out of the depot, so it is rejected.

***

## Custom routing policy II.

!!! example "Example"
    Let's modify the policy!
    We accept all orders, but we still do not assign them to vehicles out of the depot.

=== "Code snippet"

    ```python
    if len(idle_vehicles) == 0:
        return {
            'vehicles': {},
            'orders': {
                order_id: {
                    'status': 'accepted'
                } for order_id in unassigned_orders
            }
        }
    ```

=== "Output"
    ```txt
    ...
    INFO    :       13.0 | 00:00:13 | TRUCK | departed from CUSTOMER 1 to DEPOT
    INFO    :       16.0 | 00:00:16 | order O-2 is requested (DEPOT -> CUSTOMER 2)
    INFO    :       16.0 | 00:00:16 | <<< routing >>>
    INFO    :       18.0 | 00:00:18 | TRUCK | arrived at DEPOT
    INFO    :       18.0 | 00:00:18 | TRUCK | service is started
    INFO    :       18.0 | 00:00:18 | TRUCK | service is finished
    INFO    :       24.0 | 00:00:24 | order O-3 is requested (DEPOT -> CUSTOMER 3)
    INFO    :       24.0 | 00:00:24 | <<< routing >>>
    INFO    :       24.0 | 00:00:24 | TRUCK | service is started
    INFO    :       24.0 | 00:00:24 | TRUCK | order O-2 is picked up
    INFO    :       24.0 | 00:00:24 | TRUCK | order O-3 is picked up
    INFO    :       24.0 | 00:00:24 | TRUCK | service is finished
    INFO    :       24.0 | 00:00:24 | TRUCK | departed from DEPOT to CUSTOMER 2
    ...
    ```

Okay! Now the second order was picked up and delivered together with the third order.

***

However, if we set the travel time to 10, we do not have the opportunity to assign the last order to the vehicle:

=== "Code snippet"
    ```python    
    class Truck(Vehicle):
        def __init__( self, id:str ) -> None:
            super().__init__(id)

        def travel_time(self, origin:Location, destination:Location) -> int | float:
            return 10
    ```

=== "Output"
    ```txt
    ...
    INFO    :       62.0 | 00:01:02 | TRUCK | departed from CUSTOMER 4 to DEPOT
    INFO    :       72.0 | 00:01:12 | TRUCK | arrived at DEPOT
    INFO    :       72.0 | 00:01:12 | TRUCK | service is started
    INFO    :       72.0 | 00:01:12 | TRUCK | service is finished
    INFO    :       72.0 | 00:01:12 | FINISH
    WARNING : order O-5 has been accepted but has not been delivered
    ```

A possible solution is to also impose a decision point when the vehicle returns to the depot and there are unassigned orders.

***

## Decision point on vehicle arrival

!!! example
    Let's modify the model by imposing a decision point when the vehicle returns to the depot and there are unassigned orders!

There are at least two ways to impose decision point on arrivals:

- We can customize the ``on_vehicle_arrival`` callback of the model.
- We can customize the ``on_arrival`` callback of the vehicle.

=== "Model callback"
    ```python
    class DemoModel(Model):

        def on_vehicle_arrival( self, vehicle:Vehicle ) -> None:
            if vehicle.current_location.id == 'DEPOT' and any( order for order in self.orders.values() if not order.picked_up ):
                self.request_for_routing()
    ```

=== "Vehicle callback"
    ```python
    class Truck(Vehicle):
            
        def on_arrival( self ) -> None:
            if self.current_location.id == 'DEPOT' and any( order for order in self.model.orders.values() if not order.picked_up ):
                self.model.request_for_routing()
    ```

=== "Output"
    ```txt
    ...
    INFO    :       58.0 | 00:00:58 | TRUCK | arrived at DEPOT
    INFO    :       58.0 | 00:00:58 | TRUCK | service is started
    INFO    :       58.0 | 00:00:58 | TRUCK | service is finished
    INFO    :       58.0 | 00:00:58 | <<< routing >>>
    INFO    :       58.0 | 00:00:58 | TRUCK | service is started
    INFO    :       58.0 | 00:00:58 | TRUCK | order O-4 is picked up
    INFO    :       58.0 | 00:00:58 | TRUCK | order O-5 is picked up
    INFO    :       58.0 | 00:00:58 | TRUCK | service is finished
    ...
    INFO    :       88.0 | 00:01:28 | FINISH
    ```

Whatever we choose, it works!
When the vehicle returns to the depot to pick up the fourth order, a routing is requested. As a result, the vehicle also picks up the fifth order.

***

Let's explore other some features of the simulator!
