"""
Module for device discovery.

This module wraps the devices.py functionality for backward compatibility.
"""

from .devices import (
    get_devices,
    register_device,
    remove_duplicates,
    get_xml_field_text,
    SSDP_BROADCAST_PORT,
    SSDP_BROADCAST_ADDR,
    SSDP_BROADCAST_MSG,
    UPNP_DEVICE_TYPE,
    UPNP_SERVICE_TYPE
)

import logging
import re


def search_devices(query=None, timeout=3.0, host=None):
    """
    Search for devices matching a query.
    
    Args:
        query: Query string to match against device names
        timeout: Timeout for the search in seconds
        host: Host to bind to for the search
        
    Returns:
        list: List of matching devices
    """
    devices = get_devices(timeout, host)
    
    if query:
        # Create a case-insensitive regex pattern
        pattern = re.compile(query, re.IGNORECASE)
        
        # Filter devices by name
        devices = [
            device for device in devices
            if device.get("friendly_name") and pattern.search(device["friendly_name"])
        ]
        
        if not devices:
            logging.info(f"No devices matching '{query}' found")
    
    return devices 