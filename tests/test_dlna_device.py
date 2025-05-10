"""
Tests for the DLNADevice class, specifically focusing on video looping functionality.
"""
import sys
import os
import pytest
import threading
import time
from unittest.mock import MagicMock, patch

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Fix import path for backend modules
# This is needed because the backend module has relative imports 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../web/backend')))

# Mock Device class that DLNADevice inherits from
class MockDevice:
    def __init__(self, device_info):
        self.name = device_info.get("name", "Unknown")
        self.id = device_info.get("id", "unknown-id")
        self.status = "disconnected"
        self.video = None
        self.playing = False
    
    def update_status(self, status):
        self.status = status
    
    def update_video(self, video):
        self.video = video
    
    def update_playing(self, playing):
        self.playing = playing

# Patch the Device import in dlna_device
with patch('web.backend.core.device.Device', MockDevice):
    # Now import the DLNADevice class
    from web.backend.core.dlna_device import DLNADevice

class TestDLNADevice:
    """Tests for the DLNADevice class."""
    
    @pytest.fixture
    def mock_dlna_device(self):
        """Create a mock DLNA device for testing."""
        device_info = {
            "name": "Test Device",
            "id": "test-device-id",
            "location": "http://192.168.1.100:8000/device",
            "action_url": "http://192.168.1.100:8000/AVTransport/Control",
            "hostname": "192.168.1.100"
        }
        
        device = DLNADevice(device_info)
        
        # Mock the device methods we don't want to actually execute
        device._send_dlna_action = MagicMock()
        device._send_dlna_action_with_response = MagicMock()
        
        return device
    
    def test_loop_monitoring_setup(self, mock_dlna_device):
        """Test that the loop monitoring thread is set up correctly."""
        # Call the method
        mock_dlna_device._setup_loop_monitoring("http://example.com/video.mp4")
        
        # Check that the loop flag is set
        assert mock_dlna_device._loop_enabled == True
        
        # Check that the thread is created and started
        assert hasattr(mock_dlna_device, '_loop_thread')
        assert mock_dlna_device._loop_thread.is_alive()
        
        # Clean up
        with mock_dlna_device._thread_lock:
            mock_dlna_device._loop_enabled = False
        mock_dlna_device._loop_thread.join(timeout=1.0)
    
    def test_loop_monitoring_stopped_state(self, mock_dlna_device):
        """Test that the loop monitoring correctly restarts video when it's stopped."""
        # Setup the mock response for _get_transport_info
        mock_dlna_device._get_transport_info = MagicMock(return_value={"CurrentTransportState": "STOPPED"})
        
        # Start monitoring
        test_video_url = "http://example.com/video.mp4"
        mock_dlna_device._setup_loop_monitoring(test_video_url)
        
        # Give it some time to run
        time.sleep(6)  # Need to wait more than 5 seconds for the check to happen
        
        # Check that SetAVTransportURI and Play were called
        calls = mock_dlna_device._send_dlna_action.call_args_list
        
        # We need at least 2 calls (SetAVTransportURI and Play)
        assert len(calls) >= 2
        
        # Clean up
        with mock_dlna_device._thread_lock:
            mock_dlna_device._loop_enabled = False
        mock_dlna_device._loop_thread.join(timeout=1.0)
    
    def test_loop_monitoring_thread_cleanup(self, mock_dlna_device):
        """Test that the loop monitoring thread is cleaned up properly when loop is disabled."""
        # Start monitoring
        mock_dlna_device._setup_loop_monitoring("http://example.com/video.mp4")
        
        # Verify it's running
        assert mock_dlna_device._loop_enabled == True
        assert mock_dlna_device._loop_thread.is_alive()
        
        # Disable loop
        with mock_dlna_device._thread_lock:
            mock_dlna_device._loop_enabled = False
        
        # Wait for the thread to exit
        mock_dlna_device._loop_thread.join(timeout=6.0)  # Give it time to finish
        
        # Check that the thread is not alive
        assert not mock_dlna_device._loop_thread.is_alive()
    
    def test_inactivity_timeout(self, mock_dlna_device):
        """Test that the loop monitoring correctly detects inactivity and restarts."""
        # Make sure get_transport_info returns a PLAYING state
        mock_dlna_device._get_transport_info = MagicMock(return_value={"CurrentTransportState": "PLAYING"})
        mock_dlna_device._get_position_info = MagicMock(return_value={"RelTime": "00:01:30"})
        
        # Set a short inactivity timeout for testing
        mock_dlna_device._inactivity_timeout = 1  # 1 second
        
        # Start monitoring
        test_video_url = "http://example.com/video.mp4"
        mock_dlna_device._setup_loop_monitoring(test_video_url)
        
        # Set last activity time to a long time ago to trigger timeout
        with mock_dlna_device._thread_lock:
            mock_dlna_device._last_activity_time = time.time() - 10  # 10 seconds ago
        
        # Give it some time to run
        time.sleep(6)  # Need to wait more than 5 seconds for the check to happen
        
        # Check that SetAVTransportURI and Play were called
        calls = mock_dlna_device._send_dlna_action.call_args_list
        
        # We need at least 2 calls (SetAVTransportURI and Play)
        assert len(calls) >= 2
        
        # Clean up
        with mock_dlna_device._thread_lock:
            mock_dlna_device._loop_enabled = False
        mock_dlna_device._loop_thread.join(timeout=1.0) 