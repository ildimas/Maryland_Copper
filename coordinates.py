import math

def pifagor_triangle_distance(height):
    return round(((500 ** 2) - (height ** 2)) ** 0.5)
    
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000 
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    
    return distance

def get_coordinates(lat, lon, distance, bearing=45):
    R = 6371000
    
    lat = math.radians(lat)
    lon = math.radians(lon)
    bearing = math.radians(bearing)
    
    new_lat = math.asin(math.sin(lat) * math.cos(distance / R) + 
                        math.cos(lat) * math.sin(distance / R) * math.cos(bearing))
    
    new_lon = lon + math.atan2(math.sin(bearing) * math.sin(distance / R) * math.cos(lat),
                               math.cos(distance / R) - math.sin(lat) * math.sin(new_lat))
    
    new_lat = math.degrees(new_lat)
    new_lon = math.degrees(new_lon)
    
    return new_lat, new_lon

if __name__ == "__main__":
    # print(haversine(lat1=47.64138, lat2=47.64636, lon1=122.1400654, lon2=122.13243))
    # print(get_coordinates(lat=47.64636, lon=122.13243, distance=500, bearing=45))
    print(pifagor_triangle_distance(99))