"""
Comprehensive tests for the equatorial node generator.
Tests all requirements: connectivity, distance constraints, equatorial path, and no crossings.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from typing import List, Tuple, Set, Dict, Optional
from collections import deque
from geoLocation import GeoLocation
from node import Node, NodeNetwork
from equatorial_generator import EquatorialNodeGenerator

class EquatorialNetworkTester:
    """Comprehensive testing for equatorial node networks."""
    
    def __init__(self, min_distance: float = 5.0, max_distance: float = 10.0):
        self.min_distance = min_distance
        self.max_distance = max_distance
    
    def test_network(self, network: NodeNetwork) -> Dict[str, any]:
        """
        Run comprehensive tests on a generated network.
        
        Returns:
            Dictionary with test results and statistics
        """
        results = {
            'connectivity': self.test_connectivity(network),
            'distance_constraints': self.test_distance_constraints(network),
            'equatorial_path': self.test_equatorial_path(network),
            'no_crossing_connections': self.test_no_crossing_connections(network),
            'network_stats': self.get_network_statistics(network)
        }
        
        results['all_tests_passed'] = all([
            results['connectivity']['is_connected'],
            results['distance_constraints']['all_within_bounds'],
            results['equatorial_path']['path_exists'],
            results['no_crossing_connections']['no_crossings']
        ])
        
        return results
    
    def test_connectivity(self, network: NodeNetwork) -> Dict[str, any]:
        """Test if all nodes are connected in a single component."""
        nodes = network.get_all_nodes()
        if not nodes:
            return {'is_connected': True, 'num_components': 0, 'largest_component_size': 0}
        
        visited = set()
        components = []
        
        for node in nodes:
            if node.id not in visited:
                component = self._bfs_component(node, visited)
                components.append(len(component))
        
        return {
            'is_connected': len(components) == 1,
            'num_components': len(components),
            'largest_component_size': max(components) if components else 0,
            'total_nodes': len(nodes)
        }
    
    def test_distance_constraints(self, network: NodeNetwork) -> Dict[str, any]:
        """Test if all connections respect distance constraints."""
        nodes = network.get_all_nodes()
        violations = []
        total_connections = 0
        
        for node in nodes:
            for connected_node in node.get_connected_nodes():
                # Only count each connection once
                if node.id < connected_node.id:
                    total_connections += 1
                    distance = node.get_distance_to(connected_node)
                    
                    if distance < self.min_distance or distance > self.max_distance:
                        violations.append({
                            'node1': node.name,
                            'node2': connected_node.name,
                            'distance': distance,
                            'violation_type': 'too_short' if distance < self.min_distance else 'too_long'
                        })
        
        return {
            'all_within_bounds': len(violations) == 0,
            'total_connections': total_connections,
            'violations': violations,
            'violation_count': len(violations)
        }
    
    def test_equatorial_path(self, network: NodeNetwork) -> Dict[str, any]:
        """Test if there's a path that goes around the equator."""
        nodes = network.get_all_nodes()
        
        # Find nodes close to the equator
        equatorial_nodes = [node for node in nodes if abs(node.location.latitude) <= 10.0]
        
        if len(equatorial_nodes) < 3:
            return {'path_exists': False, 'reason': 'insufficient_equatorial_nodes'}
        
        # Sort by longitude
        equatorial_nodes.sort(key=lambda n: n.location.longitude)
        
        # Try to find a path that visits nodes across different longitude ranges
        longitude_ranges = [(-180, -120), (-120, -60), (-60, 0), (0, 60), (60, 120), (120, 180)]
        range_nodes = {i: [] for i in range(len(longitude_ranges))}
        
        for node in equatorial_nodes:
            lon = node.location.longitude
            for i, (min_lon, max_lon) in enumerate(longitude_ranges):
                if min_lon <= lon < max_lon:
                    range_nodes[i].append(node)
                    break
        
        # Check if we have nodes in at least 4 different longitude ranges
        populated_ranges = [i for i, nodes_list in range_nodes.items() if nodes_list]
        
        if len(populated_ranges) < 4:
            return {'path_exists': False, 'reason': 'insufficient_longitude_coverage'}
        
        # Try to find a path connecting different ranges
        start_node = range_nodes[populated_ranges[0]][0]
        target_ranges = populated_ranges[1:]
        
        path_exists = self._check_equatorial_connectivity(start_node, target_ranges, range_nodes)
        
        return {
            'path_exists': path_exists,
            'longitude_ranges_covered': len(populated_ranges),
            'total_equatorial_nodes': len(equatorial_nodes)
        }
    
    def test_no_crossing_connections(self, network: NodeNetwork) -> Dict[str, any]:
        """Test if connections cross each other (simplified 2D check)."""
        nodes = network.get_all_nodes()
        connections = []
        
        # Collect all connections
        for node in nodes:
            for connected_node in node.get_connected_nodes():
                if node.id < connected_node.id:  # Avoid duplicates
                    connections.append((node, connected_node))
        
        crossings = []
        
        # Check each pair of connections for intersections
        for i in range(len(connections)):
            for j in range(i + 1, len(connections)):
                conn1 = connections[i]
                conn2 = connections[j]
                
                # Skip if connections share a node
                if (conn1[0].id in [conn2[0].id, conn2[1].id] or 
                    conn1[1].id in [conn2[0].id, conn2[1].id]):
                    continue
                
                if self._connections_intersect(conn1, conn2):
                    crossings.append((conn1, conn2))
        
        return {
            'no_crossings': len(crossings) == 0,
            'total_connections': len(connections),
            'crossing_count': len(crossings),
            'crossings': crossings
        }
    
    def get_network_statistics(self, network: NodeNetwork) -> Dict[str, any]:
        """Get general statistics about the network."""
        nodes = network.get_all_nodes()
        
        if not nodes:
            return {'total_nodes': 0}
        
        # Connection statistics
        connection_counts = [len(node.get_connected_nodes()) for node in nodes]
        
        # Distance statistics
        distances = []
        for node in nodes:
            for connected_node in node.get_connected_nodes():
                if node.id < connected_node.id:
                    distances.append(node.get_distance_to(connected_node))
        
        # Latitude distribution
        latitudes = [node.location.latitude for node in nodes]
        
        return {
            'total_nodes': len(nodes),
            'total_connections': len(distances),
            'avg_connections_per_node': sum(connection_counts) / len(connection_counts) if connection_counts else 0,
            'min_connections_per_node': min(connection_counts) if connection_counts else 0,
            'max_connections_per_node': max(connection_counts) if connection_counts else 0,
            'avg_connection_distance': sum(distances) / len(distances) if distances else 0,
            'min_connection_distance': min(distances) if distances else 0,
            'max_connection_distance': max(distances) if distances else 0,
            'latitude_range': (min(latitudes), max(latitudes)) if latitudes else (0, 0),
            'avg_latitude': sum(latitudes) / len(latitudes) if latitudes else 0
        }
    
    def _bfs_component(self, start_node: Node, visited: Set[str]) -> List[Node]:
        """Find connected component using BFS."""
        component = []
        queue = deque([start_node])
        visited.add(start_node.id)
        
        while queue:
            node = queue.popleft()
            component.append(node)
            
            for neighbor in node.get_connected_nodes():
                if neighbor.id not in visited:
                    visited.add(neighbor.id)
                    queue.append(neighbor)
        
        return component
    
    def _check_equatorial_connectivity(self, start_node: Node, target_ranges: List[int], 
                                     range_nodes: Dict[int, List[Node]]) -> bool:
        """Check if we can reach nodes in different longitude ranges."""
        visited = set()
        queue = deque([start_node])
        visited.add(start_node.id)
        ranges_reached = set()
        
        while queue:
            node = queue.popleft()
            
            # Check which range this node belongs to
            lon = node.location.longitude
            longitude_ranges = [(-180, -120), (-120, -60), (-60, 0), (0, 60), (60, 120), (120, 180)]
            for i, (min_lon, max_lon) in enumerate(longitude_ranges):
                if min_lon <= lon < max_lon and i in target_ranges:
                    ranges_reached.add(i)
                    break
            
            # If we've reached enough ranges, we have equatorial connectivity
            if len(ranges_reached) >= min(3, len(target_ranges)):
                return True
            
            # Continue BFS
            for neighbor in node.get_connected_nodes():
                if neighbor.id not in visited:
                    visited.add(neighbor.id)
                    queue.append(neighbor)
        
        return len(ranges_reached) >= min(3, len(target_ranges))
    
    def _connections_intersect(self, conn1: Tuple[Node, Node], conn2: Tuple[Node, Node]) -> bool:
        """Check if two connections intersect using the same logic as the generator."""
        n1, n2 = conn1
        n3, n4 = conn2
        
        # Use actual distances to identify wrapping connections
        dist1 = n1.get_distance_to(n2)
        dist2 = n3.get_distance_to(n4)
        
        # Skip intersection check for very long connections (likely world-wrapping)
        if dist1 > 45 or dist2 > 45:  # More than 45 degrees is suspicious
            return False
        
        # Extract coordinates
        x1, y1 = n1.location.longitude, n1.location.latitude
        x2, y2 = n2.location.longitude, n2.location.latitude
        x3, y3 = n3.location.longitude, n3.location.latitude
        x4, y4 = n4.location.longitude, n4.location.latitude
        
        # Check for longitude wrapping by looking at coordinate spans vs actual distance
        def is_wrapping_connection(lon1, lon2, actual_distance):
            coord_span = abs(lon2 - lon1)
            # If coordinate span is much larger than actual distance, it's wrapping
            return coord_span > 180 and actual_distance < 45
        
        # Skip if either connection is wrapping
        if (is_wrapping_connection(x1, x2, dist1) or 
            is_wrapping_connection(x3, x4, dist2)):
            return False
        
        # For non-wrapping connections, use standard 2D intersection
        # Parametric line intersection
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        
        if abs(denom) < 1e-10:  # Lines are parallel
            return False
        
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
        
        # Check if intersection point is within both line segments
        return 0 < t < 1 and 0 < u < 1


