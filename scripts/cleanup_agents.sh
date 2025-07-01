#!/bin/bash
# Cleanup all agent environments

echo "Cleaning up all agents..."
echo "========================"

# Stop all agents
for i in 1 2 3 4 5; do
    if [ -f ".agent${i}.backend.pid" ] || [ -f ".agent${i}.frontend.pid" ]; then
        echo "Stopping agent ${i}..."
        ./scripts/stop_agent.sh ${i}
    fi
done

# Remove databases
echo ""
echo "Removing agent databases..."
rm -f nano_dlna_agent*.db

# Remove upload directories
echo "Removing upload directories..."
rm -rf uploads_agent*

# Remove log directories
echo "Removing log directories..."
rm -rf logs/agent*

# Remove environment files
echo "Removing environment files..."
rm -f .env.agent*

# Remove PID files (if any remain)
rm -f .agent*.pid

echo ""
echo "✓ Cleanup complete"