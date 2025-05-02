#!/usr/bin/env python3
import requests
import json
import sys
import os
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_devices(api_url="http://localhost:8000"):
    """
    Get all devices from the API
    
    Args:
        api_url: API URL
    
    Returns:
        list: List of devices
    """
    try:
        response = requests.get(f"{api_url}/api/devices")
        if response.status_code == 200:
            data = response.json()
            return data["devices"]
        else:
            logger.error(f"Error getting devices: {response.status_code} {response.text}")
            return []
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        return []

def discover_devices(api_url="http://localhost:8000", timeout=5.0):
    """
    Discover DLNA devices on the network
    
    Args:
        api_url: API URL
        timeout: Timeout for discovery in seconds
    
    Returns:
        list: List of discovered devices
    """
    try:
        response = requests.get(
            f"{api_url}/api/devices/discover",
            params={"timeout": timeout}
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Discovered {len(data['devices'])} devices")
            return data["devices"]
        else:
            logger.error(f"Error discovering devices: {response.status_code} {response.text}")
            return []
    except Exception as e:
        logger.error(f"Error discovering devices: {e}")
        return []

def update_device(device_id, update_data, api_url="http://localhost:8000"):
    """
    Update a device
    
    Args:
        device_id: ID of the device to update
        update_data: Data to update
        api_url: API URL
    
    Returns:
        dict: Updated device
    """
    try:
        response = requests.put(
            f"{api_url}/api/devices/{device_id}",
            json=update_data
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Updated device {device_id}")
            return data
        else:
            logger.error(f"Error updating device {device_id}: {response.status_code} {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error updating device {device_id}: {e}")
        return None

def fix_devices(api_url="http://localhost:8000"):
    """
    Fix all devices
    
    Args:
        api_url: API URL
    """
    # First, discover devices
    logger.info("Discovering devices...")
    discover_devices(api_url)
    
    # Get all devices
    logger.info("Getting devices...")
    devices = get_devices(api_url)
    
    if not devices:
        logger.error("No devices found")
        return
    
    logger.info(f"Found {len(devices)} devices")
    
    # Fix each device
    for device in devices:
        device_id = device["id"]
        device_name = device["name"]
        device_type = device["type"]
        device_status = device["status"]
        
        logger.info(f"Device {device_id} ({device_name}): type={device_type}, status={device_status}")
        
        # Update the device status to "connected"
        if device_status == "disconnected":
            logger.info(f"Updating device {device_id} ({device_name}) status to connected")
            update_data = {
                "status": "connected"
            }
            update_device(device_id, update_data, api_url)

def main():
    """
    Main function
    """
    api_url = "http://localhost:8000"
    
    # Fix devices
    fix_devices(api_url)
    
    logger.info("Done")

if __name__ == "__main__":
    main()
