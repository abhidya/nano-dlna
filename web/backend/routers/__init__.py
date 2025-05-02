"""
Router package initialization.
This file makes the routers directory a proper Python package.
"""

from .device_router import router as device_router
from .video_router import router as video_router
from .streaming_router import router as streaming_router

__all__ = [
    'device_router',
    'video_router',
    'streaming_router',
]