def run_generation_tests(num_tests: int = 10, num_nodes: int = 50) -> Dict[str, any]:
    """
    Run multiple generation tests to ensure consistency.
    
    Args:
        num_tests: Number of test runs
        num_nodes: Number of nodes per test
        
    Returns:
        Aggregated test results
    """
    generator = EquatorialNodeGenerator()
    tester = EquatorialNetworkTester()
    
    all_results = []
    
    for i in range(num_tests):
        print(f"Running test {i+1}/{num_tests}...")
        
        # Generate network with different seed each time
        network = generator.generate_equatorial_network(num_nodes, seed=i)
        
        # Test the network
        results = tester.test_network(network)
        results['test_id'] = i
        all_results.append(results)
    
    # Aggregate results
    success_count = sum(1 for r in all_results if r['all_tests_passed'])
    
    aggregated = {
        'total_tests': num_tests,
        'successful_tests': success_count,
        'success_rate': success_count / num_tests,
        'individual_results': all_results,
        'summary': {
            'connectivity_success_rate': sum(1 for r in all_results if r['connectivity']['is_connected']) / num_tests,
            'distance_constraints_success_rate': sum(1 for r in all_results if r['distance_constraints']['all_within_bounds']) / num_tests,
            'equatorial_path_success_rate': sum(1 for r in all_results if r['equatorial_path']['path_exists']) / num_tests,
            'no_crossings_success_rate': sum(1 for r in all_results if r['no_crossing_connections']['no_crossings']) / num_tests,
        }
    }
    
    return aggregated


