"""
Test script to verify imports work correctly.
"""

import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    print("Attempting to import from core.streaming_registry...")
    from core.streaming_registry import StreamingSessionRegistry
    print("✅ Successfully imported StreamingSessionRegistry from core.streaming_registry")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Trace:")
    import traceback
    traceback.print_exc()

try:
    print("\nAttempting to import from routers...")
    from routers import device_router, video_router, streaming_router
    print("✅ Successfully imported routers")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Trace:")
    import traceback
    traceback.print_exc()

print("\nImport test complete.") 