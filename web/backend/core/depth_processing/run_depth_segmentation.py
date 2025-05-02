#!/usr/bin/env python3
# encoding: UTF-8

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """
    Run the depth segmentation Streamlit app
    """
    try:
        # Try to import streamlit
        import streamlit
        logger.info("Streamlit is installed")
    except ImportError:
        logger.warning("Streamlit is not installed. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
            logger.info("Streamlit installed successfully")
        except Exception as e:
            logger.error(f"Failed to install Streamlit: {e}")
            print("Please install Streamlit manually: pip install streamlit")
            sys.exit(1)
    
    try:
        # Check for numpy
        import numpy
        logger.info("NumPy is installed")
    except ImportError:
        logger.warning("NumPy is not installed. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy"])
            logger.info("NumPy installed successfully")
        except Exception as e:
            logger.error(f"Failed to install NumPy: {e}")
            print("Please install NumPy manually: pip install numpy")
            sys.exit(1)
    
    try:
        # Check for PIL
        from PIL import Image
        logger.info("PIL is installed")
    except ImportError:
        logger.warning("PIL is not installed. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
            logger.info("PIL installed successfully")
        except Exception as e:
            logger.error(f"Failed to install PIL: {e}")
            print("Please install PIL manually: pip install pillow")
            sys.exit(1)
    
    try:
        # Try to import OpenCV (optional but recommended)
        import cv2
        logger.info("OpenCV is installed")
    except ImportError:
        logger.warning("OpenCV is not installed. Some features may not work properly.")
        print("For full functionality, install OpenCV: pip install opencv-python")
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the Streamlit app
    app_path = os.path.join(script_dir, "ui", "depth_segmentation_app.py")
    
    # Check if the app exists
    if not os.path.exists(app_path):
        logger.error(f"App not found at {app_path}")
        sys.exit(1)
    
    # Run the Streamlit app
    logger.info(f"Running Streamlit app: {app_path}")
    cmd = [sys.executable, "-m", "streamlit", "run", app_path]
    
    print("\n" + "=" * 80)
    print(f"Starting Depth Segmentation Tool...")
    print("=" * 80 + "\n")
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nStopping Depth Segmentation Tool...")
    except Exception as e:
        logger.error(f"Error running Streamlit app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 