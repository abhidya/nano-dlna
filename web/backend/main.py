import logging
import os
import sys
import traceback

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from database.database import init_db, get_db
from routers import device_router, video_router, streaming_router, renderer_router, overlay_router
from core.device_manager import DeviceManager
from core.streaming_registry import StreamingSessionRegistry
from core.twisted_streaming import get_instance as get_twisted_streaming
from core.streaming_service import get_streaming_service

# Configure logging
import logging.handlers

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create handlers
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create a rotating file handler for dashboard_run.log
file_handler = logging.handlers.RotatingFileHandler(
    'dashboard_run.log',
    maxBytes=10485760,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)

# Create formatters and add them to handlers
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
formatter = logging.Formatter(log_format)
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Set up root logger to use our configuration
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)
root_logger.addHandler(console_handler)
root_logger.addHandler(file_handler)

# Create FastAPI app
app = FastAPI(
    title="nano-dlna Dashboard",
    description="Web dashboard for managing DLNA and Transcreen projectors",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with /api prefix
app.include_router(device_router, prefix="/api")
app.include_router(video_router, prefix="/api")
app.include_router(streaming_router, prefix="/api")
app.include_router(renderer_router, prefix="/api")  # Add the renderer router
app.include_router(overlay_router)  # Overlay router already has /api prefix

# Try to include depth_router if dependencies are available
try:
    # First check if numpy is available without importing anything from depth_processing
    import numpy
    import cv2
    import PIL
    import sklearn
    # Only if all dependencies are available, import the depth_router
    from routers import depth_router
    app.include_router(depth_router, prefix="/api")  # Add the depth router
    logger.info("Depth processing module loaded successfully")
except ImportError as e:
    logger.warning(f"Depth processing module not loaded due to missing dependencies: {e}")
    logger.warning("Install required packages with: pip install numpy opencv-python pillow scikit-learn")

# Root endpoint
@app.get("/")
async def root():
    return RedirectResponse(url="/docs")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Global service variables (initialized in startup)
device_manager = None
streaming_service = None
streaming_registry = None
renderer_service = None

# Mount static files for the frontend
@app.on_event("startup")
async def startup_event():
    global device_manager, streaming_service, streaming_registry, renderer_service
    
    logger.info("Starting nano-dlna Dashboard API")
    
    # Initialize services here to prevent multiple executions during imports  
    device_manager = DeviceManager()
    # Stop any existing streaming servers to prevent port conflicts
    streaming_service = get_twisted_streaming()
    streaming_service.stop_server()  # Explicitly stop any existing servers
    streaming_registry = StreamingSessionRegistry.get_instance()
    
    # Inject device_manager into the StreamingService singleton
    overlay_streaming_service = get_streaming_service()
    overlay_streaming_service.set_device_manager(device_manager)

    # Get or create the renderer service
    try:
        from core.renderer_service.service import RendererService
        from routers.renderer_router import get_renderer_service
        renderer_service = get_renderer_service()
        logger.info("Renderer Service initialized successfully")
    except Exception as e:
        logger.warning(f"Renderer Service initialization failed: {e}")
        renderer_service = None
    
    # Initialize the database
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
    
    # Load devices from configuration files
    try:
        # First, check for configuration files in the project root
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_files = [
            os.path.join(root_dir, "tramscreem+device_config.json"),
            os.path.join(os.path.dirname(__file__), "my_device_config.json"),
            os.path.join(os.path.dirname(__file__), "tramscreem+device_config.json"),
            os.path.join(root_dir, "my_device_config.json"),
        ]
        
        # Remove duplicates
        config_files = list(set(config_files))
        
        # Log all potential config files for debugging
        logger.info(f"Checking for config files: {config_files}")
        
        loaded = False
        for config_file in config_files:
            if os.path.exists(config_file):
                logger.info(f"Loading devices from {config_file}")
                try:
                    # Get the database session
                    db = next(get_db())
                    
                    # Create a device service instance
                    from services.device_service import DeviceService
                    device_service = DeviceService(db, device_manager)
                    
                    # Load devices from the config file
                    devices = device_service.load_devices_from_config(config_file)
                    logger.info(f"Loaded {len(devices)} devices from {config_file}")
                    
                    loaded = True
                except Exception as e:
                    logger.error(f"Error loading devices from {config_file}: {e}")
        
        if not loaded:
            logger.warning("No configuration files found or loaded. Using sample data.")
            
        # Store the device_service in the device_manager for status updates
        device_manager.device_service = device_service
        
        # Start device discovery to find devices on the network
        # This will automatically play videos on devices when they are discovered
        # based on the configuration files loaded above
        logger.info("Starting device discovery")
        device_manager.start_discovery()
        
        # Log the number of devices in the device manager
        logger.info(f"Device manager has {len(device_manager.devices)} devices")
        
        # Log all devices in the device manager
        for device_name, device in device_manager.devices.items():
            logger.info(f"Device in manager: {device_name}, type: {device.type}, hostname: {device.hostname}, action_url: {device.action_url}")

        # Start the renderer service's streaming server
        if renderer_service:
            try:
                renderer_service.start_streaming_server()
                logger.info("RendererService streaming server started.")
            except Exception as e:
                logger.error(f"Failed to start RendererService streaming server: {e}")
        
    except Exception as e:
        logger.error(f"Error loading devices from config: {e}")
        logger.error(f"Exception details: {traceback.format_exc()}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down nano-dlna Dashboard API")
    
    # Stop streaming session monitoring
    if streaming_registry:
        streaming_registry.stop_monitoring()
    
    # Stop all streaming servers
    if streaming_service:
        streaming_service.stop_server()
    
    # Stop device discovery
    if device_manager:
        device_manager.stop_discovery()
    
    # Stop renderer service if it's running
    if renderer_service:
        try:
            renderer_service.shutdown()
            logger.info("Renderer Service stopped")
        except Exception as e:
            logger.error(f"Error stopping Renderer Service: {e}")

# Serve the frontend if the directory exists
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "build")
if os.path.exists(frontend_dir):
    app.mount("/app", StaticFiles(directory=frontend_dir, html=True), name="frontend")

# Serve static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
    
app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.mount("/backend-static", StaticFiles(directory=static_dir), name="backend-static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
