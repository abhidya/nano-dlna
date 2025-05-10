"""
Renderer Service package initialization.

This package provides functionality for rendering scenes on different display technologies.
"""

from .renderer.base import Renderer
from .renderer.chrome import ChromeRenderer

__all__ = ['Renderer', 'ChromeRenderer']
