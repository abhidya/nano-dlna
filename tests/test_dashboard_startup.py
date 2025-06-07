import unittest
import sys
import os
import importlib
import subprocess
import time
import requests
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestDashboardStartup(unittest.TestCase):
    """Test cases for verifying dashboard components start correctly"""
    
    def test_backend_imports(self):
        """Test that all necessary backend modules can be imported without errors"""
        # Test core components
        self.assertIsNotNone(importlib.import_module("web.backend.core.device_manager"))
        self.assertIsNotNone(importlib.import_module("web.backend.core.device"))
        self.assertIsNotNone(importlib.import_module("web.backend.core.dlna_device"))
        self.assertIsNotNone(importlib.import_module("web.backend.core.config_service"))
        self.assertIsNotNone(importlib.import_module("web.backend.core.streaming_registry"))
        
        # Test services
        self.assertIsNotNone(importlib.import_module("web.backend.services.device_service"))
        self.assertIsNotNone(importlib.import_module("web.backend.services.video_service"))
        
        # Test routers
        self.assertIsNotNone(importlib.import_module("web.backend.routers.device_router"))
        self.assertIsNotNone(importlib.import_module("web.backend.routers.video_router"))
        self.assertIsNotNone(importlib.import_module("web.backend.routers.streaming_router"))
        
        # Test main app
        self.assertIsNotNone(importlib.import_module("web.backend.main"))
    
    # Removed test_get_device_service_function as the targeted function
    # in web.backend.services.device_service was removed due to being problematic.
    # Service instantiation is now handled by local dependency providers in routers.
    
    def test_get_device_manager_singleton(self):
        """Test that get_device_manager returns a singleton"""
        from web.backend.core.device_manager import get_device_manager
        
        # Get instances and verify they're the same object
        manager1 = get_device_manager()
        manager2 = get_device_manager()
        self.assertIs(manager1, manager2)
    
    @unittest.skip("Only run manually, requires available backend server")
    def test_backend_startup(self):
        """Test that backend server starts without errors"""
        # Start backend in subprocess
        backend_dir = Path(__file__).parent.parent / "web" / "backend"
        process = subprocess.Popen(
            ["python", "run.py"],
            cwd=str(backend_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=dict(os.environ, PYTHONPATH=str(Path(__file__).parent.parent))
        )
        
        # Wait for server to start
        time.sleep(3)
        
        # Check if process is still running (no startup crash)
        self.assertEqual(process.poll(), None)
        
        # Try to connect to API
        try:
            response = requests.get("http://localhost:8000/api/devices/")
            self.assertEqual(response.status_code, 200)
        finally:
            # Clean up
            process.terminate()
            process.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
