"""
Unified discovery system for multiple casting methods.
Supports DLNA, AirPlay, and overlay casting with a plugin architecture.
"""

from .discovery_manager import DiscoveryManager
from .base import DiscoveryBackend, Device, CastingMethod

__all__ = [
    'DiscoveryManager',
    'DiscoveryBackend', 
    'Device',
    'CastingMethod'
]