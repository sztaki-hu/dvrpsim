# Our first orders

It's time to create and add orders (and locations) to the model!

In this short tutorial we will get familiar with the *orders* and *locations*.
We will use *order providers* to request orders and we will also impose *decision points on order requests*.

***

## Locations and orders

!!! example "Example (Same-day delivery problem)"
    Consider a problem where there is a single depot from which customer requests must be fulfilled.

Of course, we need to import the corresponding classes.

```python
from dvrpsim import Model, Location, Order
```

First, we create a location for the depot, and add to the model.
Then, we create, for example, five orders.
For each order we create a customer location, which is set as the delivery location.
The pickup location is the depot for all orders.

!!! warning
    Unlike locations (and vehicles), orders should not be added directly to the model, i.e., via method ``_add_orders``.
    We can either use method ``request_order`` for this purpose or use an order provider.

=== "Request order"
    ```python
    model = DemoModel()

    depot = Location( id= 'DEPOT' )
    model.add_location( depot )

    for i in range(5):
        customer_location = Location( f'CUSTOMER {i+1}' )
        model.add_location( customer_location )

        order = Order( id= f'O-{i+1}' )
        order.pickup_location = depot
        order.delivery_location = customer_location
        model.request_order( order )

    model.run()
    ```

=== "Order provider"
    ```python
    from dvrpsim.utils.order_providers import order_provider
    ```

    ```python
    model = DemoModel()

    depot = Location( id= 'DEPOT' )
    model.add_location( depot )

    orders_to_request = []

    for i in range(5):
        customer_location = Location( id= f'CUSTOMER {i+1}' )
        model.add_location( customer_location )

        order = Order( id= f'O-{i+1}' )
        order.pickup_location = depot
        order.delivery_location = customer_location
        orders_to_request.append( order )

    model.env.process( order_provider( model, orders_to_request ) )

    model.run()
    ```

=== "Output"

    ```txt
    INFO    :        0.0 | 00:00:00 | START
    INFO    :        0.0 | 00:00:00 | order O-1 is requested (DEPOT -> CUSTOMER 1)
    INFO    :        0.0 | 00:00:00 | order O-2 is requested (DEPOT -> CUSTOMER 2)
    INFO    :        0.0 | 00:00:00 | order O-3 is requested (DEPOT -> CUSTOMER 3)
    INFO    :        0.0 | 00:00:00 | order O-4 is requested (DEPOT -> CUSTOMER 4)
    INFO    :        0.0 | 00:00:00 | order O-5 is requested (DEPOT -> CUSTOMER 5)
    INFO    :        0.0 | 00:00:00 | FINISH
    WARNING : no decision has been made on order O-1
    WARNING : no decision has been made on order O-2
    WARNING : no decision has been made on order O-3
    WARNING : no decision has been made on order O-4
    WARNING : no decision has been made on order O-5
    ```

!!! tip "Single order provider vs. Multiple order requests"
    An order provider uses a single process to request multiple orders.

***

## Release dates

In the previous example, each order is requested at the beginning, however, we can set later release dates for the orders.

=== "Code snippet"
    ```python
    for i in range(5):
        ...
        order.release_date = (i+1)*8
        ...
    ```

=== "Output"
    ```txt
    INFO    :        0.0 | 00:00:00 | START
    INFO    :        8.0 | 00:00:08 | order O-1 is requested (DEPOT -> CUSTOMER 1)
    INFO    :       16.0 | 00:00:16 | order O-2 is requested (DEPOT -> CUSTOMER 2)
    INFO    :       24.0 | 00:00:24 | order O-3 is requested (DEPOT -> CUSTOMER 3)
    INFO    :       32.0 | 00:00:32 | order O-4 is requested (DEPOT -> CUSTOMER 4)
    INFO    :       40.0 | 00:00:40 | order O-5 is requested (DEPOT -> CUSTOMER 5)
    INFO    :       40.0 | 00:00:40 | FINISH
    WARNING : no decision has been made on order O-1
    WARNING : no decision has been made on order O-2
    WARNING : no decision has been made on order O-3
    WARNING : no decision has been made on order O-4
    WARNING : no decision has been made on order O-5
    ```

***

## Decision point on order request

!!! example "Decision points"
    Let's impose a decision point (i.e., request for routing) once an order is requested!

There are at least three ways to impose decision points on order requests:

- We can specify the routing request with the parameter of the ``request_order`` method.
- We can specify the routing request with the parameter of the ``order_provider``.
- We can override the ``on_order_request`` callback of the method.
- (We could also inherit our own ``Order`` class with a custom ``on_request`` callback, but that would be over-complicated for this simple example).

=== "Request order"

    ``` python
    model.request_order( order, decision_point_on_request= True )
    ```

=== "Order provider"

    ``` python
    model.env.process( order_provider( model, orders_to_request, decision_point_on_request= True ) )
    ```

=== "Model callback"

    ``` python
    class DemoModel(Model):
        def __init__(self) -> None:
            super().__init__()

        def on_order_request(self, order:Order) -> None:
            self.request_for_routing()
    ```    

=== "Output"
    ```txt
    INFO    :        0.0 | 00:00:00 | START
    INFO    :        8.0 | 00:00:08 | order O-1 is requested (DEPOT -> CUSTOMER 1)
    INFO    :        8.0 | 00:00:08 | <<< routing >>>
    WARNING : routing callback is not implemented (all orders will be rejected)
    INFO    :        8.0 | 00:00:08 | order O-1 is rejected
    ...
    ```

Whichever we choose, a message warning us that we have not implemented routing callback, so all open orders will be automatically rejected.

!!! tip "Multiple routing requests"
    Even if multiple routing requests arrive at the same time (e.g., multiple orders are requested at once in our case), only one routing process is performed.

***

So, let's define a simple routing callback!
