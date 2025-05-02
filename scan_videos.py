#!/usr/bin/env python3
import requests
import os
import sys
import json

def scan_directory(directory, api_url="http://localhost:8000"):
    """
    Scan a directory for videos and add them to the database
    
    Args:
        directory: Directory to scan for videos
        api_url: API URL
    """
    # Make sure the directory exists
    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist")
        return
    
    # Make sure the directory is absolute
    directory = os.path.abspath(directory)
    
    # Scan the directory for videos
    print(f"Scanning directory {directory} for videos...")
    
    try:
        response = requests.post(
            f"{api_url}/api/videos/scan-directory",
            params={"directory": directory}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data['videos'])} videos:")
            for video in data["videos"]:
                print(f"  - {video['name']} ({video['path']})")
        else:
            print(f"Error scanning directory: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Error scanning directory: {e}")

if __name__ == "__main__":
    # Get the directory from the command line
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        # Use the current directory
        directory = os.getcwd()
    
    scan_directory(directory)
