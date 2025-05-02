# transcreen.py

import logging
import requests

def play(file_url, device, loop):
    """
    Implement the Transcreen play functionality.
    """
    try:
        # Example: Send a request to the Transcreen device to play the video
        # Replace with actual Transcreen control code

        # Assuming Transcreen uses a specific API endpoint to play videos
        transcreen_play_url = f"http://{device['hostname']}/play"
        payload = {
            'url': file_url,
            'loop': loop
        }

        response = requests.post(transcreen_play_url, json=payload, timeout=5)
        response.raise_for_status()
        logging.debug(f"Sent Transcreen play command to {device['friendly_name']} with URL {file_url}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send Transcreen play command to '{device['friendly_name']}': {e}")
        raise

def stop(device):
    """
    Implement the Transcreen stop functionality.
    """
    try:
        # Example: Send a request to the Transcreen device to stop the video
        transcreen_stop_url = f"http://{device['hostname']}/stop"

        response = requests.post(transcreen_stop_url, timeout=5)
        response.raise_for_status()
        logging.debug(f"Sent Transcreen stop command to {device['friendly_name']}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send Transcreen stop command to '{device['friendly_name']}': {e}")
        raise
