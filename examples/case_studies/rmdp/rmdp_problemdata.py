from typing import Dict, Any

def read_rmdp_problem( restaurants_file:str, vehicles_file:str, orders_file:str, instance_realization:int ) -> Dict[str,Any]:
    probdata = {
        'locations': {},
        'orders':    {},
        'vehicles':  {}
    }

    __read_restaurants( probdata, restaurants_file )    
    __read_vehicles( probdata, vehicles_file )
    __read_orders( probdata, orders_file, instance_realization )

    return probdata

def __read_restaurants( probdata, filename_with_path:str ) -> None:
    with open( filename_with_path, 'r' ) as txtfile:
        for line in txtfile.readlines():
            if line == '':
                continue

            split = line.strip().split( '\t' )

            location = {
                'id':  f'restaurant-{split[0]}',
                'lat': float(split[1]),
                'lon': float(split[2]),
            }

            probdata['locations'][location['id']] = location

def __read_vehicles( probdata, filename_with_path:str ) -> None:
    with open( filename_with_path, 'r' ) as txtfile:
        for line in txtfile.readlines():
            if line == '':
                continue

            split = line.strip().split( '\t' )

            location = {
                'id':  f'vehicle-location-{split[0]}',
                'lat': float(split[1]),
                'lon': float(split[2]),
            }

            probdata['locations'][location['id']] = location

            vehicle = {
                'id':               f'V-{split[0]}',
                'initial_location': location['id']
            }

            probdata['vehicles'][vehicle['id']] = vehicle

def __read_orders( probdata, filename_with_path:str, instance_realization:int ) -> None:
    """        
    Line:
        0: instance realization (1..4000)
        1: order id
        2: release time (minutes)
        3: latitude of the customer's location
        4: longitude of the customer's location
        5: restaurant id
        6: pre-calculated ready time
    """
    with open( filename_with_path, 'r' ) as txtfile:
        for line in txtfile.readlines():
            if line == '':
                continue

            split = line.strip().split( '_' )

            if int(split[0]) != instance_realization:
                continue

            location = {
                'id':  f'customer-{split[1]}',
                'lat': float(split[3]),
                'lon': float(split[4]),
            }

            probdata['locations'][location['id']] = location

            order = {
                'id':                f'O-{split[1]}',
                'pickup_location':   f'restaurant-{split[5]}',
                'delivery_location': location['id'],
                'release_date':      int(split[2]),
                'due_date':          int(split[2]) + 40, # "To compute the delivery deadlines, we set the value of t = 40 minutes for every order."
                'ready_time':        int(split[6]),
            }

            probdata['orders'][order['id']] = order
