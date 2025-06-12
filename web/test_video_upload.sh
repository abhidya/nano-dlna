#!/bin/bash

# Test video upload with correct curl syntax
echo "Testing video upload..."

# Check if a video file is provided as argument
if [ -z "$1" ]; then
    echo "Usage: $0 <path_to_video_file>"
    echo "Example: $0 ~/Downloads/junedoor.mp4"
    exit 1
fi

VIDEO_PATH="$1"
VIDEO_NAME=$(basename "$VIDEO_PATH" .mp4)

# Check if file exists
if [ ! -f "$VIDEO_PATH" ]; then
    echo "Error: File '$VIDEO_PATH' not found"
    exit 1
fi

# Get file size in MB
FILE_SIZE=$(ls -lh "$VIDEO_PATH" | awk '{print $5}')
echo "Uploading: $VIDEO_PATH ($FILE_SIZE)"

# Upload the video using correct multipart form syntax
curl -X POST 'http://localhost:3000/api/videos/upload' \
  -F "file=@$VIDEO_PATH" \
  -F "name=$VIDEO_NAME" \
  -w "\n\nHTTP Status: %{http_code}\n" \
  -H "Accept: application/json"

echo -e "\n\nUpload complete!"
echo "You can now check the Videos page to see if '$VIDEO_NAME' appears in the list."