import requests
import time

def geocode_address(address, city=None, provincia=None):
    base_url = "https://nominatim.openstreetmap.org/search"
    query = address
    if city:
        query += f", {city}"
    if provincia:
        query += f", {provincia}, Argentina"
    params = {
        'q': query,
        'format': 'json',
        'limit': 1,
        'addressdetails': 0
    }
    headers = {'User-Agent': 'ColePagoSchoolGeocoder/1.0'}
    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            return lat, lon
        else:
            return None, None
    except Exception as e:
        print(f"Geocoding failed for {query}: {e}")
        return None, None

def geocode_with_retry(address, city=None, provincia=None, retries=3, delay=1):
    for attempt in range(retries):
        lat, lon = geocode_address(address, city, provincia)
        if lat is not None and lon is not None:
            return lat, lon
        time.sleep(delay)
    return None, None
