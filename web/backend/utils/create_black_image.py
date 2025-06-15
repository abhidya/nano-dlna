#!/usr/bin/env python3
"""
Utility to create a black image file for brightness control
"""
import os
import logging
try:
    from PIL import Image
except ImportError:
    Image = None

logger = logging.getLogger(__name__)

def create_black_image(output_path: str = None, width: int = 1920, height: int = 1080, format: str = "JPEG") -> str:
    """
    Create a black image file
    
    Args:
        output_path: Path for the output image file (default: static/black_image.jpg)
        width: Image width (default: 1920)
        height: Image height (default: 1080)
        format: Image format - JPEG or PNG (default: JPEG)
        
    Returns:
        str: Path to the created image file
    """
    if output_path is None:
        # Get the directory of this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        static_dir = os.path.join(os.path.dirname(script_dir), "static")
        os.makedirs(static_dir, exist_ok=True)
        extension = "jpg" if format.upper() == "JPEG" else "png"
        output_path = os.path.join(static_dir, f"black_image.{extension}")
    
    # Check if file already exists
    if os.path.exists(output_path):
        logger.info(f"Black image already exists at {output_path}")
        return output_path
    
    if Image is None:
        logger.warning("PIL/Pillow not found. Using fallback method...")
        return create_black_image_fallback(output_path, width, height, format)
    
    try:
        # Create a black image
        image = Image.new('RGB', (width, height), color='black')
        
        # Save the image
        if format.upper() == "JPEG":
            # For JPEG, we need to specify quality to avoid compression artifacts
            image.save(output_path, format='JPEG', quality=95, optimize=True)
        else:
            image.save(output_path, format='PNG')
        
        logger.info(f"Successfully created black image at {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error creating black image: {e}")
        raise

def create_black_image_fallback(output_path: str, width: int, height: int, format: str) -> str:
    """
    Fallback method to create a black image without PIL
    Creates a minimal valid JPEG/PNG file
    """
    logger.warning("Using fallback method to create black image")
    
    if format.upper() == "JPEG":
        # Minimal black JPEG (1x1 pixel, scaled by viewers)
        # This is a valid JPEG file structure
        black_jpeg_hex = (
            "ffd8ffe000104a46494600010101006000600000"  # JPEG header
            "ffdb004300080606070605080707070909080a0c140d0c0b0b0c1912130f141d1a1f1e1d1a1c1c20242e2720222c231c1c2837292c30313434341f27393d38323c2e333432"  # Quantization table
            "ffc0000b080001000101011100"  # Start of frame
            "ffc4001f0000010501010101010100000000000000000102030405060708090a0b"  # Huffman table
            "ffda00080101000000003f00d2cf20"  # Start of scan + compressed data
            "ffd9"  # End of image
        )
        
        with open(output_path, 'wb') as f:
            f.write(bytes.fromhex(black_jpeg_hex))
    else:
        # Minimal black PNG (1x1 pixel)
        black_png_hex = (
            "89504e470d0a1a0a"  # PNG signature
            "0000000d49484452000000010000000108020000007c41da77"  # IHDR chunk
            "0000000c4944415478da62000000000200010098dd6b41"  # IDAT chunk (black pixel)
            "0000000049454e44ae426082"  # IEND chunk
        )
        
        with open(output_path, 'wb') as f:
            f.write(bytes.fromhex(black_png_hex))
    
    logger.warning(f"Created minimal black image at {output_path}")
    return output_path

if __name__ == "__main__":
    # Test the function
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1:
        output = sys.argv[1]
    else:
        output = None
    
    path = create_black_image(output)
    print(f"Black image created at: {path}")