from typing import Dict, Any

from dvrpsim.utils.distances import manhattan_distance

def read_sddp_probdata( orders_file:str, nvehicles:int= 3, depot_deadline:int= 540 ) -> Dict[str,Any]:
    probdata = {
        'locations': {},
        'orders':    {},
        'vehicles':  {}
    }

    __read( probdata, orders_file )
    __add_vehicles( probdata, nvehicles )

    probdata['depot_deadline'] = depot_deadline
    
    return probdata

def __read( probdata, filename_with_path:str ) -> None:
    """  
    Line:
        0: customer id
        1: x-coordinate
        2: y-coordinate
        3: request time
        4: earliest arrival time
        5: latest arrival time
    """
    with open( filename_with_path, 'r' ) as txtfile:
        for line in txtfile.readlines():
            if line == '':
                continue

            split = line.strip().split( '\t' )

            if split[0] == 'Req':
                continue # header

            location = {
                'id': 'depot' if split[0] == '0' else f'customer-{split[0]}',
                'x':  int(split[1]),
                'y':  int(split[2]),
            }

            probdata['locations'][location['id']] = location

            if location['id'] != 'depot':
                order = {
                    'id':                        f'O-{split[0]}',
                    'pickup_location':           'depot',
                    'delivery_location':         f'customer-{split[0]}',
                    'release_date':              int(split[3]),
                    'earliest_delivery_arrival': int(split[4]),
                    'latest_delivery_arrival':   int(split[5]),
                }

                probdata['orders'][order['id']] = order

def __add_vehicles( probdata, nvehicles:int ) -> None:
    # "To obtain the travel times in a data set,
    # we adjust all of the distances by a data set-specific factor
    # such that the farthest customer from the depot in the data set can be reached in one hour."
    max_distance = max( manhattan_distance(
        probdata['locations']['depot']['x'],
        probdata['locations']['depot']['y'],
        probdata['locations'][customer]['x'],
        probdata['locations'][customer]['y']
    ) for customer in probdata['locations'].keys() if customer != 'depot' )

    for v in range(nvehicles):
        vehicle = {
            'id':               f'vehicle-{v+1}',
            'initial_location': 'depot',
            'speed':            max_distance # km/h
        }

        probdata['vehicles'][vehicle['id']] = vehicle
