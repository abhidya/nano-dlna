"""
Base Renderer class for the Renderer Service.

This module defines the abstract base class for all renderers.
"""

import logging
import os
import threading
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable, Tuple, Union


class RendererError(Exception):
    """Base exception for renderer errors."""
    pass


class RendererConfigError(RendererError):
    """Exception raised for configuration errors."""
    pass


class RendererRuntimeError(RendererError):
    """Exception raised for runtime errors."""
    pass


class Renderer(ABC):
    """
    Abstract base class for all renderers.
    
    A renderer is responsible for rendering a scene (HTML, video, etc.) and
    preparing it for output to a display device through a sender.
    """
    
    @abstractmethod
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """
        Initialize the renderer with configuration.
        
        Args:
            config: Configuration dictionary for the renderer
            logger: Logger instance for logging
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.is_running = False
        self.is_paused = False
        self.current_scene = None
        self.rendered_content_url = None
        self.event_handlers = {}
        self.resources = []
        self.lock = threading.Lock()
        self.error_state = None
        self.last_error = None
        self.health_check_interval = config.get('health_check_interval', 30)  # seconds
        self.health_check_thread = None
        self.health_check_running = False
    
    @abstractmethod
    def render(self, scene_template: str, scene_data: Dict[str, Any]) -> str:
        """
        Render a scene using the provided template and data.
        
        Args:
            scene_template: Path to the scene template (HTML file, video file, etc.)
            scene_data: Data to be used in rendering the scene
            
        Returns:
            URL or path to the rendered content that can be used by a sender
        """
        pass
    
    @abstractmethod
    def start(self) -> bool:
        """
        Start the renderer.
        
        Returns:
            True if the renderer was started successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def stop(self) -> bool:
        """
        Stop the renderer.
        
        Returns:
            True if the renderer was stopped successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def pause(self) -> bool:
        """
        Pause the renderer.
        
        Returns:
            True if the renderer was paused successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def resume(self) -> bool:
        """
        Resume the renderer.
        
        Returns:
            True if the renderer was resumed successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def is_alive(self) -> bool:
        """
        Check if the renderer is still running.
        
        Returns:
            True if the renderer is running, False otherwise
        """
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the renderer.
        
        Returns:
            Dictionary containing status information
        """
        pass
    
    @abstractmethod
    def update_config(self, config: Dict[str, Any]) -> bool:
        """
        Update the renderer configuration.
        
        Args:
            config: New configuration dictionary
            
        Returns:
            True if the configuration was updated successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def _process_content(self, content: Any, data: Dict[str, Any]) -> Any:
        """
        Process content before rendering.
        
        Args:
            content: Original content
            data: Data to be used in processing
            
        Returns:
            Processed content
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> bool:
        """
        Clean up resources used by the renderer.
        
        Returns:
            True if cleanup was successful, False otherwise
        """
        pass
    
    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """
        Register an event handler for a specific event type.
        
        Args:
            event_type: Type of event to handle
            handler: Function to call when the event occurs
        """
        with self.lock:
            if event_type not in self.event_handlers:
                self.event_handlers[event_type] = []
            self.event_handlers[event_type].append(handler)
    
    def unregister_event_handler(self, event_type: str, handler: Callable) -> bool:
        """
        Unregister an event handler.
        
        Args:
            event_type: Type of event
            handler: Handler function to unregister
            
        Returns:
            True if the handler was unregistered, False otherwise
        """
        with self.lock:
            if event_type in self.event_handlers and handler in self.event_handlers[event_type]:
                self.event_handlers[event_type].remove(handler)
                return True
            return False
    
    def trigger_event(self, event_type: str, event_data: Dict[str, Any] = None) -> None:
        """
        Trigger an event and call all registered handlers.
        
        Args:
            event_type: Type of event
            event_data: Data to pass to the handlers
        """
        if event_data is None:
            event_data = {}
        
        with self.lock:
            handlers = self.event_handlers.get(event_type, []).copy()
        
        for handler in handlers:
            try:
                handler(event_type, event_data)
            except Exception as e:
                self.logger.error(f"Error in event handler for {event_type}: {str(e)}")
    
    def register_resource(self, resource: Any, cleanup_func: Callable = None) -> None:
        """
        Register a resource for cleanup.
        
        Args:
            resource: Resource to register
            cleanup_func: Function to call to clean up the resource
        """
        with self.lock:
            self.resources.append((resource, cleanup_func))
    
    def cleanup_resources(self) -> bool:
        """
        Clean up all registered resources.
        
        Returns:
            True if all resources were cleaned up successfully, False otherwise
        """
        success = True
        with self.lock:
            resources = self.resources.copy()
            self.resources = []
        
        for resource, cleanup_func in resources:
            try:
                if cleanup_func:
                    cleanup_func(resource)
                elif hasattr(resource, 'close'):
                    resource.close()
                elif hasattr(resource, 'cleanup'):
                    resource.cleanup()
            except Exception as e:
                self.logger.error(f"Error cleaning up resource: {str(e)}")
                success = False
        
        return success
    
    def set_error_state(self, error: Exception) -> None:
        """
        Set the error state of the renderer.
        
        Args:
            error: Exception that caused the error
        """
        self.error_state = True
        self.last_error = error
        self.logger.error(f"Renderer error: {str(error)}")
        self.trigger_event('error', {'error': error, 'message': str(error)})
    
    def clear_error_state(self) -> None:
        """
        Clear the error state of the renderer.
        """
        self.error_state = None
        self.last_error = None
    
    def start_health_check(self) -> None:
        """
        Start the health check thread.
        """
        if self.health_check_thread and self.health_check_thread.is_alive():
            return
        
        self.health_check_running = True
        self.health_check_thread = threading.Thread(
            target=self._health_check_loop,
            daemon=True
        )
        self.health_check_thread.start()
    
    def stop_health_check(self) -> None:
        """
        Stop the health check thread.
        """
        self.health_check_running = False
        if self.health_check_thread:
            self.health_check_thread.join(timeout=5)
            self.health_check_thread = None
    
    def _health_check_loop(self) -> None:
        """
        Health check loop to monitor the renderer.
        """
        while self.health_check_running:
            try:
                if self.is_running and not self.is_alive():
                    self.logger.warning("Renderer is not alive but is marked as running")
                    self.trigger_event('health_check_failed', {'message': 'Renderer is not alive'})
                
                # Additional health checks can be implemented by subclasses
                self._perform_health_check()
                
            except Exception as e:
                self.logger.error(f"Error in health check: {str(e)}")
            
            time.sleep(self.health_check_interval)
    
    def _perform_health_check(self) -> None:
        """
        Perform renderer-specific health checks.
        This method should be overridden by subclasses.
        """
        pass
    
    def _ensure_directory_exists(self, path: str) -> None:
        """
        Ensure that the directory for the given path exists.
        
        Args:
            path: Path to check
        """
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
