import os
import pkgutil
import sys
import logging
import traceback
import time
import socket
import threading
from typing import Dict, List, Optional, Any
from xml.sax.saxutils import escape as xmlescape

if sys.version_info.major == 3:
    import urllib.request as urllibreq
else:
    import urllib2 as urllibreq

from .device import Device

logger = logging.getLogger(__name__)

# Delay between retries in seconds
RETRY_DELAY = 2

class DLNADevice(Device):
    """
    Implementation of a DLNA device
    """
    def __init__(self, device_info: Dict[str, Any]):
        super().__init__(device_info)
        self.type = "dlna"
        self.action_url = device_info.get("action_url")
        self.hostname = device_info.get("hostname")
        self.st = device_info.get("st", "urn:schemas-upnp-org:service:AVTransport:1")
        self.max_retries = 3  # Number of retries for DLNA actions
        
        # Thread management
        self._thread_lock = threading.Lock()
        self._loop_enabled = False
        self._loop_thread = None
        self._last_activity_time = None
        self._inactivity_timeout = 30  # Seconds of inactivity before considering playback stalled
        
        # Try to infer missing fields
        if not self.action_url and self.hostname:
            # Default action URL if not provided
            port = 80  # Default port
            if "location" in device_info:
                try:
                    location = urllibreq.urlparse(device_info["location"])
                    if location.port:
                        port = location.port
                except Exception:
                    pass
            
            self.action_url = f"http://{self.hostname}:{port}/AVTransport/Control"
            logger.warning(f"Inferred action_url for {self.name}: {self.action_url}")
        
        # Log warnings for missing fields but don't raise exceptions during discovery
        if not self.action_url:
            logger.error(f"DLNA device {self.name} missing action_url")
        
        if not self.hostname:
            logger.error(f"DLNA device {self.name} missing hostname")
    
    def play(self, video_url: str, loop: bool = False) -> bool:
        """
        Play a video on the DLNA device
        
        Args:
            video_url: URL of the video to play
            loop: Whether to loop the video
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Playing {video_url} on DLNA device {self.name} (loop={loop})")
            
            # Store the current video URL
            self.current_video = video_url
            
            # Create metadata for the video
            metadata = self._create_didl_metadata(video_url)
            
            # Set up AV transport
            data = {
                "CurrentURI": video_url,
                "CurrentURIMetaData": metadata
            }
            if not self._send_dlna_action(data, "SetAVTransportURI"):
                logger.error(f"Failed to set AV transport URI for {self.name}")
                return False
                
            # Start playback
            if not self._send_dlna_action(None, "Play"):
                logger.error(f"Failed to start playback on {self.name}")
                return False
                
            # Update device status
            self.update_status("playing")
            self.update_playing(True)
            
            # Set up loop monitoring if needed
            if loop:
                self._setup_loop_monitoring(video_url)
            
            return True
        except Exception as e:
            logger.error(f"Error playing video on {self.name}: {e}")
            return False
    
    def _try_play_with_config(self, video_data: Dict[str, Any], video_url: str, loop: bool, is_retry: bool = False) -> bool:
        """
        Try to play a video with a specific configuration
        
        Args:
            video_data: Video data dictionary 
            video_url: URL of the video
            loop: Whether to loop the video
            is_retry: Whether this is a retry attempt
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Send SetAVTransportURI command
            logger.info(f"Setting video URI on device {self.name}")
            self._send_dlna_action(video_data, "SetAVTransportURI")
            
            # Send Play command
            logger.info(f"Sending play command to device {self.name}")
            self._send_dlna_action(video_data, "Play")
            
            # Reset last activity time
            self._last_activity_time = time.time()
            
            # Wait a bit to check if play was successful
            if is_retry:
                logger.info(f"Waiting 2 seconds to check play status...")
                time.sleep(2)
                
                # Check if actually playing
                transport_info = self._get_transport_info()
                state = transport_info.get("CurrentTransportState", "UNKNOWN")
                
                if state != "PLAYING":
                    logger.warning(f"Play command sent but device not playing (state: {state})")
                    return False
            
            # If loop is enabled, we need to set up a background thread to monitor playback
            # and restart the video when it ends
            if loop:
                logger.info(f"Loop enabled for {self.name}, setting up background monitoring")
                self._setup_loop_monitoring(video_url)
            
            # Update device status
            self.update_status("connected")
            self.update_video(video_url)
            self.update_playing(True)
            
            logger.info(f"Successfully started playing video on {self.name}")
            return True
        except Exception as e:
            logger.error(f"Error in _try_play_with_config for {self.name}: {e}")
            return False
    
    def _setup_loop_monitoring(self, video_url: str) -> None:
        """
        Set up monitoring thread for video looping
        
        Args:
            video_url: URL of the video to monitor
        """
        logger.info(f"[{self.name}] Setting up loop monitoring for {video_url}")
        
        with self._thread_lock:
            # Clean up existing thread if present
            if hasattr(self, '_loop_thread') and self._loop_thread:
                if self._loop_thread.is_alive():
                    logger.debug(f"[{self.name}] Stopping existing loop thread")
                    self._loop_enabled = False
                    # Wait short time for thread to exit
                    self._loop_thread.join(timeout=2.0)
            
            # Enable looping
            self._loop_enabled = True
            self._last_activity_time = time.time()
            
            # Define monitoring function
            def monitor_and_restart():
                logger.info(f"[{self.name}] Loop monitoring thread started")
                current_video = video_url
                last_position = None
                position_unchanged_count = 0
                
                # For better cleanup, store reference to streaming_service if needed
                streaming_service = None
                
                while True:
                    try:
                        # Check if loop is still enabled (thread-safe)
                        with self._thread_lock:
                            if not self._loop_enabled:
                                logger.info(f"[{self.name}] Loop monitoring flag is False, exiting thread.")
                                break
                        
                        # Get video duration - try different methods
                        duration = None
                        using_ffmpeg_duration = False
                        
                        # First try to use stored duration (from database)
                        if self.current_video_duration:
                            duration = self.current_video_duration
                            logger.debug(f"[{self.name}] Using stored duration: {duration}s")
                        
                        # Next try ffmpeg for local files
                        elif self.current_video_path and os.path.exists(self.current_video_path):
                            import subprocess
                            try:
                                # Use ffprobe to get duration
                                cmd = [
                                    "ffprobe", 
                                    "-v", "error", 
                                    "-show_entries", "format=duration", 
                                    "-of", "csv=p=0", 
                                    self.current_video_path
                                ]
                                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                                if result.stdout.strip():
                                    duration = float(result.stdout.strip())
                                    using_ffmpeg_duration = True
                                    logger.debug(f"[{self.name}] Got duration from ffprobe: {duration}s")
                            except Exception as e:
                                logger.warning(f"[{self.name}] Error getting duration with ffprobe: {e}")
                        
                        # Next try to get from device position info
                        if duration is None:
                            try:
                                position_info = self._get_position_info()
                                track_duration = position_info.get("TrackDuration", "UNKNOWN")
                                if track_duration not in ("UNKNOWN", "NOT_IMPLEMENTED"):
                                    # Parse HH:MM:SS format
                                    parts = track_duration.split(":")
                                    if len(parts) == 3:
                                        hours, minutes, seconds = map(float, parts)
                                        duration = hours * 3600 + minutes * 60 + seconds
                                        logger.debug(f"[{self.name}] Got duration from position info: {duration}s")
                            except Exception as pos_error:
                                logger.warning(f"[{self.name}] Error getting position info: {pos_error}")
                        
                        # Fallback: use default duration as minimum buffer
                        if duration is None:
                            duration = 30  # Default to 30 seconds if we can't determine
                            logger.warning(f"[{self.name}] Using default duration: {duration}s")
                        
                        # Check if device may be inactive (no response to commands)
                        with self._thread_lock:
                            time_since_activity = time.time() - self._last_activity_time
                            if time_since_activity > 60:  # 60 second inactivity threshold
                                logger.warning(f"[{self.name}] No activity for {time_since_activity:.1f}s, checking transport state")
                                transport_info = self._get_transport_info()
                                if transport_info["CurrentTransportState"] != "PLAYING":
                                    logger.warning(f"[{self.name}] Device not playing, restarting video")
                                    # Restart video due to inactivity
                                    self._try_restart_video(current_video)
                                    with self._thread_lock:
                                        self._last_activity_time = time.time()

                        # Check if we should restart the video
                        if duration is not None and duration > 0:
                            # Calculate time to wait based on duration (minus safety margin)
                            wait_time = max(5, duration - 10) if duration > 15 else duration / 2
                            logger.info(f"[{self.name}] Waiting {wait_time}s before restart check")
                            
                            # Sleep until near the end of the video
                            time.sleep(wait_time)
                            
                            # Check again after sleeping (thread-safe)
                            with self._thread_lock:
                                if not self._loop_enabled:
                                    logger.info(f"[{self.name}] Loop monitoring flag is False after sleep, exiting thread.")
                                    break
                            
                            # Simply restart the video when we approach the end
                            logger.info(f"[{self.name}] Video approaching end, restarting playback...")
                            
                            try:
                                # First try to seek to position 0 (beginning)
                                try:
                                    logger.info(f"[{self.name}] Seeking to beginning...")
                                    self.seek("00:00:00")
                                    time.sleep(1)  # Short pause after seek
                                except Exception as seek_error:
                                    logger.warning(f"[{self.name}] Seek to beginning failed: {seek_error}")
                                    # If seek fails, do a full restart
                                    
                                # If seek failed or we're using a strategy that needs regular restarts,
                                # stop and restart the video completely
                                if not using_ffmpeg_duration or duration <= 30:
                                    # For short videos or when we can't determine duration, full restart is safer
                                    logger.info(f"[{self.name}] Performing full restart...")
                                    
                                    # Stop current playback
                                    try:
                                        self._send_dlna_action(None, "Stop")
                                        time.sleep(1)  # Give device time to process stop command
                                    except Exception as stop_error:
                                        logger.warning(f"[{self.name}] Error stopping: {stop_error}")
                                    
                                    # Create metadata for restart
                                    metadata_template = """
                                    <DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/" 
                                               xmlns:dc="http://purl.org/dc/elements/1.1/" 
                                               xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/"
                                               xmlns:dlna="urn:schemas-dlna-org:metadata-1-0/">
                                        <item id="1" parentID="0" restricted="0">
                                            <dc:title>Video</dc:title>
                                            <upnp:class>object.item.videoItem</upnp:class>
                                            <res protocolInfo="http-get:*:video/mp4:DLNA.ORG_OP=01;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01500000000000000000000000000000;DLNA.ORG_PN=AVC_MP4_BL_CIF15_AAC_520">{uri_video}</res>
                                        </item>
                                    </DIDL-Lite>
                                    """
                                    
                                    # Prepare video data
                                    video_data = {
                                        "uri_video": current_video,
                                        "type_video": os.path.splitext(current_video)[1][1:] if '.' in current_video else "mp4",
                                        "metadata": xmlescape(metadata_template.format(uri_video=current_video))
                                    }
                                    
                                    # Send SetAVTransportURI command
                                    self._send_dlna_action(video_data, "SetAVTransportURI")
                                    
                                    # Send Play command
                                    self._send_dlna_action(video_data, "Play")
                                
                                # Update device status
                                self.update_playing(True)
                                logger.info(f"[{self.name}] Video restarted successfully")
                                
                                # Update last activity time
                                with self._thread_lock:
                                    self._last_activity_time = time.time()
                                
                            except Exception as restart_error:
                                logger.error(f"[{self.name}] Error during video restart: {restart_error}")
                                logger.debug(traceback.format_exc())
                                # Sleep a bit before retrying
                                time.sleep(5)
                    
                    except Exception as e:
                        logger.error(f"[{self.name}] Unhandled error in loop monitoring thread: {e}")
                        logger.debug(traceback.format_exc())
                        time.sleep(5)  # Sleep a bit before retrying
                
                logger.info(f"[{self.name}] Loop monitoring thread finished.")
            
            # Start monitoring thread
            self._loop_thread = threading.Thread(target=monitor_and_restart, name=f"loop-monitor-{self.name}")
            self._loop_thread.daemon = True
            self._loop_thread.start()
            logger.info(f"[{self.name}] Loop monitoring thread started successfully.")
    
    def _get_position_info(self) -> Dict[str, str]:
        """
        Get the position info from the device
        
        Returns:
            Dict[str, str]: Position info including current time and duration
        """
        try:
            # Send GetPositionInfo action
            response = self._send_dlna_action_with_response(None, "GetPositionInfo")
            
            # Parse the response
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response)
            
            # Extract the relevant information
            rel_time = root.find(".//{urn:schemas-upnp-org:service:AVTransport:1}RelTime")
            abs_time = root.find(".//{urn:schemas-upnp-org:service:AVTransport:1}AbsTime")
            track_duration = root.find(".//{urn:schemas-upnp-org:service:AVTransport:1}TrackDuration")
            
            return {
                "RelTime": rel_time.text if rel_time is not None else "NOT_IMPLEMENTED",
                "AbsTime": abs_time.text if abs_time is not None else "NOT_IMPLEMENTED",
                "TrackDuration": track_duration.text if track_duration is not None else "NOT_IMPLEMENTED"
            }
        except Exception as e:
            logger.error(f"Error getting position info for {self.name}: {e}")
            return {"RelTime": "UNKNOWN", "AbsTime": "UNKNOWN", "TrackDuration": "UNKNOWN"}
    
    def _get_transport_info(self) -> Dict[str, str]:
        """
        Get the transport info from the device
        
        Returns:
            Dict[str, str]: Transport info
        """
        try:
            # Send GetTransportInfo action
            response = self._send_dlna_action_with_response(None, "GetTransportInfo")
            
            # Parse the response
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response)
            
            # Extract the transport state
            transport_state = root.find(".//{urn:schemas-upnp-org:service:AVTransport:1}CurrentTransportState")
            transport_status = root.find(".//{urn:schemas-upnp-org:service:AVTransport:1}CurrentTransportStatus")
            
            state = transport_state.text if transport_state is not None else "UNKNOWN"
            status = transport_status.text if transport_status is not None else "UNKNOWN"
            
            # If we got a non-null state response, update the last activity time
            if state != "UNKNOWN":
                with self._thread_lock:
                    self._last_activity_time = time.time()
            
            return {
                "CurrentTransportState": state,
                "CurrentTransportStatus": status
            }
        except Exception as e:
            logger.error(f"Error getting transport info for {self.name}: {e}")
            return {"CurrentTransportState": "UNKNOWN", "CurrentTransportStatus": "UNKNOWN"}
    
    def _send_dlna_action_with_response(self, data: Optional[Dict[str, Any]], action: str) -> str:
        """
        Send a DLNA action to the device and return the response
        
        Args:
            data: Data to send with the action
            action: Action to send
            
        Returns:
            str: Response from the device
        """
        logger.debug(f"Sending DLNA action {action} to device {self.name} with response")
        
        # Check if action_url is available
        if not self.action_url:
            raise ValueError(f"Cannot send action to device {self.name}: action_url is missing")
        
        # Get the action template
        try:
            template_data = pkgutil.get_data(
                "nanodlna", f"templates/action-{action}.xml")
            if template_data is not None:
                action_data = template_data.decode("UTF-8")
            else:
                # If template_data is None, try to find it in our package
                template_path = os.path.join(os.path.dirname(__file__), "templates", f"action-{action}.xml")
                if os.path.exists(template_path):
                    with open(template_path, "r") as f:
                        action_data = f.read()
                else:
                    raise FileNotFoundError(f"Template for action {action} not found")
        except (ImportError, FileNotFoundError):
            # If the template is not found in the nanodlna package, try to find it in our package
            template_path = os.path.join(os.path.dirname(__file__), "templates", f"action-{action}.xml")
            if os.path.exists(template_path):
                with open(template_path, "r") as f:
                    action_data = f.read()
            else:
                raise FileNotFoundError(f"Template for action {action} not found")
        
        # Format the action data with the provided data
        if data:
            action_data = action_data.format(**data)
        action_data = action_data.encode("UTF-8")
        
        # Prepare headers
        headers = {
            "Content-Type": "text/xml; charset=\"utf-8\"",
            "Content-Length": f"{len(action_data)}",
            "Connection": "close",
            "SOAPACTION": f"\"{self.st}#{action}\""
        }
        
        # Send the request with retry logic
        last_exception = None
        for retry in range(self.max_retries):
            try:
                logger.debug(f"Sending DLNA request to {self.action_url} (attempt {retry+1}/{self.max_retries})")
                request = urllibreq.Request(self.action_url, action_data, headers)
                response = urllibreq.urlopen(request)
                response_data = response.read().decode("UTF-8")
                logger.debug(f"DLNA request sent successfully")
                return response_data
            except Exception as e:
                last_exception = e
                logger.warning(f"DLNA request failed (attempt {retry+1}/{self.max_retries}): {e}")
                if retry < self.max_retries - 1:
                    logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
        
        # If we get here, all retries failed
        logger.error(f"DLNA request failed after {self.max_retries} attempts")
        if last_exception:
            raise last_exception
        return ""

    def stop(self) -> bool:
        """
        Stop playback on the DLNA device
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Stopping playback on DLNA device {self.name}")
            
            # Disable looping if it was enabled
            with self._thread_lock:
                if hasattr(self, '_loop_enabled'):
                    self._loop_enabled = False
            
            # Send stop command
            if not self._send_dlna_action(None, "Stop"):
                logger.error(f"Failed to stop playback on {self.name}")
                return False
            
            # Update device status
            self.update_status("connected")
            self.update_playing(False)
            self.current_video = None
            
            return True
        except Exception as e:
            logger.error(f"Error stopping playback on {self.name}: {e}")
            return False
    
    def pause(self) -> bool:
        """
        Pause playback on the DLNA device
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Pausing playback on DLNA device {self.name}")
            
            # Send pause command
            if not self._send_dlna_action(None, "Pause"):
                logger.error(f"Failed to pause playback on {self.name}")
                return False
            
            # Update device status
            self.update_status("paused")
            self.update_playing(False)
            
            return True
        except Exception as e:
            logger.error(f"Error pausing playback on {self.name}: {e}")
            return False
    
    def seek(self, position: str) -> bool:
        """
        Seek to a position in the current video
        
        Args:
            position: Position to seek to (format: HH:MM:SS)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Seeking to position {position} on DLNA device {self.name}")
            action_data = {
                "seek_target": position,
            }
            self._send_dlna_action(action_data, "Seek")
            
            # Update last activity time to prevent false inactivity detection
            with self._thread_lock:
                self._last_activity_time = time.time()
                
            return True
        except Exception as e:
            logger.error(f"Error seeking on DLNA device {self.name}: {e}")
            logger.debug(traceback.format_exc())
            return False
    
    def _send_dlna_action(self, data: dict, action: str) -> bool:
        """
        Send a DLNA action to the device
        
        Args:
            data: Data for the action
            action: Name of the action
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if action == "SetAVTransportURI":
                return self._send_av_transport_action(action, {
                    "CurrentURI": data["CurrentURI"],
                    "CurrentURIMetaData": data["CurrentURIMetaData"]
                })
            elif action == "Play":
                return self._send_av_transport_action(action, {
                    "Speed": "1"
                })
            elif action == "Stop":
                return self._send_av_transport_action(action, {})
            elif action == "Pause":
                return self._send_av_transport_action(action, {})
            elif action == "Seek":
                if "position" not in data:
                    logger.error("Position missing for Seek action")
                    return False
                return self._send_av_transport_action(action, {
                    "Unit": "REL_TIME",
                    "Target": data["position"]
                })
            else:
                logger.error(f"Unknown DLNA action: {action}")
                return False
        except Exception as e:
            logger.error(f"Error sending DLNA action {action}: {e}")
            return False

    def _send_av_transport_action(self, action: str, parameters: dict) -> bool:
        """
        Send an AVTransport action to the device
        
        Args:
            action: Name of the action
            parameters: Parameters for the action
            
        Returns:
            bool: True if successful, False otherwise
        """
        import requests
        import xml.etree.ElementTree as ET
        
        # Define SOAP namespaces
        ns = {
            "s": "http://schemas.xmlsoap.org/soap/envelope/",
            "u": "urn:schemas-upnp-org:service:AVTransport:1",
        }
        
        # Create SOAP envelope
        envelope = ET.Element("{http://schemas.xmlsoap.org/soap/envelope/}Envelope")
        envelope.set("xmlns:s", ns["s"])
        envelope.set("s:encodingStyle", "http://schemas.xmlsoap.org/soap/encoding/")
        
        # Create SOAP body
        body = ET.SubElement(envelope, "{http://schemas.xmlsoap.org/soap/envelope/}Body")
        
        # Create action element
        action_element = ET.SubElement(body, "{urn:schemas-upnp-org:service:AVTransport:1}" + action)
        
        # Add instance ID (always 0 for standard DLNA)
        instance_id = ET.SubElement(action_element, "InstanceID")
        instance_id.text = "0"
        
        # Add parameters
        for name, value in parameters.items():
            param = ET.SubElement(action_element, name)
            param.text = value
        
        # Convert to XML string
        from xml.dom.minidom import parseString
        xml_str = ET.tostring(envelope, encoding="utf-8", method="xml").decode()
        xml_pretty = parseString(xml_str).toprettyxml(indent="  ")
        
        # Log the request
        logger.debug(f"Sending AVTransport action {action} to {self.name}")
        logger.debug(f"Action URL: {self.action_url}")
        logger.debug(f"SOAP request: {xml_pretty}")
        
        # Define SOAP headers
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": f'"urn:schemas-upnp-org:service:AVTransport:1#{action}"',
        }
        
        # Send the request
        try:
            response = requests.post(self.action_url, data=xml_str, headers=headers, timeout=10)
            
            # Check if the request was successful
            if response.status_code == 200:
                logger.debug(f"AVTransport action {action} succeeded")
                return True
            else:
                logger.error(f"AVTransport action {action} failed with status {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending AVTransport action {action}: {e}")
            return False

    def _handle_streaming_health_check(self, session_id: str, reason: str) -> None:
        """
        Handle streaming health check events
        
        Args:
            session_id: ID of the streaming session
            reason: Reason for the health check event
        """
        logger.warning(f"[{self.name}] Handling streaming health check for session {session_id}")
        
        # Check if this session belongs to this device
        if session_id not in getattr(self, '_streaming_sessions', []):
            logger.warning(f"[{self.name}] Received health check for session belonging to device {session_id.split('-')[0]}")
            return
            
        # Handle different health check reasons
        if reason == "stalled":
            # Try to restart the video
            logger.info(f"[{self.name}] Streaming session {session_id} stalled, attempting restart")
            if self.is_playing and self.current_video:
                self.play(self.current_video, loop=True)
            
        elif reason == "completed":
            # Video playback completed naturally
            logger.info(f"[{self.name}] Streaming session {session_id} completed naturally")
            # If we're supposed to be looping, restart
            if getattr(self, '_looping', False) and self.current_video:
                logger.info(f"[{self.name}] Restarting video in loop mode")
                self.play(self.current_video, loop=True)
                
    def _setup_loop_monitoring(self, video_url: str) -> None:
        """
        Set up monitoring of video playback for looping
        
        Args:
            video_url: URL of the video
        """
        import threading
        
        self._looping = True
        
        # Create and start the monitoring thread
        logger.info(f"[{self.name}] Setting up loop monitoring for {video_url}")
        
        # Only start a new thread if one isn't already running
        if hasattr(self, '_loop_thread') and self._loop_thread.is_alive():
            logger.info(f"[{self.name}] Loop monitoring thread already running")
            return
            
        self._loop_thread = threading.Thread(
            target=self._monitor_and_loop,
            args=(video_url,),
            daemon=True
        )
        
        self._loop_thread.start()
        logger.info(f"[{self.name}] Loop monitoring thread started")
        
        # Check if thread started successfully
        if self._loop_thread.is_alive():
            logger.info(f"[{self.name}] Loop monitoring thread started successfully.")
        else:
            logger.error(f"[{self.name}] Failed to start loop monitoring thread.")
            
    def _monitor_and_loop(self, video_url: str) -> None:
        """
        Monitor video playback and restart when completed
        
        Args:
            video_url: URL of the video
        """
        import time
        
        # Keep trying to get the video duration
        while self._looping and not self.current_video_duration:
            try:
                transport_info = self._get_transport_info()
                if transport_info and transport_info.get("duration"):
                    self.current_video_duration = self._parse_time(transport_info["duration"])
                    logger.info(f"[{self.name}] Video duration: {self.current_video_duration}s")
                    break
            except Exception as e:
                logger.debug(f"[{self.name}] Error getting video duration: {e}")
                pass
                
            # Wait before trying again
            time.sleep(5)
            
        # If we couldn't get the duration, use a default value
        if not self.current_video_duration:
            logger.warning(f"[{self.name}] Couldn't determine video duration, using default")
            self.current_video_duration = 60  # Default 60 seconds
            
        # Main monitoring loop
        while self._looping:
            try:
                # Wait for video to complete (with some margin)
                # We check transport state every 5 seconds
                wait_time = max(1, self.current_video_duration - 5)
                logger.info(f"[{self.name}] Waiting {wait_time}s before restart check")
                time.sleep(wait_time)
                
                # Check current transport state
                transport_info = self._get_transport_info()
                if transport_info:
                    state = transport_info.get("transport_state", "UNKNOWN")
                    logger.info(f"[{self.name}] Transport state: {state}")
                    
                    # If stopped or in error state, restart
                    if state in ["STOPPED", "ERROR", "NO_MEDIA_PRESENT"]:
                        logger.info(f"[{self.name}] Video stopped, restarting in loop mode")
                        self.play(video_url, loop=True)
                        # Short pause to allow playback to start
                        time.sleep(2)
                    elif state == "UNKNOWN":
                        # Try to restart if we can't determine state
                        logger.warning(f"[{self.name}] Unknown transport state, attempting restart")
                        self.play(video_url, loop=True)
                        time.sleep(2)
            except Exception as e:
                logger.error(f"[{self.name}] Error in loop monitoring: {e}")
                # Continue monitoring even after errors
                time.sleep(10)
                
    def _parse_time(self, time_str: str) -> int:
        """
        Parse time string in format HH:MM:SS to seconds
        
        Args:
            time_str: Time string
            
        Returns:
            int: Time in seconds
        """
        try:
            parts = time_str.split(':')
            if len(parts) == 3:
                hours, minutes, seconds = parts
                return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
            return 60  # Default 60 seconds if parsing fails
        except Exception:
            return 60  # Default 60 seconds if parsing fails

    def _get_serve_ip(self) -> str:
        """
        Get the best IP address to serve content to this device
        
        Returns:
            str: IP address
        """
        import socket
        
        # If we know the device's hostname/IP, try to find the best interface
        if self.hostname and not self.hostname.startswith('127.') and not self.hostname == 'localhost':
            # Get all network interfaces
            interfaces = socket.getaddrinfo(socket.gethostname(), None)
            
            for interface in interfaces:
                # Only consider IPv4 addresses
                if interface[0] == socket.AF_INET:
                    local_ip = interface[4][0]
                    
                    # Skip loopback addresses
                    if not local_ip.startswith('127.'):
                        # Check if this interface can reach the device network
                        device_ip = self.hostname
                        if ':' in device_ip:
                            device_ip = device_ip.split(':')[0]
                            
                        # Simple subnet check - compare the first three octets
                        local_subnet = '.'.join(local_ip.split('.')[:3])
                        device_subnet = '.'.join(device_ip.split('.')[:3])
                        
                        if local_subnet == device_subnet:
                            logger.debug(f"Found matching interface for device {self.name}: {local_ip}")
                            return local_ip
        
        # Fallback: find a non-loopback interface
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Doesn't have to be reachable
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        
        logger.debug(f"Using fallback interface for device {self.name}: {ip}")
        return ip

    def _create_didl_metadata(self, url: str) -> str:
        """
        Create DIDL-Lite metadata for a video
        
        Args:
            url: URL of the video
            
        Returns:
            str: DIDL-Lite metadata
        """
        # Base DIDL template
        didl_template = """<DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/" 
                         xmlns:dc="http://purl.org/dc/elements/1.1/" 
                         xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" 
                         xmlns:sec="http://www.sec.co.kr/">
        <item id="0" parentID="-1" restricted="1">
            <dc:title>Video</dc:title>
            <upnp:class>object.item.videoItem</upnp:class>
            <res protocolInfo="http-get:*:video/mp4:DLNA.ORG_PN=AVC_MP4_BL_CIF15_AAC_520;DLNA.ORG_OP=01;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01500000000000000000000000000000" sec:URIType="public">{url}</res>
        </item>
        </DIDL-Lite>"""
        
        # Insert the URL
        metadata = didl_template.format(url=url)
        return metadata

    def _try_restart_video(self, video_url: str) -> bool:
        """
        Attempt to restart video playback using optimal restart strategy
        
        Args:
            video_url: URL of the video to restart
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"[{self.name}] Attempting to restart video: {video_url}")
        
        try:
            # First try to get transport info to see if the device is responsive
            transport_info = self._get_transport_info()
            current_state = transport_info.get("CurrentTransportState", "UNKNOWN")
            logger.info(f"[{self.name}] Current transport state: {current_state}")
            
            # Check if video is already playing (possible false restart trigger)
            if current_state == "PLAYING":
                # Try to get position info to confirm it's actually playing
                try:
                    position_info = self._get_position_info()
                    rel_time = position_info.get("RelTime", "UNKNOWN")
                    if rel_time not in ("UNKNOWN", "NOT_IMPLEMENTED", "00:00:00"):
                        logger.info(f"[{self.name}] Video seems to be playing at {rel_time}, no restart needed")
                        return True
                except Exception as e:
                    logger.warning(f"[{self.name}] Error checking position info: {e}")
            
            # First attempt: try seeking to beginning (this is the gentlest restart method)
            if current_state in ("PLAYING", "PAUSED_PLAYBACK"):
                try:
                    logger.info(f"[{self.name}] Seeking to beginning...")
                    self.seek("00:00:00")
                    time.sleep(1)  # Short pause
                    
                    # If state was PAUSED, we need to send Play
                    if current_state == "PAUSED_PLAYBACK":
                        logger.info(f"[{self.name}] Sending Play after seek...")
                        self._send_dlna_action(None, "Play")
                    
                    # Check if seek worked
                    position_info = self._get_position_info()
                    rel_time = position_info.get("RelTime", "UNKNOWN")
                    if rel_time in ("00:00:00", "0:00:00"):
                        logger.info(f"[{self.name}] Seek to beginning successful")
                        return True
                except Exception as e:
                    logger.warning(f"[{self.name}] Error during seek-based restart: {e}")
            
            # Second attempt: full restart with Stop+SetAVTransportURI+Play
            logger.info(f"[{self.name}] Performing full restart sequence...")
            
            # Stop current playback
            try:
                self._send_dlna_action(None, "Stop")
                time.sleep(1)  # Give device time to process stop command
            except Exception as stop_error:
                logger.warning(f"[{self.name}] Error stopping video (continuing anyway): {stop_error}")
            
            # Get file extension for content type
            ext = os.path.splitext(video_url)[1].lower() if '.' in video_url else ".mp4"
            
            # DLNA profile based on extension
            dlna_profile = "MPEG_PS_PAL"
            if ext == '.mp4':
                dlna_profile = "AVC_MP4_BL_CIF15_AAC_520"
            elif ext in ['.avi', '.mkv', '.mov']:
                dlna_profile = "MPEG_PS_PAL"
            elif ext in ['.mpeg', '.mpg']:
                dlna_profile = "MPEG_PS_PAL"
            elif ext == '.ts':
                dlna_profile = "MPEG_TS_SD_EU_ISO"
                
            # Map file extensions to MIME types
            content_type_map = {
                '.mp4': 'video/mp4',
                '.avi': 'video/x-msvideo', 
                '.mkv': 'video/x-matroska',
                '.mov': 'video/quicktime',
                '.wmv': 'video/x-ms-wmv',
                '.ts': 'video/MP2T',
                '.mpeg': 'video/mpeg',
                '.mpg': 'video/mpeg'
            }
            content_type = content_type_map.get(ext, 'video/mp4')
            
            # Create enhanced metadata for better compatibility
            metadata_template = """
            <DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/" 
                       xmlns:dc="http://purl.org/dc/elements/1.1/" 
                       xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/"
                       xmlns:dlna="urn:schemas-dlna-org:metadata-1-0/">
                <item id="1" parentID="0" restricted="0">
                    <dc:title>Video</dc:title>
                    <upnp:class>object.item.videoItem</upnp:class>
                    <res protocolInfo="http-get:*:{content_type}:DLNA.ORG_PN={dlna_profile};DLNA.ORG_OP=01;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01500000000000000000000000000000" 
                         size="0" 
                         duration="{duration}" 
                         bitrate="0"
                         sampleFrequency="0"
                         nrAudioChannels="0"
                         resolution="">{uri_video}</res>
                </item>
            </DIDL-Lite>
            """
            
            # Add duration info if we have it
            duration_str = "00:00:00"
            if hasattr(self, 'current_video_duration') and self.current_video_duration:
                # Format seconds to HH:MM:SS
                hours, remainder = divmod(int(self.current_video_duration), 3600)
                minutes, seconds = divmod(remainder, 60)
                duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            # Prepare video data with metadata
            video_data = {
                "uri_video": video_url,
                "type_video": ext[1:] if ext.startswith('.') else ext,
                "content_type": content_type,
                "dlna_profile": dlna_profile,
                "duration": duration_str,
            }
            
            # Create the metadata
            video_data["metadata"] = xmlescape(metadata_template.format(**video_data))
            
            # Send SetAVTransportURI command
            self._send_dlna_action(video_data, "SetAVTransportURI")
            time.sleep(1)  # Short pause between commands
            
            # Send Play command
            self._send_dlna_action(video_data, "Play")
            
            # Update device status
            self.update_playing(True)
            logger.info(f"[{self.name}] Video restarted successfully")
            
            # Update last activity time
            with self._thread_lock:
                self._last_activity_time = time.time()
                
            return True
            
        except Exception as e:
            logger.error(f"[{self.name}] Error during video restart: {e}")
            logger.debug(traceback.format_exc())
            return False
