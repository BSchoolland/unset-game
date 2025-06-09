"""
FastAPI server for the sphere-based game.
Provides REST API endpoints for node management and player movement.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
import sys

# Add the game module to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'game'))

from game.generate_network import generate_network
from game.geoLocation import GeoLocation
from game.node import Node, NodeNetwork

app = FastAPI(title="Sphere Game API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (frontend)
if os.path.exists("../frontend"):
    app.mount("/static", StaticFiles(directory="../frontend"), name="static")

# Global game state
game_network = NodeNetwork()
players = {}

# Pydantic models for API
class LocationModel(BaseModel):
    latitude: float
    longitude: float

class NodeModel(BaseModel):
    id: str
    name: str
    location: LocationModel
    connections: List[str]
    properties: Dict[str, Any]

class CreateNodeModel(BaseModel):
    name: str
    location: LocationModel
    properties: Optional[Dict[str, Any]] = {}

class ConnectNodesModel(BaseModel):
    node1_id: str
    node2_id: str
    bidirectional: bool = True

class PlayerModel(BaseModel):
    id: str
    name: str
    current_node_id: str
    location: LocationModel
    properties: Dict[str, Any]

class CreatePlayerModel(BaseModel):
    name: str
    starting_node_id: str
    properties: Optional[Dict[str, Any]] = {}

class MovePlayerModel(BaseModel):
    player_id: str
    target_node_id: str
    speed: float = 1.0

class PathModel(BaseModel):
    nodes: List[str]
    total_time: float

# Helper functions
def node_to_dict(node: Node) -> dict:
    """Convert a Node object to a dictionary."""
    return {
        "id": node.id,
        "name": node.name,
        "location": {
            "latitude": node.location.latitude,
            "longitude": node.location.longitude
        },
        "connections": list(node.connections.keys()),
        "properties": node.properties
    }

def location_to_dict(location: GeoLocation) -> dict:
    """Convert a GeoLocation to a dictionary."""
    return {
        "latitude": location.latitude,
        "longitude": location.longitude
    }

# Player class
class Player:
    def __init__(self, player_id: str, name: str, starting_node: Node, properties: dict = None):
        self.id = player_id
        self.name = name
        self.current_node = starting_node
        self.properties = properties or {}
    
    def move_to_node(self, target_node: Node) -> bool:
        """Move player to a target node if connected."""
        if self.current_node.is_connected_to(target_node):
            self.current_node = target_node
            return True
        return False
    
    def get_reachable_nodes(self, max_travel_time: float = None, speed: float = 1.0) -> Dict[Node, float]:
        """Get nodes reachable from current position."""
        return self.current_node.get_reachable_nodes(max_travel_time, speed)
    
    def find_path_to(self, target_node: Node, speed: float = 1.0):
        """Find path from current node to target."""
        return self.current_node.find_path_to(target_node, speed)
    
    def to_dict(self) -> dict:
        """Convert player to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "current_node_id": self.current_node.id,
            "location": location_to_dict(self.current_node.location),
            "properties": self.properties
        }

# Initialize with some sample data
def initialize_sample_data():
    """Create an equatorial network for demonstration."""
    # Use the equatorial generator to create a realistic network
    
    network = generate_network(30, 30.0, 30.0, 0.5, 0.5)
    
    # Replace the global network
    global game_network
    game_network = network
    
    print(f"Initialized equatorial network with {len(network.get_all_nodes())} nodes")
    
    # Add some properties to nodes for variety
    nodes = network.get_all_nodes()
    node_types = ["city", "port", "outpost", "base", "hub", "fort", "colony", "station"]
    
    for i, node in enumerate(nodes):
        node_type = node_types[i % len(node_types)]
        population = 200 + (i * 50) % 800  # Vary population
        
        node.set_property("type", node_type)
        node.set_property("population", population)
        node.set_property("resources", ["water", "food"][i % 2])  # Alternate resources

# Initialize sample data on startup
initialize_sample_data()

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Sphere Game API",
        "version": "1.0.0",
        "endpoints": {
            "nodes": "/nodes",
            "players": "/players",
            "docs": "/docs"
        }
    }

