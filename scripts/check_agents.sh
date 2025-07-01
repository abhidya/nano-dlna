#!/bin/bash
# Check status of all agents

echo "Agent Status Check"
echo "=================="
echo ""

for i in 1 2 3 4 5; do
    BACKEND_PORT=$((8000 + i))
    FRONTEND_PORT=$((3000 + i))
    
    # Check if agent is configured
    if [ ! -f ".env.agent${i}" ]; then
        continue
    fi
    
    echo "Agent ${i}:"
    
    # Check backend
    if curl -s http://localhost:${BACKEND_PORT}/health > /dev/null 2>&1; then
        echo "  ✓ Backend:  http://localhost:${BACKEND_PORT}"
    else
        echo "  ✗ Backend:  Not running (port ${BACKEND_PORT})"
    fi
    
    # Check frontend
    if curl -s http://localhost:${FRONTEND_PORT} > /dev/null 2>&1; then
        echo "  ✓ Frontend: http://localhost:${FRONTEND_PORT}"
    else
        echo "  ✗ Frontend: Not running (port ${FRONTEND_PORT})"
    fi
    
    # Check database
    if [ -f "nano_dlna_agent${i}.db" ]; then
        SIZE=$(du -h nano_dlna_agent${i}.db | cut -f1)
        echo "  ✓ Database: nano_dlna_agent${i}.db (${SIZE})"
    else
        echo "  ✗ Database: Not found"
    fi
    
    echo ""
done

# Show resource usage
echo "Resource Usage:"
echo "==============="
echo "Backend processes:"
ps aux | grep -E "python.*app.py" | grep -v grep | awk '{print "  PID:", $2, "CPU:", $3"%", "MEM:", $4"%"}'
echo ""
echo "Frontend processes:"
ps aux | grep -E "node.*react-scripts" | grep -v grep | awk '{print "  PID:", $2, "CPU:", $3"%", "MEM:", $4"%"}'