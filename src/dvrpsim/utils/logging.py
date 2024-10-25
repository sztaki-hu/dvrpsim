import logging, logging.config

from abc        import ABC
from simpy.core import SimTime
from typing     import TYPE_CHECKING

if TYPE_CHECKING:
    from dvrpsim.model             import Model
    from dvrpsim.elements.order    import Order
    from dvrpsim.elements.vehicle  import Vehicle
    from dvrpsim.elements.location import Location

DEFAULT_DVRPSIM_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(levelname)-8s: %(message)s"
        },
        "file": {
            "format": "%(message)s"
        }
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        },
        "stderr": {
            "class": "logging.StreamHandler",
            "level": "ERROR",
            "formatter": "simple",
            "stream": "ext://sys.stderr"
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "file",
            "filename": "dvrp.log",
            "mode": "w"
        }
    },
    "loggers": {
        "root": {
            "level": "DEBUG",
            "handlers": [
                "stderr",
                "stdout"
            ]
        },
        "dvrpsim-logger": {
            "level": "DEBUG",
            "handlers": [
                "stderr",
                "stdout",
                "file"
            ],
            "propagate": False
        }
    }
}

class LoggingCallback(ABC):
    """
    Abstract base class for logging callbacks.

    Methods of the class should be used only for logging messages via the logger of the class.

    :param Model model: associated model

    :ivar Model          model:  associated model
    :ivar logging.Logger logger: logger
    :ivar dict[str,Any]  config: config dictionary
    """
    def __init__( self, model:'Model' ) -> None:
        super().__init__()

        self.model  = model
        self.logger = logging.getLogger( 'dvrpsim-logger' )
        self.config = DEFAULT_DVRPSIM_CONFIG

        self._configure_logger()
    
    def _configure_logger(self) -> None:
        """
        Configures logger engine.
        """
        try:
            logging.config.dictConfig( self.config )

        except Exception as exc:
            self.logger.warning( f'could not initialize logger due to: {exc}' )

    def info( self, msg:str ):
        """Logs info message."""
        self.logger.info( msg )

    def warning( self, msg:str ):
        """Logs warning message."""
        self.logger.warning( msg )

    def debug( self, msg:str ):
        """Logs debug message."""
        self.logger.debug( msg )

    def error( self, msg:str ):
        """Logs error message."""
        self.logger.error( msg )

    def custom( self, msg:str, vehicle:'Vehicle'= None, order:'Order'= None, location:'Location'= None ):
        """Logs custom message."""
        pass

    #region Simulation-related
    
    def on_simulation_start( self ) -> None:
        """
        This callback method is called when the simulation is about to be started.
        """
        pass
    
    def on_simulation_finish( self ) -> None:
        """
        This callback method is called when the simulation is finished.
        """
        pass

    #endregion

    #region Order-related

    def on_order_request( self, order:'Order' ) -> None:
        """
        This method is called whenever an order is requested.
        
        :param Order order: requested order
        """
        pass

    def on_order_acceptance( self, order:'Order' ) -> None:
        """
        This method is called whenever an order is accepted.
        
        :param Order order: accepted order
        """
        pass

    def on_order_rejection( self, order:'Order' ) -> None:
        """
        This method is called whenever an order is rejected.
        
        :param Order order: rejected order
        """
        pass

    def on_order_update( self, order:'Order' ) -> None:
        """
        This method is called whenever an order is updated (modified).
        
        :param Order order: updated order
        """
        pass

    def on_order_cancellation( self, order:'Order' ) -> None:
        """
        This method is called whenever an order is cancelled.
        
        :param Order order: cancelled order
        """
        pass

    def on_order_pickup( self, order:'Order' ) -> None:
        """
        This method is called whenever an order is picked up.
        
        :param Order order: picked order
        """
        pass

    def on_order_delivery( self, order:'Order' ) -> None:
        """
        This method is called whenever an order is delivered.
        
        :param Order order: delivered order
        """
        pass

    def on_order_postponement( self, order:'Order', until:SimTime ) -> None:
        """
        This method is called whenever the decision about an order is postponed.
        
        :param Order order:   postponed order
        :param SimTime until: the time until the decision about the order is postponed
        """
        pass

    def on_order_postponement_interruption( self, order:'Order' ) -> None:
        """
        This method is called whenever the postponement process of an order is interrupted.
        
        :param Order order: iterrupted order
        """
        pass

    def on_order_postponement_expiration( self, order:'Order' ) -> None:
        """
        This method is called whenever the postponement process of an order is expired.

        :param Order order: reappeared order
        """
        pass

    #endregion

    #region Vehicle-related

    def on_departure_postponement( self, vehicle:'Vehicle', until:SimTime ) -> None:
        """
        This method is called whenever the departure of a vehicle is postponed.

        :param Vehicle vehicle: postponed vehicle
        :param SimTime until:   the time until the departure of the vehicle is postponed
        """
        pass

    def on_predeparture_interruption( self, vehicle:'Vehicle' ) -> None:
        """
        This method is called whenever the pre-departure process of a vehicle is interrupted.

        :param Vehicle vehicle: interrupted vehicle
        """
        pass

    def on_departure( self, vehicle:'Vehicle' ) -> None:
        """
        This method is called whenever a vehicle is departed from a location.
        
        :param Vehicle vehicle: departed vehicle
        """
        pass

    def on_travel_interruption( self, vehicle:'Vehicle' ) -> None:
        """
        This method is called whenever the travel process of a is interrupted.

        :param Vehicle vehicle: interrupted vehicle
        """
        pass

    def on_arrival( self, vehicle:'Vehicle' ) -> None:
        """
        This method is called whenever a vehicle is arrived at a location.
        
        :param Vehicle vehicle: arrived vehicle
        """
        pass

    def on_preservice_interruption( self, vehicle:'Vehicle' ) -> None:
        """
        This method is called whenever the pre-service process of a vehicle is interrupted.

        :param Vehicle vehicle: interrupted vehicle
        """
        pass

    def on_service_request( self, vehicle:'Vehicle' ) -> None:
        """
        This method is called whenever a vehicle reqests service.

        :param Vehicle vehicle: vehicle to serve
        """
        pass

    def on_service_start( self, vehicle:'Vehicle' ) -> None:
        """
        This method is called whenever the service a vehicle is about to start.

        :param Vehicle vehicle: vehicle to serve
        """
        pass

    def on_service_interruption( self, vehicle:'Vehicle' ) -> None:
        """
        This method is called whenever the service process of a vehicle is interrupted.

        :param Vehicle vehicle: interrupted vehicle
        """
        pass

    def on_service_finish( self, vehicle:'Vehicle' ) -> None:
        """
        This method is called whenever the service of a vehicle is finished.

        :param Vehicle vehicle: finished vehicle
        """
        pass

    #endregion

    #region Routing-related

    def on_routing_start( self ) -> None:
        """This method is called whenever a routing process is about to start."""
        pass

    def on_routing_finish( self ) -> None:
        """This method is called whenever a routing process is finished."""
        pass

    #endregion

