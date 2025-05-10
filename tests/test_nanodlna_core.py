import unittest
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from nanodlna import discover_devices, send_video, dlna


class TestNanoDLNACore(unittest.TestCase):
    """Test cases for core nanodlna functionality"""
    
    @patch('nanodlna.dlna._discover_upnp_devices')
    def test_discover_devices(self, mock_discover):
        """Test device discovery functionality"""
        # Mock the discovery response
        mock_devices = [
            {
                "location": "http://10.0.0.45:3500/",
                "friendly_name": "Smart_Projector-45[DLNA]",
                "hostname": "10.0.0.45",
                "action_url": "http://10.0.0.45:3500/AVTransport/3bd809df-2a90-4498-b92b-ae8dc63e977a/control.xml"
            },
            {
                "location": "http://10.0.0.122:49595/description.xml",
                "friendly_name": "SideProjector_dlna",
                "hostname": "10.0.0.122",
                "action_url": "http://10.0.0.122:49595/upnp/control/rendertransport1"
            }
        ]
        mock_discover.return_value = mock_devices
        
        # Call the discover function
        discovered = discover_devices()
        
        # Verify results
        self.assertEqual(len(discovered), 2)
        self.assertEqual(discovered[0]["friendly_name"], "Smart_Projector-45[DLNA]")
        self.assertEqual(discovered[1]["friendly_name"], "SideProjector_dlna")
        
        # Ensure the discovery function was called once
        mock_discover.assert_called_once()
    
    @patch('nanodlna.streaming.start_server')
    @patch('nanodlna.streaming.get_serve_ip')
    @patch('nanodlna.dlna.play')
    def test_send_video(self, mock_play, mock_get_serve_ip, mock_start_server):
        """Test sending video to device"""
        # Mock the streaming functions
        mock_get_serve_ip.return_value = "192.168.1.100"
        mock_start_server.return_value = ({"file_video": "http://192.168.1.100:8000/video.mp4"}, None)
        mock_play.return_value = True
        
        # Create a temporary video file
        with tempfile.NamedTemporaryFile(suffix='.mp4') as temp_video:
            # Write some dummy data
            temp_video.write(b'dummy video data')
            temp_video.flush()
            
            # Test with device info
            device_info = {
                "friendly_name": "Test Device",
                "location": "http://10.0.0.1:1234",
                "action_url": "http://10.0.0.1:1234/action",
                "hostname": "10.0.0.1"
            }
            
            # Call send_video
            result = send_video(device_info, temp_video.name, loop=True)
            
            # Verify results
            self.assertTrue(result)
            mock_get_serve_ip.assert_called_once_with("10.0.0.1")
            mock_start_server.assert_called_once()
            mock_play.assert_called_once()
    
    def test_config_file_handling(self):
        """Test configuration file handling"""
        # Create a temporary config file
        config_path = None
        video_path = None
        
        try:
            # Create a temporary config file with mode='w' for text mode
            config_path = tempfile.mktemp(suffix='.json')
            with open(config_path, 'w') as temp_config:
                config_data = [
                    {
                        "device_name": "Smart_Projector-45[DLNA]",
                        "type": "dlna",
                        "hostname": "10.0.0.45",
                        "action_url": "http://10.0.0.45:3500/AVTransport/control.xml",
                        "video_file": "test_video.mp4",
                        "friendly_name": "Smart_Projector-45[DLNA]"
                    }
                ]
                json.dump(config_data, temp_config)
            
            # Create a temporary video file
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_video:
                video_path = temp_video.name
            
            # Patch os.path.exists to make it think the video exists
            with patch('os.path.exists', return_value=True), \
                 patch('nanodlna.cli.send_video') as mock_send:
                mock_send.return_value = True
                
                # Import the function that processes config files
                from nanodlna.cli import process_config
                
                # Call the function with our temporary files
                result = process_config(config_path)
                
                # Verify that send_video was called with expected parameters
                self.assertTrue(result)
        finally:
            # Clean up temporary files
            if config_path and os.path.exists(config_path):
                os.unlink(config_path)
            if video_path and os.path.exists(video_path):
                os.unlink(video_path)


if __name__ == "__main__":
    unittest.main()
