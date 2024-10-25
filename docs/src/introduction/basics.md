# Basic concepts

## Main overview

**Dynamic vehicle routing:**
A fleet of vehicles must serve orders that arrive dynamically in the planning horizon.
Due to the dynamic nature of the problem, the decision maker has the opportunity to re-plan the vehicle routes at certain *decision points* (e.g., on order requests, etc.).

**Decision process:**
At a decision point, the decision maker is provided with the current *state*, which describes all the information available to make a decision (e.g., positions of the vehicles, open orders, etc.).
The result of the *decision making* (or *routing*) is a *decision* (or *action*) that includes, for example, the updated vehicle routes.

``` mermaid
sequenceDiagram
  autonumber
  Simulator->>External routing algorithm: state
  Note right of External routing algorithm: routing...
  External routing algorithm->>Simulator: decision
```

This package is for modeling and simulating dynamic vehicle routing problems.
The implementation of the routing algorithm is not tied to Python, but of course this is also an option.

### Vehicles' execution procedure

During the simulation, the vehicles follow their *route plan*, if any.
A route plan is a sequence of visits.
A *visit* is specified by a *location* to which the vehicle must travel (unless it is currently there), and by a *pickup list* and a *delivery list* containing the orders that must be picked up and delivered at that location, respectively.

## Features

Any parameter of the problem (e.g., request of orders, travel times) can be deterministic or stochastic.

### Vehicles

- The fleet of vehicles can be either homogeneous or heterogeneous.
- Vehicles can be capacitated or uncapacitated.
- Vehicles may be subject to loading rules (e.g. LIFO).

### Orders

- Pickup-and-delivery type orders are considered.
The pickup/delivery locations can refer to a designated depot, so the framework is suitable for modeling not only dynamic pickup-and-delivery problems, but also same-day delivery problems.
With slight modifications, other types of dynamic vehicle routing problems can also be modeled.
- Service time window can be associated with for both the pickup and the delivery.
- Cancellation by the customers can be handled.
- Split deliveries are allowed, but in this case, the orders must be split into the smallest deliverable units in advance.

### Locations

- Locations may have limited docking capacity, so the vehicles may have to wait for service.

### Decision making (also called routing)

- Decision points can be imposed by arbitrary events (e.g., on order request, on vehicle arrival) or may occur periodically.
- The planned routes of the vehicles can be modified during their execution.
- Delaying the departure is possible.
- Rejection by the decision maker can be handled, and the postponement of the decision on acceptance/rejection is also allowed.
