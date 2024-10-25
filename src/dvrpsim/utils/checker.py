from typing import Any, Dict, List

from dvrpsim.elements.order   import Order
from dvrpsim.elements.vehicle import Visit, Vehicle
from dvrpsim.exceptions       import RoutingError

def _check_state_feasibility_constraints_of_vehicle( vehicle:Vehicle, processed_vehicle_decision:Dict[str,Any] ):
    if processed_vehicle_decision is None:
        return
    
    # check current visit
    if processed_vehicle_decision.get( 'current_visit', None ) is not None:
        if vehicle.is_en_route:
            raise RoutingError( f'impossible to modify the current visit of an en route vehicle ({vehicle})' )

        elif vehicle.current_visit.service_start_time is not None:
            raise RoutingError( f'current visit of vehicle {vehicle} cannot be modified since the service has already started' )
    
    # check next visit
    next_visits = processed_vehicle_decision.get( 'next_visits', None )

    if next_visits is not None and vehicle.is_en_route:
        if len(next_visits) == 0:
            raise RoutingError( f'next visit of en route {vehicle} is missing' )

        if next_visits[0].location != vehicle.next_location:
            raise RoutingError( f'(en route diversion) next location of an en route vehicle ({vehicle}) cannot be changed' )           

def check_state_feasibility_constraints_of_vehicles( processed_decision:Dict[str,Any] ) -> None:
    for vehicle, processed_vehicle_decision in processed_decision['vehicles'].items():
        _check_state_feasibility_constraints_of_vehicle( vehicle, processed_vehicle_decision )

def _check_state_feasibility_constraints_of_order( order:Order, process_order_decision:Dict[str,Any] ):
    pass

def check_state_feasibility_constraints_of_orders( processed_decision:Dict[str,Any] ) -> None:
    for order, process_order_decision in processed_decision['orders'].items():
        _check_state_feasibility_constraints_of_order( order, process_order_decision )

def check_state_feasibility_constraints( processed_decision:Dict[str,Any] ) -> None:
    """
    Checks the state feasibility constraints of the given processed decision.

    :param Dict[str,Any] processed_decision: processed decision

    :raises: RoutingError: state feasibility constraints are violated
    """
    check_state_feasibility_constraints_of_vehicles( processed_decision )
    check_state_feasibility_constraints_of_orders( processed_decision )

def _get_route( vehicle:Vehicle, processed_vehicle_decision:Dict[str,Any] ) -> List[Visit]:
    route:List[Visit] = []

    if processed_vehicle_decision is None:
        route.append( vehicle.current_visit )
        route += vehicle.next_visits[:]
        return route
    
    if 'current_visit' not in processed_vehicle_decision.keys() or processed_vehicle_decision['current_visit'] is None:
        if vehicle.current_visit is not None:
            route.append( vehicle.current_visit )
    else:
        route.append( processed_vehicle_decision['current_visit'] )

    if 'next_visits' not in processed_vehicle_decision.keys() or processed_vehicle_decision['next_visits'] is None:
        route += vehicle.next_visits[:]
    else:
        route += processed_vehicle_decision['next_visits'][:]

    return route

def _check_capacity_constraint_of_vehicle( vehicle:Vehicle, route:List[Visit] ):
    """
    Checks the capacity constraint of the givel vehicle.

    :param Vehicle vehicle:   the vehicle
    :param List[Visit] route: planned route of the vehicle

    :raises: RoutingError: the capacity constraint of the vehicle is violated
    """
    if not vehicle.is_capacitated:
        return
    
    if len(route) == 0:
        return

    loaded_quantity = sum( order.quantity for order in vehicle.carrying_orders )

    if route[0].service_start_time is None:
        assert vehicle.is_en_route or vehicle.is_waiting_for_service

        loaded_quantity -= sum( order.quantity for order in route[0].delivery_list )
        loaded_quantity += sum( order.quantity for order in route[0].pickup_list )

    elif route[0].service_finish_time is None:
        assert vehicle.is_under_service

        loaded_quantity -= sum( order.quantity for order in route[0].delivery_list if not order.is_delivered )
        loaded_quantity += sum( order.quantity for order in route[0].pickup_list if not order.is_picked_up )

    if vehicle.capacity + 0.0001 <= loaded_quantity:
        raise RoutingError( f'capacity of vehicle {vehicle} is violated at location {route[0].location}: {vehicle.capacity} < {loaded_quantity}' )

    for visit in route[1:]:        
        loaded_quantity -= sum( order.quantity for order in visit.delivery_list )
        loaded_quantity += sum( order.quantity for order in visit.pickup_list )
            
        if vehicle.capacity + 0.0001 <= loaded_quantity:
            raise RoutingError( f'capacity of vehicle {vehicle} is violated at location {visit.location}: {vehicle.capacity} < {loaded_quantity}' )
        
def check_capacity_constraints( processed_decision:Dict[str,Any] ) -> None:
    """
    Checks the capacity constraints of the given vehicles.

    :param Dict[str,Any] processed_decision: processed decision

    :raises: RoutingError: somce capacity constraints are violated
    """
    for vehicle, processed_vehicle_decision in processed_decision['vehicles'].items():
        route = _get_route( vehicle, processed_vehicle_decision )
        _check_capacity_constraint_of_vehicle( vehicle, route )
