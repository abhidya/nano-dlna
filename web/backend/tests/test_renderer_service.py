"""
Test the Renderer Service functionality.
"""

import os
import json
import logging
import unittest
from unittest.mock import patch, MagicMock

from web.backend.core.renderer_service.service import RendererService
from web.backend.core.renderer_service.sender.base import Sender
from web.backend.core.renderer_service.sender.direct import DirectSender


class MockSender(Sender):
    """Mock implementation of Sender for testing."""
    
    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.connected = False
        self.target_id = None
        self.content_url = None
    
    def connect(self, target_id):
        self.target_id = target_id
        self.connected = True
        return True
    
    def disconnect(self):
        self.connected = False
        return True
    
    def send_content(self, content_url):
        if not self.connected:
            return False
        self.content_url = content_url
        return True
    
    def is_connected(self):
        return self.connected
    
    def get_status(self):
        return {
            "type": "mock",
            "connected": self.connected,
            "target": self.target_id,
            "content_url": self.content_url
        }


class TestRendererService(unittest.TestCase):
    """Test the Renderer Service functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a test configuration
        self.test_config = {
            "senders": {
                "mock": {"enabled": True}
            },
            "scenes": {
                "test-scene": {
                    "template": "test.html",
                    "data": {"key": "value"}
                }
            },
            "projectors": {
                "test-projector": {
                    "sender": "mock",
                    "target_name": "test-target"
                }
            }
        }
        
        # Save test config to a temporary file
        self.test_config_path = "/tmp/test_renderer_config.json"
        with open(self.test_config_path, "w") as f:
            json.dump(self.test_config, f)
        
        # Create a logger
        self.logger = logging.getLogger(__name__)
        
        # Create the service with the test configuration
        with patch.dict("web.backend.core.renderer_service.service.RendererService.senders", {"mock": MockSender}):
            self.service = RendererService(config_path=self.test_config_path, logger=self.logger)
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove test config file
        if os.path.exists(self.test_config_path):
            os.remove(self.test_config_path)
        
        # Stop the service if running
        if hasattr(self, "service") and self.service.running:
            self.service.stop()
    
    def test_service_init(self):
        """Test service initialization."""
        self.assertIsNotNone(self.service)
        self.assertEqual(self.service.config["senders"]["mock"]["enabled"], True)
        self.assertIn("test-scene", self.service.config["scenes"])
        self.assertIn("test-projector", self.service.config["projectors"])
    
    def test_start_stop(self):
        """Test starting and stopping the service."""
        # Start the service
        result = self.service.start()
        self.assertTrue(result)
        self.assertTrue(self.service.running)
        self.assertIsNotNone(self.service.health_check_thread)
        
        # Stop the service
        result = self.service.stop()
        self.assertTrue(result)
        self.assertFalse(self.service.running)
    
    def test_start_renderer(self):
        """Test starting a renderer."""
        # Start the service
        self.service.start()
        
        # Start a renderer
        result = self.service.start_renderer("test-scene", "test-projector")
        self.assertTrue(result)
        
        # Check active renderers
        self.assertIn("test-projector", self.service.active_renderers)
        self.assertEqual(self.service.active_renderers["test-projector"]["scene_id"], "test-scene")
        
        # Check if sender is connected
        sender = self.service.active_renderers["test-projector"]["sender"]
        self.assertTrue(sender.is_connected())
        self.assertEqual(sender.target_id, "test-target")
        self.assertEqual(sender.content_url, "test.html")
    
    def test_stop_renderer(self):
        """Test stopping a renderer."""
        # Start the service
        self.service.start()
        
        # Start a renderer
        self.service.start_renderer("test-scene", "test-projector")
        
        # Stop the renderer
        result = self.service.stop_renderer("test-projector")
        self.assertTrue(result)
        
        # Check active renderers
        self.assertNotIn("test-projector", self.service.active_renderers)
    
    def test_get_renderer_status(self):
        """Test getting renderer status."""
        # Start the service
        self.service.start()
        
        # Start a renderer
        self.service.start_renderer("test-scene", "test-projector")
        
        # Get status for all renderers
        status = self.service.get_renderer_status()
        self.assertEqual(status["active_renderers"], 1)
        self.assertIn("test-projector", status["renderers"])
        
        # Get status for specific renderer
        status = self.service.get_renderer_status("test-projector")
        self.assertEqual(status["projector_id"], "test-projector")
        self.assertEqual(status["scene_id"], "test-scene")
        self.assertIn("sender", status)
        self.assertEqual(status["sender"]["type"], "mock")
        self.assertTrue(status["sender"]["connected"])
    
    def test_nonexistent_scene(self):
        """Test starting a renderer with a nonexistent scene."""
        # Start the service
        self.service.start()
        
        # Try to start a renderer with a nonexistent scene
        result = self.service.start_renderer("nonexistent-scene", "test-projector")
        self.assertFalse(result)
    
    def test_nonexistent_projector(self):
        """Test starting a renderer with a nonexistent projector."""
        # Start the service
        self.service.start()
        
        # Try to start a renderer with a nonexistent projector
        result = self.service.start_renderer("test-scene", "nonexistent-projector")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main() 