#!/usr/bin/env python3
# encoding: UTF-8

import logging
import numpy as np
from typing import Optional, List, Tuple
import io

# Configure logger for this module
logger = logging.getLogger(__name__)

class DepthVisualizer:
    """Class for visualizing depth maps and segmentation results"""
    
    @staticmethod
    def create_colormap(n_colors: int = 10) -> np.ndarray:
        """
        Create a colormap for visualization
        
        Args:
            n_colors: Number of colors in the colormap
            
        Returns:
            Numpy array of shape (n_colors, 3) with RGB colors (0-255)
        """
        try:
            # Try using matplotlib
            import matplotlib.pyplot as plt
            import matplotlib.colors as mcolors
            
            # Create a colormap
            cmap = plt.cm.get_cmap('tab10', n_colors)
            
            # Convert to RGB array
            colors = []
            for i in range(n_colors):
                color = cmap(i)[:3]  # RGB tuple
                colors.append([int(c * 255) for c in color])
            
            return np.array(colors)
        except ImportError:
            # Fallback to manual colormap
            logger.warning("matplotlib not available, using fallback colormap")
            
            # Create a simple colormap with distinct colors
            colors = [
                [255, 0, 0],     # Red
                [0, 255, 0],     # Green
                [0, 0, 255],     # Blue
                [255, 255, 0],   # Yellow
                [255, 0, 255],   # Magenta
                [0, 255, 255],   # Cyan
                [255, 128, 0],   # Orange
                [128, 0, 255],   # Purple
                [0, 128, 255],   # Light blue
                [255, 128, 128], # Pink
            ]
            
            # Repeat colors if needed
            while len(colors) < n_colors:
                colors.extend(colors[:n_colors - len(colors)])
            
            return np.array(colors[:n_colors])
    
    @staticmethod
    def visualize_segmentation(
        segmentation: np.ndarray,
        colormap: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Visualize a segmentation mask with colors
        
        Args:
            segmentation: Segmentation mask (integer labels)
            colormap: Optional colormap to use
            
        Returns:
            RGB visualization (uint8)
        """
        if segmentation is None:
            return None
            
        # Count the number of unique segments
        unique_segments = np.unique(segmentation)
        n_segments = len(unique_segments)
        
        # Create or adjust colormap
        if colormap is None:
            colormap = DepthVisualizer.create_colormap(n_segments)
        elif len(colormap) < n_segments:
            # Extend colormap
            extended = np.zeros((n_segments, 3), dtype=np.uint8)
            extended[:len(colormap)] = colormap
            # Fill remaining with random colors
            for i in range(len(colormap), n_segments):
                extended[i] = np.random.randint(0, 256, 3)
            colormap = extended
        
        # Create an RGB image
        height, width = segmentation.shape
        visualization = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Assign colors to segments
        for i, segment_id in enumerate(unique_segments):
            mask = segmentation == segment_id
            if np.any(mask):
                # Use the colormap to color each segment
                color = colormap[min(i, len(colormap) - 1)]
                visualization[mask] = color
        
        return visualization
    
    @staticmethod
    def create_overlay(
        image: np.ndarray,
        segmentation: np.ndarray,
        alpha: float = 0.5,
        colormap: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Create an overlay of the segmentation on the original image
        
        Args:
            image: Original image (grayscale or RGB)
            segmentation: Segmentation mask (integer labels)
            alpha: Opacity of the overlay (0-1)
            colormap: Optional colormap to use
            
        Returns:
            RGB overlay (uint8)
        """
        if image is None or segmentation is None:
            return None
            
        # Ensure the image is RGB
        if len(image.shape) == 2:
            # Convert grayscale to RGB
            rgb_image = np.stack([image] * 3, axis=2)
        else:
            rgb_image = image.copy()
            
        # Visualize the segmentation
        seg_vis = DepthVisualizer.visualize_segmentation(segmentation, colormap)
        
        # Blend the segmentation with the image
        overlay = (alpha * seg_vis + (1 - alpha) * rgb_image).astype(np.uint8)
        
        return overlay
    
    @staticmethod
    def create_comparison_image(
        original: np.ndarray,
        segmentation: np.ndarray,
        colormap: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Create a side-by-side comparison image
        
        Args:
            original: Original depth map (normalized)
            segmentation: Segmentation mask (integer labels)
            colormap: Optional colormap for segmentation
            
        Returns:
            RGB comparison image (uint8)
        """
        if original is None or segmentation is None:
            return None
            
        # Convert original to grayscale visualization
        if original.max() <= 1.0:
            # Normalize to 0-255
            orig_vis = (original * 255).astype(np.uint8)
        else:
            orig_vis = original.astype(np.uint8)
            
        # Convert to RGB
        if len(orig_vis.shape) == 2:
            orig_rgb = np.stack([orig_vis] * 3, axis=2)
        else:
            orig_rgb = orig_vis
            
        # Visualize segmentation
        seg_vis = DepthVisualizer.visualize_segmentation(segmentation, colormap)
        
        # Create side-by-side image
        height, width = original.shape[:2]
        comparison = np.zeros((height, width * 2, 3), dtype=np.uint8)
        comparison[:, :width] = orig_rgb
        comparison[:, width:] = seg_vis
        
        return comparison
    
    @staticmethod
    def export_image(
        image: np.ndarray, 
        format: str = 'png'
    ) -> bytes:
        """
        Export an image as bytes
        
        Args:
            image: Image to export (uint8)
            format: Image format ('png', 'jpg')
            
        Returns:
            Image bytes
        """
        if image is None:
            return None
            
        try:
            # Use PIL for image export
            from PIL import Image
            
            # Convert to PIL Image
            pil_image = Image.fromarray(image)
            
            # Save to bytes
            output = io.BytesIO()
            pil_image.save(output, format=format)
            return output.getvalue()
            
        except ImportError:
            logger.warning("PIL not available, trying OpenCV")
            
            try:
                # Use OpenCV as fallback
                import cv2
                
                # Set image format
                if format.lower() == 'png':
                    ext = '.png'
                    params = [cv2.IMWRITE_PNG_COMPRESSION, 9]
                else:
                    ext = '.jpg'
                    params = [cv2.IMWRITE_JPEG_QUALITY, 90]
                
                # Encode image
                success, buffer = cv2.imencode(ext, image, params)
                if success:
                    return buffer.tobytes()
                else:
                    logger.error(f"Failed to encode image as {format}")
                    return None
                    
            except ImportError:
                logger.error("Neither PIL nor OpenCV available for image export")
                return None 