from geoLocation import GeoLocation
from node import Node
from game.node import NodeNetwork

import random

def is_too_close_to_existing(new_location, existing_nodes, min_distance):
    """Check if a new location is too close to any existing nodes."""
    for existing_node in existing_nodes:
        if new_location.get_distance_to_point(existing_node.location) <= min_distance:
            return True
    return False

def generate_network(num_nodes, equator_band_degrees, max_distance, deviation_bias, connection_bias):
    min_distance = max_distance * 0.5
    # step 1: generate a belt around the equator (not a perfect circle, kinda random)
    path = generate_path_with_mild_vertical_bias(deviation_bias, max_distance)
    nodes = []
    for point in path:
        new_location = GeoLocation(point[1], point[0])
        # Check if this location is too close to existing path nodes
        if not is_too_close_to_existing(new_location, nodes, min_distance):
            nodes.append(Node(new_location))
        else:
            print(f"Skipping path node at {point} - too close to existing node")
    
    for node in nodes:
        for other_node in nodes:
            if node != other_node:
                if node.get_distance_to(other_node) <= max_distance * 1.1:
                    node.connect_to(other_node, True, True)
    network = NodeNetwork()
    for node in nodes:
        network.add_node(node)
    # step 2: generate candidate nodes to add to the network
    candidates = generate_grid(int(equator_band_degrees), int(max_distance))
    
    
    # step 3: pick a random number of nodes from the candidates
    network = pick_random_nodes(candidates, num_nodes, network, max_distance)

    # step 4: add additional connections to the network
    network = add_additional_connections(network, max_distance)

    # step 5: randomly pull the nodes without breaking connections
    network = random_pull_nodes(network, max_distance)

    # step 6: thin connections
    network = thin_connections(network, 3)

    # step 7 reconnect orphaned nodes
    network = reconnect_orphaned_nodes(network, max_distance)

    # log any nodes with the same name
    for node in network.get_all_nodes():
        for other_node in network.get_all_nodes():
            if node.name == other_node.name and node != other_node:
                print('warning: same name', node.name, node.location, other_node.location)
    return network

# step 1: walk around the planet
def generate_path_with_mild_vertical_bias(deviation_bias: float, max_distance: int, return_threshold_ratio: float = 0.9):
    """
    Generate a 2D path where:
    - 'deviation_bias' controls how likely the walker is to deviate from forward movement.
    - The further the walker moves from y=0, the more likely it is to move back toward y=0.
    - Stops once x reaches return_threshold_ratio * max_x.

    Returns:
        List of (x, y) tuples representing the path.
    """
    # define movement vectors
    DIRECTIONS = {
        "f":   (max_distance, 0),
        "f+u": (max_distance * 0.5, max_distance * 0.5),
        "f+d": (max_distance * 0.5, -max_distance * 0.5),
        "u":   (0, max_distance),
        "d":   (0, -max_distance),
        "b+u": (-max_distance * 0.5, max_distance * 0.5),
        "b+d": (-max_distance * 0.5, -max_distance * 0.5),
        "b":   (-max_distance, 0),
    }

    base_forward = 1.0
    path = [(0, 0)]
    x, y = 0, 0
    threshold = int(360 * return_threshold_ratio)

    while x < threshold:
        # Symmetric vertical bias to gently pull toward y = 0
        vertical_bias = 1 + abs(y) / 20  # mild bias grows as y gets farther from 0
        up_bias = vertical_bias if y < 0 else 1.0
        down_bias = vertical_bias if y > 0 else 1.0

        weights = {
            "f": base_forward,
            "f+u": 0.75 * deviation_bias * up_bias,
            "f+d": 0.75 * deviation_bias * down_bias,
            "u": 0.5 * deviation_bias * up_bias,
            "d": 0.5 * deviation_bias * down_bias,
            "b+u": 0.2 * deviation_bias * up_bias,
            "b+d": 0.2 * deviation_bias * down_bias,
            "b": 0.1 * deviation_bias,
        }

        # Normalize weights
        total = sum(weights.values())
        weight_list = [(k, v / total) for k, v in weights.items()]

        # Pick direction based on weighted choice
        direction = random.choices([d for d, _ in weight_list], [w for _, w in weight_list])[0]
        dx, dy = DIRECTIONS[direction]
        x, y = x + dx, y + dy
        print('moving to', x, y)
        path.append((x, y))
    # close the loop by going to (360, 0) using the directions
    while distance(path[-1], (360, 0)) > max_distance:
        if abs(path[-1][1]) > 360 -path[-1][0]:
            # move y back towards 0 by max_distance
            if path[-1][1] > 0:
                y = path[-1][1] - max_distance
            else:
                y = path[-1][1] + max_distance
        else:
            # move x towards 360 by max_distance
            x = path[-1][0] + max_distance
        print('pathing to', x, y)
        path.append((x, y))
    return path

# step 2: generate candidate nodes to add to the network
# min = max/2
# max evenly divides 360
def generate_grid(equator_band_degrees, max_distance):
    min_distance = max_distance * 0.5
    
    candidates = []
    y = equator_band_degrees
    offset = True
    while y >= -equator_band_degrees:
        for x in range(-180, 180, max_distance):
            if offset:
                x += max_distance / 2
            if x > 180:
                break
            print(f"x: {x}, y: {y}")
            candidates.append(GeoLocation(y, x))
        y -= min_distance
        offset = not offset

    return candidates

