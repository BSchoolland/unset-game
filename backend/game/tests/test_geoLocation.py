import unittest
import math
import sys
import os

# Add the parent directory to the path so we can import geoLocation
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from geoLocation import GeoLocation

class TestGeoLocation(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures with some tolerance for floating point comparisons."""
        self.tolerance = 1e-6
    
    def assertAlmostEqualLocation(self, loc1, loc2, tolerance=None):
        """Helper method to compare two GeoLocation objects with tolerance."""
        if tolerance is None:
            tolerance = self.tolerance
        self.assertAlmostEqual(loc1.latitude, loc2.latitude, delta=tolerance)
        self.assertAlmostEqual(loc1.longitude, loc2.longitude, delta=tolerance)
    
    def test_distance_calculation_basic(self):
        """Test basic distance calculations."""
        # Test distance from equator to equator at different longitudes
        loc1 = GeoLocation(0, 0)
        loc2 = GeoLocation(0, 1)
        distance = loc1.get_distance_to_point(loc2)
        self.assertAlmostEqual(distance, 1.0, delta=self.tolerance)
        
        # Test distance along latitude
        loc1 = GeoLocation(0, 0)
        loc2 = GeoLocation(1, 0)
        distance = loc1.get_distance_to_point(loc2)
        self.assertAlmostEqual(distance, 1.0, delta=self.tolerance)
    
    def test_distance_across_dateline(self):
        """Test the specific case: distance between -179,0 and 180,0 should be 1."""
        loc1 = GeoLocation(0, -179)
        loc2 = GeoLocation(0, 180)
        distance = loc1.get_distance_to_point(loc2)
        # The shortest distance across the dateline should be 1 degree
        self.assertAlmostEqual(distance, 1.0, delta=self.tolerance)
    
    def test_distance_symmetry(self):
        """Test that distance calculation is symmetric."""
        loc1 = GeoLocation(10, 20)
        loc2 = GeoLocation(30, 40)
        distance1 = loc1.get_distance_to_point(loc2)
        distance2 = loc2.get_distance_to_point(loc1)
        self.assertAlmostEqual(distance1, distance2, delta=self.tolerance)
    
    def test_distance_same_point(self):
        """Test distance to the same point is zero."""
        loc1 = GeoLocation(15, 25)
        loc2 = GeoLocation(15, 25)
        distance = loc1.get_distance_to_point(loc2)
        self.assertAlmostEqual(distance, 0.0, delta=self.tolerance)
    
    def test_direction_calculation_basic(self):
        """Test basic direction calculations."""
        # North direction
        loc1 = GeoLocation(0, 0)
        loc2 = GeoLocation(1, 0)
        direction = loc1.get_direction_of_point(loc2)
        self.assertAlmostEqual(direction, 0.0, delta=self.tolerance)  # North
        
        # East direction
        loc1 = GeoLocation(0, 0)
        loc2 = GeoLocation(0, 1)
        direction = loc1.get_direction_of_point(loc2)
        self.assertAlmostEqual(direction, 90.0, delta=self.tolerance)  # East
        
        # South direction
        loc1 = GeoLocation(0, 0)
        loc2 = GeoLocation(-1, 0)
        direction = loc1.get_direction_of_point(loc2)
        self.assertAlmostEqual(direction, 180.0, delta=self.tolerance)  # South
        
        # West direction
        loc1 = GeoLocation(0, 0)
        loc2 = GeoLocation(0, -1)
        direction = loc1.get_direction_of_point(loc2)
        self.assertAlmostEqual(direction, 270.0, delta=self.tolerance)  # West
    
    def test_translate_basic_directions(self):
        """Test translation in basic cardinal directions."""
        # Move North
        loc = GeoLocation(0, 0)
        loc.translate(0, 5)  # North, 5 units
        expected = GeoLocation(5, 0)
        self.assertAlmostEqualLocation(loc, expected)
        
        # Move East
        loc = GeoLocation(0, 0)
        loc.translate(90, 5)  # East, 5 units
        expected = GeoLocation(0, 5)
        self.assertAlmostEqualLocation(loc, expected)
        
        # Move South
        loc = GeoLocation(0, 0)
        loc.translate(180, 5)  # South, 5 units
        expected = GeoLocation(-5, 0)
        self.assertAlmostEqualLocation(loc, expected)
        
        # Move West
        loc = GeoLocation(0, 0)
        loc.translate(270, 5)  # West, 5 units
        expected = GeoLocation(0, -5)
        self.assertAlmostEqualLocation(loc, expected)
    
    def test_translate_across_dateline(self):
        """Test the specific case: moving 5 units east from 180,30 should result in approximately -174.23,29.87."""
        loc = GeoLocation(30, 180)
        loc.translate(90, 5)  # Move East 5 units
        
        # With proper spherical geometry, the result will be slightly different
        # due to the curvature of the sphere at latitude 30
        expected_longitude = -174.23  # Approximately
        expected_latitude = 29.87     # Approximately (slight change due to spherical geometry)
        
        self.assertAlmostEqual(loc.longitude, expected_longitude, delta=0.5)
        self.assertAlmostEqual(loc.latitude, expected_latitude, delta=0.5)
    
    def test_translate_boundary_clamping(self):
        """Test that latitude is clamped to game boundaries (-45 to 45)."""
        # Try to move beyond north boundary
        loc = GeoLocation(40, 0)
        loc.translate(0, 10)  # Move North 10 units (would go to 50)
        self.assertLessEqual(loc.latitude, 45)
        
        # Try to move beyond south boundary
        loc = GeoLocation(-40, 0)
        loc.translate(180, 10)  # Move South 10 units (would go to -50)
        self.assertGreaterEqual(loc.latitude, -45)
    
    def test_round_trip_translation(self):
        """Test that translating in opposite directions returns close to original position."""
        original = GeoLocation(10, 20)
        loc = GeoLocation(10, 20)
        
        # Move east, then west
        loc.translate(90, 5)
        loc.translate(270, 5)
        
        # Due to spherical geometry, perfect round-trips aren't always possible
        # but should be reasonably close
        self.assertAlmostEqualLocation(loc, original, tolerance=0.1)
    
    def test_distance_and_direction_consistency(self):
        """Test that distance and direction calculations are consistent."""
        loc1 = GeoLocation(10, 20)
        loc2 = GeoLocation(15, 25)
        
        # Get distance and direction from loc1 to loc2
        distance = loc1.get_distance_to_point(loc2)
        direction = loc1.get_direction_of_point(loc2)
        
        # Create a new location and translate by the calculated distance and direction
        test_loc = GeoLocation(10, 20)
        test_loc.translate(direction, distance)
        
        # Should be very close to loc2 (allowing for spherical geometry precision)
        self.assertAlmostEqualLocation(test_loc, loc2, tolerance=0.1)
    
    def test_longitude_normalization(self):
        """Test that longitude values are properly normalized to -180 to 180 range."""
        # Test positive overflow
        loc = GeoLocation(0, 170)
        loc.translate(90, 20)  # Move east 20 degrees
        self.assertGreaterEqual(loc.longitude, -180)
        self.assertLessEqual(loc.longitude, 180)
        
        # Test negative overflow
        loc = GeoLocation(0, -170)
        loc.translate(270, 20)  # Move west 20 degrees
        self.assertGreaterEqual(loc.longitude, -180)
        self.assertLessEqual(loc.longitude, 180)
    
    def test_edge_cases(self):
        """Test various edge cases."""
        # Test at game boundaries
        loc1 = GeoLocation(45, 180)
        loc2 = GeoLocation(-45, -180)
        
        # Should not crash
        distance = loc1.get_distance_to_point(loc2)
        direction = loc1.get_direction_of_point(loc2)
        
        self.assertIsInstance(distance, float)
        self.assertIsInstance(direction, float)
        self.assertGreaterEqual(direction, 0)
        self.assertLess(direction, 360)
    
    def test_string_representation(self):
        """Test string representation methods."""
        loc = GeoLocation(12.345678, -67.890123)
        str_repr = str(loc)
        self.assertIn("12.345678", str_repr)
        self.assertIn("-67.890123", str_repr)
        
        # Test that repr and str are the same
        self.assertEqual(str(loc), repr(loc))

if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2) 