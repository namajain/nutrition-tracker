#!/bin/bash

# Nutrition Tracker startup script
# Starts both FastAPI backend and Streamlit frontend in background

# Exit on error
set -e

echo "Starting Nutrition Tracker..."

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Create logs directory if it doesn't exist
mkdir -p logs

# Kill any existing processes on the ports
echo "Checking for existing processes..."
sudo fuser -k 8000/tcp 2>/dev/null || true
sudo fuser -k 80/tcp 2>/dev/null || true

# Start FastAPI backend
echo "Starting FastAPI backend on port 8000..."
nohup uvicorn backend.main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"

# Wait a moment for backend to initialize
sleep 2

# Start Streamlit frontend on port 80 (requires sudo)
echo "Starting Streamlit frontend on port 80..."
nohup sudo streamlit run frontend/Home.py --server.port 80 --server.address 0.0.0.0 --server.headless true > logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"

# Save PIDs to file for later shutdown
echo $BACKEND_PID > logs/backend.pid
echo $FRONTEND_PID > logs/frontend.pid

echo ""
echo "====================================="
echo "Nutrition Tracker started successfully!"
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost"
echo "====================================="
echo ""
echo "Logs:"
echo "  Backend:  tail -f logs/backend.log"
echo "  Frontend: tail -f logs/frontend.log"
echo ""
echo "To stop: ./stop.sh"

