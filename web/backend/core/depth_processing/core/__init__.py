"""
Core module for depth map processing.
"""

from core.depth_processing.core.depth_loader import DepthLoader
from core.depth_processing.core.segmentation import DepthSegmenter

__all__ = ['DepthLoader', 'DepthSegmenter'] 