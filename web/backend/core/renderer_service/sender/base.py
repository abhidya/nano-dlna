"""
Base Sender abstract class for the Renderer Service.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional


class Sender(ABC):
    """Abstract base class for all sender implementations."""
    
    @abstractmethod
    def __init__(self, config: Dict, logger: Optional[logging.Logger] = None):
        """Initialize the sender with configuration.
        
        Args:
            config: Configuration dictionary with sender-specific parameters
            logger: Optional logger for sender logging (uses default logger if not provided)
        """
        pass
    
    @abstractmethod
    def connect(self, target_id: str) -> bool:
        """Connect to the target device/display.
        
        Args:
            target_id: Identifier for the target (device name, ID, or display number)
            
        Returns:
            bool: True if connection was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from the target device/display.
        
        Returns:
            bool: True if disconnection was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def send_content(self, content_url: str) -> bool:
        """Send content to the target device/display.
        
        Args:
            content_url: URL or file path to the content to be displayed
            
        Returns:
            bool: True if content was successfully sent, False otherwise
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if sender is connected to target device/display.
        
        Returns:
            bool: True if connected, False otherwise
        """
        pass
    
    @abstractmethod
    def get_status(self) -> Dict:
        """Get current status of the sender.
        
        Returns:
            Dict: Status information in a dictionary format including:
                - type: String identifier of the sender type
                - connected: Boolean indicating if sender is connected
                - target: Target identifier
                - Additional sender-specific status information
        """
        pass 