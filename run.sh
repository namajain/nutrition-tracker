#!/bin/bash

set -e

echo "Starting Nutrition Tracker..."

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

mkdir -p logs

echo "Checking for existing processes..."
sudo fuser -k 8000/tcp 2>/dev/null || true
fuser -k 8501/tcp 2>/dev/null || true

echo "Starting FastAPI backend on port 8000..."
nohup venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"

sleep 2

echo "Starting Streamlit frontend on port 8501..."
nohup venv/bin/streamlit run frontend/Home.py --server.port 8501 --server.address 0.0.0.0 --server.headless true > logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"

echo $BACKEND_PID > logs/backend.pid
echo $FRONTEND_PID > logs/frontend.pid

echo ""
echo "====================================="
echo "Nutrition Tracker started successfully!"
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:8501 (nginx forwards port 80)"
echo "====================================="
echo ""
echo "Logs:"
echo "  Backend:  tail -f logs/backend.log"
echo "  Frontend: tail -f logs/frontend.log"
echo ""
echo "To stop: ./stop.sh"