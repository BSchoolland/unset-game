#!/usr/bin/env python3
"""
Demonstration of Node and NodeNetwork classes.
Shows how to create connected locations on the planet surface with pathfinding.
"""

import sys
import os

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from geoLocation import GeoLocation
from node import Node, NodeNetwork

def print_separator(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_path(path, total_time):
    """Helper function to print a path nicely."""
    if path:
        path_str = " -> ".join([node.name for node in path])
        print(f"Path: {path_str}")
        print(f"Total travel time: {total_time:.2f} time units")
    else:
        print("No path found!")

def main():
    print("Node System Demonstration")
    print("Creating connected movable spaces on the planet surface")
    
    # Create a network
    network = NodeNetwork()
    
    print_separator("Creating Individual Nodes")
    
    # Create some interesting locations
    locations = [
        (GeoLocation(0, 0), "Origin", "The starting point of our journey"),
        (GeoLocation(0, 10), "Eastern Outpost", "A trading post to the east"),
        (GeoLocation(10, 0), "Northern Settlement", "A small village in the north"),
        (GeoLocation(10, 10), "Mountain Pass", "A strategic mountain crossing"),
        (GeoLocation(5, 5), "Central Hub", "The heart of the region"),
        (GeoLocation(-5, 5), "Western Fort", "A defensive position"),
        (GeoLocation(15, 5), "Distant City", "A major population center")
    ]
    
    nodes = {}
    for location, name, description in locations:
        node = Node(location, name)
        node.set_property("description", description)
        node.set_property("type", "settlement")
        network.add_node(node)
        nodes[name] = node
        print(f"Created: {node}")
        print(f"  Description: {description}")
    
    print_separator("Connecting Nodes")
    
    # Create connections between nodes
    connections = [
        ("Origin", "Eastern Outpost"),
        ("Origin", "Northern Settlement"),
        ("Origin", "Central Hub"),
        ("Eastern Outpost", "Mountain Pass"),
        ("Northern Settlement", "Mountain Pass"),
        ("Central Hub", "Mountain Pass"),
        ("Central Hub", "Western Fort"),
        ("Mountain Pass", "Distant City"),
    ]
    
    for start_name, end_name in connections:
        start_node = nodes[start_name]
        end_node = nodes[end_name]
        start_node.connect_to(end_node)
        distance = start_node.get_distance_to(end_node)
        print(f"Connected {start_name} <-> {end_name} (distance: {distance:.2f})")
    
    print_separator("Network Statistics")
    
    stats = network.get_network_stats()
    print(f"Total nodes: {stats['total_nodes']}")
    print(f"Total connections: {stats['total_connections']}")
    print(f"Average connections per node: {stats['average_connections_per_node']:.2f}")
    print(f"Isolated nodes: {stats['isolated_nodes']}")
    
    print_separator("Basic Pathfinding Examples")
    
    # Example 1: Simple path
    print("1. Finding path from Origin to Mountain Pass:")
    origin = nodes["Origin"]
    mountain_pass = nodes["Mountain Pass"]
    result = origin.find_path_to(mountain_pass)
    if result:
        path, total_time = result
        print_path(path, total_time)
    
    # Example 2: Longer path
    print("\n2. Finding path from Western Fort to Distant City:")
    western_fort = nodes["Western Fort"]
    distant_city = nodes["Distant City"]
    result = western_fort.find_path_to(distant_city)
    if result:
        path, total_time = result
        print_path(path, total_time)
    
    # Example 3: Multiple possible paths
    print("\n3. Finding path from Origin to Distant City (multiple routes possible):")
    result = origin.find_path_to(distant_city)
    if result:
        path, total_time = result
        print_path(path, total_time)
    
    print_separator("Travel Time with Different Speeds")
    
    speeds = [0.5, 1.0, 2.0, 5.0]
    print("Travel time from Origin to Distant City at different speeds:")
    
    for speed in speeds:
        result = origin.find_path_to(distant_city, speed=speed)
        if result:
            path, total_time = result
            print(f"  Speed {speed:3.1f}: {total_time:6.2f} time units")
    
    print_separator("Reachable Nodes Analysis")
    
    # Show what's reachable from Origin within different time limits
    time_limits = [5, 10, 15, 20]
    print("Nodes reachable from Origin within time limits:")
    
    for time_limit in time_limits:
        reachable = origin.get_reachable_nodes(max_travel_time=time_limit)
        reachable_names = [node.name for node in reachable.keys() if node != origin]
        print(f"  Within {time_limit:2d} time units: {', '.join(reachable_names) if reachable_names else 'None'}")
    
    print_separator("Grid Network Creation")
    
    # Create a separate grid network for demonstration
    grid_network = NodeNetwork()
    center = GeoLocation(50, 50)
    grid_size = 4
    spacing = 3.0
    
    print(f"Creating {grid_size}x{grid_size} grid network:")
    print(f"Center: {center}")
    print(f"Spacing: {spacing} degrees")
    
    grid_nodes = grid_network.create_grid_network(center, grid_size, spacing)
    
    grid_stats = grid_network.get_network_stats()
    print(f"\nGrid network created:")
    print(f"  Nodes: {grid_stats['total_nodes']}")
    print(f"  Connections: {grid_stats['total_connections']}")
    print(f"  Average connections per node: {grid_stats['average_connections_per_node']:.2f}")
    
    # Test pathfinding in the grid
    if len(grid_nodes) >= 2:
        start_grid = grid_nodes[0]  # Top-left corner
        end_grid = grid_nodes[-1]   # Bottom-right corner
        
        print(f"\nPathfinding in grid from {start_grid.name} to {end_grid.name}:")
        result = start_grid.find_path_to(end_grid)
        if result:
            path, total_time = result
            print_path(path, total_time)
            print(f"Path length: {len(path)} nodes")
    
    print_separator("Location-Based Queries")
    
    # Find nodes near a specific location
    search_location = GeoLocation(5, 8)
    print(f"Searching for nodes near {search_location}:")
    
    nearby = network.get_nodes_near_location(search_location, max_distance=8.0)
    print(f"Nodes within 8.0 degrees:")
    for node, distance in nearby:
        print(f"  {node.name}: {distance:.2f} degrees away")
    
    print_separator("Node Properties Example")
    
    # Demonstrate node properties
    central_hub = nodes["Central Hub"]
    central_hub.set_property("population", 5000)
    central_hub.set_property("resources", ["food", "water", "fuel"])
    central_hub.set_property("defense_level", 3)
    
    print(f"Properties of {central_hub.name}:")
    print(f"  Population: {central_hub.get_property('population')}")
    print(f"  Resources: {central_hub.get_property('resources')}")
    print(f"  Defense Level: {central_hub.get_property('defense_level')}")
    print(f"  Climate: {central_hub.get_property('climate', 'temperate')}")  # Default value
    
    print_separator("Advanced Pathfinding Scenarios")
    
    # Scenario: What if a connection is broken?
    print("Scenario: Breaking the connection between Central Hub and Mountain Pass")
    central_hub.disconnect_from(mountain_pass)
    
    print("New path from Origin to Distant City:")
    result = origin.find_path_to(distant_city)
    if result:
        path, total_time = result
        print_path(path, total_time)
        print("(Notice the path may be different now)")
    else:
        print("No path available!")
    
    # Restore the connection
    central_hub.connect_to(mountain_pass)
    print("\nConnection restored.")
    
    print_separator("Summary")
    print("Node System Features Demonstrated:")
    print("✓ Creating nodes at specific geographic locations")
    print("✓ Connecting nodes to form a network")
    print("✓ Calculating travel times based on distance and speed")
    print("✓ Pathfinding using Dijkstra's algorithm")
    print("✓ Finding reachable nodes within time constraints")
    print("✓ Creating structured networks (grids)")
    print("✓ Location-based queries")
    print("✓ Custom node properties for game mechanics")
    print("✓ Dynamic network modification")
    print("\nThe node system is ready for your sphere-based game!")

if __name__ == "__main__":
    main() 