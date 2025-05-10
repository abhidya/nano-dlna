#!/usr/bin/env python3

import os
import argparse
import sqlite3
import json
from datetime import datetime

def generate_sample_data(db_path):
    """
    Generate sample data for the application
    
    Args:
        db_path: Path to the SQLite database file
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        type TEXT NOT NULL,
        hostname TEXT NOT NULL,
        action_url TEXT,
        friendly_name TEXT,
        manufacturer TEXT,
        location TEXT,
        status TEXT DEFAULT 'disconnected',
        is_playing BOOLEAN DEFAULT 0,
        current_video TEXT,
        config TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS videos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        path TEXT NOT NULL UNIQUE,
        file_name TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        duration REAL,
        format TEXT,
        resolution TEXT,
        has_subtitle BOOLEAN DEFAULT 0,
        subtitle_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP
    )
    ''')
    
    # Insert sample devices
    sample_devices = [
        {
            "name": "living_room_tv",
            "type": "dlna",
            "hostname": "192.168.1.100",
            "action_url": "http://192.168.1.100:49152/upnp/control/AVTransport1",
            "friendly_name": "Living Room TV",
            "manufacturer": "Samsung",
            "location": "Living Room",
            "status": "disconnected",
            "is_playing": False,
            "current_video": None,
            "config": json.dumps({
                "device_name": "living_room_tv",
                "type": "dlna",
                "hostname": "192.168.1.100",
                "action_url": "http://192.168.1.100:49152/upnp/control/AVTransport1",
                "friendly_name": "Living Room TV",
                "manufacturer": "Samsung",
                "location": "Living Room"
            })
        },
        {
            "name": "bedroom_tv",
            "type": "dlna",
            "hostname": "192.168.1.101",
            "action_url": "http://192.168.1.101:49152/upnp/control/AVTransport1",
            "friendly_name": "Bedroom TV",
            "manufacturer": "LG",
            "location": "Bedroom",
            "status": "disconnected",
            "is_playing": False,
            "current_video": None,
            "config": json.dumps({
                "device_name": "bedroom_tv",
                "type": "dlna",
                "hostname": "192.168.1.101",
                "action_url": "http://192.168.1.101:49152/upnp/control/AVTransport1",
                "friendly_name": "Bedroom TV",
                "manufacturer": "LG",
                "location": "Bedroom"
            })
        },
        {
            "name": "office_projector",
            "type": "transcreen",
            "hostname": "192.168.1.102",
            "action_url": None,
            "friendly_name": "Office Projector",
            "manufacturer": "Epson",
            "location": "Office",
            "status": "disconnected",
            "is_playing": False,
            "current_video": None,
            "config": json.dumps({
                "device_name": "office_projector",
                "type": "transcreen",
                "hostname": "192.168.1.102",
                "friendly_name": "Office Projector",
                "manufacturer": "Epson",
                "location": "Office"
            })
        }
    ]
    
    for device in sample_devices:
        try:
            cursor.execute('''
            INSERT INTO devices (
                name, type, hostname, action_url, friendly_name, manufacturer, location, 
                status, is_playing, current_video, config
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                device["name"], device["type"], device["hostname"], device["action_url"],
                device["friendly_name"], device["manufacturer"], device["location"],
                device["status"], device["is_playing"], device["current_video"], device["config"]
            ))
        except sqlite3.IntegrityError:
            # Device already exists, skip
            pass
    
    # Insert sample videos
    sample_videos = [
        {
            "name": "Big Buck Bunny",
            "path": "/tmp/nanodlna/uploads/big_buck_bunny.mp4",
            "file_name": "big_buck_bunny.mp4",
            "file_size": 158008374,
            "duration": 596.5,
            "format": "mp4",
            "resolution": "1920x1080",
            "has_subtitle": True,
            "subtitle_path": "/tmp/nanodlna/uploads/big_buck_bunny.srt"
        },
        {
            "name": "Sintel",
            "path": "/tmp/nanodlna/uploads/sintel.mp4",
            "file_name": "sintel.mp4",
            "file_size": 129241752,
            "duration": 888.0,
            "format": "mp4",
            "resolution": "1280x720",
            "has_subtitle": False,
            "subtitle_path": None
        },
        {
            "name": "Tears of Steel",
            "path": "/tmp/nanodlna/uploads/tears_of_steel.mp4",
            "file_name": "tears_of_steel.mp4",
            "file_size": 201258231,
            "duration": 734.2,
            "format": "mp4",
            "resolution": "1920x800",
            "has_subtitle": True,
            "subtitle_path": "/tmp/nanodlna/uploads/tears_of_steel.srt"
        }
    ]
    
    for video in sample_videos:
        try:
            cursor.execute('''
            INSERT INTO videos (
                name, path, file_name, file_size, duration, format, resolution, 
                has_subtitle, subtitle_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                video["name"], video["path"], video["file_name"], video["file_size"],
                video["duration"], video["format"], video["resolution"],
                video["has_subtitle"], video["subtitle_path"]
            ))
        except sqlite3.IntegrityError:
            # Video already exists, skip
            pass
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print(f"Sample data generated in {db_path}")
    print("Sample devices:")
    for device in sample_devices:
        print(f"  - {device['friendly_name']} ({device['type']})")
    print("Sample videos:")
    for video in sample_videos:
        print(f"  - {video['name']} ({video['format']}, {video['resolution']})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate sample data for the application")
    parser.add_argument("--db", default="data/nanodlna.db", help="Path to the SQLite database file")
    args = parser.parse_args()
    
    generate_sample_data(args.db)
