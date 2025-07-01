#!/bin/bash
# Stop script for multi-agent environment

AGENT_ID=${1:-1}

echo "Stopping Agent ${AGENT_ID}..."

# Stop backend
if [ -f ".agent${AGENT_ID}.backend.pid" ]; then
    BACKEND_PID=$(cat .agent${AGENT_ID}.backend.pid)
    if ps -p ${BACKEND_PID} > /dev/null 2>&1; then
        kill ${BACKEND_PID}
        echo "✓ Backend stopped (PID: ${BACKEND_PID})"
    else
        echo "⚠ Backend not running (PID: ${BACKEND_PID})"
    fi
    rm .agent${AGENT_ID}.backend.pid
else
    echo "⚠ No backend PID file found"
fi

# Stop frontend
if [ -f ".agent${AGENT_ID}.frontend.pid" ]; then
    FRONTEND_PID=$(cat .agent${AGENT_ID}.frontend.pid)
    if ps -p ${FRONTEND_PID} > /dev/null 2>&1; then
        kill ${FRONTEND_PID}
        echo "✓ Frontend stopped (PID: ${FRONTEND_PID})"
    else
        echo "⚠ Frontend not running (PID: ${FRONTEND_PID})"
    fi
    rm .agent${AGENT_ID}.frontend.pid
else
    echo "⚠ No frontend PID file found"
fi

echo "✓ Agent ${AGENT_ID} stopped"