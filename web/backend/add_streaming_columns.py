#!/usr/bin/env python3
import sqlite3
import os

# Get database path
db_path = os.path.join(os.path.dirname(__file__), 'nanodlna.db')
print(f"Adding streaming columns to database: {db_path}")

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Add streaming_url column
    cursor.execute("ALTER TABLE devices ADD COLUMN streaming_url VARCHAR")
    print("Added streaming_url column")
except sqlite3.OperationalError as e:
    if "duplicate column" in str(e):
        print("streaming_url column already exists")
    else:
        print(f"Error adding streaming_url: {e}")

try:
    # Add streaming_port column
    cursor.execute("ALTER TABLE devices ADD COLUMN streaming_port INTEGER")
    print("Added streaming_port column")
except sqlite3.OperationalError as e:
    if "duplicate column" in str(e):
        print("streaming_port column already exists")
    else:
        print(f"Error adding streaming_port: {e}")

# Commit and close
conn.commit()
conn.close()
print("Migration complete!")