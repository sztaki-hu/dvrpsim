# Model

Here is a brief description of the modeling of the problem in this simulation framework.

***

## Locations

The default ``Location`` class is used.

- Each location is associated with a shared resource to model the usage of its docking ports.

```python
for location_id, location_data in probdata['locations'].items():
    location = Location( location_id )
    location.resource = model.create_resource( capacity= location_data['docking_ports'] )
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
    order.original_id = order_data['original_id']
    order.quantity = order_data['quantity']
    order.release_date = order_data['release_date']
    order.due_date = order_data['due_date']
    order.pickup_location = model.get_location_by_id( order_data['pickup_location'] )
    order.delivery_location = model.get_location_by_id( order_data['delivery_location'] )  
    order.pickup_duration = probdata.['loading_time'] * order.quantity
    order.delivery_duration = probdata['unloading_time'] * order.quantity
    orders.append( order )
    
model.env.process( order_provider( model, orders ) )
```

***

## Vehicles

A custom vehicle class (``DPDPVehicle``) is used.

- The travel time (``travel_time``) and travel distance (``travel_distance``) callbacks use the pre-calculated values from the problem data.
- The service callback (``_service``) models the dock approaching, then applies the defualt service procedure (i.e., unloading takes place first and then loading takes place afterwards).
- The callback ``on_service_finish`` sets the delivery time of the corresponding orders to the arrival time of the vehicle.
(The delivery times in the original version of the problem/simulator were also calculated in this way).

=== "Vehicle class"

    ```python
    class DPDPVehicle(Vehicle):
        def __init__(self, id: str) -> None:
            super().__init__(id)

        @property
        def loaded_orders_after_current_visit(self) -> List[Order]:
            after_list = self.carrying_orders[:]
            
            if self.is_on_the_way:
                return after_list
            
            for order in self.current_visit.delivery_list:
                if order in after_list:
                    after_list.remove(order)

            for order in self.current_visit.pickup_list:
                if order not in after_list:
                    after_list.append(order)

            return after_list
    ```
=== "Travel time and distance"

    ```python
    def travel_distance( self, origin, destination ):
        return self.model.private_data.get( 'distances' ).get( ( origin.id, destination.id ), 0 )
    
    def travel_time( self, origin, destination ):
        return self.model.private_data.get( 'travel_times' ).get( ( origin.id, destination.id ), 0 )
    ```

=== "Service"

    ```python
    def _service(self):
        # docking
        yield self.model.env.medium_timeout( self.model.private_data.get( 'docking_time' ) )

        # default service procedure
        yield self.model.env.process( super()._service() )
    ```

=== "Service finish"

    ```python    
    def on_service_finish(self):
        # adjust delivery times
        for order in self.current_visit.delivery_list:
            order.delivery_time = self.current_visit.arrival_time
            self.model.log.custom( f'delivery time of order {order} has been set to {order.delivery_time}', vehicle= self )
    ```

- Vehicles are capacitated.
- Vehicles are subject to LIFO loading rule.

```python
for vehicle_id, vehicle_data in probdata['vehicles'].items():        
    vehicle = DPDPVehicle( vehicle_id )
    vehicle.capacity = vehicle_data['capacity']
    vehicle.initial_location = model.get_location_by_id( vehicle_data['initial_location'] )
    vehicle.loading_rule = VehicleLoading.LIFO
    model.add_vehicle( vehicle )
```

***

## Periodic decision points

The periodic updater is used to impose decision points in every 10 minutes (=600 seconds).
To be consistent with the original simulator, the decision points do not stop when the last order arrives, but keep arriving until all orders are delivered.

```
model.env.process( periodic_updater( model, 600, stop_after_last_order_request= False ) )
```

***

## Custom states and decisions

To make the simulator linkable to existing solution methods (which are tailored to the original simulator), we use the same state structure.
This is not described in detail here.
