import unittest
import sys
import os

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from geoLocation import GeoLocation
from node import Node, NodeNetwork

class TestNode(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.loc1 = GeoLocation(0, 0)
        self.loc2 = GeoLocation(0, 5)
        self.loc3 = GeoLocation(5, 0)
        self.loc4 = GeoLocation(5, 5)
        
        self.node1 = Node(self.loc1, "Origin")
        self.node2 = Node(self.loc2, "East")
        self.node3 = Node(self.loc3, "North")
        self.node4 = Node(self.loc4, "Northeast")
    
    def test_node_creation(self):
        """Test basic node creation."""
        node = Node(self.loc1, "Test Node")
        self.assertEqual(node.name, "Test Node")
        self.assertEqual(node.location, self.loc1)
        self.assertIsNotNone(node.id)
        self.assertEqual(len(node.connections), 0)
        self.assertEqual(len(node.properties), 0)
    
    def test_node_auto_naming(self):
        """Test automatic node naming."""
        node = Node(self.loc1)
        self.assertTrue(node.name.startswith("Node_"))
        self.assertIn("0.00", node.name)
    
    def test_node_custom_id(self):
        """Test custom node ID."""
        custom_id = "custom_node_123"
        node = Node(self.loc1, "Test", custom_id)
        self.assertEqual(node.id, custom_id)
    
    def test_connect_nodes(self):
        """Test connecting nodes."""
        # Test bidirectional connection (default)
        result = self.node1.connect_to(self.node2)
        self.assertTrue(result)
        self.assertTrue(self.node1.is_connected_to(self.node2))
        self.assertTrue(self.node2.is_connected_to(self.node1))
        self.assertEqual(len(self.node1.connections), 1)
        self.assertEqual(len(self.node2.connections), 1)
        
        # Test duplicate connection
        result = self.node1.connect_to(self.node2)
        self.assertFalse(result)  # Should return False for duplicate
    
    def test_unidirectional_connection(self):
        """Test unidirectional connections."""
        result = self.node1.connect_to(self.node2, bidirectional=False)
        self.assertTrue(result)
        self.assertTrue(self.node1.is_connected_to(self.node2))
        self.assertFalse(self.node2.is_connected_to(self.node1))
    
    def test_disconnect_nodes(self):
        """Test disconnecting nodes."""
        # First connect them
        self.node1.connect_to(self.node2)
        self.assertTrue(self.node1.is_connected_to(self.node2))
        
        # Then disconnect
        result = self.node1.disconnect_from(self.node2)
        self.assertTrue(result)
        self.assertFalse(self.node1.is_connected_to(self.node2))
        self.assertFalse(self.node2.is_connected_to(self.node1))
        
        # Test disconnecting non-connected nodes
        result = self.node1.disconnect_from(self.node3)
        self.assertFalse(result)
    
    def test_distance_calculation(self):
        """Test distance calculation between nodes."""
        distance = self.node1.get_distance_to(self.node2)
        self.assertAlmostEqual(distance, 5.0, places=6)
        
        distance = self.node1.get_distance_to(self.node3)
        self.assertAlmostEqual(distance, 5.0, places=6)
    
    def test_travel_time_calculation(self):
        """Test travel time calculation."""
        # Default speed (1.0)
        travel_time = self.node1.get_travel_time_to(self.node2)
        self.assertAlmostEqual(travel_time, 5.0, places=6)
        
        # Custom speed
        travel_time = self.node1.get_travel_time_to(self.node2, speed=2.0)
        self.assertAlmostEqual(travel_time, 2.5, places=6)
    
    def test_get_connected_nodes(self):
        """Test getting connected nodes."""
        self.node1.connect_to(self.node2)
        self.node1.connect_to(self.node3)
        
        connected = self.node1.get_connected_nodes()
        self.assertEqual(len(connected), 2)
        self.assertIn(self.node2, connected)
        self.assertIn(self.node3, connected)
    
    def test_simple_pathfinding(self):
        """Test basic pathfinding."""
        # Create a simple path: node1 -> node2 -> node4
        self.node1.connect_to(self.node2)
        self.node2.connect_to(self.node4)
        
        # Find path from node1 to node4
        result = self.node1.find_path_to(self.node4)
        self.assertIsNotNone(result)
        
        path, total_time = result
        self.assertEqual(len(path), 3)
        self.assertEqual(path[0], self.node1)
        self.assertEqual(path[1], self.node2)
        self.assertEqual(path[2], self.node4)
        
        # Check total time is reasonable
        expected_time = (self.node1.get_travel_time_to(self.node2) + 
                        self.node2.get_travel_time_to(self.node4))
        self.assertAlmostEqual(total_time, expected_time, places=6)
    
    def test_pathfinding_no_path(self):
        """Test pathfinding when no path exists."""
        # Don't connect the nodes
        result = self.node1.find_path_to(self.node4)
        self.assertIsNone(result)
    
    def test_pathfinding_same_node(self):
        """Test pathfinding to the same node."""
        result = self.node1.find_path_to(self.node1)
        self.assertIsNotNone(result)
        
        path, total_time = result
        self.assertEqual(len(path), 1)
        self.assertEqual(path[0], self.node1)
        self.assertEqual(total_time, 0.0)
    
    def test_complex_pathfinding(self):
        """Test pathfinding in a more complex network."""
        # Create a diamond-shaped network
        self.node1.connect_to(self.node2)  # Origin -> East
        self.node1.connect_to(self.node3)  # Origin -> North
        self.node2.connect_to(self.node4)  # East -> Northeast
        self.node3.connect_to(self.node4)  # North -> Northeast
        
        # Find shortest path from node1 to node4
        result = self.node1.find_path_to(self.node4)
        self.assertIsNotNone(result)
        
        path, total_time = result
        self.assertEqual(len(path), 3)
        self.assertEqual(path[0], self.node1)
        self.assertEqual(path[-1], self.node4)
        
        # Should choose the shorter path (both paths have same distance in this case)
        self.assertIn(path[1], [self.node2, self.node3])
    
    def test_reachable_nodes(self):
        """Test getting reachable nodes within travel time."""
        # Create connections
        self.node1.connect_to(self.node2)  # Distance 5
        self.node2.connect_to(self.node4)  # Distance ~7.07
        
        # Get nodes reachable within time 6 (speed 1.0)
        reachable = self.node1.get_reachable_nodes(max_travel_time=6.0)
        
        self.assertIn(self.node1, reachable)  # Self
        self.assertIn(self.node2, reachable)  # Direct connection
        self.assertNotIn(self.node4, reachable)  # Too far (5 + 7.07 > 6)
        
        # Get all reachable nodes (no time limit)
        reachable_all = self.node1.get_reachable_nodes()
        self.assertIn(self.node1, reachable_all)
        self.assertIn(self.node2, reachable_all)
        self.assertIn(self.node4, reachable_all)
    
    def test_node_properties(self):
        """Test node property system."""
        self.node1.set_property("type", "city")
        self.node1.set_property("population", 1000)
        
        self.assertEqual(self.node1.get_property("type"), "city")
        self.assertEqual(self.node1.get_property("population"), 1000)
        self.assertIsNone(self.node1.get_property("nonexistent"))
        self.assertEqual(self.node1.get_property("nonexistent", "default"), "default")
    
    def test_node_equality(self):
        """Test node equality and hashing."""
        node_copy = Node(self.loc1, "Origin", self.node1.id)
        self.assertEqual(self.node1, node_copy)
        self.assertEqual(hash(self.node1), hash(node_copy))
        
        self.assertNotEqual(self.node1, self.node2)
        self.assertNotEqual(hash(self.node1), hash(self.node2))
    
    def test_node_string_representation(self):
        """Test string representation of nodes."""
        node_str = str(self.node1)
        self.assertIn("Node", node_str)
        self.assertIn("Origin", node_str)
        self.assertIn("connections=0", node_str)


class TestNodeNetwork(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.network = NodeNetwork()
        self.loc1 = GeoLocation(0, 0)
        self.loc2 = GeoLocation(0, 5)
        self.loc3 = GeoLocation(5, 0)
        
        self.node1 = Node(self.loc1, "Node1")
        self.node2 = Node(self.loc2, "Node2")
        self.node3 = Node(self.loc3, "Node3")
    
    def test_add_node(self):
        """Test adding nodes to network."""
        result = self.network.add_node(self.node1)
        self.assertTrue(result)
        self.assertIn(self.node1.id, self.network.nodes)
        
        # Test adding duplicate
        result = self.network.add_node(self.node1)
        self.assertFalse(result)
    
    def test_remove_node(self):
        """Test removing nodes from network."""
        # Add and connect nodes
        self.network.add_node(self.node1)
        self.network.add_node(self.node2)
        self.node1.connect_to(self.node2)
        
        # Remove node1
        result = self.network.remove_node(self.node1)
        self.assertTrue(result)
        self.assertNotIn(self.node1.id, self.network.nodes)
        
        # Check that connections were removed
        self.assertFalse(self.node2.is_connected_to(self.node1))
        
        # Test removing non-existent node
        result = self.network.remove_node(self.node3)
        self.assertFalse(result)
    
    def test_get_node_by_id(self):
        """Test getting node by ID."""
        self.network.add_node(self.node1)
        
        found_node = self.network.get_node_by_id(self.node1.id)
        self.assertEqual(found_node, self.node1)
        
        not_found = self.network.get_node_by_id("nonexistent")
        self.assertIsNone(not_found)
    
    def test_get_nodes_by_name(self):
        """Test getting nodes by name."""
        # Add nodes with same name
        node_a = Node(self.loc1, "SameName")
        node_b = Node(self.loc2, "SameName")
        node_c = Node(self.loc3, "DifferentName")
        
        self.network.add_node(node_a)
        self.network.add_node(node_b)
        self.network.add_node(node_c)
        
        same_name_nodes = self.network.get_nodes_by_name("SameName")
        self.assertEqual(len(same_name_nodes), 2)
        self.assertIn(node_a, same_name_nodes)
        self.assertIn(node_b, same_name_nodes)
        
        different_name_nodes = self.network.get_nodes_by_name("DifferentName")
        self.assertEqual(len(different_name_nodes), 1)
        self.assertIn(node_c, different_name_nodes)
    
    def test_get_nodes_near_location(self):
        """Test getting nodes near a location."""
        self.network.add_node(self.node1)  # At (0, 0)
        self.network.add_node(self.node2)  # At (0, 5)
        self.network.add_node(self.node3)  # At (5, 0)
        
        # Find nodes within distance 3 of origin
        search_location = GeoLocation(0, 0)
        nearby = self.network.get_nodes_near_location(search_location, max_distance=3.0)
        
        # Only node1 should be within distance 3
        self.assertEqual(len(nearby), 1)
        self.assertEqual(nearby[0][0], self.node1)
        self.assertAlmostEqual(nearby[0][1], 0.0, places=6)
        
        # Find nodes within distance 6
        nearby = self.network.get_nodes_near_location(search_location, max_distance=6.0)
        self.assertEqual(len(nearby), 3)  # All nodes should be included
    
    def test_create_grid_network(self):
        """Test creating a grid network."""
        center = GeoLocation(0, 0)
        grid_size = 3
        spacing = 2.0
        
        created_nodes = self.network.create_grid_network(center, grid_size, spacing)
        
        # Check correct number of nodes created
        self.assertEqual(len(created_nodes), grid_size * grid_size)
        self.assertEqual(len(self.network.nodes), grid_size * grid_size)
        
        # Check that nodes are connected properly
        # Each interior node should have 4 connections, edge nodes fewer
        total_connections = sum(len(node.connections) for node in created_nodes)
        
        # In a 3x3 grid:
        # - 4 corner nodes have 2 connections each = 8
        # - 4 edge nodes have 3 connections each = 12
        # - 1 center node has 4 connections = 4
        # Total = 24 connections (counting each connection twice)
        expected_connections = 24
        self.assertEqual(total_connections, expected_connections)
    
    def test_get_all_nodes(self):
        """Test getting all nodes."""
        self.network.add_node(self.node1)
        self.network.add_node(self.node2)
        
        all_nodes = self.network.get_all_nodes()
        self.assertEqual(len(all_nodes), 2)
        self.assertIn(self.node1, all_nodes)
        self.assertIn(self.node2, all_nodes)
    
    def test_network_stats(self):
        """Test network statistics."""
        # Empty network
        stats = self.network.get_network_stats()
        self.assertEqual(stats['total_nodes'], 0)
        self.assertEqual(stats['total_connections'], 0)
        self.assertEqual(stats['average_connections_per_node'], 0)
        self.assertEqual(stats['isolated_nodes'], 0)
        
        # Add nodes and connections
        self.network.add_node(self.node1)
        self.network.add_node(self.node2)
        self.network.add_node(self.node3)
        self.node1.connect_to(self.node2)
        
        stats = self.network.get_network_stats()
        self.assertEqual(stats['total_nodes'], 3)
        self.assertEqual(stats['total_connections'], 1)  # One bidirectional connection
        self.assertAlmostEqual(stats['average_connections_per_node'], 2/3, places=6)  # (2+0)/3
        self.assertEqual(stats['isolated_nodes'], 1)  # node3 is isolated
    
    def test_network_string_representation(self):
        """Test string representation of network."""
        self.network.add_node(self.node1)
        self.network.add_node(self.node2)
        self.node1.connect_to(self.node2)
        
        network_str = str(self.network)
        self.assertIn("NodeNetwork", network_str)
        self.assertIn("nodes=2", network_str)
        self.assertIn("connections=1", network_str)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2) 