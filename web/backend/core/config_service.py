"""
Configuration service for managing device and application configuration.
Provides thread-safe access to device configurations and prevents duplicate loading.
"""

import json
import os
import logging
import threading
import time
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class ConfigService:
    """
    Thread-safe configuration service for device configurations
    Provides a single source of truth for configuration data
    """
    _instance = None
    _lock = threading.Lock()
    
    @classmethod
    def get_instance(cls):
        """
        Get the singleton instance of the ConfigService
        
        Returns:
            ConfigService: The singleton instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """
        Initialize the ConfigService
        """
        self._config_lock = threading.RLock()  # Using RLock to allow re-entrant locking
        self._lock_timeout = 5.0  # Timeout in seconds
        self._device_configs: Dict[str, Dict[str, Any]] = {}
        self._config_sources: Dict[str, str] = {}  # Track where each config came from
        self._loaded_files: List[str] = []  # Track which files have been loaded
    
    def _acquire_lock(self):
        """Acquire the config lock with timeout to prevent deadlock"""
        start_time = time.time()
        while not self._config_lock.acquire(blocking=False):
            time.sleep(0.1)
            if time.time() - start_time > self._lock_timeout:
                logger.warning("Failed to acquire config lock within timeout")
                return False
        return True
    
    def _release_lock(self):
        """Release the config lock"""
        try:
            self._config_lock.release()
        except RuntimeError:
            # Lock wasn't held
            pass
    
    def clear_configurations(self):
        """
        Clear all loaded configurations
        """
        if not self._acquire_lock():
            return
        try:
            self._device_configs.clear()
            self._config_sources.clear()
            self._loaded_files.clear()
            logger.info("Cleared all device configurations")
        finally:
            self._release_lock()
    
    def get_device_config(self, device_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the configuration for a device
        
        Args:
            device_name: Name of the device
            
        Returns:
            Optional[Dict[str, Any]]: Device configuration if found, None otherwise
        """
        if not self._acquire_lock():
            return None
            
        try:
            config = self._device_configs.get(device_name)
            if config:
                # Return a copy to prevent modification
                return dict(config)
            return None
        finally:
            self._release_lock()
    
    def get_all_device_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all device configurations
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of device configurations
        """
        if not self._acquire_lock():
            return {}
        try:
            return self._device_configs.copy()
        finally:
            self._release_lock()
    
    def add_device_config(self, device_name: str, config: Dict[str, Any], source: str = "manual") -> bool:
        """
        Add a device configuration
        
        Args:
            device_name: Name of the device
            config: Device configuration
            source: Source of the configuration
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._acquire_lock():
            return False
            
        try:
            # Validate required fields
            required_fields = ["type", "hostname", "action_url", "video_file"]
            missing_fields = [field for field in required_fields if not config.get(field)]
            if missing_fields:
                logger.error(f"Missing required fields for device {device_name}: {missing_fields}")
                return False
                
            # Ensure device_name is in the config
            config["device_name"] = device_name
            
            # Check if the video file exists
            video_file = config.get("video_file")
            if not os.path.exists(video_file):
                logger.error(f"Video file not found: {video_file}")
                return False
                
            # Check if this would override a higher priority source
            current_source = self._config_sources.get(device_name)
            if current_source:
                if self._get_source_priority(current_source) > self._get_source_priority(source):
                    logger.warning(f"Not overriding configuration for {device_name} from {current_source} with {source}")
                    return False
                    
            # Store the configuration
            self._device_configs[device_name] = config
            self._config_sources[device_name] = source
            logger.info(f"Added device configuration for {device_name} from {source}")
            return True
        finally:
            self._release_lock()
    
    def _get_source_priority(self, source: str) -> int:
        """
        Get the priority of a configuration source
        
        Args:
            source: Source to get priority for
            
        Returns:
            int: Priority value (higher is more important)
        """
        # Config files have higher priority than manual configurations
        if source.endswith('.json'):
            return 100
        return 50
    
    def update_device_config(self, device_name: str, config_update: Dict[str, Any], source: str = "manual") -> bool:
        """
        Update a device configuration
        
        Args:
            device_name: Name of the device
            config_update: Configuration updates
            source: Source of the configuration
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._acquire_lock():
            return False
        try:
            if device_name not in self._device_configs:
                logger.warning(f"Device {device_name} not found in configurations")
                return False
            
            # Update the configuration
            current_config = self._device_configs[device_name]
            current_config.update(config_update)
            self._config_sources[device_name] = source
            logger.info(f"Updated device configuration for {device_name} from {source}")
            return True
        finally:
            self._release_lock()
    
    def remove_device_config(self, device_name: str) -> bool:
        """
        Remove a device configuration
        
        Args:
            device_name: Name of the device
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._acquire_lock():
            return False
        try:
            if device_name not in self._device_configs:
                logger.warning(f"Device {device_name} not found in configurations")
                return False
            
            # Remove the configuration
            del self._device_configs[device_name]
            if device_name in self._config_sources:
                del self._config_sources[device_name]
            logger.info(f"Removed device configuration for {device_name}")
            return True
        finally:
            self._release_lock()
    
    def load_configs_from_file(self, config_file: str) -> List[str]:
        """
        Load device configurations from a file
        
        Args:
            config_file: Path to the configuration file
            
        Returns:
            List[str]: List of device names that were loaded
        """
        if not self._acquire_lock():
            return []
            
        try:
            logger.info(f"Loading configurations from {config_file}")
            
            # Clear existing configurations from this source
            self._clear_configs_from_source(config_file)
            
            # Load and validate the configuration file
            with open(config_file, 'r') as f:
                configs = json.load(f)
                
            if not isinstance(configs, list):
                logger.error(f"Invalid configuration format in {config_file}, expected a list")
                return []
                
            loaded_devices = []
            for config in configs:
                if not isinstance(config, dict):
                    logger.error(f"Invalid configuration entry in {config_file}, expected a dictionary")
                    continue
                    
                device_name = config.get("device_name")
                if not device_name:
                    logger.error("Missing device_name in configuration entry")
                    continue
                    
                # Validate required fields
                required_fields = ["type", "hostname", "action_url", "video_file"]
                missing_fields = [field for field in required_fields if not config.get(field)]
                if missing_fields:
                    logger.error(f"Missing required fields for device {device_name}: {missing_fields}")
                    continue
                    
                # Validate video file exists
                video_file = config.get("video_file")
                if not os.path.exists(video_file):
                    logger.error(f"Video file not found for device {device_name}: {video_file}")
                    continue
                    
                # Store the configuration
                if self.add_device_config(device_name, config, source=config_file):
                    loaded_devices.append(device_name)
                    logger.info(f"Loaded configuration for device {device_name}")
                else:
                    logger.error(f"Failed to add configuration for device {device_name}")
                    
            logger.info(f"Successfully loaded {len(loaded_devices)} device configurations from {config_file}")
            return loaded_devices
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file {config_file}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error loading configurations from {config_file}: {e}")
            return []
        finally:
            self._release_lock()
            
    def _clear_configs_from_source(self, source: str) -> None:
        """
        Clear all configurations from a specific source
        
        Args:
            source: Source to clear configurations from
        """
        to_remove = []
        for device_name, src in self._config_sources.items():
            if src == source:
                to_remove.append(device_name)
                
        for device_name in to_remove:
            del self._device_configs[device_name]
            del self._config_sources[device_name]
            logger.info(f"Cleared configuration for device {device_name} from {source}")
            
    def save_configs_to_file(self, config_file: str, filter_source: Optional[str] = None) -> bool:
        """
        Save device configurations to a file
        
        Args:
            config_file: Path to the configuration file
            filter_source: Optional source filter to save only configurations from a specific source
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            abs_path = os.path.abspath(config_file)
            logger.info(f"Saving device configurations to {abs_path}")
            
            if not self._acquire_lock():
                return False
            
            try:
                # Filter configurations by source if requested
                configs_to_save = {}
                for device_name, config in self._device_configs.items():
                    if filter_source is None or self._config_sources.get(device_name) == filter_source:
                        configs_to_save[device_name] = config
            finally:
                self._release_lock()
                
            # Save the configurations without holding the lock
            with open(abs_path, "w") as f:
                json.dump(list(configs_to_save.values()), f, indent=4)
            
            logger.info(f"Saved {len(configs_to_save)} device configurations to {abs_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving configurations to {config_file}: {e}")
            return False
    
    def get_config_source(self, device_name: str) -> Optional[str]:
        """
        Get the source of a device configuration
        
        Args:
            device_name: Name of the device
            
        Returns:
            Optional[str]: Source of the configuration if found, None otherwise
        """
        if not self._acquire_lock():
            return None
        try:
            return self._config_sources.get(device_name)
        finally:
            self._release_lock() 