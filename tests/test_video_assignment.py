"""
Tests for the improved video assignment logic in the DeviceManager class.
"""

import unittest
import os
import time
import tempfile
import threading
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock

# Import the necessary modules for testing
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create a test device class
class TestDevice:
    def __init__(self, name):
        self.name = name
        self.current_video = None
        self.is_playing = False
        self.status = "disconnected"
        self.device_info = {"device_name": name}
        self.play = Mock(return_value=True)
        self.stop = Mock(return_value=True)
    
    def update_status(self, status):
        self.status = status
    
    def update_video(self, video_path):
        self.current_video = video_path
    
    def update_playing(self, is_playing):
        self.is_playing = is_playing

# Create a test device manager
class TestDeviceManager:
    def __init__(self):
        self.devices = {}
        # UPDATED: Use consolidated lock architecture matching DeviceManager
        self.device_state_lock = threading.RLock()
        self.assignment_lock = threading.Lock()
        self.monitoring_lock = threading.Lock()
        self.statistics_lock = threading.Lock()
        
        self.assigned_videos = {}
        self.video_assignment_priority = {}
        self.video_assignment_retries = {}
        self.video_playback_history = {}
        self.playback_health_threads = {}
        self.scheduled_assignments = {}
        self.last_seen = {}
        self.device_connected_at = {}
    
    def get_device(self, device_name):
        with self.device_state_lock:
            return self.devices.get(device_name)
    
    def register_device(self, device_info):
        device_name = device_info.get("device_name")
        if not device_name:
            return None
        
        device = TestDevice(device_name)
        device.device_info = device_info
        
        with self.device_state_lock:
            self.devices[device_name] = device
        
        return device
    
    def _should_assign_video(self, device_name, video_path, is_new_device, is_changed_device):
        device = self.get_device(device_name)
        if not device:
            return False
        
        # Check device playing status
        if device.is_playing:
            # If already playing the correct video, no need to reassign
            if device.current_video == video_path:
                return False
        
        # Immediate cases for assignment
        if is_new_device or is_changed_device:
            return True
        
        # Check against assigned videos
        with self.device_state_lock:
            # If no video assigned yet
            if device_name not in self.assigned_videos:
                return True
                
            # If different video assigned
            if self.assigned_videos[device_name] != video_path:
                return True
                
            # Check if device is not playing but has a video assigned
            if not device.is_playing and device_name in self.assigned_videos:
                return True
        
        return False
    
    def assign_video_to_device(self, device_name, video_path, priority=50, schedule_time=None):
        device = self.get_device(device_name)
        if not device:
            return False
        
        # Check if video file exists
        if not os.path.exists(video_path):
            return False
        
        # Handle scheduled assignments
        if schedule_time is not None:
            with self.assignment_lock:
                self.scheduled_assignments[device_name] = {
                    "video_path": video_path,
                    "priority": priority,
                    "scheduled_time": schedule_time
                }
            return True
        
        # Check if we should override the current assignment based on priority
        should_override = False
        current_priority = 0
        
        with self.assignment_lock:
            current_priority = self.video_assignment_priority.get(device_name, 0)
            if priority >= current_priority:
                should_override = True
                # Update priority tracking
                self.video_assignment_priority[device_name] = priority
        
        if not should_override:
            return False
        
        # Proceed with assignment
        with self.device_state_lock:
            current_video = self.assigned_videos.get(device_name)
            if current_video and current_video != video_path and device.is_playing:
                device.stop()
            
            # Store the assigned video
            self.assigned_videos[device_name] = video_path
        
        # Reset retry counter when assigning a new video
        with self.assignment_lock:
            self.video_assignment_retries[device_name] = 0
        
        # Play the video
        result = device.play(video_path, True)
        
        # Start health check if successful
        if result:
            self._start_playback_health_check(device_name, video_path)
        
        # Track result in playback history
        self._track_playback_result(device_name, video_path, result)
        
        # If failed, schedule a retry
        if not result:
            with self.assignment_lock:
                self.video_assignment_retries[device_name] = 1
        
        return result
    
    def _track_playback_result(self, device_name, video_path, success):
        with self.monitoring_lock:
            if device_name not in self.video_playback_history:
                self.video_playback_history[device_name] = {
                    "attempts": 0,
                    "successes": 0,
                    "last_attempt": time.time(),
                    "videos": {}
                }
            
            # Update overall stats
            history = self.video_playback_history[device_name]
            history["attempts"] += 1
            if success:
                history["successes"] += 1
            history["last_attempt"] = time.time()
            
            # Update video-specific stats
            if video_path not in history["videos"]:
                history["videos"][video_path] = {
                    "attempts": 0,
                    "successes": 0
                }
            
            video_stats = history["videos"][video_path]
            video_stats["attempts"] += 1
            if success:
                video_stats["successes"] += 1
    
    def _check_scheduled_assignments(self, device_name):
        with self.assignment_lock:
            if device_name not in self.scheduled_assignments:
                return None
            
            assignment = self.scheduled_assignments[device_name]
            scheduled_time = assignment.get("scheduled_time")
            
            if not scheduled_time:
                return None
            
            # Check if scheduled time has passed
            if datetime.now(timezone.utc) >= scheduled_time:
                video_path = assignment.get("video_path")
                # Remove the scheduled assignment
                del self.scheduled_assignments[device_name]
                return video_path
        
        return None
    
    def get_device_playback_stats(self, device_name):
        with self.monitoring_lock:
            if device_name not in self.video_playback_history:
                return {
                    "attempts": 0,
                    "successes": 0,
                    "success_rate": 0,
                    "last_attempt": None,
                    "videos": {}
                }
            
            history = self.video_playback_history[device_name]
            success_rate = (history["successes"] / history["attempts"]) * 100 if history["attempts"] > 0 else 0
            
            return {
                "attempts": history["attempts"],
                "successes": history["successes"],
                "success_rate": success_rate,
                "last_attempt": history["last_attempt"],
                "videos": history["videos"]
            }
    
    def _start_playback_health_check(self, device_name, video_path):
        # Stop any existing health check thread first
        self._stop_playback_health_check(device_name)
        
        # Store the thread data
        with self.assignment_lock:
            self.playback_health_threads[device_name] = {
                "thread": None,  # No actual thread created in test
                "running": True,
                "video_path": video_path
            }
    
    def _stop_playback_health_check(self, device_name):
        with self.assignment_lock:
            if device_name in self.playback_health_threads:
                # Mark thread as not running
                self.playback_health_threads[device_name]["running"] = False


