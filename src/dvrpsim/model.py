import time

from simpy.core               import SimTime
from simpy.resources.resource import Resource
from typing                   import Any, Dict, Generator, Iterator

import dvrpsim.utils.checker as decision_checker

from dvrpsim.exceptions       import ModelError, RoutingError, SimulationError
from dvrpsim.elements.order   import Order, OrderStatus
from dvrpsim.environment      import DVRPEnvironment, Event

from dvrpsim.elements.vehicle  import Visit, Vehicle, VehicleStatus
from dvrpsim.elements.location import Location

from dvrpsim.utils.logging import LoggingCallback, DefaultLoggingCallback

class Model:
    """
    Discrete event-based simulator for dynamic vehicle routing.

    :param Any probdata: (optional) problem data

    Elements:

    :ivar Any                private_data: private problem data (should not be shared with the external routing algorithm)
    :ivar Any                public_data:  public problem data (could be shared with the external routing algorithm)
    :ivar DVRPEnvironment    env:          simulation environment
    :ivar int                epoch:        current decision epoch
    :ivar Dict[Any,Location] _locations:   dictionary of locations (id -> location)
    :ivar Dict[Any,Vehicle]  _vehicles:    dictionary of vehicles  (id -> vehicle)
    :ivar Dict[Any,Order]    _orders:      dictionary of orders    (id -> order)
    :ivar LoggingCallback    log:          logger

    :ivar int epoch: sequence number of the current epoch
    """
    def __init__(self) -> None:
        self.private_data:Any = None
        self.public_data:Any = None

        self.env:DVRPEnvironment = DVRPEnvironment()
        self.epoch:int = 0

        # elements (id -> object)
        self._locations:Dict[Any,Location] = {}
        self._vehicles:Dict[Any,Vehicle]   = {}
        self._orders:Dict[Any,Order]       = {}

        # auxiliary
        self.all_orders_are_requested:Event = self.env.event()
        self._routing_in_progress:bool = False
        self._requested_routing_finished:Event = None

        # logger
        self.log:LoggingCallback = None
        self._init_logger()

    def _init_logger(self) -> None:
        """Initializes the logging callback."""
        self.log = DefaultLoggingCallback(self)
    
    #region Basic properties and functions

    @property
    def locations(self):
        """Returns a collection of the locations."""
        return self._locations.values()
    
    @property
    def vehicles(self):
        """Returns a collection of the vehicles."""
        return self._vehicles.values()
    
    @property
    def orders(self):
        """Returns a collection of the orders."""
        return self._orders.values()

    @property
    def open_orders(self) -> Iterator[Order]:
        """Returns an iterator yielding those requested orders which are not rejected, not canceled, and not yet delivered."""
        return filter( lambda order : order.is_open, self.orders )
    
    @property
    def orders_under_delivery(self) -> Iterator[Order]:
        """Returns an iterator yielding those orders, which are currently under delivery."""
        return filter( lambda order : order.is_under_delivery, self.orders )
    
    @property
    def delivered_orders(self) -> Iterator[Order]:
        """Returns an iterator yielding already delivered orders."""
        return filter( lambda order : order.is_delivered, self.orders )
    
    @property
    def cancelled_orders(self) -> Iterator[Order]:
        """Returns an iterator yielding already cancelled orders."""
        return filter( lambda order : order.is_canceled, self.orders )

    #endregion

    #region Model builders

    def get_location_by_id( self, location_id:str ) -> Location:
        """
        Returns the location with the given id, if it exists, otherwise None.

        :param str location_id: location id
        """
        return self._locations.get( location_id, None )
    
    def get_vehicle_by_id( self, vehicle_id:str ) -> Vehicle:
        """
        Returns the vehicle with the given id, if it exists, otherwise None.

        :param str vehicle_id: vehicle id        
        """
        return self._vehicles.get( vehicle_id, None )
    
    def get_order_by_id( self, order_id:str ) -> Order:
        """
        Returns the order with the given id, if it exists, otherwise None.

        :param str order_id: order id        
        """
        return self._orders.get( order_id, None )
        
    def add_location( self, location:Location ) -> None:
        """
        Adds the given location to the model.
        
        :param Location location: location to add
        """
        # check environment
        if location.model is not None and location.model is not self:
            raise ModelError( f'location {location} belongs to a different model' )
        
        if location.resource is not None and self.env is not location.resource._env:
            raise ModelError( f'resource of location {location} belongs to a different environment' )
        
        if self.get_location_by_id( location.id ) is not None:
            raise ModelError( f'location with id "{location.id}" already exists' )
        
        # store location
        self._locations[location.id] = location
        location.model = self

    def add_vehicle( self, vehicle:Vehicle ) -> None:
        """
        Adds the given vehicle to the model.
        
        :param Vehicle vehicle: vehicle to add
        """
        # check environment
        if vehicle.model is not None and vehicle.model is not self:
            raise ModelError( f'vehicle {vehicle} belongs to a different model' )
        
        # check id
        if self.get_vehicle_by_id( vehicle.id ) is not None:
            raise ModelError( f'vehicle with id "{vehicle.id}" already exists' )
        
        # store vehicle
        self._vehicles[vehicle.id] = vehicle
        vehicle.model = self

    def request_order( self, order:Order, decision_point_on_request:bool= False ) -> None:
        """
        Requests the given order at its release time.
        If the release time is not set or has already passed, the release time is set to the current simulation time.
        Once the order has been requested, it is added to the model.

        :param Order order:                     order to request
        :param bool  decision_point_on_request: should a decision point be imposed on the order request?
        """
        # check environment
        if order.model is not None and order.model is not self:
            raise ModelError( f'order {order} belongs to a different model' )

        if self.get_order_by_id( order.id ) is not None:
            raise ModelError( f'could not request order {order} since an order with the same id is already added to the model' )
        
        # request order
        if order.release_date is None or order.release_date < self.env.now:
            order.release_date = self.env.now

        self.env.process( self._request_order_proc( order, decision_point_on_request ) )
    
    def _request_order_proc( self, order:Order, decision_point_on_request:bool= False ) -> Generator[Event,Any,None]:
        """
        An auxiliary method for requesting orders in separate processes (see request_order)).
        """
        if self.env.now < order.release_date:
            yield self.env.medium_timeout( order.release_date - self.env.now )
        
        self._add_order( order )

        # log
        self.log.on_order_request( order )

        # callbacks
        order.on_request()
        self.on_order_request( order )

        # decision point
        if decision_point_on_request:
            self.request_for_routing()
        
    def _add_order( self, order:Order ) -> None:
        """
        Adds the given order to the model.
        
        :param Order order: order to add
        """
        # check environment  
        if order.model is not None and order.model is not self:
            raise ModelError( f'order {order} belongs to a different model' )
        
        # check id
        if order.id in self._orders.keys():
            raise ModelError( f'order with id: "{order.id}" already exists' )
        
        # store
        self._orders[order.id] = order
        order.model = self

    def create_resource( self, capacity:int = 1 ) -> Resource:
        """
        Creates and return a shared resource with the given capacity.
        """
        return Resource( self.env, capacity= capacity )

    #endregion
        
    #region Main functions

    def init( self ) -> None:
        return

    def run( self ) -> None:
        """Starts simulation."""        
        try:
            self.init()

            self.on_simulation_start()
            self.env.run()
            self.on_simulation_finish()
        
        except Exception as error:
            self.log.error( f'could not finish simulation due to the following error: {error}' )

    def request_for_routing( self ) -> Event:
        """
        This method imposes a decision point for routing.
        If multiple requests arrive at the same time, only one process will be created.

        The method creates a separate :class:`~.simpy.Process` for the routing.

        The method returns the event, which will be "succeeded" when the routing is finished.
        """
        if self._requested_routing_finished is None:      
            self._requested_routing_finished = Event( self.env )
            self.env.process( self._routing() )

        return self._requested_routing_finished

    def _routing( self ) -> Generator[Event,Any,None]:
        """
        Main process for routing.
        """
        yield self.env.high_timeout(0) # dummy event to wait for other events happening at the same time

        # init
        finish_event = self._requested_routing_finished
        self._requested_routing_finished = None
        
        if self._routing_in_progress:
            raise SimulationError( 'routing is already in progress' ) # TODO policy

        self.epoch += 1
        
        # log
        self.log.on_routing_start()

        # callback
        self.on_routing_start()

        # routing
        yield self.env.high_timeout(0) # dummy event to avoid conflicts with possible interruptions in the previous callback

        self._routing_in_progress = True
        
        elapsed_seconds = 0
        
        # callback: routing
        decision = None
        
        try:
            start_time = time.time()            
            decision = self.routing_callback()
            elapsed_seconds = time.time() - start_time

        except Exception as exc:
            raise RoutingError( f'problem with routing: {exc}' )
        
        # create event
        yield self.env.process( self._simulate_elapsed_routing_time(elapsed_seconds) )

        self._routing_in_progress = False

        # log
        self.log.on_routing_finish()

        # callback
        self.on_routing_finish( decision )

        # decision enforcement
        self._enforce_decision( decision )

        # set routing finished
        finish_event.succeed()

    def _simulate_elapsed_routing_time( self, elapsed_seconds:float ) -> Generator[Event,Any,None]:
        """
        This method can be used to convert the real execution time of decision making to simulation time.

        By default, decision making is instantaneous.

        :param float elapsed_seconds: elapsed seconds in real time
        """
        yield self.env.low_timeout( delay= 0 )

    def get_state( self ) -> Dict[str,Any]:
        """
        Returns the current state.
        """
        state = {
            'time': self.env.now,
            'vehicles': {},
            'open_orders': {},
            'cancelled_orders': [],
            'aux': {}
        }

        # vehicles
        for vehicle in self.vehicles:
            state['vehicles'][vehicle.id] = {
                'status': vehicle.status.name,
                'loaded_orders': [ order.id for order in vehicle.carrying_orders ],
                'previous_visit': {
                    'location':       vehicle.previous_visit.location.id,
                    'departure_time': vehicle.previous_visit.departure_time
                } if vehicle.is_on_the_way else None,
                'current_visit': {
                    'location':            vehicle.current_visit.location.id,
                    'arrival_time':        vehicle.current_visit.arrival_time,
                    'service_start_time':  vehicle.current_visit.service_start_time,
                    'service_finish_time': vehicle.current_visit.service_finish_time,
                    'pickup_list':         [ order.id for order in vehicle.current_visit.pickup_list ],
                    'delivery_list':       [ order.id for order in vehicle.current_visit.delivery_list ],
                    'aux':                 vehicle.current_visit.aux
                } if vehicle.is_at_location else None,
                'next_visits': [ visit.to_dict() for visit in vehicle.next_visits ]
            }

        # orders
        for order in self.open_orders:
            state['open_orders'][order.id] = {
                'id':                      order.id,
                'original_id':             order.original_id,
                'quantity':                order.quantity,
                'release_date':            order.release_date,
                'due_date':                order.due_date,
                'pickup_location':         order.pickup_location.id,
                'earliest_pickup_start':   order.earliest_pickup_start,
                'latest_pickup_start':     order.latest_pickup_start,
                'pickup_duration':         order.pickup_duration,
                'delivery_location':       order.delivery_location.id,
                'earliest_delivery_start': order.earliest_delivery_start,
                'latest_delivery_start':   order.latest_delivery_start,
                'delivery_duration':       order.delivery_duration,                
                'pickup_time':             order.pickup_time,
                'pickup_vehicle':          order.pickup_vehicle.id if order.pickup_vehicle is not None else None,
                'aux':                     order.aux
            }

        for order in self.open_orders:
            state['open_orders'][order.id]['assigned_vehicle'] = None

            if order.pickup_vehicle is not None:
                state['open_orders'][order.id]['assigned_vehicle'] = order.pickup_vehicle.id
                continue

        for vehicle in self.vehicles:
            if vehicle.current_visit is not None:
                for order in vehicle.current_visit.pickup_list:
                    state['open_orders'][order.id]['assigned_vehicle'] = vehicle.id

            for visit in vehicle.next_visits:
                for order in visit.pickup_list:
                    state['open_orders'][order.id]['assigned_vehicle'] = vehicle.id                

        state['cancelled_orders'] = [ order.id for order in self.cancelled_orders ]

        return state
    
    def _enforce_decision( self, raw_decision:Dict[str,Any] ) -> None:
        """
        Processes and enforces the given "raw" decision.

        :param Dict[str,Any] raw_decision: "raw" decision
        """
        try:
            # process decision
            processed_decision = self._process_decision( raw_decision )

            # check decision
            self._check_decision( processed_decision )

            # enforce decision on orders
            order:Order
            for order, order_decision in processed_decision['orders'].items():
                order_status = order_decision['status']

                if order_status == OrderStatus.ACCEPTED:
                    order.accept()

                elif order_status == OrderStatus.REJECTED:
                    order.reject()

                elif order_status == OrderStatus.POSTPONED:
                    if order_decision.get( 'postponed_until', None ) is None:
                        raise RoutingError( f'(missing key "postponed_until") no postponement time is given' )
                    
                    order.postpone( until= order_decision['postponed_until'] )

                else:
                    raise RoutingError( f'unexpected decision on order {order}: {order_status}' )
                    
            # enforce decision on vehicles
            for vehicle, vehicle_decision in processed_decision['vehicles'].items():
                if vehicle_decision is None:
                    continue

                # update current visit, if needed
                if vehicle_decision['current_visit'] is not None:
                    if vehicle.current_visit is None:
                        raise RoutingError( f'current visit of {vehicle} cannot be modified since it does not exist' )
                    
                    if vehicle.current_visit.service_start_time is not None:
                        raise RoutingError( f'current visit of {vehicle} cannot be modified since the service has already started' )

                    vehicle.current_visit.pickup_list = vehicle_decision['current_visit'].pickup_list
                    vehicle.current_visit.delivery_list = vehicle_decision['current_visit'].delivery_list

                # update next visits, if needed
                new_route = vehicle_decision.get( 'next_visits', None )
            
                if new_route is not None:
                    if vehicle.is_en_route:                        
                        if len(new_route) == 0:
                            raise RoutingError( f'next visit of en route {vehicle} is missing' )
                        
                        if new_route[0].location != vehicle.next_location:
                            raise RoutingError( f'(en route diversion) next location of an en route vehicle ({vehicle}) cannot be changed' )

                    vehicle.next_visits = new_route[:]

                if vehicle.is_idle:
                    vehicle.run()

        except Exception as exc:
            raise RoutingError( f'could not enforce decision due to: {exc}' )

    def _process_decision( self, raw_decision:Dict[str,Any] ) -> Dict[str,Any]:
        """
        Transforms the external routing algorithm's "raw" decision to "processed" decision.

        :param Dict[str,Any] raw_decision: "raw" decision
        """
        try:
            processed_decision = {
                'vehicles': {},
                'orders': {}
            }

            # vehicles
            for vehicle_id, raw_vehicle_decision in raw_decision['vehicles'].items():
                vehicle = self.get_vehicle_by_id( vehicle_id )

                if vehicle is None:
                    raise RoutingError( f'unknown vehicle: {vehicle_id}' )

                processed_decision['vehicles'][vehicle] = {
                    'current_visit': None,
                    'next_visits': None
                }

                # current 
                raw_current_visit = raw_vehicle_decision.get( 'current_visit', None )
                if raw_current_visit is not None:
                    current_visit = Visit.parse_dict( self, raw_current_visit ) # NOTE times are not given! # TODO

                    processed_decision['vehicles'][vehicle]['current_visit'] = current_visit

                # next visits
                raw_next_visits = raw_vehicle_decision.get( 'next_visits', None )
                if raw_vehicle_decision['next_visits'] is not None:
                    processed_decision['vehicles'][vehicle]['next_visits'] = []

                    for raw_visit in raw_next_visits:
                        next_visit = Visit.parse_dict( self, raw_visit )
                        
                        processed_decision['vehicles'][vehicle]['next_visits'].append( next_visit )

            # orders
            for order_id, raw_order_decision in raw_decision['orders'].items():
                order = self.get_order_by_id( order_id )

                if order is None:
                    raise RoutingError( f'unknown order {order_id}' )

                order_status = raw_order_decision['status']

                try:
                    raw_order_decision['status'] = OrderStatus[order_status.upper()]

                except Exception:
                    raise RoutingError( f'could not process status of order {order}: {order_status}' )
                
                processed_decision['orders'][order] = raw_order_decision

            return processed_decision
        
        except Exception as exc:
            raise RoutingError( f'could not process decision due to: {exc}' )
   
    def _check_decision( self, processed_decision:Dict[str,Any] ) -> None:
        """
        Checks the given "processed" solution.

        Raises ``RoutingError`` if the decision is not feasible with respect to the current state.

        :param Dict[str,Any] processed_decision: "processed" decision
        """        
        try:
            decision_checker.check_state_feasibility_constraints( processed_decision )
            decision_checker.check_capacity_constraints( processed_decision )
            
        except Exception as exc:
            raise RoutingError( f'could not apply decision due to: {exc}' )

    #endregion
        
    #region Callbacks - Simulation-related events

    def on_simulation_start( self ) -> None:
        """
        This callback method is called when the simulation is about to be started.
        """
        self.log.on_simulation_start()

        # set current visits for vehicles according to their initial location
        for vehicle in self.vehicles:
            vehicle.current_visit                     = Visit()
            vehicle.current_visit.location            = vehicle.initial_location
            vehicle.current_visit.arrival_time        = self.env.now
            vehicle.current_visit.service_start_time  = self.env.now
            vehicle.current_visit.service_finish_time = self.env.now

        # check vehicles' initial status
        for vehicle in self.vehicles:
            if vehicle.initial_location is None:
                self.log.warning( f'vehicle {vehicle} is not associated with initial location' )

            elif vehicle.initial_location.model != self:
                raise SimulationError( f'initial location {vehicle.initial_location.id} of vehicle {vehicle} belongs to another model' )

    def on_simulation_finish( self ) -> None:
        """
        This callback method is called when the simulation is finished.
        """
        self.log.on_simulation_finish()        
        
        for vehicle in self.vehicles:
            if vehicle.status != VehicleStatus.IDLE:
                raise SimulationError( f'could not finalize simulation, since the status of vehicle {vehicle} is not {VehicleStatus.IDLE.name}, but {vehicle.status.name}' )
            
            vehicle.current_visit.departure_time = self.env.now
            vehicle.previous_visits.append( vehicle.current_visit )
            vehicle.current_visit = None

        for order in self.orders:
            if order.is_without_decision:
                self.log.warning( f'no decision has been made on order {order}' )

            if order.is_accepted and not order.is_delivered:
                self.log.warning( f'order {order} has been accepted but has not been delivered' )

    #endregion

    #region Callbacks - Order-related events
    
    def on_order_request( self, order:Order ) -> None:
        """
        This callback method is called whenever an order is requested.

        :param Order order: requested order
        """
        pass

    def on_order_acceptance( self, order:Order ) -> None:
        """
        This callback method is called whenever an order is accapted.

        :param Order order: accepted order
        """
        pass

    def on_order_rejection( self, order:Order ) -> None:
        """
        This callback method is called whenever an order is rejected.

        :param Order order: rejected order
        """
        return
    
    def on_order_update( self, order:Order ) -> None:
        """
        This callback method is called whenever an order is updated (modified).

        :param Order order: updated order
        """
        self.request_for_routing()

    def on_order_cancellation( self, order:Order ) -> None:
        """
        This callback method is called whenever an order is canceled.

        :param Order order: canceled order
        """
        self.request_for_routing()
    
    def on_order_postponement( self, order:Order, until:SimTime ) -> None:
        """
        This callback method is called whenever an order is about to be postponed.

        :param Order   order: order to postpone
        :param SimTime until: the time until the decision about the order is postponed
        """
        return
    
    def on_order_postponement_interruption( self, order:Order ) -> None:
        """
        This callback method is called whenever the postponement process of an order is interrupted.

        :param Order order: interrupted order
        """
        return
    
    def on_order_postponement_expiration( self, order:Order ) -> None:
        """
        This callback method is called whenever the postponement process of an order is expired.

        :param Order order: reappeared order
        """
        self.request_for_routing()

    def on_order_pickup( self, order:Order ) -> None:
        """
        This method is called whenever an order is picked up.
        
        :param Order order: picked order
        """
        return

    def on_order_delivery( self, order:Order ) -> None:
        """
        This method is called whenever an order is delivered.
        
        :param Order order: delivered order
        """
        return

    #endregion

    #region Callbacks - Vehicle-related events

    def on_vehicle_predeparture_interruption( self, vehicle:Vehicle ) -> None:
        """
        This callback method is called whenever the pre-departure process of a vehicle is interrupted.

        :param Vehicle vehicle: interrupted vehicle
        """
        return

    def on_vehicle_departure( self, vehicle:Vehicle ) -> None:
        """
        This callback method is called whenever a vehicle is departed from a location.

        :param Vehicle vehicle: departed vehicle
        """
        return

    def on_vehicle_travel_interruption( self, vehicle:Vehicle ) -> None:
        """
        This callback method is called whenever the travel process of a vehicle is interrupted.

        :param Vehicle vehicle: interrupted vehicle
        """
        return

    def on_vehicle_arrival( self, vehicle:Vehicle ) -> None:
        """
        This callback method is called whenever a vehicle is arrived at a location.

        :param Vehicle vehicle: arrived vehicle
        """
        return

    def on_vehicle_preservice_interruption( self, vehicle:Vehicle ) -> None:
        """
        This callback method is called whenever the pre-service process of a vehicle is interrupted.

        :param Vehicle vehicle: interrupted vehicle
        """
        return

    def on_vehicle_service_start( self, vehicle:Vehicle ) -> None:
        """
        This callback method is called whenever the service of a vehicle is about to start.

        :param Vehicle vehicle: vehicle under service
        """
        for order in vehicle.current_visit.pickup_list:
            order.can_be_rejected_or_canceled = False

    def on_vehicle_service_interruption( self, vehicle:Vehicle ) -> None:
        """
        This callback method is called whenever the service process of a vehicle is interrupted.

        :param Vehicle vehicle: interrupted vehicle
        """
        return

    def on_vehicle_service_finish( self, vehicle:Vehicle ) -> None:
        """
        This callback method is called whenever the service of a vehicle is finished.

        :param Vehicle vehicle: finished vehicle
        """
        return

    #endregion

    #region Callbacks - Routing-related events

    def on_routing_start(self) -> None:
        """
        This callback method is called whenever a routing procedure is about to start.

        By default, this method interrupts the orders' postponement and the vehicle's deparutre postponement.
        """
        # interrupt order postponement process, if in progress        
        for order in self.orders:
            order.interrupt_postponement()

        # interrupt departure postponement processes, if in progress
        for vehicle in self.vehicles:
            vehicle.interrupt_predeparture()

    def routing_callback(self) -> Any:
        """
        This callback invokes the external routing algorithm.
        """
        self.log.warning( 'routing callback is not implemented (all orders will be rejected)' )

        state = self.get_state()

        return {
            'vehicles': {},
            'orders': { order_id: { 'status': 'rejected' } for order_id in state['open_orders'] }
        }

    def on_routing_finish( self, decision:Dict[str,Any] ) -> None:
        """
        This callback method is called whenever a decision is ready to be set.

        :param Dict[str,Any] decision: decision to be set
        """
        return
    
    #endregion
