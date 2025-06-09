# Sphere Game

A 3D sphere-based game where players can move between connected nodes on a planet surface. Built with Python (FastAPI backend) and Three.js (frontend).

## Features

- **3D Sphere Visualization**: Interactive 3D sphere with nodes positioned using geographic coordinates
- **Node Network**: Connected locations with realistic travel times based on spherical geometry
- **Player Movement**: Move between connected nodes with pathfinding and travel time calculations
- **Real-time Visualization**: See connections, reachable nodes, and optimal paths
- **REST API**: Complete backend API for game state management

## Project Structure

```
unset-game/
├── backend/
│   ├── game/
│   │   ├── geoLocation.py      # Geographic calculations on sphere
│   │   ├── node.py             # Node network and pathfinding
│   │   └── tests/              # Comprehensive test suite
│   ├── server.py               # FastAPI server
│   └── requirements.txt        # Python dependencies
├── frontend/
│   ├── index.html              # Main HTML file
│   └── js/
│       └── game.js             # Three.js game logic
└── README.md                   # This file
```

## Setup Instructions

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the server:**
   ```bash
   python server.py
   ```

   The server will start on `http://localhost:8000`

### Frontend Setup

1. **Open the frontend:**
   - Open `frontend/index.html` in a web browser, OR
   - Serve it through the FastAPI server at `http://localhost:8000/static/index.html`

2. **For development with live reload:**
   ```bash
   # In the frontend directory
   python -m http.server 3000
   ```
   Then open `http://localhost:3000`

## Usage

### Game Controls

1. **Create Player**: Click "Create Player" to spawn a player at the first node
2. **Select Nodes**: Click on any node (colored spheres) to select it
3. **View Information**: Selected node details appear in the left panel
4. **Movement Speed**: Adjust the speed slider to change travel times
5. **Show Connections**: Toggle visibility of node connections (green lines)
6. **Show Reachable**: Highlight all nodes reachable from player's current position (yellow lines)
7. **Find Path**: Show the optimal path to selected node (red lines)
8. **Move Player**: Move to a connected node (only works for directly connected nodes)
9. **Reset View**: Return camera to default position and clear highlights

### Visual Elements

- **Blue Sphere**: The planet surface
- **Colored Nodes**: Different colors represent different node types:
  - Red: Cities
  - Teal: Ports
  - Blue: Outposts
  - Green: Bases
  - Yellow: Hubs
  - Purple: Forts
  - Light Green: Colonies
- **Red Cone**: Player position
- **Green Lines**: Node connections
- **Yellow Lines**: Reachable nodes from player position
- **Red Lines**: Optimal path to selected destination

### Camera Controls

- **Rotate**: Left mouse drag
- **Zoom**: Mouse wheel
- **Pan**: Right mouse drag (or Ctrl + left drag)

## API Endpoints

The FastAPI server provides a complete REST API:

### Node Endpoints
- `GET /nodes` - Get all nodes
- `GET /nodes/{node_id}` - Get specific node
- `POST /nodes` - Create new node
- `POST /nodes/connect` - Connect two nodes
- `DELETE /nodes/disconnect` - Disconnect two nodes
- `GET /nodes/{node_id}/reachable` - Get reachable nodes
- `GET /nodes/{start_node_id}/path/{end_node_id}` - Find path between nodes

### Player Endpoints
- `GET /players` - Get all players
- `GET /players/{player_id}` - Get specific player
- `POST /players` - Create new player
- `POST /players/move` - Move player to connected node
- `GET /players/{player_id}/reachable` - Get nodes reachable by player
- `GET /players/{player_id}/path/{target_node_id}` - Find path from player to target

### Network Endpoints
- `GET /network/stats` - Get network statistics

### API Documentation
Visit `http://localhost:8000/docs` for interactive API documentation.

## Game Mechanics

### Geographic System
- Uses proper spherical geometry for accurate distance calculations
- Latitude range: -45° to 45° (avoiding poles)
- Longitude range: -180° to 180° (full sphere)
- Distance calculations use haversine formula
- Direction calculations use spherical bearing

### Movement System
- Players can only move between directly connected nodes
- Travel time = distance / speed
- Pathfinding uses Dijkstra's algorithm for optimal routes
- Speed can be adjusted from 0.5 to 5.0 units per time

### Node Types
Sample nodes include different settlement types with varying populations:
- **Cities**: Major population centers
- **Ports**: Coastal trading posts
- **Outposts**: Remote settlements
- **Bases**: Military installations
- **Hubs**: Central connection points
- **Forts**: Defensive positions
- **Colonies**: Distant settlements

## Development

### Running Tests

```bash
cd backend/game/tests

# Run all tests
python test_geoLocation.py
python test_node.py

# Run with verbose output
python test_geoLocation.py -v
python test_node.py -v

# Run demonstrations
python demo_geoLocation.py
python demo_node.py
```

### Adding New Features

1. **Backend**: Extend the FastAPI server in `backend/server.py`
2. **Game Logic**: Modify node/player classes in `backend/game/`
3. **Frontend**: Update the Three.js visualization in `frontend/js/game.js`
4. **Tests**: Add tests in `backend/game/tests/`

## Technical Details

### Backend Technologies
- **FastAPI**: Modern Python web framework
- **Pydantic**: Data validation and serialization
- **Uvicorn**: ASGI server for FastAPI
- **Custom Math**: Spherical geometry calculations

### Frontend Technologies
- **Three.js**: 3D graphics library
- **OrbitControls**: Camera controls for 3D navigation
- **Canvas API**: Dynamic text labels for nodes
- **Fetch API**: Communication with backend

### Mathematical Foundation
- **Haversine Formula**: Accurate distance calculation on sphere
- **Spherical Bearing**: Direction calculations
- **Dijkstra's Algorithm**: Shortest path finding
- **Spherical Coordinates**: Lat/lon to 3D position conversion

## Troubleshooting

### Common Issues

1. **Server won't start**: Make sure port 8000 is available
2. **Frontend can't connect**: Ensure backend server is running
3. **CORS errors**: Check that CORS is properly configured in server.py
4. **Three.js not loading**: Check internet connection for CDN resources

### Performance Tips

1. **Large networks**: Consider reducing connection line visibility
2. **Slow rendering**: Lower sphere geometry resolution in game.js
3. **Memory usage**: Clear path/reachable lines regularly

## License

This project is open source. Feel free to modify and extend for your own use.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Future Enhancements

- **Multiplayer Support**: Multiple players on the same sphere
- **Resource System**: Nodes with resources and trading
- **Time System**: Real-time movement with scheduling
- **Terrain Types**: Different movement speeds based on terrain
- **Weather Effects**: Dynamic conditions affecting travel
- **Save/Load**: Persistent game state
- **Mobile Support**: Touch controls for mobile devices