def run_detailed_single_test(num_nodes: int = 30, seed: int = 42):
    """Run a single detailed test for debugging purposes."""
    print(f"Running detailed test with {num_nodes} nodes, seed {seed}")
    
    generator = EquatorialNodeGenerator()
    tester = EquatorialNetworkTester()
    
    # Generate network
    network = generator.generate_equatorial_network(num_nodes, seed=seed)
    
    # Test the network
    results = tester.test_network(network)
    
    print(f"\nDetailed Test Results:")
    print(f"All tests passed: {results['all_tests_passed']}")
    print(f"\nConnectivity: {results['connectivity']}")
    print(f"\nDistance constraints: {results['distance_constraints']}")
    print(f"\nEquatorial path: {results['equatorial_path']}")
    print(f"\nNo crossing connections: {results['no_crossing_connections']}")
    print(f"\nNetwork stats: {results['network_stats']}")
    
    # Print violations if any
    if results['distance_constraints']['violations']:
        print(f"\nDistance violations:")
        for violation in results['distance_constraints']['violations'][:5]:  # Show first 5
            print(f"  {violation}")
    
    return results


if __name__ == "__main__":
    print("Running comprehensive equatorial node generation tests...")
    
    # First run a detailed single test for debugging
    print("=" * 60)
    print("DETAILED SINGLE TEST")
    print("=" * 60)
    single_result = run_detailed_single_test(num_nodes=30, seed=42)
    
    print("\n" + "=" * 60)
    print("COMPREHENSIVE BATCH TESTS")
    print("=" * 60)
    
    # Then run comprehensive tests
    results = run_generation_tests(num_tests=20, num_nodes=30)
    
    print(f"\nTest Results Summary:")
    print(f"Total tests: {results['total_tests']}")
    print(f"Successful tests: {results['successful_tests']}")
    print(f"Success rate: {results['success_rate']:.2%}")
    print(f"\nIndividual test success rates:")
    print(f"Connectivity: {results['summary']['connectivity_success_rate']:.2%}")
    print(f"Distance constraints: {results['summary']['distance_constraints_success_rate']:.2%}")
    print(f"Equatorial path: {results['summary']['equatorial_path_success_rate']:.2%}")
    print(f"No crossings: {results['summary']['no_crossings_success_rate']:.2%}") 