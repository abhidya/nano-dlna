#!/bin/bash

# Exit on error
set -e

# Stop the dashboard
echo "Stopping the dashboard..."

# Kill processes on specific ports
echo "Killing any processes using ports 3000 and 8000..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Kill specific processes by name that might not be bound to these ports
echo "Killing any React, Uvicorn, or Twisted processes..."
pkill -f "react-scripts" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "twisted" 2>/dev/null || true
pkill -f "TwistedStreamingServer" 2>/dev/null || true

# Kill processes on specific ports again to make sure
echo "Killing any processes using ports 3000 and 8000..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Kill specific processes by name again to make sure
echo "Killing any React, Uvicorn, or Twisted processes..."
pkill -f "react-scripts" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "twisted" 2>/dev/null || true
pkill -f "TwistedStreamingServer" 2>/dev/null || true

# Use the web stop script to clean up
cd web && ./stop_direct.sh
cd ..

# Verify all processes are stopped
if pgrep -f "react-scripts" > /dev/null || pgrep -f "uvicorn" > /dev/null || pgrep -f "twisted" > /dev/null || pgrep -f "TwistedStreamingServer" > /dev/null; then
    echo "Warning: Some processes may still be running."
    # Try one more time with more aggressive approach
    pkill -9 -f "react-scripts" || true
    pkill -9 -f "uvicorn" || true
    pkill -9 -f "twisted" || true
    pkill -9 -f "TwistedStreamingServer" || true
    sleep 1
fi

# Final check
if pgrep -f "react-scripts" > /dev/null || pgrep -f "uvicorn" > /dev/null || pgrep -f "twisted" > /dev/null || pgrep -f "TwistedStreamingServer" > /dev/null; then
    echo "Warning: Unable to stop all processes. You may need to manually kill them."
    echo "Try running: ps aux | grep -E 'react-scripts|uvicorn|twisted|TwistedStreamingServer' to find remaining processes"
else
    echo "Application stopped."
    echo "Dashboard stopped."
fi

# Make the script executable
chmod +x stop_dashboard.sh
