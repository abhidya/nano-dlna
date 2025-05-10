#!/usr/bin/env python3

"""
This module serves as an entry point for the application.
It imports the FastAPI app from the main module and can be run directly.
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the FastAPI app from the main module
from main import app

# This allows the file to be run directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
