# Problem data

## Instances

Benchmark instances of Voccia et al. (2019).

Instance files, e.g., ``TWr_R_1_het1_2_actual_001.txt``, contain for each customer (and for the depot) the location coordinates, the request time, and the time window.

## Conversion

Procedure ``read_sddp_probdata`` converts instances into the following structure.

``` python
probdata = {
    'locations': {}, # location id -> location data
    'orders': {},    # order id    -> order data
    'vehicles': {},  # vehicle id  -> vehicle data
}
```

The location data consists of the unique id of the location (`depot` for the depot, with `customer-` prefix for customers), and the latitude and longitude of the location.

``` python
location_data = {
    'id': 'customer-1',
    'x': 11,
    'y': 31
}
```

The vehicle data consists of the unique id of the vehicle (with `vehicle-` prefix), its initial location and its speed.

``` python
vehicle_data = {
    'id': 'vehicle-1',
    'initial_location': 'depot',
    'speed': 69
}
```

The order data consists of the unique id of the order (with `O-` prefix),
the pickup location (i.e., the depot),
the delivery location (i.e., the customer),
the order request time,
and the earliest and latest arrival times.

``` python
order_data = {
   'id': 'O-1',
   'pickup_location': 'depot',
   'delivery_location': 'customer-1',
   'release_date': 2,
   'earliest_delivery_arrival': 61,
   'latest_delivery_arrival': 121
}
```
