from simpy.core   import Environment, SimTime
from simpy.events import Event, EventCallbacks, EventPriority, Timeout
from typing       import Optional, Any

class DVRPEvent(Event):
    """
    Customized simpy Event with priority.
    """
    def __init__( self, env:Environment, delay:SimTime= 0, priority:int= 1, value:Optional[Any]= None ):
        if delay < 0:
            raise ValueError(f'Negative delay {delay}')
        
        self.env                      = env
        self.callbacks:EventCallbacks = []
        self._value                   = value
        self._delay                   = delay
        self._ok                      = True

        env.schedule( self, EventPriority(priority), delay )

class DVRPEnvironment(Environment):
    """
    Customized simpy Environment.
    """
    def __init__( self ):
        super().__init__( initial_time= 0 )

    def timeout( self, delay:SimTime= 0, priority:int = 3, value:Optional[Any]= None ) -> Timeout:
        return DVRPEvent( self, delay, priority, value )
    
    def low_timeout( self, delay:SimTime= 0, value:Optional[Any]= None ) -> Timeout:
        """Returns a timeout event with low priority."""
        return self.timeout( delay= delay, priority= 1, value= value )
    
    def medium_timeout( self, delay:SimTime= 0, value:Optional[Any]= None ) -> Timeout:
        """Returns a timeout event with medium priority."""
        return self.timeout( delay= delay, priority= 3, value= value )
    
    def high_timeout( self, delay:SimTime= 0, value:Optional[Any]= None ) -> Timeout:
        """Returns a timeout event with high priority."""
        return self.timeout( delay= delay, priority= 5, value= value )
    