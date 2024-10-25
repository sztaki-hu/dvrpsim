# Same-day delivery problem (SDDP)

In this case study, we model the *same-day delivery problem (SDDP)* proposed by Voccia et al. (2019).

!!! info "Proof-of-concept"
    The aim of this case study is to show how the problem can be modeled in this framework.
    The focus is only on the modeling and the presentation of the features.
    A simple routing algorithm is used for testing purposes.
    No effort has been made to reproduce the solution method proposed by the authors.

This case study demonstrates the following features of the framework:

- Delivery from a designated depot.
- Earliest service start times.
- Delaying the departure of the vehicles.
- Order rejection.
- Decision postponement along with self-imposed decision points.
- Direct interaction between the simulator and the external routing algorithm.

***

## Problem overview

The problem is characterized by a fleet of vehicles operating from a depot and by a set of locations.
Customers request service throughout the day until a fixed cut-off time.
Arrivals of requests are described by a known arrival rate and distribution.
Associated with each request is a known service time and a delivery time window at the customer location.

Once requests are made, a vehicle at the depot can be assigned requests and leave the depot immediately.
Alternatively, a vehicle can wait at the depot before being assigned requests.
Once a vehicle leaves the depot, the route for that vehicle is fixed, and the vehicle returns to the depot when it has made all its assigned deliveries.

A request is assigned to a third party when it is no longer feasible for the request to be served by a vehicle at the depot or one of the vehicles en route.

**Dynamic decision making:**
A decison point is imposed as a result of at least one of the following.
(i) a vehicle arrives at the depot;
(ii) a vehicle ends its waiting period;
(iii) a new request arrives and at least one vehicle is waiting at the depot.

***

## References

Voccia, S. A., Campbell, A. M., & Thomas, B. W. (2019).
*The same-day delivery problem for online purchases*.
<a href="https://doi.org/10.1287/trsc.2016.0732" target="_blank">Transportation Science, 53(1), 167-184.</a>

### Benchmark tools

<a href="https://iro.uiowa.edu/esploro/outputs/dataset/Instances-for-The-Same-Day-Delivery-Problem/9983557554202771" target="_blank">Benchmark instances of Voccia et al. (2019)</a>
