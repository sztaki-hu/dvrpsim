from enum                     import Enum
from simpy                    import Event, Interrupt, Process
from simpy.core               import SimTime
from simpy.resources.resource import Request
from typing                   import TYPE_CHECKING, Any, Dict, List, Generator

if TYPE_CHECKING:
    from dvrpsim.model             import Model
    from dvrpsim.elements.location import Location

from dvrpsim.elements.visit import Visit
from dvrpsim.elements.order import Order
from dvrpsim.exceptions     import SimulationError

class VehicleStatus(Enum):
    """Vehicle statuses."""
    IDLE                = 0
    EN_ROUTE            = 1
    WAITING_FOR_SERVICE = 2
    UNDER_SERVICE       = 3

class VehicleLoading(Enum):
    """Vehicle loading rules."""
    NONE = 0
    FIFO = 1
    LIFO = 2

class Vehicle:
    """
    Base class for vehicles.

    :param str id: unique vehicle ID

    Basic attributes:

    :ivar str             id:               unique vehicle ID
    :ivar Model           model:            associated simulation model
    :ivar Location        initial_location: initial location of the vehicle
    :ivar float           capacity:         (optional) capacity of the vehicle (in quantity), may be ``None`` for uncapacitated vehicles
    :ivar VehicleLoading  loading_rule:     (optional) loading rule of the vehicle, if any

    Attributes set by the simulator:
    
    :ivar status: status of the vehicle (idle, moving, busy)

    :ivar List[Visit] previous_visits: (historical route) list of previous visits (in visiting order), if any
    :ivar Visit       current_visit:   current visit, if any, otherwise ``None``
    :ivar List[Visit] next_visits:     (tentative route) list of next visits (in visiting order), if any
    :ivar List[Order] carrying_orders: list of orders that are currently on the vehicle (in loading order), if any
    
    :ivar Process _predeparture_process: current pre-departure process, if any
    :ivar Process _travel_process:       current travel process, if any
    :ivar Process _preservice_process:   current preservice process, if any
    :ivar Process _service_process:      current service process, if any
    :ivar Request _service_request:      current service request, if any
    """
    def __init__( self, id:str ) -> None:
        self.id:str = id

        self.model:Model = None

        # basic attributes

        self.initial_location:'Location' = None
        self.capacity:int|float          = None
        self.loading_rule:VehicleLoading = VehicleLoading.NONE
        
        self.aux:Dict[str,Any] = {}

        # simulation data
        self.status:VehicleStatus = VehicleStatus.IDLE

        self.previous_visits:List[Visit] = []
        self.current_visit:Visit         = None
        self.next_visits:List[Visit]     = []
        self.carrying_orders:List[Order] = []

        self._predeparture_process:Process = None
        self._travel_process:Process       = None
        self._preservice_process:Process   = None
        self._service_process:Process      = None
        self._service_request:Request      = None

    def __str__(self) -> str:
        return f'{self.id}'
        
    #region Basic properties

    @property
    def is_capacitated(self) -> bool:
        """Returns whether the vehicle is capacitated."""
        return self.capacity is not None
    
    @property
    def is_subject_to_lifo_load(self) -> bool:
        """Returns whether the vehicle is subject to the last-in-first-out loading rule."""
        return self.loading_rule == VehicleLoading.LIFO
    
    @property
    def is_subject_to_fifo_load(self) -> bool:
        """Returns whether the vehicle is subject to the first-in-first-out loading rule."""
        return self.loading_rule == VehicleLoading.FIFO

    #endregion

    #region Status properties

    @property
    def is_idle(self) -> bool:
        """Returns whether the vehicle is in the IDLE status."""
        return self.status == VehicleStatus.IDLE
    
    @property
    def is_en_route(self) -> bool:
        """Returns whether the vehicle is in the EN_ROUTE status."""
        return self.status == VehicleStatus.EN_ROUTE
    
    @property
    def is_waiting_for_service(self) -> bool:
        """Returns whether the vehicle is in the WAITING_FOR_SERVICE status."""
        return self.status == VehicleStatus.WAITING_FOR_SERVICE
    
    @property
    def is_under_service(self) -> bool:
        """Returns whether the vehicle is in the UNDER_SERVICE status."""
        return self.status == VehicleStatus.UNDER_SERVICE

    @property
    def is_at_location(self) -> bool:
        """Returns whether the vehicle is currently at a location (i.e., has current visit)."""
        return self.current_visit is not None
    
    @property
    def is_on_the_way(self) -> bool:
        """Returns whether the vehicle is currently traveling (i.e., has no current visit)."""
        return self.current_visit is None

    @property
    def has_next_visit(self) -> bool:
        """Returns whether the vehicle has a next location to visit."""
        return self.next_visits is not None and 0 < len(self.next_visits)
    
    @property
    def next_visit(self) -> Visit:
        """Returns the vehicle's next visit, if any."""
        return self.next_visits[0] if self.has_next_visit else None
    
    @property
    def has_previous_visit(self) -> bool:
        """Returns whether the vehicle has a previously visited location."""
        return self.previous_visits is not None and 0 < len(self.previous_visits)
    
    @property
    def previous_visit(self) -> Visit:
        """Returns the vehicle's previous visit, if any."""
        return self.previous_visits[-1] if self.has_previous_visit else None
    
    @property
    def previous_location(self) -> 'Location':
        """Returns the previously visited location of the vehicle, if any."""
        return self.previous_visit.location if self.previous_visit is not None else None
    
    @property
    def current_location(self) -> 'Location':
        """Returns the current location of the vehicle, if any."""
        return self.current_visit.location if self.current_visit is not None else None
    
    @property
    def next_location(self) -> 'Location':
        """Returns the next location of the vehicle to visit, if any."""
        return self.next_visit.location if self.next_visit is not None else None

    #endregion

    #region Main procedures
        
    def run(self) -> None:
        """
        Create a separate process to invoke the default execution procedure of the vehicle.

        See :func:`~._execution_procedure`.
        """
        # check status
        try:
            assert self.is_idle,                       f'starting vehicle {self} has unexpected status ({self.status.name})'
            assert self.is_at_location,                f'starting vehicle {self} has no current visit to departure from'
            assert self._predeparture_process is None, f'starting vehicle {self} has pre-departure process'
            assert self._travel_process is None,       f'starting vehicle {self} has travel process'        
            assert self._preservice_process is None,   f'starting vehicle {self} has pre-service process'
            assert self._service_process is None,      f'starting vehicle {self} has service process'
            assert self._service_request is None,      f'starting vehicle {self} has current service request'

        except Exception as exc:
            raise SimulationError( exc.args[0] )
        
        # execute
        self.model.env.process( self._execution_procedure() )

    def _execution_procedure(self) -> Generator[Event,Any,None]:
        """
        Default execution procedure for vehicles.

        See :func:`~.run`.

        Main steps:
            1. Pre-departure
            2. Travel
                1. Departure
                2. Travel
                3. Arrival
            3. Pre-Service
            4. Service
                1. Service start
                2. Service
                3. Service finish
            5. GOTO 1.
        """

        if not self.has_next_visit:
            return # nothing to do

        # ----- PRE-DEPARTURE       

        try:
            self._predeparture_process = self.model.env.process( self._predeparture() )
            yield self._predeparture_process

        except Interrupt:
            # log
            self.model.log.on_predeparture_interruption( self )

            # callbacks
            self.on_predeparture_interruption()
            self.model.on_vehicle_predeparture_interruption( self )

            return
        
        finally:
            self._predeparture_process = None

        # ----- DEPARTURE

        factual_travel = self.current_location != self.next_location

        self._departure()

        # ----- TRAVEL

        if factual_travel:
            try:
                self._travel_process = self.model.env.process( self._travel() )
                yield self._travel_process

            except Interrupt:
                # log
                self.model.log.on_travel_interruption( self )

                # callbacks
                self.on_travel_interruption()
                self.model.on_vehicle_travel_interruption( self )

                return
            
            finally:
                self._travel_process = None

        # ----- ARRIVAL

        self._arrival()

        # ----- PRE-SERVICE

        try:        
            self._preservice_process = self.model.env.process( self._preservice() )
            yield self._preservice_process

        except Interrupt:
            # log
            self.model.log.on_preservice_interruption( self )

            # callbacks
            self.on_preservice_interruption()
            self.model.on_vehicle_preservice_interruption( self )

            return
        
        finally:
            self._preservice_process = None
        
        # ----- SERVICE START

        self._service_start()

        # ----- SERVICE
        
        try:
            # service
            self._service_process = self.model.env.process( self._service() )
            yield self._service_process

        except Interrupt:
            # log
            self.model.log.on_service_interruption( self )

            # callbacks
            self.on_service_interruption()
            self.model.on_vehicle_service_interruption( self )

            return
        
        finally:
            # release resource request, if any
            if self.current_location.resource is not None and self._service_request is not None:
                self.current_location.resource.release( self._service_request )
                self._service_request = None
                
            self._service_process = None

        # ----- SERVICE FINISH

        self._service_finish()

        # ----- WHAT'S NEXT?
        
        if self.has_next_visit:
            self.run()

    def interrupt_predeparture(self) -> None:
        """
        Interrupts the pre-departure process of the vehicle, if in progress.
        """
        if self._predeparture_process is not None and self._predeparture_process.is_alive:
            self._predeparture_process.interrupt()

    def interrupt_travel(self) -> None:
        """
        Interrupts the travel process of the vehicle, if in progress.

        By default, interrupting travel is NOT allowed.
        """
        if self._travel_process is not None and self._travel_process.is_alive:
            self._travel_process.interrupt()

    def interrupt_preservice(self) -> None:
        """
        Interrupts the pre-service process of the vehicle, if in progress.

        By default, interrupting pre-service is NOT allowed.
        """
        if self._preservice_process is not None and self._preservice_process.is_alive:
            self._preservice_process.interrupt()

    def interrupt_service(self) -> None:
        """
        Interrupts the service process of the vehicle, if in progress.

        By default, interrupting service is NOT allowed.
        """
        if self._service_process is not None and self._service_process.is_alive:
            self._service_process.interrupt()

    #endregion

    #region Internal execution procedures

    def _predeparture(self) -> Generator[Event, Any, None]:
        """
        Pre-departure procedure.
        
        By default, the vehicle waits until the earliest departure time (i.e., until the next visit's earliest start time).
        """
        yield self.model.env.process( self._wait_for_earliest_departure() )
   
    def _departure( self ) -> None:
        """
        Departure.

        :param bool real_depature: is it really a departure, or is the next location the same as the current one?
        """
        # update status
        self.current_visit.departure_time = self.model.env.now

        self.previous_visits.append( self.current_visit )
        self.current_visit = None
        
        self.status = VehicleStatus.EN_ROUTE

        # log
        self.model.log.on_departure( self )

        # callbacks
        self.on_departure()
        self.model.on_vehicle_departure( self )
 
    def _travel(self) -> Generator[Event,Any,None]:
        """
        Travel procedure.

        By defalt, the travel time callback is used to obtain the corresponding travel time.
        """
        yield self.model.env.medium_timeout( self.travel_time( self.previous_location, self.next_location ) )

    def _arrival( self ) -> None:
        """
        Arrival.

        :param bool factual_arrival: is it really an arrival, or is the previous location the same as the next one?
        """
        # update status
        self.current_visit = self.next_visits[0]
        self.next_visits   = self.next_visits[1:]
        
        self.current_visit.arrival_time = self.model.env.now

        self.status = VehicleStatus.WAITING_FOR_SERVICE

        # log
        self.model.log.on_arrival( self )        

        # callbacks
        self.on_arrival()
        self.model.on_vehicle_arrival( self )

    def _request_for_service(self) -> Generator[Event,Any,None]:
        """
        This utility method requests a usage slot in the resource (if any) of the current location, and yields an event at the time, when the service can be started.
        """
        if self.current_location.resource is not None:
            self._service_request = self.current_location.resource.request()            
            self.model.log.on_service_request( self )
            yield self._service_request

    def _preservice(self) -> Generator[Event, Any, None]:
        """
        Pre-service procedure.

        By default, the vehicle waits for a free slot in the resource (if any) of the current location, and waits until the latest earliest service start time.
        """
        yield self.model.env.process( self._request_for_service() ) & self.model.env.process( self._wait_for_earliest_service_start() )

    def _service_start(self) -> None:
        """
        Service start.
        """
        # update status
        self.current_visit.service_start_time = self.model.env.now

        self.status = VehicleStatus.UNDER_SERVICE

        # log
        self.model.log.on_service_start( self )
        
        # callbacks
        self.on_service_start()
        self.model.on_vehicle_service_start( self )

    def _service(self) -> Generator[Event,Any,None]:
        """
        Service procedure.
        
        By default, unloading takes place first and then loading takes place afterwards.
        """
        # unloading
        for order in self.current_visit.delivery_list:
            yield self.model.env.process( self._deliver_order( order, service_duration= order.delivery_duration ) )

        # loading
        for order in self.current_visit.pickup_list:
            yield self.model.env.process( self._pickup_order( order, service_duration= order.pickup_duration ) )
    
    def _service_finish(self) -> None:
        """
        Service finish.
        """ 
        # update status
        self.current_visit.service_finish_time = self.model.env.now

        self.status = VehicleStatus.IDLE
        
        # log
        self.model.log.on_service_finish( self )

        # callbacks
        self.on_service_finish()
        self.model.on_vehicle_service_finish( self )
    
    #endregion
    
    #region Callbacks
    
    def travel_time( self, origin:'Location', destination:'Location' ) -> SimTime:
        """
        Returns the travel time between the given locations.

        :param Location origin:      origin (or 'from') location
        :param Location destination: destination (or 'to') location
        """
        return 0
    
    def travel_distance( self, origin:'Location', destination:'Location' ) -> int|float:
        """
        Returns the travel distance between the given locations.

        :param Location origin:      origin (or 'from') location
        :param Location destination: destination (or 'to') location
        """
        return 0

    def on_predeparture_interruption(self) -> None:
        """
        This method is called whenever the pre-departure process of the vehicle is interrupted.
        """
        return

    def on_departure(self) -> None:
        """
        This method is called whenever the vehicle is departed from its current (i.e., now its previous) location.
        """
        return

    def on_travel_interruption(self) -> None:
        """
        This method is called whenever the travel process of the vehicle is interrupted.

        By default, interrupting travel is NOT allowed.
        """
        raise SimulationError( 'interrupting travel is NOT allowed' )

    def on_arrival(self) -> None:
        """
        This method is called whenever the vehicle is arrived at its next (i.e., now its current) location.
        """
        return

    def on_preservice_interruption(self) -> None:
        """
        This method is called whenever the pre-service process of the vehicle is interrupted.

        By default, interrupting pre-service is NOT allowed.
        """
        raise SimulationError( 'interrupting pre-service is not allowed' )

    def on_service_start(self) -> None:
        """
        This method is called whenever the service of the vehicle is about to be started.
        """
        return

    def on_service_interruption(self) -> None:
        """
        This method is called whenever the service process of the vehicle is interrupted.

        By default, interrupting service is NOT allowed.
        """
        raise SimulationError( 'interrupting service is not allowed' )

    def on_service_finish(self) -> None:
        """
        This method is called whenever the service of the vehicle is finished.
        """
        return

    #endregion

    #region Utility methods

    def _wait_for_earliest_departure(self) -> Generator[Event,Any,None]:
        """
        This utility method yields an event at the time, when the vehicle can depart.
        """
        assert self.is_idle and self.has_next_visit, f'incorrect state to call method {self._wait_for_earliest_departure.__name__}'

        waiting_time = self.next_visit.earliest_start_time - self.model.env.now if self.next_visit.earliest_start_time is not None else 0

        if 0 < waiting_time:        
            self.model.log.on_departure_postponement( self, self.next_visit.earliest_start_time )
            yield self.model.env.medium_timeout( waiting_time )

    def _wait_for_earliest_service_start(self) -> Generator[Event,Any,None]:
        """
        This utility method yields an event at the time, when the service of the vehicle's current visit can be started with respect to the orders' earliest start time.
        """
        earliest_service_start = max(
            max( ( order.earliest_pickup_start   for order in self.current_visit.pickup_list   if order.earliest_pickup_start   is not None ), default= 0 ),
            max( ( order.earliest_delivery_start for order in self.current_visit.delivery_list if order.earliest_delivery_start is not None ), default= 0 )
        )

        if self.model.env.now < earliest_service_start:
            self.model.log.custom( f'waiting for earliest start time at {earliest_service_start}', vehicle= self )
            yield self.model.env.medium_timeout( earliest_service_start - self.model.env.now )

    def _pickup_order( self, order:Order, service_duration:SimTime= 0, check_capacity:bool= True ) -> Generator[Event,Any,None]:
        # check pre conditions
        if order.is_delivered:
            raise SimulationError( f'order {order} to pickup is already delivered' )

        if order.is_picked_up:
            raise SimulationError( f'order {order} to pickup is already picked up' )
        
        if self.current_location is not order.pickup_location:
            raise SimulationError( f'the pickup location of order {order} is {order.pickup_location}' )
        
        if self.is_capacitated and check_capacity:
            if self.capacity + 0.000001 < sum( loaded.quantity for loaded in self.carrying_orders ) + order.quantity:
                raise SimulationError( f'capacity constraint for vehicle {self} is violated when loading order {order}' )

        # simulate loading
        if 0 < service_duration:
            yield self.model.env.medium_timeout( service_duration )
        
        # update vehicle status
        self.carrying_orders.append( order )

        # update order status
        order.pickup( self )

    def _deliver_order( self, order:Order, service_duration:SimTime= 0 ) -> Generator[Event,Any,None]:
        # check pre conditions
        if not order.is_picked_up:
            raise SimulationError( f'order {order} to deliver is not picked up yet' )

        if order.is_delivered:
            raise SimulationError( f'order {order} to deliver is already delivered' )
        
        if self.current_location is not order.delivery_location:
            raise SimulationError( f'delivery location of order {order} is {order.delivery_location}' )
        
        # simulate unloading
        if 0 < service_duration:
            yield self.model.env.medium_timeout( service_duration )

        # update vehicle status
        if self.is_subject_to_fifo_load:
            if order != self.carrying_orders[0]:
                raise SimulationError( f'FIFO loading rule for self {self} is violated by delivering order {order}' )
            
            self.carrying_orders.pop( 0 )
        
        elif self.is_subject_to_lifo_load:
            if order != self.carrying_orders[-1]:
                raise SimulationError( f'LIFO loading rule for self {self} is violated by delivering order {order}' )
        
            self.carrying_orders.pop( -1 )
        
        else:         
            if order not in self.carrying_orders:
                raise SimulationError( f'order {order} to deliver is currently not on vehicle {self}' )
            
            self.carrying_orders.remove( order )

        # update order status
        order.deliver()

    #endregion
