import statistics

from typing import Dict, List

from dvrpsim.model import Model

#region History

def collect_vehicle_history( model:Model ) -> Dict[str,List[dict]]:
    """
    Collects the history of the vehicles.
    
    Returns:
        history: vehicle id -> visits
    """
    history = { vehicle_id : [] for vehicle_id in model.vehicles.keys() }

    for vehicle_id, vehicle in model.vehicles.items():
        for visit in vehicle.previous_visits:
            history[vehicle_id].append(
                {
                    'location':       visit.location.id,
                    'arrival_time':   visit.arrival_time,
                    'service_start':  visit.service_start_time,
                    'service_finish': visit.service_finish_time,
                    'departure_time': visit.departure_time,
                    'delivery_list':  [ order.id for order in visit.delivery_list ],
                    'pickup_list':    [ order.id for order in visit.pickup_list ],
                }
            )

    return history

#endregion

#region Statistics

def collect_vehicle_statistics( model:Model ) -> Dict[str,dict]:
    """
    Collects default statistics of vehicles.

    :param Model model: model

    :return: vehicle id -> statistics (distance traveled, moving/waiting/service/idle time)
    """
    vehicle_statistics = { vehicle.id : {} for vehicle in model.vehicles }

    for vehicle in model.vehicles:
        vehicle_statistics[vehicle.id]['distance'] = 0
        vehicle_statistics[vehicle.id]['moving']   = 0

        if 1 < len(vehicle.previous_visits):
            for i in range(1,len(vehicle.previous_visits)):
                vehicle_statistics[vehicle.id]['distance'] += vehicle.travel_distance( vehicle.previous_visits[i-1].location, vehicle.previous_visits[i].location )
                vehicle_statistics[vehicle.id]['moving']   += vehicle.previous_visits[i].arrival_time - vehicle.previous_visits[i-1].departure_time

        vehicle_statistics[vehicle.id]['waiting'] = sum( visit.waiting_time for visit in vehicle.previous_visits )
        vehicle_statistics[vehicle.id]['service'] = sum( visit.service_time for visit in vehicle.previous_visits )
        vehicle_statistics[vehicle.id]['idle']    = sum( visit.idle_time for visit in vehicle.previous_visits )

    return vehicle_statistics

def collect_order_statistics( model:Model ) -> Dict[str,dict]:
    """
    Collects default statistics of orders.

    :param Model model: model

    :return: vehicle id -> statistics (tardiness)
    """
    order_statistics = { order.original_id: {} for order in model.orders }

    for original_id in order_statistics.keys():
        suborders = list( filter( lambda order : order.original_id == original_id, model.orders ) )
        due_date = max( order.due_date for order in suborders )
        delivery_time = max( order.delivery_time for order in suborders )

        if due_date is None or delivery_time is None:
            order_statistics[original_id]['tardiness'] = 0
            
        else:
            order_statistics[original_id]['tardiness'] = max( 0, delivery_time - due_date )

    return order_statistics

def print_statistics( dvrp_statistics:Dict[str,dict], header:str= '', onebyone:bool= True, column_width:int= 10 ) -> None:
    all_keys = sorted( list( set( key for stats in dvrp_statistics.values() for key in stats.keys() ) ) )

    ncols = len(all_keys) + 1

    print( '─┬─'.join( [ '─' * column_width ] * ncols ) )

    print( ' │ '.join( [ f'{header[:column_width].ljust(column_width)}' ] + list( map( lambda key : f'{key[:column_width]:>{column_width}s}', all_keys ) ) ) )
        
    if onebyone:
        print( '─┼─'.join( [ '─' * column_width ] * ncols ) )

        for id, stats in dvrp_statistics.items():
            print( ' │ '.join(
                [ f'{id[:column_width].ljust(column_width)}' ] +
                list( map( lambda key : f'{stats[key]:{column_width}.1f}' if key in stats.keys() else ' ' * column_width, all_keys ) )
            ) )

    print( '─┼─'.join( [ '─' * column_width ] * ncols ) )

    print( ' │ '.join(
        [ f'{"total"[:column_width].ljust(column_width)}' ] +
        list( map( lambda key : f'{sum( stat[key] if key in stat.keys() else 0 for stat in dvrp_statistics.values() ):{column_width}.1f}', all_keys ) )
    ) )

    print( '─┼─'.join( [ '─' * column_width ] * ncols ) )

    print( ' │ '.join(
        [ f'{"avg"[:column_width].ljust(column_width)}' ] +
        list( map( lambda key : f'{statistics.mean( vehicle_statistics[key] if key in vehicle_statistics.keys() else 0 for vehicle_statistics in dvrp_statistics.values() ):{column_width}.1f}', all_keys ) )
    ) )

    print( '─┴─'.join( [ '─' * column_width ] * ncols ) )

#endregion
