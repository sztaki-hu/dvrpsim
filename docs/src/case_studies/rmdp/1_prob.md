# Restaurant meal delivery problem (RMDP)

In this case study, we model the *restaurant meal delivery problem (RMDP)* proposed by Ulmer et al. (2021).

!!! info "Proof-of-concept"
    The aim of this case study is to show how the problem can be modeled in this framework.
    The focus is only on the modeling and the presentation of the features.
    A dummy routing algorithm is used for testing purposes.
    No effort has been made to implement the solution method proposed by the authors.

This case study demonstrates the following features of the framework:

- Customized pre-service procedure to model stochastic ready times at restaurants.
- Decision postponement along with self-imposed decision points.
- Decision points on order requests.
- File-based interaction between the simulator and the external routing algorithm.

***

## Problem overview

The RMDP is characterized by a fleet of vehicles that seeks to fulfill a random set of delivery orders that arrive during the finite order horizon from restaurants located in a service area.
Orders occur according to a known stochastic process.
Each realized order is associated with an order time, a delivery location, a pickup restaurant, and a soft deadline.

The time to prepare a customer’s food at each restaurant is random.
Thus, the driver may need to wait for the order’s completion when arriving to a restaurant.

The dispatcher determines which orders are assigned to which vehicles.
Once made, assignments cannot be altered, therefore, assignments can be postponed.

**Dynamic decision making:**
A decision point occurs when a new customer requests service.
A decision point can also be "self-imposed", which happens when an order is postponed.

***

## References

Ulmer, M. W., Thomas, B. W., Campbell, A. M., & Woyak, N. (2021).
*The restaurant meal delivery problem: Dynamic pickup and delivery with deadlines and random ready times*.
<a href="https://doi.org/10.1287/trsc.2020.1000" target="_blank">Transportation Science, 55(1), 75-100.</a>

### Benchmark tools

<a href="https://iro.uiowa.edu/esploro/outputs/9983557680602771" target="_blank">Benchmark instances of Ulmer et al. (2021)</a>
