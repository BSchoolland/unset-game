# keeps track of the planetary location of objects for the game.

# x is the longitude in degrees
# y is the latitude in distance units from the equator (constrained to -45 to 45) to prevent access to the poles

import math

class GeoLocation:
    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude

    def get_distance_to_point(self, other_location):
        # calculate the distance between two points on a sphere
        # For a cylindrical projection, we need to handle longitude wrapping
        
        # Calculate latitude difference (straightforward)
        lat_diff = other_location.latitude - self.latitude
        
        # Calculate longitude difference with wrapping
        lon_diff = other_location.longitude - self.longitude
        
        # Handle longitude wrapping (shortest path around the cylinder)
        if lon_diff > 180:
            lon_diff -= 360
        elif lon_diff < -180:
            lon_diff += 360
            
        # For small distances, we can use Euclidean distance
        # For larger distances, we should account for the spherical nature
        # Using a compromise that works well for game distances
        
        # Convert to radians for spherical calculation
        lat1_rad = math.radians(self.latitude)
        lat2_rad = math.radians(other_location.latitude)
        lon_diff_rad = math.radians(lon_diff)
        
        # Use haversine formula but with our coordinate system
        a = (math.sin((lat2_rad - lat1_rad) / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(lon_diff_rad / 2) ** 2)
        
        c = 2 * math.asin(math.sqrt(a))
        
        # Convert back to degrees
        return math.degrees(c)
        
    def get_direction_of_point(self, other_location):
        # calculate the direction of a point from the current location
        # Returns bearing in degrees (0 = North, 90 = East, 180 = South, 270 = West)
        
        # Calculate differences with longitude wrapping
        lat_diff = other_location.latitude - self.latitude
        lon_diff = other_location.longitude - self.longitude
        
        # Handle longitude wrapping
        if lon_diff > 180:
            lon_diff -= 360
        elif lon_diff < -180:
            lon_diff += 360
        
        # Convert to radians
        lat1_rad = math.radians(self.latitude)
        lat2_rad = math.radians(other_location.latitude)
        lon_diff_rad = math.radians(lon_diff)
        
        # Calculate bearing
        y = math.sin(lon_diff_rad) * math.cos(lat2_rad)
        x = (math.cos(lat1_rad) * math.sin(lat2_rad) - 
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(lon_diff_rad))
        
        bearing = math.atan2(y, x)
        bearing_degrees = math.degrees(bearing)
        
        # Normalize to 0-360 degrees
        return (bearing_degrees + 360) % 360

    def translate(self, direction, distance):
        # move the location in the direction by the distance
        # direction in degrees (0 = North, 90 = East, etc.)
        # distance in the same units as our coordinate system
        
        # Convert inputs to radians
        lat1 = math.radians(self.latitude)
        lon1 = math.radians(self.longitude)
        bearing = math.radians(direction)
        angular_distance = math.radians(distance)
        
        # Calculate new latitude using spherical geometry
        lat2 = math.asin(math.sin(lat1) * math.cos(angular_distance) +
                        math.cos(lat1) * math.sin(angular_distance) * math.cos(bearing))
        
        # Calculate new longitude using spherical geometry
        lon2 = lon1 + math.atan2(math.sin(bearing) * math.sin(angular_distance) * math.cos(lat1),
                                math.cos(angular_distance) - math.sin(lat1) * math.sin(lat2))
        
        # Convert back to degrees
        new_latitude = math.degrees(lat2)
        new_longitude = math.degrees(lon2)
        
        # Normalize longitude to -180 to 180 range
        new_longitude = ((new_longitude + 180) % 360) - 180
        
        # Clamp latitude to our game bounds (-45 to 45)
        new_latitude = max(-45, min(45, new_latitude))
        
        # Update current location
        self.latitude = new_latitude
        self.longitude = new_longitude
    
    def __str__(self):
        return f"GeoLocation(lat={self.latitude:.6f}, lon={self.longitude:.6f})"
    
    def __repr__(self):
        return self.__str__()
    

