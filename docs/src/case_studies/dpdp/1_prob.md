# Dynamic pickup and delivery problem (DPDP)

In this case study, we model the *dynamic pickup-and-delivery problem (DPDP)* introduced in a competition organized by the International Conference on Automated Planning and Scheduling in 2021 (ICAPS 2021).

!!! info "Proof-of-concept"
    The aim of this case study is to show how the problem can be modeled in this framework.
    The focus is only on the modeling and the presentation of the features.
    A dummy routing algorithm is used for testing purposes.
    No effort has been made to reproduce any of the existing solutions to the problem.

This case study demonstrates the following features of the framework:

- LIFO loading rule for capacitated vehicles.
- Docking constraints (limited number of docking ports) at locations.
- Customized service procedure to model dock approaching at locations.
- Periodic decision points.
- File-based interaction between the simulator and the external routing algorithm.

***

## Problem overview

There is a fleet of homogeneous vehicles that has to serve pickup-and-delivery order requests which occur over a day.
Each order is characterized by a quantity, a pickup factory, a delivery factory, a release time, and a due date.

The vehicles can be loaded up to their capacity, while unloading has to follow the last-in-first-out (LIFO) rule.
Those, but only those orders whose quantity exceeds the capacity of the vehicles, can be split and delivered separately. 
The travel times and the distances between the factories are given.

Each factory has a given number of docking ports for serving (that is, loading and unloading) the vehicles.
Vehicles are served on a first-come-first-served basis.
If a vehicle arrives at a factory and all ports are occupied, its service cannot begin immediately, but the vehicle has to join the waiting queue.
That is, the vehicle must wait until one of the docking ports becomes free, and no vehicle that arrived earlier is waiting for a port.

The objective is to satisfy all the requests such that a combination of tardiness penalties and traveling distances is minimized.

**Dynamic decision making:** Decision points occur in every 10 minutes.

***

## References

Hao, J., Lu, J., Li, X., Tong, X., Xiang, X., Yuan, M., & Zhuo, H. H. (2022).
Introduction to the dynamic pickup and delivery problem benchmark--ICAPS 2021 competition.
<a href="https://arxiv.org/abs/2202.01256" target="_blank">arXiv preprint arXiv:2202.01256</a>.

<a href="https://competition.huaweicloud.com/information/1000041411/circumstance" target="_blank">Webpage of the competetion</a>

### Benchmark tools

<a href="https://github.com/huawei-noah/xingtian/tree/master/simulator/dpdp_competition" target="_blank">Benchmark instances and the *original simulator*</a>
