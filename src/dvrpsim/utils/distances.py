from math import radians, sin, cos, asin, sqrt

def great_circle_distance( lon1:float, lat1:float, lon2:float, lat2:float ) -> float:
    """
    Returns the greate-circle distance between the given points (provided by longitudes and latitudes) using the Haversine formula.

    :param float lon1: longitude of the first point
    :param float lat1: latitude of the first point
    :param float lon2: longitude of the second point
    :param float lat2: latitude of the second point

    :return: greate-circle distance (in kilometers)
    :rtype: float
    """
    rlon1 = radians(lon1)
    rlat1 = radians(lat1)
    rlon2 = radians(lon2)
    rlat2 = radians(lat2)

    delta_lon = rlon2 - rlon1
    delta_lat = rlat2 - rlat1

    return 6373.0 * 2 * asin( sqrt( sin( delta_lat / 2 )**2 + cos(lat1) * cos(lat2) * sin( delta_lon / 2 )**2 ) )

def euclidean_distance( x1:float, y1:float, x2:float, y2:float ) -> float:
    """
    Returns the Euclidean distance between the given points (provided by (x,y)-coordinates).

    :param float x1: x-coordinate of the first point
    :param float y1: y-coordinate of the first point
    :param float x2: x-coordinate of the second point
    :param float y2: y-coordinate of the second point

    :return: Euclidean distance
    :rtype: float
    """
    return sqrt( (x2-x1)**2 + (y2-y1)**2 )

def manhattan_distance( x1:float, y1:float, x2:float, y2:float ) -> float:
    """
    Returns the Manhattan distance between the given points (provided by (x,y)-coordinates).

    :param float x1: x-coordinate of the first point
    :param float y1: y-coordinate of the first point
    :param float x2: x-coordinate of the second point
    :param float y2: y-coordinate of the second point

    :return: Manhattan distance
    :rtype: float
    """
    return abs( x2-x1 ) + abs( y2-y1 )
