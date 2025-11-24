#!/bin/bash

# Stop Nutrition Tracker services

echo "Stopping Nutrition Tracker..."

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Kill processes by PID if files exist
if [ -f logs/backend.pid ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
    fi
    rm logs/backend.pid
fi

if [ -f logs/frontend.pid ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "Stopping frontend (PID: $FRONTEND_PID)..."
        sudo kill $FRONTEND_PID
    fi
    rm logs/frontend.pid
fi

# Also kill any remaining processes on the ports
sudo fuser -k 8000/tcp 2>/dev/null || true
sudo fuser -k 80/tcp 2>/dev/null || true

echo "Nutrition Tracker stopped."


