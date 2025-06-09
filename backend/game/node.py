"""
Node system for creating connected movable spaces on the planet surface.
Nodes are connected locations that players can move between, with travel time
based on distance and pathfinding support.
"""

from geoLocation import GeoLocation
from typing import Dict, List, Optional, Set, Tuple
import heapq
import uuid

class Node:
    """
    Represents a location on the planet that can be connected to other nodes.
    Players can move between connected nodes with travel time based on distance.
    """
    
    def __init__(self, location: GeoLocation, name: str = None, node_id: str = None):
        """
        Initialize a new node.
        
        Args:
            location: GeoLocation representing the position on the planet
            name: Optional human-readable name for the node
            node_id: Optional unique identifier (auto-generated if not provided)
        """
        self.location = location
        self.name = name or f"Node_{location.latitude:.2f}_{location.longitude:.2f}"
        self.id = node_id or str(uuid.uuid4())
        
        # Dictionary of connected nodes: {node_id: Node}
        self.connections: Dict[str, 'Node'] = {}
        
        # Optional properties for game mechanics
        self.properties: Dict[str, any] = {}
    
    def connect_to(self, other_node: 'Node', bidirectional: bool = True) -> bool:
        """
        Create a connection to another node.
        
        Args:
            other_node: The node to connect to
            bidirectional: If True, creates connection in both directions
            
        Returns:
            True if connection was created, False if already exists
        """
        if other_node.id in self.connections:
            return False  # Connection already exists
        
        self.connections[other_node.id] = other_node
        
        if bidirectional and self.id not in other_node.connections:
            other_node.connections[self.id] = self
        
        return True
    
    def disconnect_from(self, other_node: 'Node', bidirectional: bool = True) -> bool:
        """
        Remove a connection to another node.
        
        Args:
            other_node: The node to disconnect from
            bidirectional: If True, removes connection in both directions
            
        Returns:
            True if connection was removed, False if didn't exist
        """
        if other_node.id not in self.connections:
            return False  # Connection doesn't exist
        
        del self.connections[other_node.id]
        
        if bidirectional and self.id in other_node.connections:
            del other_node.connections[self.id]
        
        return True
    
    def get_distance_to(self, other_node: 'Node') -> float:
        """
        Calculate the distance to another node using spherical geometry.
        
        Args:
            other_node: The target node
            
        Returns:
            Distance in degrees
        """
        return self.location.get_distance_to_point(other_node.location)
    
    def get_travel_time_to(self, other_node: 'Node', speed: float = 1.0) -> float:
        """
        Calculate travel time to another node based on distance and speed.
        
        Args:
            other_node: The target node
            speed: Travel speed in degrees per time unit (default: 1.0)
            
        Returns:
            Travel time in time units
        """
        distance = self.get_distance_to(other_node)
        return distance / speed
    
    def is_connected_to(self, other_node: 'Node') -> bool:
        """
        Check if this node is directly connected to another node.
        
        Args:
            other_node: The node to check connection to
            
        Returns:
            True if directly connected, False otherwise
        """
        return other_node.id in self.connections
    
    def get_connected_nodes(self) -> List['Node']:
        """
        Get a list of all directly connected nodes.
        
        Returns:
            List of connected Node objects
        """
        return list(self.connections.values())
    
    def find_path_to(self, target_node: 'Node', speed: float = 1.0) -> Optional[Tuple[List['Node'], float]]:
        """
        Find the shortest path to a target node using Dijkstra's algorithm.
        
        Args:
            target_node: The destination node
            speed: Travel speed for calculating travel times
            
        Returns:
            Tuple of (path_nodes, total_travel_time) or None if no path exists
        """
        if self == target_node:
            return ([self], 0.0)
        
        # Dijkstra's algorithm implementation
        distances = {self.id: 0.0}
        previous = {}
        unvisited = [(0.0, self.id, self)]
        visited = set()
        
        while unvisited:
            current_distance, current_id, current_node = heapq.heappop(unvisited)
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            if current_node == target_node:
                # Reconstruct path
                path = []
                node = current_node
                while node:
                    path.append(node)
                    node = previous.get(node.id)
                path.reverse()
                return (path, current_distance)
            
            # Check all connected nodes
            for neighbor in current_node.get_connected_nodes():
                if neighbor.id in visited:
                    continue
                
                travel_time = current_node.get_travel_time_to(neighbor, speed)
                new_distance = current_distance + travel_time
                
                if neighbor.id not in distances or new_distance < distances[neighbor.id]:
                    distances[neighbor.id] = new_distance
                    previous[neighbor.id] = current_node
                    heapq.heappush(unvisited, (new_distance, neighbor.id, neighbor))
        
        return None  # No path found
    
    def get_reachable_nodes(self, max_travel_time: float = None, speed: float = 1.0) -> Dict['Node', float]:
        """
        Get all nodes reachable from this node within a given travel time.
        
        Args:
            max_travel_time: Maximum travel time to consider (None for unlimited)
            speed: Travel speed for calculations
            
        Returns:
            Dictionary mapping reachable nodes to their travel times
        """
        reachable = {self: 0.0}
        distances = {self.id: 0.0}
        unvisited = [(0.0, self.id, self)]
        visited = set()
        
        while unvisited:
            current_distance, current_id, current_node = heapq.heappop(unvisited)
            
            if current_id in visited:
                continue
            
            if max_travel_time is not None and current_distance > max_travel_time:
                continue
            
            visited.add(current_id)
            
            # Check all connected nodes
            for neighbor in current_node.get_connected_nodes():
                if neighbor.id in visited:
                    continue
                
                travel_time = current_node.get_travel_time_to(neighbor, speed)
                new_distance = current_distance + travel_time
                
                if max_travel_time is None or new_distance <= max_travel_time:
                    if neighbor.id not in distances or new_distance < distances[neighbor.id]:
                        distances[neighbor.id] = new_distance
                        reachable[neighbor] = new_distance
                        heapq.heappush(unvisited, (new_distance, neighbor.id, neighbor))
        
        return reachable
    
    def set_property(self, key: str, value: any) -> None:
        """
        Set a custom property for this node.
        
        Args:
            key: Property name
            value: Property value
        """
        self.properties[key] = value
    
    def get_property(self, key: str, default: any = None) -> any:
        """
        Get a custom property value.
        
        Args:
            key: Property name
            default: Default value if property doesn't exist
            
        Returns:
            Property value or default
        """
        return self.properties.get(key, default)
    
    def __str__(self) -> str:
        """String representation of the node."""
        return f"Node(id={self.id[:8]}..., name='{self.name}', location={self.location}, connections={len(self.connections)})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return self.__str__()
    
    def __eq__(self, other) -> bool:
        """Check equality based on node ID."""
        if not isinstance(other, Node):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash based on node ID for use in sets and dictionaries."""
        return hash(self.id)


class NodeNetwork:
    """
    Manages a network of connected nodes on the planet surface.
    Provides utilities for creating, managing, and querying node networks.
    """
    
    def __init__(self):
        """Initialize an empty node network."""
        self.nodes: Dict[str, Node] = {}
    
    def add_node(self, node: Node) -> bool:
        """
        Add a node to the network.
        
        Args:
            node: The node to add
            
        Returns:
            True if added, False if node ID already exists
        """
        if node.id in self.nodes:
            return False
        
        self.nodes[node.id] = node
        return True
    
    def remove_node(self, node: Node) -> bool:
        """
        Remove a node from the network and all its connections.
        
        Args:
            node: The node to remove
            
        Returns:
            True if removed, False if node wasn't in network
        """
        if node.id not in self.nodes:
            return False
        
        # Remove all connections to this node
        for other_node in list(node.connections.values()):
            node.disconnect_from(other_node, bidirectional=True)
        
        del self.nodes[node.id]
        return True
    
    def get_node_by_id(self, node_id: str) -> Optional[Node]:
        """
        Get a node by its ID.
        
        Args:
            node_id: The node ID to search for
            
        Returns:
            Node object or None if not found
        """
        return self.nodes.get(node_id)
    
    def get_nodes_by_name(self, name: str) -> List[Node]:
        """
        Get all nodes with a specific name.
        
        Args:
            name: The name to search for
            
        Returns:
            List of matching nodes
        """
        return [node for node in self.nodes.values() if node.name == name]
    
    def get_nodes_near_location(self, location: GeoLocation, max_distance: float) -> List[Tuple[Node, float]]:
        """
        Get all nodes within a certain distance of a location.
        
        Args:
            location: The reference location
            max_distance: Maximum distance in degrees
            
        Returns:
            List of (node, distance) tuples sorted by distance
        """
        nearby_nodes = []
        
        for node in self.nodes.values():
            distance = location.get_distance_to_point(node.location)
            if distance <= max_distance:
                nearby_nodes.append((node, distance))
        
        # Sort by distance
        nearby_nodes.sort(key=lambda x: x[1])
        return nearby_nodes
    
    def create_grid_network(self, center: GeoLocation, grid_size: int, spacing: float) -> List[Node]:
        """
        Create a grid of connected nodes centered on a location.
        
        Args:
            center: Center location for the grid
            grid_size: Size of the grid (grid_size x grid_size)
            spacing: Distance between adjacent nodes in degrees
            
        Returns:
            List of created nodes
        """
        created_nodes = []
        node_grid = {}
        
        # Create nodes in a grid pattern
        for i in range(grid_size):
            for j in range(grid_size):
                # Calculate offset from center
                lat_offset = (i - grid_size // 2) * spacing
                lon_offset = (j - grid_size // 2) * spacing
                
                # Create location for this grid position
                node_location = GeoLocation(
                    center.latitude + lat_offset,
                    center.longitude + lon_offset
                )
                
                # Create and add node
                node = Node(
                    location=node_location,
                    name=f"Grid_{i}_{j}"
                )
                
                self.add_node(node)
                created_nodes.append(node)
                node_grid[(i, j)] = node
        
        # Connect adjacent nodes
        for i in range(grid_size):
            for j in range(grid_size):
                current_node = node_grid[(i, j)]
                
                # Connect to right neighbor
                if j + 1 < grid_size:
                    right_node = node_grid[(i, j + 1)]
                    current_node.connect_to(right_node)
                
                # Connect to bottom neighbor
                if i + 1 < grid_size:
                    bottom_node = node_grid[(i + 1, j)]
                    current_node.connect_to(bottom_node)
        
        return created_nodes
    
    def get_all_nodes(self) -> List[Node]:
        """
        Get all nodes in the network.
        
        Returns:
            List of all nodes
        """
        return list(self.nodes.values())
    
    def get_network_stats(self) -> Dict[str, any]:
        """
        Get statistics about the network.
        
        Returns:
            Dictionary with network statistics
        """
        total_nodes = len(self.nodes)
        total_connections = sum(len(node.connections) for node in self.nodes.values()) // 2  # Divide by 2 for bidirectional
        
        if total_nodes == 0:
            return {
                'total_nodes': 0,
                'total_connections': 0,
                'average_connections_per_node': 0,
                'isolated_nodes': 0
            }
        
        isolated_nodes = sum(1 for node in self.nodes.values() if len(node.connections) == 0)
        average_connections = sum(len(node.connections) for node in self.nodes.values()) / total_nodes
        
        return {
            'total_nodes': total_nodes,
            'total_connections': total_connections,
            'average_connections_per_node': average_connections,
            'isolated_nodes': isolated_nodes
        }
    
    def __str__(self) -> str:
        """String representation of the network."""
        stats = self.get_network_stats()
        return f"NodeNetwork(nodes={stats['total_nodes']}, connections={stats['total_connections']})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return self.__str__() 