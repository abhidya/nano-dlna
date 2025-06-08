"""
Core module for depth map processing.
"""

from .depth_loader import DepthLoader
from .segmentation import DepthSegmenter

__all__ = ['DepthLoader', 'DepthSegmenter']
