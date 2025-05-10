"""
Renderer package initialization.

This package provides renderer implementations for the Renderer Service.
"""

from .base import Renderer
from .chrome import ChromeRenderer

__all__ = ['Renderer', 'ChromeRenderer']
