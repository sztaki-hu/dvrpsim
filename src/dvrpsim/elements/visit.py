from __future__ import annotations


from simpy.core import SimTime
from typing     import TYPE_CHECKING, Any, Dict, List

from dvrpsim.elements.location import Location
from dvrpsim.elements.order    import Order

if TYPE_CHECKING:
    from dvrpsim.model import Model

class Visit:
    """
    Base class for visits.
    
    Basic attributes:

    :ivar Location    location:        location of the visit
    :ivar List[Order] delivery_list:   list of orders to unload at the visit (may be empty)
    :ivar List[Order] pickup_list:     list of orders to load   at the visit (may be empty)
    :ivar SimTime earliest_start_time: (optional) earliest start time for this route-suffix

    :ivar Dict[str,Any] aux: auxiliary data

    Attributes set during the simulation:

    :ivar SimTime arrival_time:        factual arrival time at the location
    :ivar SimTime service_start_time:  factual service start time
    :ivar SimTime service_finish_time: factual service finish time
    :ivar SimTime departure_time:      factual departure time from the location
    """
    def __init__(self) -> None:
        self.location:Location           = None
        self.delivery_list:List[Order]   = []
        self.pickup_list:List[Order]     = []
        self.earliest_start_time:SimTime = None

        self.aux:Dict[str,Any] = {}

        #region Simulation data
        
        self.arrival_time:SimTime        = None
        self.service_start_time:SimTime  = None
        self.service_finish_time:SimTime = None
        self.departure_time:SimTime      = None

        #endregion

    @property
    def waiting_time(self) -> SimTime:
        """
        Returns the total waiting time at the visit, if applicable, else ``None``.
        """
        if self.arrival_time is None or self.service_start_time is None:
            return None
        
        return self.service_start_time - self.arrival_time
    
    @property
    def service_time(self) -> SimTime:
        """
        Returns the total service time at the visit, if applicable, else ``None``.
        """
        if self.service_finish_time is None or self.service_start_time is None:
            return None
        
        return self.service_finish_time - self.service_start_time
    
    @property
    def idle_time(self) -> SimTime:
        """
        Returns the total idle time at the visit, if applicable, else ``None``.
        """
        if self.departure_time is None or self.service_finish_time is None:
            return None
        
        return self.departure_time - self.service_finish_time

    @property
    def earliest_service_start_time(self) -> SimTime:
        """
        Returns the earliest service start time based on the orders' earliest service start times.
        """
        return max(
            max( ( order.earliest_pickup_start   for order in self.pickup_list   if order.earliest_pickup_start   is not None ), default= 0 ),
            max( ( order.earliest_delivery_start for order in self.delivery_list if order.earliest_delivery_start is not None ), default= 0 )
        )
    
    def to_dict(self) -> dict:
        """
        Returns a dictionary corresponding to the visit.
        """   
        return {
            'location':           self.location.id,
            'pickup_list':        [order.id for order in self.pickup_list],
            'delivery_list':      [order.id for order in self.delivery_list],
            'earliest_start_time': self.earliest_service_start_time,
            'aux':                 self.aux,
            'arrival_time':        self.arrival_time,
            'service_start_time':  self.service_start_time,
            'service_finish_time': self.service_finish_time,
            'departure_time':      self.departure_time
        }

    @staticmethod
    def parse_dict( model:'Model', dict:Dict ) -> Visit:
        """
        Returns the visit parsed from the given dictionary.
        """
        visit = Visit()

        visit.location            = model.get_location_by_id( dict['location'] )
        visit.pickup_list         = [ model.get_order_by_id(order_id) for order_id in dict['pickup_list'] ] if dict.get('pickup_list',None) is not None else []
        visit.delivery_list       = [ model.get_order_by_id(order_id) for order_id in dict['delivery_list'] ] if dict.get('delivery_list',None) is not None else []
        visit.earliest_start_time = dict.get('earliest_start_time', None)

        visit.aux = dict.get('aux',{})

        visit.arrival_time        = dict.get('arrival_time', None)
        visit.service_start_time  = dict.get('service_start_time', None)
        visit.service_finish_time = dict.get('service_finish_time', None)
        visit.departure_time      = dict.get('departure_time', None)

        return visit
