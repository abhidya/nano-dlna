"""
Sender implementations for the Renderer Service.

This package contains classes for sending content to different types of display devices:
- DirectSender: Local display output
- DLNASender: DLNA-compatible devices
- AirPlaySender: AirPlay-compatible devices
"""

from .base import Sender
from .direct import DirectSender
from .airplay import AirPlaySender
from .hdmi import HDMISender


def __getattr__(name):
    if name == 'DLNASender':
        from .dlna import DLNASender
        return DLNASender
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    'Sender',
    'DirectSender',
    'DLNASender',
    'AirPlaySender',
    'HDMISender',
]
