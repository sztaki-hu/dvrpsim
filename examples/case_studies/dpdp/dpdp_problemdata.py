import logging
import csv
import random

from typing import Dict

def read_dpdp_problem( location_file: str, route_file: str, vehice_file: str, order_file: str ) -> dict:
    logging.info( 'read problem data...' )

    probdata = {
        'locations': {},
        'orders':    {},
        'vehicles':  {},

        'travel_times': {},
        'distances':    {},

        'docking_time':   1800, # seconds
        'loading_time':   240,  # seconds per order quantity
        'unloading_time': 240,  # seconds per order quantity
    }
    
    __read_locations( probdata, location_file ),
    __read_routes( probdata, route_file ),
    __read_vehicles( probdata, vehice_file ),
    __read_orders( probdata, order_file )
    __set_initial_locations_for_vehicles( probdata )

    logging.info( 'problem data has been read' )

    return probdata

def __read_locations( probdata, filename_with_path:str ) -> None:
    with open( filename_with_path, 'r' ) as csvfile:
        csvreader = csv.reader( csvfile, delimiter=',' )
        next( csvreader ) # skip header

        for line in csvreader:
            location = {
                'id':            line[0],
                'docking_ports': int(line[3])
            }
            probdata['locations'][location['id']] = location

def __read_routes( probdata, filename_with_path:str ) -> None:
    with open( filename_with_path, 'r' ) as csvfile:
        csvreader = csv.reader( csvfile, delimiter=',' )
        next( csvreader ) # skip header

        for line in csvreader:
            probdata['distances'][(line[1],line[2])]    = float(line[3])
            probdata['travel_times'][(line[1],line[2])] = int(line[4])

def __read_vehicles( probdata, filename_with_path:str ) -> None:
    with open( filename_with_path, 'r' ) as csvfile:
        csvreader = csv.reader( csvfile, delimiter=',' )
        next( csvreader ) # skip header

        for line in csvreader:
            vehicle = {
                'id':               line[0],
                'capacity':         int(line[1]),
                'initial_location': None
            }

            probdata['vehicles'][vehicle['id']] = vehicle    

def __read_orders( probdata, filename_with_path:str ) -> None:
    with open( filename_with_path, 'r' ) as csvfile:
        csvreader = csv.reader( csvfile, delimiter=',' )
        next( csvreader ) # skip header

        for line in csvreader:
            _release_date = list(map( int, line[5].split(':') ))
            _due_date     = list(map( int, line[6].split(':') ))

            release_date = _release_date[0] * 3600 + _release_date[1] * 60 + _release_date[2]
            due_date     =     _due_date[0] * 3600 +     _due_date[1] * 60 +     _due_date[2]

            if due_date < release_date: # due date is on the next day
                due_date += 86400

            items = [ 1.0 ] * int(line[1]) + [ 0.5 ] * int(line[2]) + [ 0.25 ] * int(line[3])

            for i in range(len(items)):
                order = {
                    'id':                f'{line[0]}-{i+1}',
                    'original_id':       line[0],
                    'release_date':      release_date,
                    'pickup_location':   line[9],
                    'delivery_location': line[10],
                    'due_date':          due_date,
                    'quantity':          items[i]
                }

                probdata['orders'][order['id']] = order

def __set_initial_locations_for_vehicles( probdata:Dict[str,dict] ) -> None:
    random.seed(0)
    location_list = list(probdata['locations'].values())

    for vehicle in probdata['vehicles'].values():
        index = random.randint(0, len(location_list) - 1)
        vehicle['initial_location'] = location_list[index]['id']
