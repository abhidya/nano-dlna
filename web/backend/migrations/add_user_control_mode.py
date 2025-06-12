#!/usr/bin/env python3
"""
Add user control mode to devices table

This migration adds fields to track when a device is under user control
vs automatic discovery loop control.
"""

import sqlite3
import sys
import os
from datetime import datetime

def upgrade():
    """Add user control mode fields to devices table"""
    # Look for database in a few common locations
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "nanodlna.db"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "nano_dlna.db"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "nano_dlna.db"),
        "./nanodlna.db",
        "./nano_dlna.db",
        "./data/nano_dlna.db"
    ]
    
    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        # Try to find any .db file
        for root, dirs, files in os.walk(os.path.dirname(os.path.dirname(__file__))):
            for file in files:
                if file.endswith('.db'):
                    db_path = os.path.join(root, file)
                    break
            if db_path:
                break
    
    if not db_path:
        print("Database not found! Please ensure the dashboard has been started at least once.")
        return False
    
    print(f"Found database at: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(devices)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add user_control_mode column if it doesn't exist
        if 'user_control_mode' not in columns:
            print("Adding user_control_mode column...")
            cursor.execute("""
                ALTER TABLE devices 
                ADD COLUMN user_control_mode VARCHAR(50) DEFAULT 'auto'
            """)
            print("✓ Added user_control_mode column")
        else:
            print("✓ user_control_mode column already exists")
        
        # Add user_control_expires_at column if it doesn't exist
        if 'user_control_expires_at' not in columns:
            print("Adding user_control_expires_at column...")
            cursor.execute("""
                ALTER TABLE devices 
                ADD COLUMN user_control_expires_at TIMESTAMP
            """)
            print("✓ Added user_control_expires_at column")
        else:
            print("✓ user_control_expires_at column already exists")
        
        # Add user_control_reason column if it doesn't exist
        if 'user_control_reason' not in columns:
            print("Adding user_control_reason column...")
            cursor.execute("""
                ALTER TABLE devices 
                ADD COLUMN user_control_reason VARCHAR(255)
            """)
            print("✓ Added user_control_reason column")
        else:
            print("✓ user_control_reason column already exists")
        
        # Create index for performance
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_devices_user_control_mode 
                ON devices(user_control_mode)
            """)
            print("✓ Created index on user_control_mode")
        except sqlite3.OperationalError:
            print("✓ Index on user_control_mode already exists")
        
        conn.commit()
        print("\nMigration completed successfully!")
        
        # Show current state
        cursor.execute("SELECT COUNT(*) FROM devices")
        count = cursor.fetchone()[0]
        print(f"Total devices in database: {count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error during migration: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

def downgrade():
    """Remove user control mode fields from devices table"""
    print("Downgrade not implemented - SQLite doesn't support DROP COLUMN easily")
    print("To manually downgrade, create a new table without these columns and copy data")
    return False

if __name__ == "__main__":
    print("Running user control mode migration...")
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()