"""
Renderer Service implementation.

This module provides the main functionality for the Renderer Service,
which manages scene rendering on different display technologies.
"""

import logging
import os
import json
import threading
from urllib.parse import urlencode
from typing import Dict, Any, Optional, List, Tuple

from .renderer import Renderer, ChromeRenderer
from .sender import AirPlaySender, HDMISender
from ..dlna_device import DLNADevice


class RendererService:
    """
    Renderer Service for managing scene rendering on different display technologies.
    
    This service provides functionality to start and stop renderers, and to send
    rendered content to display devices.
    """
    
    def __init__(self, config_file: str = None, logger: Optional[logging.Logger] = None):
        """
        Initialize the Renderer Service with configuration.
        
        Args:
            config_file: Path to the configuration file
            logger: Logger instance for logging
        """
        self.logger = logger or logging.getLogger(__name__)
        self.config_file = config_file or os.path.join(os.path.dirname(__file__), '../../config/renderer_config.json')
        self.config = self._load_config()
        self.renderers = {}
        self.active_renderers = {}
        self.lock = threading.RLock()
        self.streaming_server = None
        self._lan_ip = None
        self.projector_power_states = {}
        # Persisted projection state so HDMI projections survive a restart/power cycle.
        self.state_file = os.path.join(
            os.path.dirname(os.path.abspath(self.config_file)), 'renderer_state.json'
        )
        self._shutting_down = False
        
    def start_streaming_server(self):
        """Starts the internal TwistedStreamingServer."""
        if not self._lan_ip:
            import socket
            try:
                # Create a socket that connects to an external server
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                self._lan_ip = s.getsockname()[0]
                s.close()
            except Exception as e:
                self.logger.error(f"Error detecting LAN IP: {str(e)}")
                self._lan_ip = '127.0.0.1'
            self.logger.info(f"Auto-detected LAN IP for streaming: {self._lan_ip}")

        try:
            # Pass an empty dict for files initially, can be updated later
            self._get_streaming_server().start_server({}, serve_ip=self._lan_ip)
            self.logger.info(f"Streaming server started on {self._lan_ip} using configured port range.")
        except Exception as e:
            self.logger.error(f"Failed to start streaming server in RendererService: {e}")
            # Potentially re-raise or handle as critical failure
            raise

    def _get_streaming_server(self):
        if self.streaming_server is None:
            from ..twisted_streaming import TwistedStreamingServer

            self.streaming_server = TwistedStreamingServer()
        return self.streaming_server
        
    def _load_config(self) -> Dict[str, Any]:
        """
        Load the configuration from the config file.
        
        Returns:
            Configuration dictionary
        """
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            self.logger.info(f"Loaded configuration from {self.config_file}")
            return config
        except Exception as e:
            self.logger.error(f"Error loading configuration: {str(e)}")
            return {
                'senders': {},
                'renderers': {},
                'scenes': {},
                'projectors': {}
            }
    
    def get_renderer(self, renderer_type: str) -> Optional[Renderer]:
        """
        Get a renderer instance of the specified type.
        
        Args:
            renderer_type: Type of renderer to get
            
        Returns:
            Renderer instance or None if the renderer type is not supported
        """
        with self.lock:
            if renderer_type in self.renderers:
                return self.renderers[renderer_type]
            
            # Check if the renderer type exists in the configuration
            renderer_config = self.config.get('renderers', {}).get(renderer_type)
            if renderer_config:
                # For now, we only support Chrome-based renderers
                if renderer_type.startswith('chrome'):
                    renderer = ChromeRenderer(renderer_config, self.logger)
                    self.renderers[renderer_type] = renderer
                    return renderer
            
            self.logger.error(f"Unsupported renderer type: {renderer_type}")
            return None
    
    def get_scene_config(self, scene_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the configuration for a scene.
        
        Args:
            scene_id: ID of the scene
            
        Returns:
            Scene configuration or None if the scene is not found
        """
        return self.config.get('scenes', {}).get(scene_id)
    
    def get_projector_config(self, projector_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the configuration for a projector.
        
        Args:
            projector_id: ID of the projector
            
        Returns:
            Projector configuration or None if the projector is not found
        """
        return self.config.get('projectors', {}).get(projector_id)
    
    def render_scene(self, scene_id: str, renderer_type: str = 'chrome') -> Optional[str]:
        """
        Render a scene using the specified renderer.
        
        Args:
            scene_id: ID of the scene to render
            renderer_type: Type of renderer to use
            
        Returns:
            URL or path to the rendered content, or None if rendering failed
        """
        scene_config = self.get_scene_config(scene_id)
        if not scene_config:
            self.logger.error(f"Scene not found: {scene_id}")
            return None
        
        renderer = self.get_renderer(renderer_type)
        if not renderer:
            self.logger.error(f"Renderer not found: {renderer_type}")
            return None
        
        try:
            template = scene_config.get('template')
            data = scene_config.get('data', {})
            
            # Render the scene
            rendered_content_url = renderer.render(template, data)
            self.logger.info(f"Rendered scene {scene_id} to {rendered_content_url}")
            
            return rendered_content_url
            
        except Exception as e:
            self.logger.error(f"Error rendering scene {scene_id}: {str(e)}")
            return None
    
    def start_renderer(self, scene_id: str, projector_id: str) -> bool:
        """
        Start a configured scene on a projector.
        """
        with self.lock:
            if projector_id in self.active_renderers:
                self.logger.warning("Projector %s already active; restarting", projector_id)
                self.stop_renderer(projector_id)

            projector_config = self.get_projector_config(projector_id)
            if not projector_config:
                self.logger.error("Projector not found: %s", projector_id)
                return False

            scene_config = self.get_scene_config(scene_id)
            if not scene_config:
                self.logger.error("Scene not found: %s", scene_id)
                return False

            renderer_type = projector_config.get('renderer', 'chrome')
            rendered_content_url = self.render_scene(scene_id, renderer_type)
            if not rendered_content_url:
                self.logger.error("Failed to render scene %s", scene_id)
                return False

            renderer = self.get_renderer(renderer_type)
            if not renderer:
                self.logger.error("Renderer not found: %s", renderer_type)
                return False

            sender_type = projector_config.get('sender')
            target_name = projector_config.get('target_name')
            sender = None

            if sender_type == 'hdmi':
                sender = self._create_sender(sender_type, projector_id)
                if not sender or not sender.connect(target_name):
                    self.logger.error("Failed to connect HDMI sender for projector %s", projector_id)
                    return False
                if not sender.send_content(rendered_content_url):
                    self.logger.error("Failed to send rendered scene to HDMI display %s", target_name)
                    sender.disconnect()
                    return False
            else:
                if not renderer.start():
                    self.logger.error("Failed to start renderer for scene %s", scene_id)
                    return False

                if sender_type == 'dlna':
                    success = self._send_to_dlna(target_name, rendered_content_url)
                    if not success:
                        self.logger.error("Failed to send content to DLNA device %s", target_name)
                        renderer.stop()
                        return False
                elif sender_type == 'direct':
                    pass
                elif sender_type == 'airplay':
                    sender = self._create_sender(sender_type, projector_id)
                    if not target_name:
                        self.logger.error("No target name specified for AirPlay projector %s", projector_id)
                        renderer.stop()
                        return False
                    if not sender.connect(target_name):
                        self.logger.error("Failed to connect to AirPlay device %s", target_name)
                        renderer.stop()
                        return False
                    if not sender.send_content(rendered_content_url):
                        self.logger.error("Failed to send content to AirPlay device %s", target_name)
                        sender.disconnect()
                        renderer.stop()
                        return False
                else:
                    self.logger.error("Unsupported sender type: %s", sender_type)
                    renderer.stop()
                    return False

            self.active_renderers[projector_id] = {
                'renderer': renderer,
                'sender': sender,
                'scene_id': scene_id,
                'projector_id': projector_id,
                'sender_type': sender_type,
                'target_name': target_name,
                'content_mode': 'scene',
            }

            self._persist_state()
            self.logger.info("Started renderer for scene %s on projector %s", scene_id, projector_id)
            return True

    def list_hdmi_displays(self) -> List[Dict[str, Any]]:
        """List local displays that can be used as HDMI projector targets."""
        return HDMISender.discover_displays()

    def list_projectors(self) -> List[Dict[str, Any]]:
        """List configured projectors with runtime status."""
        projectors = []
        with self.lock:
            for projector_id, projector_data in self.config.get("projectors", {}).items():
                projector = dict(projector_data)
                projector["id"] = projector_id
                projector["runtime_status"] = self.get_renderer_status(projector_id)
                if projector.get("sender") == "hdmi" and not projector["runtime_status"]:
                    projector["runtime_status"] = self._idle_hdmi_status(projector_id, projector)
                projectors.append(projector)
        return projectors

    def list_scenes(self) -> List[Dict[str, Any]]:
        """List configured scenes with stable IDs."""
        scenes = []
        for scene_id, scene_data in self.config.get("scenes", {}).items():
            scene = dict(scene_data)
            scene["id"] = scene_id
            scene.setdefault("name", scene_id)
            scenes.append(scene)
        return scenes

    def start_projector(self, projector_id: str) -> bool:
        """Start a projector using its configured default scene or content mode."""
        projector_config = self.get_projector_config(projector_id)
        if not projector_config:
            self.logger.error("Projector not found: %s", projector_id)
            return False

        scene_id = projector_config.get("scene")
        if scene_id:
            return self.start_renderer(scene_id, projector_id)

        if projector_config.get("sender") == "hdmi":
            mode = projector_config.get("content_mode", "identify")
            return self.start_projector_mode(
                projector_id,
                mode,
                projector_config.get("content_options", {}),
            )

        self.logger.error("No default scene configured for projector %s", projector_id)
        return False

    def _idle_hdmi_status(self, projector_id: str, projector: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "projector_id": projector_id,
            "sender_type": "hdmi",
            "target_name": projector.get("target_name"),
            "content_mode": None,
            "status": "idle",
            "sender_status": {
                "type": "hdmi",
                "connection_state": "unknown",
                "projection_state": "idle",
                "power_state": self.projector_power_states.get(projector_id, "unknown"),
            },
        }

    def start_projector_mode(
        self,
        projector_id: str,
        mode: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Start a non-scene content mode on an HDMI projector."""
        options = options or {}
        if mode == "scene":
            scene_id = options.get("scene") or options.get("scene_id")
            if not scene_id:
                self.logger.error("Scene mode requires scene or scene_id option")
                return False
            return self.start_renderer(scene_id, projector_id)

        with self.lock:
            if projector_id in self.active_renderers:
                self.stop_renderer(projector_id)

            projector_config = self.get_projector_config(projector_id)
            if not projector_config:
                self.logger.error("Projector not found: %s", projector_id)
                return False

            sender_type = projector_config.get("sender")
            if sender_type != "hdmi":
                self.logger.error("Content mode %s requires an HDMI projector, got %s", mode, sender_type)
                return False

            sender = self._create_sender("hdmi", projector_id)
            target_name = projector_config.get("target_name")
            if not sender.connect(target_name):
                return False

            content_url = self._content_mode_url(mode, projector_id, options)
            if not content_url:
                sender.disconnect()
                return False

            if not sender.send_content(content_url):
                sender.disconnect()
                return False

            self.active_renderers[projector_id] = {
                "renderer": None,
                "sender": sender,
                "scene_id": None,
                "projector_id": projector_id,
                "sender_type": sender_type,
                "target_name": target_name,
                "content_mode": mode,
                "options": options,
            }
            self._persist_state()
            return True

    def identify_projector(self, projector_id: str) -> bool:
        """Launch an identify pattern on an HDMI projector."""
        return self.start_projector_mode(projector_id, "identify", {})

    def set_projector_power_state(self, projector_id: str, power_state: str) -> bool:
        """Set the user-observed projector power state."""
        if power_state not in HDMISender.VALID_POWER_STATES:
            self.logger.error("Invalid projector power state: %s", power_state)
            return False
        self.projector_power_states[projector_id] = power_state
        active = self.active_renderers.get(projector_id)
        sender = active.get("sender") if active else None
        if hasattr(sender, "set_power_state"):
            sender.set_power_state(power_state)
        self._persist_state()
        return True

    def record_projector_heartbeat(self, projector_id: str) -> bool:
        """Record a heartbeat from a browser-based projector page."""
        active = self.active_renderers.get(projector_id)
        sender = active.get("sender") if active else None
        if hasattr(sender, "record_heartbeat"):
            sender.record_heartbeat()
            return True
        return False

    def _create_sender(self, sender_type: str, projector_id: Optional[str] = None):
        sender_config = dict(self.config.get("senders", {}).get(sender_type, {}))
        if sender_type == "hdmi":
            if projector_id and projector_id in self.projector_power_states:
                sender_config["power_state"] = self.projector_power_states[projector_id]
            return HDMISender(sender_config, self.logger)
        if sender_type == "airplay":
            return AirPlaySender(sender_config, self.logger)
        return None

    def _server_base_url(self) -> str:
        return self.config.get("server_base_url") or os.environ.get("NANO_DLNA_SERVER_BASE_URL", "http://localhost:8000")

    def _content_mode_url(
        self,
        mode: str,
        projector_id: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        options = options or {}
        page_by_mode = {
            "identify": "hdmi_identify.html",
            "structured_light": "structured_light.html",
            "overlay": "overlay_window.html",
            "blank": "blank.html",
        }
        page = page_by_mode.get(mode)
        if not page:
            self.logger.error("Unsupported projector content mode: %s", mode)
            return None

        params = {"projector_id": projector_id, "mode": mode}
        params.update({
            key: self._url_param_value(value)
            for key, value in options.items()
            if value is not None
        })
        return f"{self._server_base_url().rstrip('/')}/static/{page}?{urlencode(params)}"

    @staticmethod
    def _url_param_value(value: Any) -> Any:
        if isinstance(value, bool):
            return str(value).lower()
        return value
    
    def _send_to_dlna(self, device_name: str, content_url: str) -> bool:
        """
        Send content to a DLNA device.
        
        Args:
            device_name: Name of the DLNA device
            content_url: URL or path to the content
            
        Returns:
            True if the content was sent successfully, False otherwise
        """
        try:
            # Import here to avoid circular imports
            from ..services.device_service import DeviceService # Changed to relative
            
            # Get the device instance
            device_service = DeviceService() # This instantiation might be problematic if DeviceService expects db/manager
            device = device_service.get_device_instance(device_name)
            
            if not device:
                self.logger.error(f"DLNA device not found: {device_name}")
                return False
            
            # If the content URL is a file:// URL, extract the file path
            if content_url.startswith('file://'):
                content_path = content_url[7:]
            else:
                content_path = content_url
            
            # Play the content on the device
            loop = True  # Always loop the content
            device.play(content_path, loop=loop)
            
            self.logger.info(f"Sent content to DLNA device {device_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending content to DLNA device {device_name}: {str(e)}")
            return False
    
    def stop_renderer(self, projector_id: str) -> bool:
        """
        Stop a renderer on a projector.
        
        Args:
            projector_id: ID of the projector
            
        Returns:
            True if the renderer was stopped successfully, False otherwise
        """
        with self.lock:
            if projector_id not in self.active_renderers:
                self.logger.warning(f"No active renderer found for projector {projector_id}")
                return True
            
            active_renderer = self.active_renderers[projector_id]
            renderer = active_renderer.get('renderer')
            sender = active_renderer.get('sender')
            sender_type = active_renderer['sender_type']
            target_name = active_renderer['target_name']
            
            # Stop the renderer
            if renderer and not renderer.stop():
                self.logger.error(f"Failed to stop renderer for projector {projector_id}")
                return False

            if sender and hasattr(sender, "disconnect"):
                sender.disconnect()
            
            # Stop the content on the device
            if sender_type == 'dlna':
                try:
                    # Import here to avoid circular imports
                    from ..services.device_service import DeviceService # Changed to relative
                    
                    # Get the device instance
                    device_service = DeviceService() # This instantiation might be problematic
                    device = device_service.get_device_instance(target_name)
                    
                    if device:
                        device.stop()
                        self.logger.info(f"Stopped content on DLNA device {target_name}")
                    
                except Exception as e:
                    self.logger.error(f"Error stopping content on DLNA device {target_name}: {str(e)}")
            elif sender_type == 'airplay' and not sender:
                try:
                    # Get the sender from the active renderer
                    sender = active_renderer.get('sender')
                    if sender:
                        # Disconnect from the AirPlay device
                        if sender.disconnect():
                            self.logger.info(f"Disconnected from AirPlay device {target_name}")
                        else:
                            self.logger.error(f"Failed to disconnect from AirPlay device {target_name}")
                except Exception as e:
                    self.logger.error(f"Error disconnecting from AirPlay device {target_name}: {str(e)}")
            
            # Remove the active renderer
            del self.active_renderers[projector_id]

            self._persist_state()
            self.logger.info(f"Stopped renderer for projector {projector_id}")
            return True
    
    def pause_renderer(self, projector_id: str) -> bool:
        """
        Pause a renderer on a projector.
        
        Args:
            projector_id: ID of the projector
            
        Returns:
            True if the renderer was paused successfully, False otherwise
        """
        with self.lock:
            if projector_id not in self.active_renderers:
                self.logger.warning(f"No active renderer found for projector {projector_id}")
                return False
            
            active_renderer = self.active_renderers[projector_id]
            renderer = active_renderer.get('renderer')
            if not renderer:
                self.logger.warning("Projector %s has no pausable renderer", projector_id)
                return False
            
            # Pause the renderer
            success = renderer.pause()
            
            if success:
                self.logger.info(f"Paused renderer for projector {projector_id}")
                # Update the status to indicate the renderer is paused
                active_renderer['status'] = 'paused'
            else:
                self.logger.error(f"Failed to pause renderer for projector {projector_id}")
            
            return success
    
    def resume_renderer(self, projector_id: str) -> bool:
        """
        Resume a paused renderer on a projector.
        
        Args:
            projector_id: ID of the projector
            
        Returns:
            True if the renderer was resumed successfully, False otherwise
        """
        with self.lock:
            if projector_id not in self.active_renderers:
                self.logger.warning(f"No active renderer found for projector {projector_id}")
                return False
            
            active_renderer = self.active_renderers[projector_id]
            renderer = active_renderer.get('renderer')
            if not renderer:
                self.logger.warning("Projector %s has no resumable renderer", projector_id)
                return False
            
            # Resume the renderer
            success = renderer.resume()
            
            if success:
                self.logger.info(f"Resumed renderer for projector {projector_id}")
                # Update the status to indicate the renderer is running
                active_renderer['status'] = 'running'
            else:
                self.logger.error(f"Failed to resume renderer for projector {projector_id}")
            
            return success
    
    def get_renderer_status(self, projector_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a renderer on a projector.
        
        Args:
            projector_id: ID of the projector
            
        Returns:
            Status dictionary or None if no renderer is active on the projector
        """
        with self.lock:
            if projector_id not in self.active_renderers:
                return None
            
            active_renderer = self.active_renderers[projector_id]
            renderer = active_renderer.get('renderer')
            sender = active_renderer.get('sender')

            status = renderer.get_status() if renderer else {}
            sender_status = sender.get_status() if sender and hasattr(sender, "get_status") else None
            status.update({
                'scene_id': active_renderer['scene_id'],
                'projector_id': active_renderer['projector_id'],
                'sender_type': active_renderer['sender_type'],
                'target_name': active_renderer['target_name'],
                'content_mode': active_renderer.get('content_mode', 'scene'),
                'options': active_renderer.get('options', {}),
                'sender_status': sender_status,
                'status': active_renderer.get(
                    'status',
                    'running' if not renderer or not getattr(renderer, 'is_paused', False) else 'paused',
                )
            })
            if sender_status and sender_status.get("projection_state"):
                status["status"] = sender_status["projection_state"]
            
            return status
    
    def list_active_renderers(self) -> List[Dict[str, Any]]:
        """
        List all active renderers.
        
        Returns:
            List of active renderer status dictionaries
        """
        with self.lock:
            return [self.get_renderer_status(projector_id) for projector_id in self.active_renderers]
    
    def _persist_state(self) -> None:
        """Write resumable projection state to disk for power-cycle recovery.

        Only the recipe needed to relaunch is stored (mode, scene, options,
        target) -- never the live renderer/sender objects. Skipped during a
        graceful shutdown so a reboot still resumes what was active.
        """
        if self._shutting_down:
            return
        try:
            with self.lock:
                projections = [
                    {
                        "projector_id": projector_id,
                        "content_mode": active.get("content_mode", "scene"),
                        "scene_id": active.get("scene_id"),
                        "options": active.get("options", {}),
                        "target_name": active.get("target_name"),
                    }
                    for projector_id, active in self.active_renderers.items()
                ]
                state = {
                    "projections": projections,
                    "power_states": dict(self.projector_power_states),
                }
            tmp_file = f"{self.state_file}.tmp"
            with open(tmp_file, "w") as handle:
                json.dump(state, handle, indent=2)
            os.replace(tmp_file, self.state_file)
        except Exception as exc:
            self.logger.error(f"Failed to persist renderer state: {exc}")

    def _load_state(self) -> Optional[Dict[str, Any]]:
        """Load persisted projection state, or None if there is nothing saved."""
        try:
            if not os.path.exists(self.state_file):
                return None
            with open(self.state_file, "r") as handle:
                return json.load(handle)
        except Exception as exc:
            self.logger.error(f"Failed to load renderer state: {exc}")
            return None

    def resume_active_projections(self, attempts: int = 10, delay: float = 3.0) -> None:
        """Re-launch projections that were active before a restart.

        Each projection is replayed in a background thread that retries, so the
        HDMI display has time to come up after a power cycle. Call this once at
        startup, after the streaming server is running.
        """
        state = self._load_state()
        if not state:
            return

        # Restore manual power states first so HDMI senders report correctly.
        power_states = state.get("power_states") or {}
        if isinstance(power_states, dict):
            self.projector_power_states.update(power_states)

        projections = state.get("projections") or []
        if not projections:
            return

        self.logger.info("Resuming %d saved projection(s) after restart", len(projections))
        for projection in projections:
            thread = threading.Thread(
                target=self._resume_one,
                args=(projection, attempts, delay),
                daemon=True,
            )
            thread.start()

    def _resume_one(self, projection: Dict[str, Any], attempts: int, delay: float) -> None:
        """Replay a single saved projection with retries."""
        import time

        projector_id = projection.get("projector_id")
        if not projector_id:
            return
        content_mode = projection.get("content_mode") or "scene"
        scene_id = projection.get("scene_id")
        options = projection.get("options") or {}

        for attempt in range(1, attempts + 1):
            try:
                if content_mode == "scene":
                    if not scene_id:
                        self.logger.error(
                            "Cannot resume scene projection for %s without scene_id", projector_id
                        )
                        return
                    success = self.start_renderer(scene_id, projector_id)
                else:
                    success = self.start_projector_mode(projector_id, content_mode, options)
                if success:
                    self.logger.info(
                        "Resumed projection on %s (mode=%s) on attempt %d",
                        projector_id, content_mode, attempt,
                    )
                    return
            except Exception as exc:
                self.logger.warning(
                    "Resume attempt %d for projector %s failed: %s", attempt, projector_id, exc
                )
            time.sleep(delay)

        self.logger.error(
            "Gave up resuming projection on %s after %d attempts", projector_id, attempts
        )

    def shutdown(self) -> None:
        """
        Shutdown the Renderer Service.

        This method stops all active renderers and cleans up resources.
        """
        with self.lock:
            # Mark shutdown so stop_renderer does not clear the persisted
            # resume state: a reboot should bring these projections back.
            self._shutting_down = True

            # Stop all active renderers
            for projector_id in list(self.active_renderers.keys()):
                self.stop_renderer(projector_id)
            
            # Stop the streaming server
            if self.streaming_server:
                self.streaming_server.stop_server()
            
            self.logger.info("Renderer Service shutdown complete")
