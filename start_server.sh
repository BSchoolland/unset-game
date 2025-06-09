#!/bin/bash

echo "Starting Sphere Game Server..."
echo "================================"

# Check if we're in the right directory
if [ ! -f "backend/server.py" ]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

# Navigate to backend directory
cd backend

# Check if requirements are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing dependencies..."
    python -m pip install -r requirements.txt
fi

echo "Starting FastAPI server on http://localhost:8000"
echo "API documentation available at http://localhost:8000/docs"
echo "Frontend available at http://localhost:8000/static/index.html"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python server.py 