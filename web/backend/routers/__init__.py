"""
Router package initialization.
This file makes the routers directory a proper Python package.
"""

from .device_router import router as device_router
from .video_router import router as video_router
from .streaming_router import router as streaming_router
from .renderer_router import router as renderer_router
try:
    from .depth_router import router as depth_router
    __all__ = [
        'device_router',
        'video_router',
        'streaming_router',
        'renderer_router',
        'depth_router',
    ]
except ImportError:
    # Depth router is optional and may not be available if dependencies are missing
    __all__ = [
        'device_router',
        'video_router',
        'streaming_router',
        'renderer_router',
    ]
