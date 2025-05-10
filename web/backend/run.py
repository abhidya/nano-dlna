#!/usr/bin/env python3

import uvicorn
import argparse
import logging

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the nano-dlna Dashboard API")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()
    
    # Configure logging - only if not already configured
    log_level = logging.DEBUG if args.debug else logging.INFO
    
    # Check if root logger already has handlers (configured in main.py)
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        # Only configure logging if it hasn't been configured yet
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        
        # Add a rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            'dashboard_run.log',
            maxBytes=10485760,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Run the server
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="debug" if args.debug else "info",
    )
