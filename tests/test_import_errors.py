import unittest
import os
import sys
import importlib
import pkgutil
import inspect
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestImportErrors(unittest.TestCase):
    """Test that all modules can be imported without errors"""
    
    def test_nanodlna_imports(self):
        """Test importing nanodlna core modules"""
        # Core nanodlna package
        import nanodlna
        self.assertIsNotNone(nanodlna)
        
        # Import submodules
        import nanodlna.cli
        import nanodlna.dlna
        
        # Verify they're properly loaded
        self.assertIsNotNone(nanodlna.cli)
        self.assertIsNotNone(nanodlna.dlna)
        
        # Test functions exist
        self.assertTrue(hasattr(nanodlna, 'discover_devices'))
        self.assertTrue(hasattr(nanodlna, 'send_video'))
    
    def test_backend_imports(self):
        """Test importing backend modules"""
        # Import backend core modules
        from web.backend.core import device_manager
        from web.backend.core import device
        from web.backend.core import dlna_device
        from web.backend.core import config_service
        from web.backend.core import streaming_registry
        
        # Import backend services
        from web.backend.services import device_service
        from web.backend.services import video_service
        
        # Import models
        from web.backend.models import device as device_model
        from web.backend.models import video as video_model
        
        # Import routers
        from web.backend.routers import device_router
        from web.backend.routers import video_router
        
        # Test if get_device_service exists
        self.assertTrue(hasattr(device_service, 'get_device_service'))
        
        # Test streaming router imports streaming_registry without error
        from web.backend.routers import streaming_router
    
    def test_critical_functions(self):
        """Test critical functions exist and have correct signatures"""
        # Import modules
        from web.backend.services import device_service
        from web.backend.core import device_manager
        
        # Test get_device_service
        self.assertTrue(hasattr(device_service, 'get_device_service'))
        get_device_service = getattr(device_service, 'get_device_service')
        sig = inspect.signature(get_device_service)
        self.assertIn('db', sig.parameters)
        
        # Test get_device_manager
        self.assertTrue(hasattr(device_manager, 'get_device_manager'))
        get_device_manager = getattr(device_manager, 'get_device_manager')
        sig = inspect.signature(get_device_manager)
        # Should have no required parameters
        for param in sig.parameters.values():
            self.assertNotEqual(param.default, inspect.Parameter.empty)
    
    def test_main_app_imports(self):
        """Test importing the main app module"""
        try:
            # Import the main FastAPI app
            from web.backend.main import app
            # Verify it's a FastAPI instance
            from fastapi import FastAPI
            self.assertIsInstance(app, FastAPI)
        except ImportError as e:
            self.fail(f"Failed to import main app: {e}")
    
    def test_recursive_module_imports(self):
        """Recursively test importing all modules"""
        failed_imports = []
        
        # Define the root paths to scan
        root_paths = [
            Path('nanodlna'),
            Path('web/backend')
        ]
        
        # Function to recursively import all modules
        def import_all_modules(package_path, package_name):
            for _, name, is_pkg in pkgutil.iter_modules([str(package_path)]):
                full_name = f"{package_name}.{name}" if package_name else name
                try:
                    module = importlib.import_module(full_name)
                    self.assertIsNotNone(module)
                    if is_pkg:
                        import_all_modules(package_path / name, full_name)
                except ImportError as e:
                    failed_imports.append((full_name, str(e)))
        
        # Scan each root path
        for root_path in root_paths:
            if root_path.exists():
                import_all_modules(root_path, root_path.name)
        
        # Report any failed imports
        if failed_imports:
            for module, error in failed_imports:
                print(f"Failed to import {module}: {error}")
            self.fail(f"Failed to import {len(failed_imports)} modules")
    
    def test_circular_imports(self):
        """Test for known circular import issues"""
        # Problem modules identified from error logs
        modules_to_test = [
            'web.backend.routers.streaming_router',
            'web.backend.services.device_service',
            'web.backend.core.device_manager'
        ]
        
        # Import each module in isolation
        for module_name in modules_to_test:
            try:
                # Clear module from cache if it was already imported
                if module_name in sys.modules:
                    del sys.modules[module_name]
                
                # Try importing
                module = importlib.import_module(module_name)
                self.assertIsNotNone(module)
            except ImportError as e:
                self.fail(f"Circular import detected in {module_name}: {e}")


if __name__ == "__main__":
    unittest.main() 