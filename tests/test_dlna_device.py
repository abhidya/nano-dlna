"""
Tests for the DLNADevice class, specifically focusing on video looping functionality.
"""
import sys
import os
import pytest
import threading
import time
from unittest.mock import MagicMock, patch

# sys.path modifications are handled by tests/conftest.py

# Import mocks from central location
from tests.mocks.device_mocks import MockDevice

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

    def test_loop_monitoring_v2_setup_and_basic_run(self, mock_dlna_device):
        """Test that the v2 loop monitoring thread is set up and runs."""
        test_video_url = "http://example.com/video_v2.mp4"
        
        # Mock methods called by the monitor thread
        mock_dlna_device._get_transport_info = MagicMock(return_value={"CurrentTransportState": "PLAYING"})
        mock_dlna_device._get_position_info = MagicMock(return_value={"RelTime": "00:00:01", "TrackDuration": "00:01:00"})
        mock_dlna_device.device_manager = MagicMock() # Mock device_manager if not already
        mock_dlna_device._try_restart_video = MagicMock(return_value=True)

        mock_dlna_device._setup_loop_monitoring_v2(test_video_url)
        
        assert mock_dlna_device._loop_enabled
        assert mock_dlna_device._loop_thread is not None
        assert mock_dlna_device._loop_thread.is_alive()
        
        # Allow thread to run a cycle
        time.sleep(3) # Should be enough for one or two cycles of monitor_and_loop_v2

        # Verify device_manager.update_device_playback_progress was called
        mock_dlna_device.device_manager.update_device_playback_progress.assert_called()
        
        # Clean up
        with mock_dlna_device._thread_lock:
            mock_dlna_device._loop_enabled = False
        if mock_dlna_device._loop_thread and mock_dlna_device._loop_thread.is_alive():
            mock_dlna_device._loop_thread.join(timeout=5.0)
        assert not (mock_dlna_device._loop_thread and mock_dlna_device._loop_thread.is_alive())

    def test_loop_monitoring_v2_reaches_end_and_restarts(self, mock_dlna_device):
        """Test v2 loop monitoring restarts video when it reaches the end."""
        test_video_url = "http://example.com/short_video.mp4"
        mock_dlna_device.current_video_duration = 5 # 5 seconds duration
        
        # Simulate video playing and then reaching near end
        mock_dlna_device._get_transport_info = MagicMock(return_value={"CurrentTransportState": "PLAYING"})
        # First call to get_position_info, video is playing
        # Second call, video is near end (e.g., 99% progress)
        mock_dlna_device._get_position_info = MagicMock(side_effect=[
            {"RelTime": "00:00:01", "TrackDuration": "00:00:05"}, # Playing
            {"RelTime": "00:00:04.9", "TrackDuration": "00:00:05"}, # Near end
            {"RelTime": "00:00:01", "TrackDuration": "00:00:05"}, # After restart
        ])
        mock_dlna_device._try_restart_video = MagicMock(return_value=True)
        mock_dlna_device.device_manager = MagicMock()

        mock_dlna_device._setup_loop_monitoring_v2(test_video_url)
        
        time.sleep(7) # Allow time for one full play and restart attempt (5s video + 2s interval)

        mock_dlna_device._try_restart_video.assert_called_with(test_video_url)
        
        # Clean up
        with mock_dlna_device._thread_lock:
            mock_dlna_device._loop_enabled = False
        if mock_dlna_device._loop_thread and mock_dlna_device._loop_thread.is_alive():
            mock_dlna_device._loop_thread.join(timeout=5.0)

    def test_loop_monitoring_v2_handles_stopped_state_and_restarts(self, mock_dlna_device):
        """Test v2 loop monitoring restarts video if found in STOPPED state."""
        test_video_url = "http://example.com/stoppable_video.mp4"
        mock_dlna_device.current_video_duration = 30

        # Simulate video playing then suddenly stopping
        mock_dlna_device._get_transport_info = MagicMock(side_effect=[
            {"CurrentTransportState": "PLAYING"},
            {"CurrentTransportState": "STOPPED"}, 
            {"CurrentTransportState": "PLAYING"} # After restart
        ])
        mock_dlna_device._get_position_info = MagicMock(return_value={"RelTime": "00:00:05", "TrackDuration": "00:00:30"})
        mock_dlna_device._try_restart_video = MagicMock(return_value=True)
        mock_dlna_device.device_manager = MagicMock()

        mock_dlna_device._setup_loop_monitoring_v2(test_video_url)
        
        time.sleep(5) # Allow time for state change and restart attempt

        mock_dlna_device._try_restart_video.assert_called_with(test_video_url)
        
        # Clean up
        with mock_dlna_device._thread_lock:
            mock_dlna_device._loop_enabled = False
        if mock_dlna_device._loop_thread and mock_dlna_device._loop_thread.is_alive():
            mock_dlna_device._loop_thread.join(timeout=5.0)

    def test_stop_method_cleans_up_v2_loop_thread(self, mock_dlna_device):
        """Test that the stop() method correctly stops and joins the v2 loop monitoring thread."""
        test_video_url = "http://example.com/video_for_stop_test.mp4"
        
        mock_dlna_device._get_transport_info = MagicMock(return_value={"CurrentTransportState": "PLAYING"})
        mock_dlna_device._get_position_info = MagicMock(return_value={"RelTime": "00:00:01", "TrackDuration": "00:01:00"})
        mock_dlna_device.device_manager = MagicMock()
        mock_dlna_device._send_dlna_action = MagicMock(return_value=True) # Mock the actual stop SOAP call

        # Start looping
        mock_dlna_device._setup_loop_monitoring_v2(test_video_url)
        assert mock_dlna_device._loop_thread is not None
        assert mock_dlna_device._loop_thread.is_alive()
        
        # Call stop
        mock_dlna_device.stop()
        
        # Assertions
        assert not mock_dlna_device._loop_enabled
        # The thread should have been joined and thus not alive
        # Give a very short time for the join in stop() to complete
        time.sleep(0.1) # Ensure join has time if thread was mid-operation
        assert not (mock_dlna_device._loop_thread and mock_dlna_device._loop_thread.is_alive()), "Loop thread should not be alive after stop()"
        mock_dlna_device._send_dlna_action.assert_called_with(None, "Stop")

    def test_loop_monitoring_v2_thread_stops_when_loop_disabled(self, mock_dlna_device):
        """Test that the v2 monitoring thread exits gracefully when _loop_enabled is set to False."""
        test_video_url = "http://example.com/video_disable_test.mp4"
        mock_dlna_device._get_transport_info = MagicMock(return_value={"CurrentTransportState": "PLAYING"})
        mock_dlna_device._get_position_info = MagicMock(return_value={"RelTime": "00:00:01", "TrackDuration": "00:01:00"})
        mock_dlna_device.device_manager = MagicMock()

        mock_dlna_device._setup_loop_monitoring_v2(test_video_url)
        loop_thread = mock_dlna_device._loop_thread
        assert loop_thread is not None and loop_thread.is_alive()

        # Disable loop
        with mock_dlna_device._thread_lock:
            mock_dlna_device._loop_enabled = False
        
        loop_thread.join(timeout=5.0) # Wait for thread to exit
        assert not loop_thread.is_alive(), "Loop thread should exit when _loop_enabled is False."
    
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