class DefaultLoggingCallback(LoggingCallback):
    """
    Default logging callback.
    """
    def __init__( self, model:'Model' ) -> None:
        super().__init__( model )

    def simtime_to_str( self, time:SimTime ) -> str:
        """
        Converts the given simulation time to a string of the format "%H:%M:%S".
        """
        hours, remainder = divmod(int(time), 3600)
        days, hours = divmod( hours, 24 )
        minutes, seconds = divmod(remainder, 60)

        return f'{hours:02d}:{minutes:02d}:{seconds:02d}'

    @property
    def _prefix(self) -> str:
        return f'{self.model.env.now:10.1f} | {self.simtime_to_str( self.model.env.now )} |'

    def custom( self, msg:str, vehicle:'Vehicle'= None, order:'Order'= None, location:'Location'= None ):
        self.logger.info( f'{self._prefix} {f"{vehicle} | " if vehicle is not None else ""}{msg}' )

    #region Simulation-related
    
    def on_simulation_start( self ) -> None:
        self.custom( 'START' )
    
    def on_simulation_finish( self ) -> None:
        self.custom( 'FINISH' )

    #endregion

    #region Order-related

    def on_order_request( self, order:'Order' ) -> None:
        self.logger.info( f'{self._prefix} order {order} is requested ({order.pickup_location} -> {order.delivery_location})' )

    def on_order_rejection( self, order:'Order' ) -> None:
        self.logger.info( f'{self._prefix} order {order} is rejected' )

    def on_order_update( self, order:'Order' ) -> None:
        self.logger.info( f'{self._prefix} order {order} is updated' )
    
    def on_order_cancellation( self, order:'Order' ) -> None:
        self.logger.info( f'{self._prefix} order {order} is cancelled' )

    def on_order_pickup( self, order:'Order' ) -> None:
        self.logger.info( f'{self._prefix} {order.pickup_vehicle} | order {order} is picked up' )

    def on_order_delivery( self, order:'Order' ) -> None:
        self.logger.info( f'{self._prefix} {order.pickup_vehicle} | order {order} is delivered' )

    def on_order_postponement( self, order:'Order', until:SimTime ) -> None:
        self.logger.info( f'{self._prefix} order {order} is postponed until {until}' )

    def on_order_postponement_interruption( self, order:'Order' ) -> None:
        self.logger.info( f'{self._prefix} postponement of order {order} is interrupted' )

    def on_order_postponement_expiration( self, order:'Order' ) -> None:
        self.logger.info( f'{self._prefix} postponement of order {order} is expired' )

    #endregion

    #region Vehicle-related

    def on_departure_postponement( self, vehicle:'Vehicle', until:SimTime ) -> None:
        self.logger.info( f'{self._prefix} {vehicle} | departure is postponed until {until}' )

    def on_predeparture_interruption( self, vehicle:'Vehicle' ) -> None:
        self.logger.info( f'{self._prefix} {vehicle} | pre-departure process is interrupted' )

    def on_departure( self, vehicle:'Vehicle' ) -> None:
        if vehicle.previous_location == vehicle.next_location:
            return # it is not a real departure
        
        self.logger.info( f'{self._prefix} {vehicle} | departed from {vehicle.previous_location} to {vehicle.next_location}' )

    def on_travel_interruption( self, vehicle:'Vehicle' ) -> None:
        self.logger.info( f'{self._prefix} {vehicle} | travel from {vehicle.previous_location} to {vehicle.next_location} is interrupted' )

    def on_arrival( self, vehicle:'Vehicle' ) -> None:
        if vehicle.previous_location == vehicle.current_location:
            return # it is not a real arrival
        
        self.logger.info( f'{self._prefix} {vehicle} | arrived at {vehicle.current_location}' )

    def on_preservice_interruption( self, vehicle:'Vehicle' ) -> None:
        self.logger.info( f'{self._prefix} {vehicle} | pre-service process is interrupted' )

    def on_service_request( self, vehicle:'Vehicle' ) -> None:
        self.logger.info( f'{self._prefix} {vehicle} | service is requested' )

    def on_service_start( self, vehicle:'Vehicle' ) -> None:
        self.logger.info( f'{self._prefix} {vehicle} | service is started' )

    def on_service_interruption( self, vehicle:'Vehicle' ) -> None:
        self.logger.info( f'{self._prefix} {vehicle} | service process is interrupted' )

    def on_service_finish( self, vehicle:'Vehicle' ) -> None:
        self.logger.info( f'{self._prefix} {vehicle} | service is finished' )

    #endregion

    #region Routing-related

    def on_routing_start( self ) -> None:
        self.logger.info( f'{self._prefix} <<< routing >>>' )

    def on_routing_finish( self ) -> None:
        return

    #endregion
