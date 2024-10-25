from simpy.resources.resource import Resource
from typing                   import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from dvrpsim.model import Model

class Location:
    """
    Base class for locations.

    :param str      id:       unique location id
    :param Resource resource: shared resource of the location, if any
    :param Model    model:    the associated model
    :param float    x:        x-coordinate (or latitude) of the location, if given
    :param float    y:        y-coordinate (or longitude) of the location, if given
    
    :ivar str           id:       unique location id
    :ivar Resource      resource: shared resource of the location, if any
    :ivar Model         model:    the associated model
    :ivar float         x:        x-coordinate (or latitude) of the location, if given
    :ivar float         y:        y-coordinate (or longitude) of the location, if given
    :ivar Dict[str,Any] aux:      auxiliary data
    """
    def __init__( self, id:str, resource:Resource= None, model:'Model'= None, x:float= None, y:float= None ) -> None:
        self.id = id
        self.resource:Resource = resource
        self.model:'Model' = model
        self.x:float = x
        self.y:float = y
        self.aux:Dict[str,Any] = {}

    def __str__(self) -> str:
        return f'{self.id}'
    
    @property
    def capacity(self) -> float|int:
        """Returns the capacity of the resource, if any."""
        return self.resource.capacity if self.resource is not None else None
    