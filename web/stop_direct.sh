#!/bin/bash

# Kill any processes using the relevant ports first
echo "Killing any processes using ports 3000 and 8000..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Kill any React or Uvicorn processes
echo "Killing any React or Uvicorn processes..."
pkill -f "node.*react-scripts" || true
pkill -f "uvicorn" || true

# Check if the running PIDs file exists
if [ -f .running_pids ]; then
    # Read the PIDs from the file
    read BACKEND_PID FRONTEND_PID < .running_pids
    
    # Kill the processes forcefully
    echo "Stopping backend server (PID: $BACKEND_PID)..."
    kill -9 $BACKEND_PID 2>/dev/null || true
    
    echo "Stopping frontend server (PID: $FRONTEND_PID)..."
    kill -9 $FRONTEND_PID 2>/dev/null || true
    
    # Remove the PIDs file
    rm -f .running_pids
fi

# Verify all processes are stopped
if pgrep -f "node.*react-scripts" > /dev/null || pgrep -f "uvicorn" > /dev/null; then
    echo "Warning: Some processes may still be running."
    # Try one more time with more aggressive approach
    pkill -9 -f "node.*react-scripts" || true
    pkill -9 -f "uvicorn" || true
    sleep 1
fi

# Final check
if pgrep -f "node.*react-scripts" > /dev/null || pgrep -f "uvicorn" > /dev/null; then
    echo "Warning: Unable to stop all processes. You may need to manually kill them."
else
    echo "Application stopped."
fi