# Node endpoints
@app.get("/nodes", response_model=List[NodeModel])
async def get_all_nodes():
    """Get all nodes in the network."""
    return [node_to_dict(node) for node in game_network.get_all_nodes()]

@app.get("/nodes/{node_id}", response_model=NodeModel)
async def get_node(node_id: str):
    """Get a specific node by ID."""
    node = game_network.get_node_by_id(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node_to_dict(node)

@app.post("/nodes", response_model=NodeModel)
async def create_node(node_data: CreateNodeModel):
    """Create a new node."""
    location = GeoLocation(node_data.location.latitude, node_data.location.longitude)
    node = Node(location, node_data.name)
    
    for key, value in node_data.properties.items():
        node.set_property(key, value)
    
    if not game_network.add_node(node):
        raise HTTPException(status_code=400, detail="Node with this ID already exists")
    
    return node_to_dict(node)

@app.post("/nodes/connect")
async def connect_nodes(connection: ConnectNodesModel):
    """Connect two nodes."""
    node1 = game_network.get_node_by_id(connection.node1_id)
    node2 = game_network.get_node_by_id(connection.node2_id)
    
    if not node1 or not node2:
        raise HTTPException(status_code=404, detail="One or both nodes not found")
    
    success = node1.connect_to(node2, connection.bidirectional)
    if not success:
        raise HTTPException(status_code=400, detail="Nodes are already connected")
    
    return {"message": "Nodes connected successfully"}

@app.delete("/nodes/disconnect")
async def disconnect_nodes(connection: ConnectNodesModel):
    """Disconnect two nodes."""
    node1 = game_network.get_node_by_id(connection.node1_id)
    node2 = game_network.get_node_by_id(connection.node2_id)
    
    if not node1 or not node2:
        raise HTTPException(status_code=404, detail="One or both nodes not found")
    
    success = node1.disconnect_from(node2, connection.bidirectional)
    if not success:
        raise HTTPException(status_code=400, detail="Nodes are not connected")
    
    return {"message": "Nodes disconnected successfully"}

@app.get("/nodes/{node_id}/reachable")
async def get_reachable_nodes(node_id: str, max_travel_time: Optional[float] = None, speed: float = 1.0):
    """Get nodes reachable from a specific node."""
    node = game_network.get_node_by_id(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    reachable = node.get_reachable_nodes(max_travel_time, speed)
    return {
        "reachable_nodes": [
            {
                "node": node_to_dict(n),
                "travel_time": time
            }
            for n, time in reachable.items()
        ]
    }

@app.get("/nodes/{start_node_id}/path/{end_node_id}")
async def find_path(start_node_id: str, end_node_id: str, speed: float = 1.0):
    """Find path between two nodes."""
    start_node = game_network.get_node_by_id(start_node_id)
    end_node = game_network.get_node_by_id(end_node_id)
    
    if not start_node or not end_node:
        raise HTTPException(status_code=404, detail="One or both nodes not found")
    
    result = start_node.find_path_to(end_node, speed)
    if not result:
        raise HTTPException(status_code=404, detail="No path found between nodes")
    
    path, total_time = result
    return {
        "path": [node.id for node in path],
        "node_details": [node_to_dict(node) for node in path],
        "total_time": total_time
    }

# Player endpoints
@app.get("/players", response_model=List[PlayerModel])
async def get_all_players():
    """Get all players."""
    return [player.to_dict() for player in players.values()]

@app.get("/players/{player_id}", response_model=PlayerModel)
async def get_player(player_id: str):
    """Get a specific player by ID."""
    if player_id not in players:
        raise HTTPException(status_code=404, detail="Player not found")
    return players[player_id].to_dict()

@app.post("/players", response_model=PlayerModel)
async def create_player(player_data: CreatePlayerModel):
    """Create a new player."""
    starting_node = game_network.get_node_by_id(player_data.starting_node_id)
    if not starting_node:
        raise HTTPException(status_code=404, detail="Starting node not found")
    
    # Generate unique player ID
    player_id = f"player_{len(players) + 1}"
    
    player = Player(player_id, player_data.name, starting_node, player_data.properties)
    players[player_id] = player
    
    return player.to_dict()

@app.post("/players/move")
async def move_player(move_data: MovePlayerModel):
    """Move a player to a target node."""
    if move_data.player_id not in players:
        raise HTTPException(status_code=404, detail="Player not found")
    
    player = players[move_data.player_id]
    target_node = game_network.get_node_by_id(move_data.target_node_id)
    
    if not target_node:
        raise HTTPException(status_code=404, detail="Target node not found")
    
    # Check if move is valid (nodes are connected)
    if not player.current_node.is_connected_to(target_node):
        raise HTTPException(status_code=400, detail="Target node is not connected to current node")
    
    # Calculate travel time
    travel_time = player.current_node.get_travel_time_to(target_node, move_data.speed)
    
    # Move the player
    success = player.move_to_node(target_node)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to move player")
    
    return {
        "message": "Player moved successfully",
        "player": player.to_dict(),
        "travel_time": travel_time
    }

@app.get("/players/{player_id}/reachable")
async def get_player_reachable_nodes(player_id: str, max_travel_time: Optional[float] = None, speed: float = 1.0):
    """Get nodes reachable by a specific player."""
    if player_id not in players:
        raise HTTPException(status_code=404, detail="Player not found")
    
    player = players[player_id]
    reachable = player.get_reachable_nodes(max_travel_time, speed)
    
    return {
        "reachable_nodes": [
            {
                "node": node_to_dict(n),
                "travel_time": time
            }
            for n, time in reachable.items()
        ]
    }

@app.get("/players/{player_id}/path/{target_node_id}")
async def get_player_path(player_id: str, target_node_id: str, speed: float = 1.0):
    """Find path from player's current location to target node."""
    if player_id not in players:
        raise HTTPException(status_code=404, detail="Player not found")
    
    player = players[player_id]
    target_node = game_network.get_node_by_id(target_node_id)
    
    if not target_node:
        raise HTTPException(status_code=404, detail="Target node not found")
    
    result = player.find_path_to(target_node, speed)
    if not result:
        raise HTTPException(status_code=404, detail="No path found to target node")
    
    path, total_time = result
    return {
        "path": [node.id for node in path],
        "node_details": [node_to_dict(node) for node in path],
        "total_time": total_time
    }

# Network statistics
@app.get("/network/stats")
async def get_network_stats():
    """Get network statistics."""
    return game_network.get_network_stats()

# Equatorial generator endpoints
@app.post("/network/generate-equatorial")
async def generate_equatorial_network(config):
    """Generate a new equatorial network with specified parameters."""
    global game_network, players
    
    try:
        new_network = generate_network(config.num_nodes, config.equator_band_degrees, config.max_distance, config.deviation_bias, config.connection_bias)
    
        
        return {
            "message": "Equatorial network generated successfully",
            "nodes_generated": len(new_network.get_all_nodes()),
            "total_nodes": len(game_network.get_all_nodes()),
            "replaced_network": config.replace_current
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate network: {str(e)}")

@app.get("/network/equatorial-preview")
async def preview_equatorial_network(
    num_nodes: int = 30,
    equator_band_degrees: float = 30.0,
    min_distance: float = 5.0,
    max_distance: float = 10.0,
    seed: Optional[int] = None
):
    """Preview an equatorial network without adding it to the game."""
    try:
        generator = EquatorialNodeGenerator(
            equator_band_degrees=equator_band_degrees,
            min_distance=min_distance,
            max_distance=max_distance
        )
        
        preview_network = generator.generate_equatorial_network(
            num_nodes=num_nodes,
            seed=seed
        )
        
        # Get network statistics
        stats = preview_network.get_network_stats()
        
        # Get all nodes for preview
        nodes = [node_to_dict(node) for node in preview_network.get_all_nodes()]
        
        return {
            "preview_nodes": nodes,
            "network_stats": stats,
            "generation_params": {
                "num_nodes": num_nodes,
                "equator_band_degrees": equator_band_degrees,
                "min_distance": min_distance,
                "max_distance": max_distance,
                "seed": seed
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to preview network: {str(e)}")

@app.delete("/network/clear")
async def clear_network():
    """Clear all nodes and players from the network."""
    global game_network, players
    
    game_network = NodeNetwork()
    players.clear()
    
    return {"message": "Network cleared successfully"}

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
