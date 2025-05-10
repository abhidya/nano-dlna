"""
Test the AirPlay integration with the Chrome renderer.

This script tests the integration between the Chrome renderer and AirPlay sender.
"""

import logging
import os
import sys
import time
import unittest
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.renderer_service.service import RendererService
from core.renderer_service.sender.airplay import AirPlaySender


def test_chrome_airplay():
    """
    Test Chrome renderer with AirPlay sender.
    
    This function tests the integration between the Chrome renderer and AirPlay sender.
    It finds an AirPlay projector in the configuration, starts the renderer with a scene,
    and verifies that the renderer is running and the AirPlay connection is established.
    """
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Starting Chrome to AirPlay integration test")
    
    # Initialize renderer service
    renderer_service = RendererService(logger=logger)
    
    # Get available projectors
    projectors = renderer_service.config.get('projectors', {})
    airplay_projector = None
    
    # Find an AirPlay projector
    for proj_id, proj_config in projectors.items():
        if proj_config.get('sender') == 'airplay':
            airplay_projector = proj_id
            logger.info(f"Found AirPlay projector: {proj_id} ({proj_config.get('target_name')})")
            break
    
    if not airplay_projector:
        logger.error("No AirPlay projector found in config")
        return False
    
    # Get available scenes
    scenes = renderer_service.config.get('scenes', {})
    if not scenes:
        logger.error("No scenes found in config")
        return False
    
    # Use the first scene
    scene_id = list(scenes.keys())[0]
    logger.info(f"Using scene: {scene_id}")
    
    try:
        # Start the renderer
        logger.info(f"Starting renderer for scene {scene_id} on projector {airplay_projector}")
        success = renderer_service.start_renderer(scene_id, airplay_projector)
        
        if success:
            logger.info("Renderer started successfully")
            
            # Get the renderer status
            status = renderer_service.get_renderer_status(airplay_projector)
            logger.info(f"Renderer status: {status}")
            
            # Wait for user to verify content is displayed
            input("Press Enter to stop the renderer...")
            
            # Stop the renderer
            renderer_service.stop_renderer(airplay_projector)
            logger.info("Renderer stopped")
            return True
        else:
            logger.error("Failed to start renderer")
            return False
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        # Make sure to stop the renderer if an exception occurs
        try:
            renderer_service.stop_renderer(airplay_projector)
        except:
            pass
        return False


class TestAirPlayIntegration(unittest.TestCase):
    """
    Test the AirPlay integration with the Chrome renderer.
    """
    
    @patch('core.renderer_service.sender.airplay.AirPlaySender.connect')
    @patch('core.renderer_service.sender.airplay.AirPlaySender.send_content')
    @patch('core.renderer_service.sender.airplay.AirPlaySender.disconnect')
    @patch('core.renderer_service.renderer.chrome.ChromeRenderer.render')
    @patch('core.renderer_service.renderer.chrome.ChromeRenderer.start')
    @patch('core.renderer_service.renderer.chrome.ChromeRenderer.stop')
    def test_airplay_renderer_integration(self, mock_stop, mock_start, mock_render, 
                                          mock_disconnect, mock_send_content, mock_connect):
        """
        Test the integration between the Chrome renderer and AirPlay sender.
        """
        # Configure mocks
        mock_connect.return_value = True
        mock_send_content.return_value = True
        mock_render.return_value = "file:///tmp/test.html"
        mock_start.return_value = True
        mock_stop.return_value = True
        mock_disconnect.return_value = True
        
        # Create a test configuration
        test_config = {
            "senders": {
                "airplay": {"enabled": True, "script_path": "auto"}
            },
            "scenes": {
                "test-scene": {
                    "template": "test.html",
                    "data": {"key": "value"}
                }
            },
            "projectors": {
                "test-projector": {
                    "sender": "airplay",
                    "target_name": "Test AirPlay Device"
                }
            }
        }
        
        # Create a temporary config file
        import tempfile
        import json
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            json.dump(test_config, f)
            config_path = f.name
        
        try:
            # Initialize the renderer service with the test configuration
            renderer_service = RendererService(config_file=config_path)
            
            # Start the renderer
            result = renderer_service.start_renderer("test-scene", "test-projector")
            self.assertTrue(result)
            
            # Verify that the mocks were called correctly
            mock_render.assert_called_once()
            mock_start.assert_called_once()
            mock_connect.assert_called_once_with("Test AirPlay Device")
            mock_send_content.assert_called_once_with("file:///tmp/test.html")
            
            # Stop the renderer
            result = renderer_service.stop_renderer("test-projector")
            self.assertTrue(result)
            
            # Verify that the mocks were called correctly
            mock_stop.assert_called_once()
            mock_disconnect.assert_called_once()
            
        finally:
            # Clean up the temporary file
            os.unlink(config_path)


if __name__ == "__main__":
    # If run as a script, run the interactive test
    if len(sys.argv) > 1 and sys.argv[1] == "--unittest":
        # Run the unit tests
        unittest.main(argv=['first-arg-is-ignored'])
    else:
        # Run the interactive test
        test_chrome_airplay()