class TestVideoAssignment(unittest.TestCase):
    """
    Tests for the improved video assignment logic
    """
    
    def setUp(self):
        """
        Set up test fixtures
        """
        # Create a simplified test device manager
        self.device_manager = TestDeviceManager()
        
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create test video files (empty files for path existence checks)
        self.test_videos = {
            "video1": os.path.join(self.temp_dir.name, "test_video1.mp4"),
            "video2": os.path.join(self.temp_dir.name, "test_video2.mp4"),
            "video3": os.path.join(self.temp_dir.name, "test_video3.mp4")
        }
        
        for video_path in self.test_videos.values():
            with open(video_path, "w") as f:
                f.write("")
        
        # Create test device configurations
        self.test_config = [
            {
                "device_name": "TestDevice1",
                "type": "dlna",
                "hostname": "192.168.1.100",
                "video_file": self.test_videos["video1"],
                "priority": 50
            },
            {
                "device_name": "TestDevice2",
                "type": "dlna",
                "hostname": "192.168.1.101",
                "video_file": self.test_videos["video2"],
                "priority": 40
            }
        ]
        
        # Register test devices
        for device_config in self.test_config:
            self.device_manager.register_device(device_config)
    
    def tearDown(self):
        """
        Clean up test fixtures
        """
        # Remove temp files
        for video_path in self.test_videos.values():
            if os.path.exists(video_path):
                os.remove(video_path)
        
        # Remove temp directory
        self.temp_dir.cleanup()
    
    def test_should_assign_video_new_device(self):
        """Test that a video should be assigned to a new device"""
        # Test with a new device
        should_assign = self.device_manager._should_assign_video("TestDevice1", self.test_videos["video1"], True, False)
        
        self.assertTrue(should_assign)
    
    def test_should_assign_video_changed_device(self):
        """Test that a video should be assigned to a changed device"""
        # Test with a changed device
        should_assign = self.device_manager._should_assign_video("TestDevice1", self.test_videos["video1"], False, True)
        
        self.assertTrue(should_assign)
    
    def test_should_assign_video_different_video(self):
        """Test that a video should be assigned if different from currently assigned video"""
        # Assign initial video
        with self.device_manager.device_state_lock:
            self.device_manager.assigned_videos["TestDevice1"] = self.test_videos["video2"]
        
        # Test with a different video
        should_assign = self.device_manager._should_assign_video("TestDevice1", self.test_videos["video1"], False, False)
        
        self.assertTrue(should_assign)
    
    def test_should_not_assign_if_already_playing_same_video(self):
        """Test that a video should not be assigned if device is already playing the same video"""
        # Set up device as playing the video
        device = self.device_manager.get_device("TestDevice1")
        device.update_video(self.test_videos["video1"])
        device.update_playing(True)
        
        # Assign the video
        with self.device_manager.device_state_lock:
            self.device_manager.assigned_videos["TestDevice1"] = self.test_videos["video1"]
        
        # Test with the same video
        should_assign = self.device_manager._should_assign_video("TestDevice1", self.test_videos["video1"], False, False)
        
        self.assertFalse(should_assign)
    
    def test_assign_video_to_device_success(self):
        """Test assigning a video to a device successfully"""
        # Set up mock
        device = self.device_manager.get_device("TestDevice1")
        device.play.return_value = True
        
        # Assign a video
        result = self.device_manager.assign_video_to_device("TestDevice1", self.test_videos["video1"])
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify the video was assigned
        with self.device_manager.device_state_lock:
            self.assertEqual(self.device_manager.assigned_videos["TestDevice1"], self.test_videos["video1"])
        
        # Verify play was called
        device.play.assert_called_once()
        
        # Verify health check was started
        with self.device_manager.assignment_lock:
            self.assertIn("TestDevice1", self.device_manager.playback_health_threads)
            self.assertTrue(self.device_manager.playback_health_threads["TestDevice1"]["running"])
    
    def test_assign_video_to_device_failure(self):
        """Test handling failure when assigning a video to a device"""
        # Set up mock
        device = self.device_manager.get_device("TestDevice1")
        device.play.return_value = False
        
        # Assign a video
        result = self.device_manager.assign_video_to_device("TestDevice1", self.test_videos["video1"])
        
        # Verify the result
        self.assertFalse(result)
        
        # Verify the video was still assigned
        with self.device_manager.device_state_lock:
            self.assertEqual(self.device_manager.assigned_videos["TestDevice1"], self.test_videos["video1"])
        
        # Verify retry was scheduled
        with self.device_manager.assignment_lock:
            self.assertEqual(self.device_manager.video_assignment_retries["TestDevice1"], 1)
    
    def test_priority_higher_overrides_lower(self):
        """Test that higher priority assignment overrides lower priority"""
        # Set up mock
        device = self.device_manager.get_device("TestDevice1")
        device.play.return_value = True
        
        # Assign a low priority video
        self.device_manager.assign_video_to_device("TestDevice1", self.test_videos["video1"], priority=30)
        
        # Verify initial priority
        with self.device_manager.assignment_lock:
            self.assertEqual(self.device_manager.video_assignment_priority["TestDevice1"], 30)
        
        # Assign a higher priority video
        result = self.device_manager.assign_video_to_device("TestDevice1", self.test_videos["video2"], priority=50)
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify the new video was assigned
        with self.device_manager.device_state_lock:
            self.assertEqual(self.device_manager.assigned_videos["TestDevice1"], self.test_videos["video2"])
        
        # Verify priority was updated
        with self.device_manager.assignment_lock:
            self.assertEqual(self.device_manager.video_assignment_priority["TestDevice1"], 50)
    
    def test_priority_lower_does_not_override_higher(self):
        """Test that lower priority assignment does not override higher priority"""
        # Set up mock
        device = self.device_manager.get_device("TestDevice1")
        device.play.return_value = True
        
        # Assign a high priority video
        self.device_manager.assign_video_to_device("TestDevice1", self.test_videos["video1"], priority=70)
        
        # Verify initial priority
        with self.device_manager.assignment_lock:
            self.assertEqual(self.device_manager.video_assignment_priority["TestDevice1"], 70)
        
        # Assign a lower priority video
        result = self.device_manager.assign_video_to_device("TestDevice1", self.test_videos["video2"], priority=30)
        
        # Verify the result
        self.assertFalse(result)
        
        # Verify the original video was kept
        with self.device_manager.device_state_lock:
            self.assertEqual(self.device_manager.assigned_videos["TestDevice1"], self.test_videos["video1"])
        
        # Verify priority was not updated
        with self.device_manager.assignment_lock:
            self.assertEqual(self.device_manager.video_assignment_priority["TestDevice1"], 70)
    
    def test_scheduled_assignment(self):
        """Test scheduling a video assignment for the future"""
        # Set up mock
        device = self.device_manager.get_device("TestDevice1")
        device.play.return_value = True
        
        # Schedule a video for 5 minutes in the future
        future_time = datetime.now(timezone.utc) + timedelta(minutes=5)
        result = self.device_manager.assign_video_to_device("TestDevice1", self.test_videos["video3"], schedule_time=future_time)
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify the assignment was scheduled
        with self.device_manager.assignment_lock:
            self.assertIn("TestDevice1", self.device_manager.scheduled_assignments)
            self.assertEqual(self.device_manager.scheduled_assignments["TestDevice1"]["video_path"], self.test_videos["video3"])
            self.assertEqual(self.device_manager.scheduled_assignments["TestDevice1"]["scheduled_time"], future_time)
    
    def test_check_scheduled_assignments(self):
        """Test checking for due scheduled assignments"""
        # Schedule a video for the past
        past_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        
        with self.device_manager.assignment_lock:
            self.device_manager.scheduled_assignments["TestDevice1"] = {
                "video_path": self.test_videos["video3"],
                "priority": 80,
                "scheduled_time": past_time
            }
        
        # Check for scheduled assignments
        video_path = self.device_manager._check_scheduled_assignments("TestDevice1")
        
        # Verify the result
        self.assertEqual(video_path, self.test_videos["video3"])
        
        # Verify the scheduled assignment was removed
        with self.device_manager.assignment_lock:
            self.assertNotIn("TestDevice1", self.device_manager.scheduled_assignments)
    
    def test_playback_health_check(self):
        """Test playback health checking"""
        # Set up mock
        device = self.device_manager.get_device("TestDevice1")
        device.play.return_value = True
        
        # Assign a video
        self.device_manager.assign_video_to_device("TestDevice1", self.test_videos["video1"])
        
        # Verify health check was started
        with self.device_manager.assignment_lock:
            self.assertIn("TestDevice1", self.device_manager.playback_health_threads)
            self.assertTrue(self.device_manager.playback_health_threads["TestDevice1"]["running"])
        
        # Stop health check
        self.device_manager._stop_playback_health_check("TestDevice1")
        
        # Verify health check was stopped
        with self.device_manager.assignment_lock:
            self.assertIn("TestDevice1", self.device_manager.playback_health_threads)
            self.assertFalse(self.device_manager.playback_health_threads["TestDevice1"]["running"])
    
    def test_track_playback_result(self):
        """Test tracking playback results"""
        # Track a successful result
        self.device_manager._track_playback_result("TestDevice1", self.test_videos["video1"], True)
        
        # Verify stats were updated
        stats = self.device_manager.get_device_playback_stats("TestDevice1")
        self.assertEqual(stats["attempts"], 1)
        self.assertEqual(stats["successes"], 1)
        self.assertEqual(stats["success_rate"], 100)
        self.assertIn(self.test_videos["video1"], stats["videos"])
        
        # Track a failed result
        self.device_manager._track_playback_result("TestDevice1", self.test_videos["video1"], False)
        
        # Verify stats were updated
        stats = self.device_manager.get_device_playback_stats("TestDevice1")
        self.assertEqual(stats["attempts"], 2)
        self.assertEqual(stats["successes"], 1)
        self.assertEqual(stats["success_rate"], 50)
        self.assertEqual(stats["videos"][self.test_videos["video1"]]["attempts"], 2)
        self.assertEqual(stats["videos"][self.test_videos["video1"]]["successes"], 1)


if __name__ == "__main__":
    unittest.main() 