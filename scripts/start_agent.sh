#!/bin/bash
# Start script for multi-agent environment

AGENT_ID=${1:-1}

# Check if agent is configured
if [ ! -f ".env.agent${AGENT_ID}" ]; then
    echo "❌ Agent ${AGENT_ID} not configured. Run: ./scripts/setup_agent.sh ${AGENT_ID}"
    exit 1
fi

# Load agent environment
source .env.agent${AGENT_ID}

echo "Starting Agent ${AGENT_ID}..."
echo "================================"

# Start backend
echo "Starting backend on port ${BACKEND_PORT}..."
cd web/backend
PORT=${BACKEND_PORT} python app.py > ../../logs/agent${AGENT_ID}/backend.log 2>&1 &
BACKEND_PID=$!
cd ../..

# Wait for backend to start
sleep 3

# Check if backend started
if curl -s http://localhost:${BACKEND_PORT}/health > /dev/null 2>&1; then
    echo "✓ Backend started (PID: ${BACKEND_PID})"
else
    echo "❌ Backend failed to start. Check logs/agent${AGENT_ID}/backend.log"
    exit 1
fi

# Start frontend
echo "Starting frontend on port ${FRONTEND_PORT}..."
cd web/frontend
REACT_APP_API_URL=http://localhost:${BACKEND_PORT} PORT=${FRONTEND_PORT} npm start > ../../logs/agent${AGENT_ID}/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ../..

# Save PIDs for cleanup
echo "${BACKEND_PID}" > .agent${AGENT_ID}.backend.pid
echo "${FRONTEND_PID}" > .agent${AGENT_ID}.frontend.pid

echo "✓ Frontend started (PID: ${FRONTEND_PID})"
echo ""
echo "Agent ${AGENT_ID} is running:"
echo "  - Backend: http://localhost:${BACKEND_PORT}"
echo "  - Frontend: http://localhost:${FRONTEND_PORT}"
echo ""
echo "To stop: ./scripts/stop_agent.sh ${AGENT_ID}"
echo "To check status: ./scripts/check_agents.sh"