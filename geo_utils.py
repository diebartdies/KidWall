from models import User, School, Child

def is_payment_location_valid(child: Child, merchant: User, pay_lat: float, pay_lon: float, db, radius_km=1.5):
    """
    Returns True if the payment location is within radius_km of either the merchant's address or the child's school.
    """
    # Check merchant location
    if merchant.latitude and merchant.longitude:
        if is_within_radius(pay_lat, pay_lon, merchant.latitude, merchant.longitude, radius_km):
            return True
    # Check school location
    if child.school_lat and child.school_lon:
        if is_within_radius(pay_lat, pay_lon, child.school_lat, child.school_lon, radius_km):
            return True
    # Optionally, check for a linked School object if more detail is needed
    return False
import math

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on the Earth (specified in decimal degrees)
    Returns distance in kilometers.
    """
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def is_within_radius(lat1, lon1, lat2, lon2, radius_km=1.5):
    if None in [lat1, lon1, lat2, lon2]:
        return False
    return haversine(lat1, lon1, lat2, lon2) <= radius_km
