import unittest
import sys
import os
import subprocess
import time
import signal
import requests
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestRunDashboard(unittest.TestCase):
    """Test cases for verifying run_dashboard.sh properly starts components"""
    
    @unittest.skip("Run manually, starts actual servers")
    def test_run_dashboard_script(self):
        """Test that run_dashboard.sh starts all necessary components"""
        root_dir = Path(__file__).parent.parent
        
        # Run the dashboard script in subprocess
        process = subprocess.Popen(
            ["./run_dashboard.sh"],
            cwd=str(root_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )
        
        try:
            # Wait for servers to start
            time.sleep(10)
            
            # Check if process is still running
            self.assertIsNone(process.poll(), "Dashboard process terminated unexpectedly")
            
            # Test API endpoints
            backend_running = False
            frontend_running = False
            
            # Try to connect to backend API
            try:
                response = requests.get("http://localhost:8000/api/devices/")
                if response.status_code == 200:
                    backend_running = True
                    print("Backend API is responsive")
            except requests.RequestException:
                print("Backend API is not responding")
            
            # Try to connect to frontend
            try:
                response = requests.get("http://localhost:3000/")
                if response.status_code == 200:
                    frontend_running = True
                    print("Frontend is responsive")
            except requests.RequestException:
                print("Frontend is not responding")
            
            # Assert components are running
            self.assertTrue(backend_running, "Backend server is not running")
            self.assertTrue(frontend_running, "Frontend server is not running")
            
        finally:
            # Clean up - terminate the script which should clean up all processes
            process.terminate()
            process.wait(timeout=5)
            
            # Make sure everything is really stopped
            subprocess.run(["./stop_dashboard.sh"], cwd=str(root_dir))
    
    def test_device_discovery(self):
        """Test device discovery functionality"""
        from web.backend.core.device_manager import get_device_manager
        
        # Get DeviceManager instance
        device_manager = get_device_manager()
        
        # Test discovering devices (timeout for quick test)
        devices = device_manager._discover_dlna_devices(timeout=1.0)
        
        # Just verify the function runs without errors (actual results depend on network)
        print(f"Discovered {len(devices)} DLNA devices")

    def test_video_loading(self):
        """Test video loading from configuration"""
        from web.backend.core.device_manager import get_device_manager
        from web.backend.core.config_service import ConfigService
        
        # Get instances
        device_manager = get_device_manager()
        config_service = ConfigService.get_instance()
        
        # Test loading config (check if my_device_config.json exists)
        config_file = Path(__file__).parent.parent / "my_device_config.json"
        if config_file.exists():
            # Load config and verify it doesn't raise exceptions
            device_names = config_service.load_configs_from_file(str(config_file))
            print(f"Loaded {len(device_names)} device configurations")
        else:
            print("my_device_config.json not found, skipping test")


if __name__ == "__main__":
    unittest.main() 