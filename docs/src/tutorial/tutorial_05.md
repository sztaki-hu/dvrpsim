# Location-related features

In this short tutorial, we will demonstrate some location-related simulator features, such as *coordinates* and *shared resources*.

***

## Location coordinates

Locations can be associated with coordinates, which can be used, for example, to calculate travel times.

!!! example "Example (location coordinates)"
    Let's modify our demo model by adding random coordinates to the locations!
    Also modify the travel time callback of the vehicle.

=== "Main"
    ```python
    import random

    if __name__ == '__main__':
        random.seed(42)

        model = DemoModel()

        depot = Location( id= 'DEPOT', x= 0, y= 0 )
        model.add_location( depot )

        for i in range(5):
            x = random.randint( -10, 10 )
            y = random.randint( -10, 10 )
            customer_location = Location( id= f'CUSTOMER {i+1} at ({x},{y})', x= x, y= y )
            model.add_location( customer_location )

            order = Order( id= f'O-{i+1}' )
            order.pickup_location = depot
            order.delivery_location = customer_location
            order.release_date = 0
            order.pickup_duration = 2
            order.delivery_duration = 3
            model.request_order( order, decision_point_on_request= True )

        vehicle = Truck( 'TRUCK' )
        vehicle.initial_location = depot
        model.add_vehicle( vehicle )

        model.run()
    ```

=== "Travel time callback"
    ```python
    from dvrpsim.utils.distances import manhattan_distance

    class Truck(Vehicle):
        def __init__( self, id:str ) -> None:
            super().__init__(id)

        def travel_time( self, origin:Location, destination:Location ) -> int | float:
            return manhattan_distance( origin.x, origin.y, destination.x, destination.y )
            
        def on_arrival( self ) -> None:
            super().on_arrival()

            if self.is_idle and self.current_location.id == 'DEPOT':
                self.model.request_for_routing()
    ```

=== "Output"
    ```txt
    ...
    INFO    :       10.0 | 00:00:10 | TRUCK | departed from DEPOT to CUSTOMER 1 at (10,-7)
    INFO    :       27.0 | 00:00:27 | TRUCK | arrived at CUSTOMER 1 at (10,-7)
    ...
    ```    

As a result, travel times are calculated based on the Manhattan-distance.
Indeed, the travel time, for example, from the depot located at (0,0) to the customer located at (10,-7) is |10| + |-7| = 17.

***

## Location resources

Locations can be associated with shared resource.

!!! example "Example (shared resources)"
    Assume that there is only one docking gate at the depot, so multiple vehicles cannot be loaded/unloaded at the same time.
    Let's associate a resource with the depot, and add more vehicles to the model!

=== "Main"
    ```python
    random.seed(42)

    model = DemoModel()

    depot = Location( id= 'DEPOT', x= 0, y= 0 )
    depot.resource = Resource( model.env, 1 )
    model.add_location( depot )

    for i in range(5):
        x = random.randint( -10, 10 )
        y = random.randint( -10, 10 )
        customer_location = Location( id= f'CUSTOMER {i+1}', x= x, y= y )
        model.add_location( customer_location )

        order = Order( id= f'O-{i+1}' )
        order.pickup_location = depot
        order.delivery_location = customer_location
        order.release_date = 0
        order.pickup_duration = 2
        order.delivery_duration = 3
        model.request_order( order, decision_point_on_request= True )

    for i in range(2):
        vehicle = Truck( f'TRUCK-{i+1}' )
        vehicle.initial_location = depot
        model.add_vehicle( vehicle )

    model.run()
    ```

=== "Output"
    ```txt
    INFO    :        0.0 | 00:00:00 | START
    INFO    :        0.0 | 00:00:00 | order O-1 is requested (DEPOT -> CUSTOMER 1 at (10,-7))
    INFO    :        0.0 | 00:00:00 | order O-2 is requested (DEPOT -> CUSTOMER 2 at (-10,-2))
    INFO    :        0.0 | 00:00:00 | order O-3 is requested (DEPOT -> CUSTOMER 3 at (-3,-3))
    INFO    :        0.0 | 00:00:00 | order O-4 is requested (DEPOT -> CUSTOMER 4 at (-6,-7))
    INFO    :        0.0 | 00:00:00 | order O-5 is requested (DEPOT -> CUSTOMER 5 at (7,-8))
    INFO    :        0.0 | 00:00:00 | <<< routing >>>
    INFO    :        0.0 | 00:00:00 | TRUCK-1 | service is requested
    INFO    :        0.0 | 00:00:00 | TRUCK-2 | service is requested
    INFO    :        0.0 | 00:00:00 | TRUCK-1 | service is started
    INFO    :        2.0 | 00:00:02 | TRUCK-1 | order O-1 is picked up
    INFO    :        2.0 | 00:00:02 | TRUCK-1 | service is finished
    INFO    :        2.0 | 00:00:02 | TRUCK-1 | departed from DEPOT to CUSTOMER 1 at (10,-7)
    INFO    :        2.0 | 00:00:02 | TRUCK-2 | service is started
    ```

Cool! Both vehicles, initially located at the depot, request a service, i.e. a capacity from the shared resource at time 0.
The first vehicle gets it first, so the other vehicle has to wait until the resource becomes free at time 2.
