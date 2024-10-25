# Model

Here is a brief description of the modeling of the problem in this simulation framework.

***

## Locations

The default ``Location`` class is used.

```python
for location_id, location_data in probdata['locations'].items():
    location = Location( location_id )    
    location.x = location_data['lon']
    location.y = location_data['lat']
    model.add_location( location )
```

***

## Orders

The default ``Order`` class is used.

- An order provider is used to request the orders.
- Decision points on order requests are also imposed by the order provider.

```python
orders = []

for order_id, order_data in probdata['orders'].items():        
    order = Order( order_data['id'] )
    order.release_date = order_data['release_date']
    order.due_date = order_data['due_date']
    order.pickup_location = model.get_location_by_id( order_data['pickup_location'] )
    order.delivery_location = model.get_location_by_id( order_data['delivery_location'] )
    order.pickup_duration = 2   # "The service time (...) at a restaurant, once the food is ready, is two minutes."        
    order.delivery_duration = 2 # "The service time at a customer (...) is two minutes.
            
    orders.append( order )
    
model.env.process( order_provider( model, orders, decision_point_on_request= True ) )
```

***

## Vehicles

A custom vehicle class (``RMDPDriver``) is used.

- The distance callback (``travel_distance``) and the travel times callback (``travel_time``) return the (vehicle-independent) distance and travel time, respectively, between the given locations.
- The pre-service callback (``_preservice``) models the waiting of the driver when the food is not ready.

=== "Vehicle class"

    ```python
    class RMDPDriver(Vehicle):
        def __init__( self, id:str ) -> None:
            super().__init__(id)
    ```
=== "Travel time and distance"

    ```python
    def travel_distance( self, origin:Location, destination:Location ) -> float:
        """
        "(...) multiplying Euclidean distances by a factor of 1.4 closely approximates the relationship between Euclidean and street distances."
        """
        return 1.4 * great_circle_distance( origin.x, origin.y, destination.x, destination.y )
    
    def travel_time( self, origin:Location, destination:Location ) -> Generator[Event,Any,None]:
        """
        "(...) assuming the travel speed over the resulting distances is 40 kilometers per hour."
        """
        travel_time = 60 * self.travel_distance( origin, destination ) / 40.0

        return round( travel_time )
    ```

=== "Pre-service"

    ```python
    def _preservice(self) -> Generator[Event, Any, None]:
        """
        "(...) the driver may need to wait for the order's completion when arriving to a restaurant."
        """
        waiting_time = max( ( self.model.private_data['orders'][order.id]['ready_time']
            for order in self.current_visit.pickup_list ), default= 0 ) - self.model.env.now

        if 0 < waiting_time:
            self.model.log.custom( 'waiting for food...', vehicle= self )
            yield self.model.env.medium_timeout( waiting_time )
    ```
