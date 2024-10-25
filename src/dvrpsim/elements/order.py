from enum       import Enum
from simpy      import Event, Interrupt, Process
from simpy.core import SimTime
from typing     import TYPE_CHECKING, Any, Dict, Generator

from dvrpsim.exceptions import SimulationError

if TYPE_CHECKING:
    from dvrpsim.model import Location, Model, Vehicle

class OrderStatus(Enum):
    """Order statuses."""
    NO_DECISION = 0
    POSTPONED   = 1
    ACCEPTED    = 2
    REJECTED    = 3
    CANCELED    = 4

class Order:
    """
    Base class for orders.

    :param str id: unique order id

    Basic attributes:

    :ivar str      id:                      unique order id
    :ivar str      original_id:             original id of the order
    :ivar Model    model:                   the associated model
    :ivar float    quantity:                (optional) quantity
    :ivar SimTime  release_date:            request time
    :ivar SimTime  due_date:                (optional) due date / deadline
    :ivar Location pickup_location:         location to pickup the order
    :ivar SimTime  earliest_pickup_start:   (optional) earliest service start time for pickup
    :ivar SimTime  latest_pickup_start:     (optional) latest service start time for pickup
    :iver SimTime  pickup_duration:         (optional) service time at the pickup
    :ivar Location delivery_location:       location to deliver the order
    :ivar SimTime  earliest_delivery_start: (optional) earliest service start time for delivery
    :ivar SimTime  latest_delivery_start:   (optional) latest service start time for delivery
    :ivar SimTime  delivery_duration:       (optional) service time at the delivery
    
    Attributes set by the simulator:

    :ivar OrderStatus status:                  order status
    :ivar SimTime pickup_time:                 factual pickup time
    :ivar SimTime delivery_time:               factual delivery time
    :ivar Vehicle pickup_vehicle:              the vehicle that picked up the order
    :ivar SimTime acceptance_time:             factual acceptance time (if accepted)
    :ivar SimTime rejection_time:              factual rejection time (if rejected)
    :ivar SimTime cancellation_time:           factual cancellation time (if canceled)
    :ivar bool    can_be_rejected_or_canceled: indicates whether the order can be rejected or canceled
    :ivar Process _postponement_process:       postponement process, if in progress
    """
    def __init__( self, id:str, original_id:str= None ) -> None:
        self.id          = id
        self.original_id = original_id if original_id is not None else id

        self.model:'Model' = None

        # basic attributes
        self.quantity:float = 0

        self.release_date:SimTime = 0
        self.due_date:SimTime     = None

        self.pickup_location:Location      = None
        self.earliest_pickup_start:SimTime = None
        self.latest_pickup_start:SimTime   = None
        self.pickup_duration:SimTime       = 0

        self.delivery_location:Location      = None
        self.earliest_delivery_start:SimTime = None
        self.latest_delivery_start:SimTime   = None
        self.delivery_duration:SimTime       = 0

        self.aux:Dict[str,Any] = {}

        # simulation data
        self.status = OrderStatus.NO_DECISION

        self.acceptance_time:SimTime   = None
        self.rejection_time:SimTime    = None
        self.cancellation_time:SimTime = None

        self.pickup_time:SimTime      = None
        self.pickup_vehicle:'Vehicle' = None
        self.delivery_time:SimTime    = None        

        self.can_be_rejected_or_canceled = True

        self._postponement_process:Process = None

    def __str__(self) -> str:
        return f'{self.id}'

    # region Decision properties

    @property
    def is_without_decision(self) -> bool:
        """Returns whether the order is without decision."""
        return self.status == OrderStatus.NO_DECISION

    @property
    def is_postponed(self) -> bool:
        """Returns whether the order is postponed."""
        return self.status == OrderStatus.POSTPONED

    @property
    def is_accepted(self) -> bool:
        """Returns whether the order is accepted."""
        return self.status == OrderStatus.ACCEPTED

    @property
    def is_rejected(self) -> bool:
        """Returns whether the order is rejected (by the decision maker)."""
        return self.status == OrderStatus.REJECTED

    @property
    def is_canceled(self) -> bool:
        """Returns whether the order is canceled (by the customer)."""
        return self.status == OrderStatus.CANCELED

    # endregion

    # region Status properties

    @property
    def is_picked_up(self) -> bool:
        """Returns whether the order has already been picked up."""
        return self.pickup_time is not None

    @property
    def is_delivered(self) -> bool:
        """Returns whether the order has already been delivered."""
        return self.delivery_time is not None

    @property
    def is_under_delivery(self) -> bool:
        """Returns whether the order is currently under delivery (i.e., already picked up but not yet delivered).""" 
        return self.is_picked_up and not self.is_delivered

    @property
    def is_open(self) -> bool:
        """Returns whether the order is open for routing."""
        return not self.is_delivered and not self.is_rejected and not self.is_canceled

    # endregion

    # region Statistic properties

    @property
    def lateness(self) -> SimTime:
        """Returns the lateness of the order, if applicable."""
        if self.due_date is None:
            return 0

        return self.delivery_time - self.due_date if self.is_delivered else None

    @property
    def tardiness(self) -> SimTime:
        """Returns the tardiness of the order, if applicable."""
        return max( 0, self.lateness ) if self.is_delivered else None

    # endregion

    # region Callbacks I - Decisions

    def accept(self) -> None:
        """
        Accepts the order request.
        """
        if self.status == OrderStatus.REJECTED:
            raise SimulationError( f'already rejected order {self} cannot be accepted' )

        # update status
        self.status = OrderStatus.ACCEPTED
        self.acceptance_time = self.model.env.now

        # log
        self.model.log.on_order_acceptance( self )

        # callbacks
        self.on_acceptance()
        self.model.on_order_acceptance( self )

    def reject(self) -> None:
        """
        Rejects the order request.
        """
        if self.status == OrderStatus.ACCEPTED:
            raise SimulationError( f'already accepted order {self} cannot be rejected' )

        if not self.can_be_rejected_or_canceled:
            raise SimulationError( f'order {self} cannot be rejected (it may have already been picked up)' )

        # update status
        self.status = OrderStatus.REJECTED
        self.rejection_time = self.model.env.now

        # log
        self.model.log.on_order_rejection( self )

        # callbacks
        self.on_rejection()
        self.model.on_order_rejection( self )

    def cancel(self) -> None:
        """
        Cancels the order request.
        """
        if not self.can_be_rejected_or_canceled:
            raise SimulationError( f'order {self} cannot be canceled (it may have already been picked up)' )

        # update status
        self.status = OrderStatus.CANCELED
        self.cancellation_time = self.model.env.now

        # log
        self.model.log.on_order_cancellation( self )

        # callbacks
        self.on_cancellation()
        self.model.on_order_cancellation( self )

    def postpone( self, until:SimTime ) -> None:
        """
        Postpones the order request until the given time.
        
        :param SimTime until: time to postpone until
        """
        if self._postponement_process is not None:
            raise SimulationError( f'could not postpone order {self} due to an ongoing postponement process' )

        if until < self.model.env.now:
            self.model.log.warning( f'could not postpone order {self} until {until} since the current time is {self.model.env.now}' )
            return

        self._postponement_process = self.model.env.process( self._postpone_proc( until ) )

    def _postpone_proc( self, until:SimTime ) -> Generator[Event,Any,None]:
        """
        An auxiliary method for postponing the order in a separate process (see method postpone).
        """
        try:
            self.status = OrderStatus.POSTPONED

            # log
            self.model.log.on_order_postponement( self, until )

            # callbacks
            self.on_postponement( until )
            self.model.on_order_postponement( self, until )

            # wait until the given time
            yield self.model.env.medium_timeout( until - self.model.env.now )

            # log
            self.model.log.on_order_postponement_expiration( self )

            # callbacks
            self.on_postponement_expiration()
            self.model.on_order_postponement_expiration( self )

        except Interrupt:
            # log
            self.model.log.on_order_postponement_interruption( self )

            # callbacks
            self.on_postponement_interruption()
            self.model.on_order_postponement_interruption( self )

            return

        finally:
            self._postponement_process = None

    def interrupt_postponement(self) -> None:
        """
        Interrupts the postponement process of the order, if in progress.
        """
        if self._postponement_process is not None:
            self._postponement_process.interrupt()

    def pickup( self, vehicle:'Vehicle' ) -> None:
        """
        Sets the order to be picked up.

        :param Vehicle vehicle: corresponding vehicle
        """
        # update status
        self.pickup_time = self.model.env.now
        self.pickup_vehicle = vehicle

        # log
        self.model.log.on_order_pickup( self )

        # callbacks
        self.on_pickup()
        self.model.on_order_pickup( self )

    def deliver(self) -> None:
        """
        Sets the order to be delivered.
        """
        # update status
        self.delivery_time = self.model.env.now

        # log
        self.model.log.on_order_delivery( self )

        # callbacks
        self.on_delivery()
        self.model.on_order_delivery( self )

    def update(self) -> None:
        """
        Updates (modifies) the order or notifies about the modification.
        """
        # log
        self.model.log.on_order_update( self )

        # callbacks
        self.on_update()
        self.model.on_order_update( self )

    # endregion

    # region Callbacks II - Events

    def on_request(self) -> None:
        """
        This callback method is called when the order is requested.
        """
        return

    def on_acceptance(self) -> None:
        """
        This callback method is called when the order is accepted.
        """
        return

    def on_rejection(self) -> None:
        """
        This callback method is called when the order is rejected.
        """
        return

    def on_update(self) -> None:
        """
        This callback method is called when the order is updated (modified).
        """
        return

    def on_cancellation(self) -> None:
        """
        This callback method is called when the order is withdrawn.
        """
        return

    def on_postponement( self, until:SimTime ) -> None:
        """
        This callback method is called when the order is about to be postponed.
        
        :param SimTime until: time to postpone until
        """
        return

    def on_postponement_interruption(self) -> None:
        """
        This callback method is called when the postponement process is interrupted.
        """
        return

    def on_postponement_expiration(self) -> None:
        """
        This callback method is called when the postponement process is expired.
        """
        return

    def on_pickup(self) -> None:
        """
        This callback method is called when the order is picked up.
        """
        return

    def on_delivery(self) -> None:
        """
        This callback method is called when the order is delivered.
        """
        return

    # endregion
