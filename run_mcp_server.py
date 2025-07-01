#!/usr/bin/env python3
"""
Startup script for the nano-dlna MCP log streaming server
"""

import os
import sys
import asyncio
import logging

# Add the backend directory to Python path
backend_dir = os.path.join(os.path.dirname(__file__), 'web', 'backend')
sys.path.insert(0, backend_dir)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def main():
    """Main entry point for the MCP server"""
    try:
        # Import and run the MCP server
        from mcp_server import mcp
        
        logger.info("Starting nano-dlna MCP log streaming server...")
        logger.info("Server will be available for Claude to connect to")
        logger.info("Available tools:")
        logger.info("  - get_backend_logs: Get backend Python logs")
        logger.info("  - get_frontend_logs: Get frontend React logs") 
        logger.info("  - get_database_logs: Get database operation logs")
        logger.info("  - get_aggregated_logs: Get filtered logs from all sources")
        logger.info("  - search_logs: Search through logs for specific patterns")
        logger.info("  - tail_logs_realtime: Real-time log tailing")
        
        # Run the MCP server
        await mcp.run_stdio()
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error running MCP server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())