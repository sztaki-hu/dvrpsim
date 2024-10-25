from simpy      import Event
from simpy.core import SimTime
from typing     import Any, Generator

from dvrpsim import Model

def periodic_updater( model:Model, step:SimTime, stop_after_last_order_request:bool= True ) -> Generator[Event, Any, None]:
    """
    A simple method to impose decision points (i.e., to call routing algorithm) at given time steps.

    Usage:
        model.env.process( periodic_updater( model, step, ... ) )
    
    :param Model   model: associated model
    :param SimTime step:  time step
    :param bool stop_after_last_order_request: should the method stop after all orders are requested?

    :rtype: Iterator[Event]
    """
    while True:
        # check termination criteria
        if model.all_orders_are_requested.processed and stop_after_last_order_request:
            break
            
        if model.all_orders_are_requested.processed and not any(model.open_orders):
            break

        # impose decision point
        model.request_for_routing()

        # go to the next fixed decision point
        yield model.env.medium_timeout( step )
