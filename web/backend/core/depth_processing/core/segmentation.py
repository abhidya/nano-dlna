#!/usr/bin/env python3
# encoding: UTF-8

import logging
import numpy as np
from typing import List, Tuple, Optional
import time

# Configure logger for this module
logger = logging.getLogger(__name__)

class DepthSegmenter:
    """Class for segmenting depth maps"""
    
    @staticmethod
    def kmeans_segmentation(
        depth_map: np.ndarray, 
        n_clusters: int = 5, 
        iterations: int = 10,
        random_state: int = 42
    ) -> Tuple[np.ndarray, List[float]]:
        """
        Segment a depth map using KMeans clustering
        
        Args:
            depth_map: Normalized depth map
            n_clusters: Number of clusters
            iterations: Maximum number of iterations
            random_state: Random seed for reproducibility
            
        Returns:
            Tuple of (segmentation mask, cluster centers)
        """
        if depth_map is None or depth_map.size == 0:
            return None, []
            
        # Reshape to 1D array for clustering
        flattened = depth_map.flatten()
        
        # Filter out non-finite values
        valid_mask = np.isfinite(flattened)
        valid_values = flattened[valid_mask]
        
        if valid_values.size == 0:
            logger.error("No valid values in depth map for clustering")
            return None, []
        
        try:
            # Try sklearn KMeans if available
            try:
                from sklearn.cluster import KMeans
                
                # Reshape for sklearn (n_samples, n_features)
                X = valid_values.reshape(-1, 1)
                
                # Run KMeans
                kmeans = KMeans(
                    n_clusters=n_clusters,
                    max_iter=iterations,
                    random_state=random_state,
                    n_init=1  # For faster execution
                )
                
                start_time = time.time()
                labels = kmeans.fit_predict(X)
                logger.debug(f"KMeans clustering completed in {time.time() - start_time:.2f} seconds")
                
                # Create the segmentation mask
                segmentation = np.zeros_like(flattened)
                segmentation[valid_mask] = labels + 1  # Add 1 to avoid 0 (background)
                
                # Reshape back to original shape
                segmentation = segmentation.reshape(depth_map.shape)
                
                # Get cluster centers (depths)
                centers = kmeans.cluster_centers_.flatten()
                
                return segmentation, sorted(centers)
                
            except ImportError:
                logger.warning("sklearn not available, using simple KMeans implementation")
                # Fall back to simple implementation
                return DepthSegmenter._simple_kmeans(
                    depth_map, n_clusters, iterations, random_state
                )
                
        except Exception as e:
            logger.error(f"Error during KMeans segmentation: {e}")
            return None, []
    
    @staticmethod
    def _simple_kmeans(
        depth_map: np.ndarray, 
        n_clusters: int = 5, 
        iterations: int = 10,
        random_state: int = 42
    ) -> Tuple[np.ndarray, List[float]]:
        """Simple KMeans implementation for fallback"""
        # Flatten the depth map
        flattened = depth_map.flatten()
        
        # Filter out non-finite values
        valid_mask = np.isfinite(flattened)
        valid_values = flattened[valid_mask]
        
        if valid_values.size == 0:
            return None, []
        
        # Initialize random centers
        np.random.seed(random_state)
        min_val, max_val = np.min(valid_values), np.max(valid_values)
        centers = np.linspace(min_val, max_val, n_clusters)
        
        # Run simple KMeans
        start_time = time.time()
        for _ in range(iterations):
            # Assign each point to the nearest center
            labels = np.zeros(valid_values.shape, dtype=int)
            for i in range(valid_values.size):
                distances = np.abs(valid_values[i] - centers)
                labels[i] = np.argmin(distances)
            
            # Update centers
            for j in range(n_clusters):
                if np.sum(labels == j) > 0:
                    centers[j] = np.mean(valid_values[labels == j])
        
        logger.debug(f"Simple KMeans completed in {time.time() - start_time:.2f} seconds")
        
        # Create the segmentation mask
        segmentation = np.zeros_like(flattened)
        segmentation[valid_mask] = labels + 1  # Add 1 to avoid 0 (background)
        
        # Reshape back to original shape
        segmentation = segmentation.reshape(depth_map.shape)
        
        return segmentation, sorted(centers)
    
    @staticmethod
    def threshold_segmentation(
        depth_map: np.ndarray, 
        thresholds: List[float]
    ) -> np.ndarray:
        """
        Segment a depth map using thresholds
        
        Args:
            depth_map: Normalized depth map
            thresholds: List of threshold values (0-1)
            
        Returns:
            Segmentation mask
        """
        if depth_map is None or depth_map.size == 0:
            return None
            
        if not thresholds:
            return np.zeros_like(depth_map, dtype=int)
            
        # Sort thresholds
        thresholds = sorted(thresholds)
        
        # Create segmentation mask
        segmentation = np.zeros_like(depth_map, dtype=int)
        
        # Apply thresholds
        for i, threshold in enumerate(thresholds):
            mask = depth_map >= threshold
            segmentation[mask] = i + 1  # Segment ID (1-based)
        
        return segmentation
    
    @staticmethod
    def depth_band_segmentation(
        depth_map: np.ndarray, 
        n_bands: int = 5
    ) -> np.ndarray:
        """
        Segment a depth map into equal-width bands
        
        Args:
            depth_map: Normalized depth map
            n_bands: Number of bands
            
        Returns:
            Segmentation mask
        """
        if depth_map is None or depth_map.size == 0:
            return None
            
        # Create equal-width bands
        thresholds = np.linspace(0, 1, n_bands + 1)[1:-1]  # Exclude 0 and 1
        
        return DepthSegmenter.threshold_segmentation(depth_map, thresholds)
    
    @staticmethod
    def extract_binary_mask(
        segmentation: np.ndarray, 
        segment_id: int
    ) -> np.ndarray:
        """
        Extract a binary mask for a specific segment
        
        Args:
            segmentation: Segmentation mask
            segment_id: Segment ID to extract
            
        Returns:
            Binary mask
        """
        if segmentation is None:
            return None
            
        binary_mask = (segmentation == segment_id).astype(np.uint8) * 255
        return binary_mask
    
    @staticmethod
    def clean_binary_mask(
        mask: np.ndarray, 
        min_area: int = 100, 
        kernel_size: int = 3
    ) -> np.ndarray:
        """
        Clean a binary mask using morphological operations and area filtering
        
        Args:
            mask: Binary mask
            min_area: Minimum connected component area
            kernel_size: Size of the morphological kernel
            
        Returns:
            Cleaned binary mask
        """
        if mask is None:
            return None
            
        try:
            # Try using OpenCV
            import cv2
            
            # Convert to proper binary mask (0 or 255)
            binary = np.where(mask > 127, 255, 0).astype(np.uint8)
            
            # Create a kernel for morphological operations
            kernel = np.ones((kernel_size, kernel_size), np.uint8)
            
            # Apply morphological closing (dilation followed by erosion)
            closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            # Remove small components
            if min_area > 0:
                # Find connected components
                num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(closed, 8, cv2.CV_32S)
                
                # Create a new mask keeping only components above min_area
                cleaned = np.zeros_like(binary)
                for i in range(1, num_labels):  # Skip background
                    if stats[i, cv2.CC_STAT_AREA] >= min_area:
                        cleaned[labels == i] = 255
                
                return cleaned
            else:
                return closed
                
        except ImportError:
            logger.warning("OpenCV not available, returning original mask")
            return mask 