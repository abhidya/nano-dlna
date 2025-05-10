#!/usr/bin/env python3

import json
import os
import argparse
from pathlib import Path

def generate_sample_config(output_path):
    """
    Generate a sample device configuration file
    
    Args:
        output_path: Path to save the configuration file
    """
    sample_config = {
        "devices": [
            {
                "device_name": "Living Room TV",
                "type": "dlna",
                "hostname": "192.168.1.100",
                "action_url": "http://192.168.1.100:49152/upnp/control/AVTransport1",
                "friendly_name": "Living Room TV",
                "manufacturer": "Samsung",
                "location": "Living Room"
            },
            {
                "device_name": "Bedroom TV",
                "type": "dlna",
                "hostname": "192.168.1.101",
                "action_url": "http://192.168.1.101:49152/upnp/control/AVTransport1",
                "friendly_name": "Bedroom TV",
                "manufacturer": "LG",
                "location": "Bedroom"
            },
            {
                "device_name": "Office Projector",
                "type": "transcreen",
                "hostname": "192.168.1.102",
                "friendly_name": "Office Projector",
                "manufacturer": "Epson",
                "location": "Office"
            }
        ]
    }
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Write the configuration file
    with open(output_path, 'w') as f:
        json.dump(sample_config, f, indent=2)
    
    print(f"Sample configuration file generated at {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a sample device configuration file")
    parser.add_argument("--output", "-o", default="sample_device_config.json", help="Output file path")
    args = parser.parse_args()
    
    generate_sample_config(args.output)
