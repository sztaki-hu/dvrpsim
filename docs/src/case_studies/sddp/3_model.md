# Model

Here is a brief description of the modeling of the problem in this simulation framework.

***

## Locations

The default ``Location`` class is used.

```python
for location_id, location_data in probdata['locations'].items():
    location = Location( location_id )
    location.x = location_data['x']
    location.y = location_data['y']
    model.add_location( location )
```

***

## Orders

The default ``Order`` class is used.

- An order provider is used to request the orders.

```python
orders = []

for order_id, order_data in probdata['orders'].items():
    order = Order( order_data['id'] )
    order.release_date = order_data['release_date']
    order.pickup_location = model.get_location_by_id( order_data['pickup_location'] )
    order.delivery_location = model.get_location_by_id( order_data['delivery_location'] )
    order.earliest_delivery_start = order_data['earliest_delivery_arrival']
    order.latest_delivery_start = order_data['latest_delivery_arrival']    
    orders.append( order )

model.env.process( order_provider( model, orders, decision_point_on_request= False ) )
```

***

## Vehicles

A custom vehicle class (``SDDPVehicle``) is used.

- The distance callback (``travel_distance``) and the travel times callback (``travel_time``) return the (vehicle-independent) distance and travel time, respectively, between the given locations.

=== "Vehicle class"

    ```python
    class SDDPVehicle(Vehicle):
        def __init__( self, id:str ) -> None:
            super().__init__(id)
    ```
=== "Travel time and distance"

    ```python
    def travel_distance( self, origin:Location, destination:Location ):
        """
        "(...) we first calculate the Manhattan distance between locations (...)"
        """
        return manhattan_distance( origin.x, origin.y, destination.x, destination.y )
    
    def travel_time( self, origin:Location, destination:Location ):
        return round( 60 * self.travel_distance( origin, destination ) / self.aux['speed'] )
    ```

- Initial location and speed are set for each vehicle.

```python
for vehicle_id, vehicle_data in probdata['vehicles'].items():        
        vehicle = SDDPVehicle( vehicle_id )
        vehicle.initial_location = model.get_location_by_id( vehicle_data['initial_location'] )
        vehicle.aux['speed'] = vehicle_data['speed']

        if vehicle.initial_location is None:
            raise ModelError( f'unknown initial location for order {vehicle_id}: {vehicle_data["initial_location"]}' )
        
        model.add_vehicle( vehicle )
```

***

## Custom callbacks

The ``on_vehicle_arrival`` and the ``on_order_request`` callbacks of the model are customized to impose decision points on order requests and on vehicle arrivals.

=== "Vehicle arrival"

    ```python
    def on_vehicle_arrival( self, vehicle:Vehicle ) -> None:
        """
        "(...) epoch occurs (...) as a result of (...) the following:
            1. a vehicle arrives at the depot (...)"
        """
        # check arrival at the depot from other location
        if vehicle.current_location.id == 'depot' and vehicle.previous_location.id != 'depot':
            self.request_for_routing()
    ```

=== "Order request"

    ```python
    def on_order_request( self, order:Order ) -> None:
        """
        "(...) epoch occurs (...) as a result of (...) the following:
            2. a new request arrives and at least one vehicle is waiting at the depot."
        """
        if any( vehicle for vehicle in self.vehicles if vehicle.is_idle and vehicle.current_visit.location.id == 'depot' and not vehicle.has_next_visit ):
            self.request_for_routing()
    ```
    