# step 3: pick a random number of nodes from the candidates
def pick_random_nodes(candidates, num_nodes, network, max_distance):
    min_distance = max_distance * 0.5
    possible_positions = random.sample(candidates, min(num_nodes * 2, len(candidates)))  # Sample more than needed
    possibleNodes = []
    
    # Filter candidates to ensure they're not too close to existing nodes or each other
    for position in possible_positions:
        # Check against existing network nodes
        if is_too_close_to_existing(position, network.get_all_nodes(), min_distance):
            print(f"Skipping candidate at {position.latitude:.2f}, {position.longitude:.2f} - too close to existing network node")
            continue
        
        # Check against already selected possible nodes
        if is_too_close_to_existing(position, possibleNodes, min_distance):
            print(f"Skipping candidate at {position.latitude:.2f}, {position.longitude:.2f} - too close to other candidate")
            continue
            
        possibleNodes.append(Node(position))
        if len(possibleNodes) >= num_nodes:
            break
    
    print(f"Selected {len(possibleNodes)} candidate nodes after proximity filtering")

    total_count = 0
    count = -1
    while count != 0:
        count = 0
        nodes_to_remove = set()  # Use set to avoid duplicates
        for node in possibleNodes:
            for other_node in network.get_all_nodes():
                if node.get_distance_to(other_node) <= max_distance * 1.1:
                    node.connect_to(other_node)
                    network.add_node(node)
                    nodes_to_remove.add(node)  # Add to set instead of list
                    count += 1
                    total_count += 1
                    break  # Break inner loop once node is connected and added
        for node in nodes_to_remove:
            possibleNodes.remove(node)
    print('no more could connect found. Missed', len(possibleNodes), 'nodes')
    
    return network

# step 4: add additional connections to the network
def add_additional_connections(network, max_distance):
    # chance to add 0, 1, or 2 connections to a node
    for node in network.get_all_nodes():
        near_nodes = []
        for other_node in network.get_all_nodes():
            if node != other_node:
                if node.get_distance_to(other_node) <= max_distance * 1.1 and not node.is_connected_to(other_node):
                    near_nodes.append(other_node)
        should_connect = len(near_nodes)/2
        num = random.random()
        if num < 0.33:
            should_connect -= 2
        elif num < 0.66:
            should_connect -= 1
        else:
            pass
        for other_node in near_nodes:
            if node != other_node and should_connect > 0:
                if node.get_distance_to(other_node) <= max_distance * 1.1 and not node.is_connected_to(other_node):
                    node.connect_to(other_node)
                    should_connect -= 1
       
    return network

# step 5: randomly pull the nodes without breaking connections
def random_pull_nodes(network, max_distance):
    min_distance = max_distance * 0.5
    for node in network.get_all_nodes():
        connected_nodes = node.get_connected_nodes()
        for i in range(3): # try to translate n times
            x_translation = random.randint(-5, 5)
            y_translation = random.randint(-5, 5)
            
            node.translate(x_translation, y_translation)
            cancelMove = False
            
            # Check if translation breaks connection distances
            for connection in connected_nodes:
                if node.get_distance_to(connection) > max_distance * 1.1:
                    cancelMove = True
                    break
            
            # Check if translation makes this node too close to other nodes
            if not cancelMove:
                for other_node in network.get_all_nodes():
                    if other_node != node:
                        if node.get_distance_to(other_node) <= min_distance:
                            cancelMove = True
                            print(f"Translation cancelled - would be too close to {other_node.name}")
                            break
            
            if cancelMove:
                node.translate(-x_translation, -y_translation)
    return network

# step 6: thin connections for nodes that have too many connections
def thin_connections(network, max_connections):
    for node in network.get_all_nodes():
        num_connections = len(node.get_connected_nodes())
        if num_connections > max_connections:
            while num_connections > max_connections:
                # disconnect the furthest connection until num_connections is 3
                furthest_connection = None
                furthest_distance = 0
                for connection in node.get_connected_nodes():
                    if node.get_distance_to(connection) > furthest_distance:
                        furthest_distance = node.get_distance_to(connection)
                        furthest_connection = connection
                if furthest_connection:
                    node.disconnect_from(furthest_connection)
                num_connections = len(node.get_connected_nodes())
    return network

# step 7: reconnect orphaned nodes
def reconnect_orphaned_nodes(network, max_distance):
    for node in network.get_all_nodes():
        # if unable to path to the first node, connect to all nodes it can
        if not node.find_path_to(network.get_all_nodes()[0]):
            for other_node in network.get_all_nodes():
                if node.get_distance_to(other_node) <= max_distance * 1.1 and not node.is_connected_to(other_node):
                    node.connect_to(other_node)
    return network


def distance(point1, point2):
    return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5

def main():
    path = generate_path_with_mild_vertical_bias(5, 10)
    print(path)

if __name__ == "__main__":
    main()