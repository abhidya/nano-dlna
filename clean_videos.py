#!/usr/bin/env python3
"""
Script to clean up the database by removing duplicate videos and videos that don't exist on disk.
"""

import os
import sys
import logging
import sqlite3
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def clean_videos(db_path):
    """
    Clean up the videos table in the database.
    
    Args:
        db_path: Path to the SQLite database file
    """
    if not os.path.exists(db_path):
        logger.error(f"Database file not found: {db_path}")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all videos
        cursor.execute("SELECT id, name, path FROM videos")
        videos = cursor.fetchall()
        logger.info(f"Found {len(videos)} videos in the database")
        
        # Check for videos that don't exist on disk
        missing_videos = []
        for video_id, name, path in videos:
            if not os.path.exists(path):
                missing_videos.append((video_id, name, path))
        
        if missing_videos:
            logger.info(f"Found {len(missing_videos)} videos that don't exist on disk")
            for video_id, name, path in missing_videos:
                logger.info(f"Deleting video {name} (ID: {video_id}) with path {path}")
                cursor.execute("DELETE FROM videos WHERE id = ?", (video_id,))
        
        # Normalize paths - convert relative paths to absolute
        cursor.execute("SELECT id, path FROM videos")
        all_videos = cursor.fetchall()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        paths_to_delete = []  # Track IDs to delete due to duplicate paths
        
        for video_id, path in all_videos:
            if not os.path.isabs(path):
                # Relative path - make it absolute
                abs_path = os.path.abspath(os.path.join(script_dir, path))
                
                # Check if this absolute path already exists
                cursor.execute("SELECT id FROM videos WHERE path = ? AND id != ?", (abs_path, video_id))
                existing = cursor.fetchone()
                
                if existing:
                    # Path already exists, mark this video for deletion
                    logger.info(f"Video {video_id} has duplicate path {abs_path}, marking for deletion")
                    paths_to_delete.append(video_id)
                else:
                    cursor.execute("UPDATE videos SET path = ? WHERE id = ?", (abs_path, video_id))
                    logger.info(f"Updated relative path to absolute for video {video_id}: {abs_path}")
        
        # Delete videos with duplicate paths
        for video_id in paths_to_delete:
            cursor.execute("DELETE FROM videos WHERE id = ?", (video_id,))
            logger.info(f"Deleted video {video_id} due to duplicate path")
        
        # Check for duplicate videos (same path)
        cursor.execute("""
            SELECT path, COUNT(*) as count
            FROM videos
            GROUP BY path
            HAVING count > 1
        """)
        duplicates = cursor.fetchall()
        
        if duplicates:
            logger.info(f"Found {len(duplicates)} duplicate video paths")
            for path, count in duplicates:
                logger.info(f"Path {path} appears {count} times")
                
                # Keep the first one, delete the rest
                cursor.execute("""
                    DELETE FROM videos
                    WHERE path = ? AND id NOT IN (
                        SELECT MIN(id) FROM videos WHERE path = ?
                    )
                """, (path, path))
                
                logger.info(f"Deleted {count - 1} duplicate entries for {path}")
        
        # Update any NULL has_subtitle values to False
        cursor.execute("""
            UPDATE videos
            SET has_subtitle = 0
            WHERE has_subtitle IS NULL
        """)
        logger.info("Updated NULL has_subtitle values to False")
        
        # Fix corrupted names with repeated filenames
        cursor.execute("SELECT id, name, path FROM videos WHERE name LIKE '%.mp4) (%.mp4%'")
        corrupted_names = cursor.fetchall()
        if corrupted_names:
            logger.info(f"Found {len(corrupted_names)} videos with corrupted names")
            for video_id, name, path in corrupted_names:
                # Extract the base name (before the first parenthesis)
                base_name = name.split(' (')[0] if ' (' in name else name
                # Get the actual filename from the path
                actual_filename = os.path.basename(path)
                new_name = f"{base_name} ({actual_filename})"
                cursor.execute("UPDATE videos SET name = ? WHERE id = ?", (new_name, video_id))
                logger.info(f"Fixed corrupted name for video {video_id}: {new_name}")
        
        # Check for videos with the same name but different paths
        cursor.execute("""
            SELECT name, COUNT(*) as count
            FROM videos
            WHERE name IS NOT NULL AND name != ''
            GROUP BY name
            HAVING count > 1
        """)
        name_duplicates = cursor.fetchall()
        
        if name_duplicates:
            logger.info(f"Found {len(name_duplicates)} videos with duplicate names")
            for name, count in name_duplicates:
                logger.info(f"Name '{name}' appears {count} times")
                
                # Get all videos with this name
                cursor.execute("SELECT id, path FROM videos WHERE name = ?", (name,))
                same_name_videos = cursor.fetchall()
                
                # Update the names to include the filename
                for video_id, path in same_name_videos:
                    filename = os.path.basename(path)
                    # Check if the name already has the filename appended (to avoid double appending)
                    if f"({filename})" in name:
                        # Already has filename, skip
                        continue
                    # Extract base name if it already has some filename appended
                    base_name = name.split(' (')[0] if ' (' in name else name
                    new_name = f"{base_name} ({filename})"
                    cursor.execute("UPDATE videos SET name = ? WHERE id = ?", (new_name, video_id))
                    logger.info(f"Updated video {video_id} name to {new_name}")
        
        # Commit the changes
        conn.commit()
        logger.info("Database cleanup completed successfully")
        
        # Get the final count of videos
        cursor.execute("SELECT COUNT(*) FROM videos")
        final_count = cursor.fetchone()[0]
        logger.info(f"Final video count: {final_count}")
        
        # Close the connection
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"Error cleaning videos: {e}")
        return False

if __name__ == "__main__":
    # Get the database path
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        # Default to the web/backend directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(script_dir, "web", "backend", "nanodlna.db")
    
    logger.info(f"Using database at {db_path}")
    clean_videos(db_path)
