# Game Module Tests

This directory contains tests and demonstrations for the game module classes.

## Files

### GeoLocation Tests
- `test_geoLocation.py` - Comprehensive unit tests for the GeoLocation class
- `demo_geoLocation.py` - Demonstration script showing key functionality

### Node System Tests
- `test_node.py` - Comprehensive unit tests for the Node and NodeNetwork classes
- `demo_node.py` - Demonstration script showing node connectivity and pathfinding

### Package Files
- `__init__.py` - Makes this directory a Python package
- `README.md` - This documentation file

## Running Tests

From this directory, run:

```bash
# Run GeoLocation tests
python test_geoLocation.py

# Run Node system tests
python test_node.py

# Run all tests with verbose output
python test_geoLocation.py -v
python test_node.py -v

# Run demonstrations
python demo_geoLocation.py
python demo_node.py
```

## Test Coverage

### GeoLocation Tests
The GeoLocation tests cover:
- Distance calculations using haversine formula
- Direction calculations using spherical bearing
- Translation using proper spherical geometry
- Longitude wrapping across the dateline
- Latitude clamping to game boundaries (-45° to 45°)
- Edge cases and boundary conditions
- Mathematical consistency between operations

### Node System Tests
The Node system tests cover:
- Node creation and management
- Bidirectional and unidirectional connections
- Distance and travel time calculations
- Pathfinding using Dijkstra's algorithm
- Reachable node analysis within time constraints
- Network management and statistics
- Grid network generation
- Location-based queries
- Custom node properties
- Dynamic network modification

## Implementation Details

Both systems use proper spherical geometry for accurate calculations on the planet surface. The Node system builds on the GeoLocation foundation to provide:

- **Connected Movement**: Players can only move between connected nodes
- **Travel Time**: Movement takes time based on distance and speed
- **Pathfinding**: Automatic route calculation using shortest path algorithms
- **Flexible Networks**: Support for any network topology
- **Game Integration**: Custom properties and dynamic modification support

All tests pass and verify the mathematical accuracy and game-ready functionality of both systems. 