#!/usr/bin/env python3
# encoding: UTF-8

import os
import sys
import numpy as np
from PIL import Image
import tempfile
import logging
import io

# Add parent directories to the Python path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, parent_dir)

try:
    import streamlit as st
    from core.depth_processing import DepthLoader, DepthSegmenter, DepthVisualizer
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please install Streamlit: pip install streamlit")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    st.set_page_config(
        page_title="Depth Map Segmentation Tool",
        page_icon="🎭",
        layout="wide"
    )
    
    st.title("Depth Map Segmentation Tool")
    st.markdown("""
    Upload a depth map image and segment it into distinct surface masks.
    Supports PNG, JPEG, TIFF, and EXR files.
    """)
    
    # Sidebar for controls
    with st.sidebar:
        st.header("Segmentation Controls")
        
        # Segmentation method
        method = st.selectbox(
            "Segmentation Method",
            ["KMeans Clustering", "Depth Thresholds", "Equal Depth Bands"]
        )
        
        if method == "KMeans Clustering":
            n_clusters = st.slider("Number of Clusters", 2, 10, 5)
        elif method == "Depth Thresholds":
            # Custom thresholds
            st.markdown("#### Custom Thresholds (0-1)")
            thresholds = []
            for i in range(1, 5):  # Allow up to 4 thresholds
                threshold = st.slider(f"Threshold {i}", 0.0, 1.0, i * 0.2, 0.01)
                thresholds.append(threshold)
                
            # Option to add more thresholds
            if st.checkbox(f"Add more thresholds", False):
                for i in range(5, 9):  # Allow up to 8 thresholds total
                    threshold = st.slider(f"Threshold {i}", 0.0, 1.0, i * 0.1, 0.01)
                    thresholds.append(threshold)
                    
            # Remove duplicates and sort
            thresholds = sorted(list(set(thresholds)))
            st.write(f"Thresholds: {[round(t, 2) for t in thresholds]}")
            
        elif method == "Equal Depth Bands":
            n_bands = st.slider("Number of Bands", 2, 10, 5)
        
        # Mask cleaning
        st.markdown("#### Mask Cleaning")
        clean_masks = st.checkbox("Clean masks (remove noise)", True)
        
        if clean_masks:
            min_area = st.slider("Minimum area (pixels)", 10, 1000, 100)
            kernel_size = st.slider("Morphological kernel size", 1, 15, 3, 2)
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload a depth map (PNG, JPEG, TIFF, EXR)",
        type=["png", "jpg", "jpeg", "tif", "tiff", "exr"]
    )
    
    if uploaded_file is not None:
        # Create columns for displaying images
        col1, col2 = st.columns(2)
        
        # Save the uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix="." + uploaded_file.name.split(".")[-1]) as temp:
            temp.write(uploaded_file.getvalue())
            temp_path = temp.name
        
        try:
            # Load the depth map
            depth_map = DepthLoader.load_depth_map(temp_path)
            
            if depth_map is None:
                st.error("Failed to load depth map. Ensure the file is valid.")
                return
            
            # Normalize the depth map
            normalized = DepthLoader.normalize_depth_map(depth_map)
            
            if normalized is None:
                st.error("Failed to normalize depth map. Check for invalid values.")
                return
            
            # Visualize the normalized depth map
            visualization = DepthLoader.visualize_depth_map(normalized)
            
            # Display the depth map
            with col1:
                st.subheader("Original Depth Map")
                st.image(visualization, use_column_width=True)
                
                # Show depth map stats
                st.markdown(f"**Depth Map Information:**")
                st.markdown(f"- Shape: {depth_map.shape}")
                st.markdown(f"- Original range: [{depth_map.min():.4f}, {depth_map.max():.4f}]")
                st.markdown(f"- Data type: {depth_map.dtype}")
            
            # Segment the depth map
            segmentation = None
            
            if method == "KMeans Clustering":
                # KMeans segmentation
                segmentation, centers = DepthSegmenter.kmeans_segmentation(
                    normalized, n_clusters=n_clusters
                )
                
                # Display cluster centers
                with col1:
                    st.markdown("**Cluster Centers (Depth Values):**")
                    for i, center in enumerate(centers):
                        st.markdown(f"- Cluster {i+1}: {center:.4f}")
                
            elif method == "Depth Thresholds":
                # Threshold segmentation
                segmentation = DepthSegmenter.threshold_segmentation(
                    normalized, thresholds=thresholds
                )
                
            elif method == "Equal Depth Bands":
                # Depth band segmentation
                segmentation = DepthSegmenter.depth_band_segmentation(
                    normalized, n_bands=n_bands
                )
            
            if segmentation is None:
                st.error("Segmentation failed. Try different parameters.")
                return
            
            # Visualize the segmentation
            segment_vis = DepthVisualizer.visualize_segmentation(segmentation)
            
            # Display the segmentation
            with col2:
                st.subheader("Segmentation Result")
                st.image(segment_vis, use_column_width=True)
                
                # Count unique segments
                unique_segments = np.unique(segmentation)
                st.markdown(f"**Found {len(unique_segments)} segments**")
            
            # Create a header for binary masks
            st.header("Binary Masks")
            
            # Create a grid of binary masks
            mask_cols = st.columns(min(4, len(unique_segments)))
            
            # Keep track of selected masks
            selected_masks = []
            
            # Create a binary mask for each segment
            for i, segment_id in enumerate(unique_segments):
                # Skip background (0)
                if segment_id == 0:
                    continue
                    
                # Extract binary mask
                binary_mask = DepthSegmenter.extract_binary_mask(segmentation, segment_id)
                
                # Clean the mask if requested
                if clean_masks:
                    binary_mask = DepthSegmenter.clean_binary_mask(
                        binary_mask, min_area=min_area, kernel_size=kernel_size
                    )
                
                # Display the mask
                col_idx = (i - 1) % len(mask_cols)
                with mask_cols[col_idx]:
                    st.image(binary_mask, caption=f"Segment {segment_id}")
                    
                    # Add a checkbox to select this mask
                    if st.checkbox(f"Select Segment {segment_id}", value=True):
                        selected_masks.append(segment_id)
            
            # Export selected masks
            if selected_masks:
                st.header("Export Selected Masks")
                
                # Create a ZIP file with the masks
                if st.button("Export Selected Masks as ZIP"):
                    # Create a ZIP file
                    import zipfile
                    zip_buffer = io.BytesIO()
                    
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for segment_id in selected_masks:
                            # Extract binary mask
                            binary_mask = DepthSegmenter.extract_binary_mask(
                                segmentation, segment_id
                            )
                            
                            # Clean the mask if requested
                            if clean_masks:
                                binary_mask = DepthSegmenter.clean_binary_mask(
                                    binary_mask, min_area=min_area, kernel_size=kernel_size
                                )
                            
                            # Convert to PIL Image
                            mask_image = Image.fromarray(binary_mask)
                            
                            # Save to bytes
                            mask_bytes = io.BytesIO()
                            mask_image.save(mask_bytes, format="PNG")
                            
                            # Add to ZIP
                            zip_file.writestr(f"mask_{segment_id}.png", mask_bytes.getvalue())
                    
                    # Offer the ZIP for download
                    zip_buffer.seek(0)
                    
                    # Get base filename
                    base_name = os.path.splitext(uploaded_file.name)[0]
                    
                    st.download_button(
                        "Download Masks ZIP",
                        data=zip_buffer,
                        file_name=f"{base_name}_masks.zip",
                        mime="application/zip"
                    )
            
        except Exception as e:
            logger.error(f"Error processing depth map: {e}", exc_info=True)
            st.error(f"Error processing depth map: {str(e)}")
        
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except:
                pass

if __name__ == "__main__":
    main() 