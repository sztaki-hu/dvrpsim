from simpy  import Event
from typing import Generator, Iterable, Any

from dvrpsim import Model, Order
    
def order_provider( model:Model, orders:Iterable[Order], decision_point_on_request:bool= False ) -> Generator[Event, Any, None]:
    """
    A simple method to provide the given orders online.

    Each time an order is released:
    1. the order is added to the model,
    2. callbacks on order request are called, and
    3. if needed, a decision point is imposed (i.e., the routing algorithm is called).

    Finally, if all orders are released, the event :attr:`~.Model.all_orders_are_requested` of the model is secceded.

    Usage:
        model.env.process( order_provider( model, order, ... ) )

    :param Model           model:                     associated model
    :param Iterable[Order] orders:                    a collection of orders
    :param bool            decision_point_on_request: should a decision point be imposed on the order request?

    :rtype: Iterator[Event]
    """
    for order in sorted( orders, key= lambda x : x.release_date ):
        # yield event at the order's release date
        yield model.env.medium_timeout( order.release_date - model.env.now )

        # store order
        model._add_order( order )

        # log
        model.log.on_order_request( order )

        # model callback
        order.on_request()
        model.on_order_request( order )

        # impose decision point, if needed
        if decision_point_on_request:
            model.request_for_routing()

    model.all_orders_are_requested.succeed()
