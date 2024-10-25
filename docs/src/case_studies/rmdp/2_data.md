# Problem data

## Instances

Benchmark instances of Ulmer et al. (2021).

The restaurant file, ``restaurants.txt``, contains the longitude and the latitude of the restaurants indexed from 1 to 110.
The vehicle file, ``vehicles.txt``, contains the initial position (i.e., longitude and latitude) of the vehicles indexed from 1 to 15/30.
Order files, e.g., ``180_2.csv`` , contain data for all the orders which is requested on the planning horizon.
These are, the location of the customers (i.e., longitude and latitude) indexed from 1,
the index of the corresponding restaurant from which the customer orders,
the time of the request,
and a soft deadline.
The pre-generated stochastic ready times of the orders are also indicated.

## Conversion

Procedure ``read_rmdp_problem`` converts instances into the following structure.

``` python
probdata = {
    'locations': {}, # location id -> location data
    'orders': {},    # order id    -> order data
    'vehicles': {},  # vehicle id  -> vehicle data
}
```

The location data consists of the unique id of the location (`restaurant-` prefix for restaurants, `customer-` prefix for customers, and `vehicle-location-` prefix for the initial location of vehicles), and the latitude and longitude of the location.

``` python
location_data = {
    'id': 'restaurant-1',
    'lat': 41.6427535,
    'lon': -91.5055967
}
```

The vehicle data consists of the unique id of the vehicle (with `V-` prefix) and its initial location.

``` python
vehicle_data = {
    'id': 'V-1',
    'initial_location': 'vehicle-location-1
}
```

The order data consists of the unique id of the order (with `O-` prefix),
the pickup location (i.e., the restaurant),
the delivery location (i.e., the customer),
the order request time,
the soft deadline,
and the pre-generated order ready time.

``` python
order_data = {
    'id': 'O-2',
    'pickup_location': 'restaurant-70',
    'delivery_location': 'customer-2',
    'release_date': 2, # e.g., 12:02
    'due_date': 42,    # e.g., 12:42
    'ready_time': 14   # e.g., 12:14
}
```
