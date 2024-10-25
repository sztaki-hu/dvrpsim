# Order-related features

In this short tutorial, we will demonstrate some order-related simulator features, such as *service duration* and *earliest service start time*.

***

## Service duration

Loading and unloading may take some time.
An easy way to associate such order-dependent service times with orders is to use their service duration attributes (``pickup_duration`` and ``delivery_duration``).

!!! example "Example (service duration)"
    Let's assume the loading time is 2 units and the unloading time is 3 units!

=== "Code snippet"
    ```python         
    order.pickup_duration = 2
    order.delivery_duration = 3
    orders_to_request.append( order )
    ```

=== "Output"
    ```txt
    INFO    :        0.0 | 00:00:00 | START
    INFO    :        8.0 | 00:00:08 | order O-1 is requested (DEPOT -> CUSTOMER 1)
    INFO    :        8.0 | 00:00:08 | <<< routing >>>
    INFO    :        8.0 | 00:00:08 | TRUCK | service is started
    INFO    :       10.0 | 00:00:10 | TRUCK | order O-1 is picked up
    INFO    :       10.0 | 00:00:10 | TRUCK | service is finished
    INFO    :       10.0 | 00:00:10 | TRUCK | departed from DEPOT to CUSTOMER 1
    INFO    :       16.0 | 00:00:16 | order O-2 is requested (DEPOT -> CUSTOMER 2)
    INFO    :       16.0 | 00:00:16 | <<< routing >>>
    INFO    :       20.0 | 00:00:20 | TRUCK | arrived at CUSTOMER 1
    INFO    :       20.0 | 00:00:20 | TRUCK | service is started
    INFO    :       23.0 | 00:00:23 | TRUCK | order O-1 is delivered
    INFO    :       23.0 | 00:00:23 | TRUCK | service is finished
    INFO    :       23.0 | 00:00:23 | TRUCK | departed from CUSTOMER 1 to DEPOT
    ...
    ```

It works! The first service at the depot starts at time 8, however, the order is officially picked up two minutes later.
Similarly, the service at the first customer starts at 20, and the order is delivered at 23.

***

## Earliest service start time

Orders can be associated with time windows (i.e. earliest and latest service start times) for both pickup and delivery.
Earliest service start times are hard constraints, meaning that if a vehicle arrives early at a location, it must wait until the time window opens.

!!! example "Example (service duration)"
    Let's set earliest delivery start time for the orders!

=== "Code snippet"
    ```python
    order.earliest_delivery_start = order.release_date + 15
    orders_to_request.append( order )
    ```

=== "Output"
    ```txt
    ...
    INFO    :       10.0 | 00:00:10 | TRUCK | departed from DEPOT to CUSTOMER 1
    INFO    :       16.0 | 00:00:16 | order O-2 is requested (DEPOT -> CUSTOMER 2)
    INFO    :       16.0 | 00:00:16 | <<< routing >>>
    INFO    :       20.0 | 00:00:20 | TRUCK | arrived at CUSTOMER 1
    INFO    :       20.0 | 00:00:20 | TRUCK | waiting for earliest start time at 23
    INFO    :       23.0 | 00:00:23 | TRUCK | service is started
    ...
    ```

As a result, the earliest service start time for the delivery of the first order is at 23.
Therefore, although the vehicle arrives at 20, the service does not start until 23.
