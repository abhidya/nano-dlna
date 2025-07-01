#!/bin/bash
# Setup script for multi-agent environment

AGENT_ID=${1:-1}
BASE_BACKEND_PORT=$((8000 + AGENT_ID))
BASE_FRONTEND_PORT=$((3000 + AGENT_ID))

# Create agent-specific environment file
cat > .env.agent${AGENT_ID} << EOF
# Agent ${AGENT_ID} Configuration
AGENT_NAME=agent${AGENT_ID}
BACKEND_PORT=${BASE_BACKEND_PORT}
FRONTEND_PORT=${BASE_FRONTEND_PORT}
DATABASE_URL=sqlite:///nano_dlna_agent${AGENT_ID}.db
UPLOAD_DIR=./uploads_agent${AGENT_ID}
REACT_APP_API_URL=http://localhost:${BASE_BACKEND_PORT}
EOF

# Create agent-specific directories
mkdir -p uploads_agent${AGENT_ID}
mkdir -p logs/agent${AGENT_ID}

# Copy base database if it exists
if [ -f "nanodlna.db" ]; then
    cp nanodlna.db nano_dlna_agent${AGENT_ID}.db
    echo "✓ Copied base database for agent ${AGENT_ID}"
fi

echo "✓ Agent ${AGENT_ID} configured:"
echo "  - Backend port: ${BASE_BACKEND_PORT}"
echo "  - Frontend port: ${BASE_FRONTEND_PORT}"
echo "  - Database: nano_dlna_agent${AGENT_ID}.db"
echo "  - Upload dir: uploads_agent${AGENT_ID}/"
echo ""
echo "To start this agent, run: ./scripts/start_agent.sh ${AGENT_ID}"