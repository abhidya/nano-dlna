# Frontend Dashboard API Endpoints

This document provides information about the API endpoints used by the frontend dashboard and how to test them.

## API Configuration

The frontend dashboard communicates with the backend API using relative URLs that are proxied to the backend server. This is configured in two places:

1. **package.json**: The `proxy` field is set to `http://localhost:8000`, which forwards all API requests from the frontend to the backend.

```json
{
  "proxy": "http://localhost:8000"
}
```

2. **src/services/api.js**: The `baseURL` is set to `/api`, which uses the proxy configuration to forward requests to the backend.

```javascript
const api = axios.create({
  baseURL: '/api',  // Use relative URL to work with the proxy
  headers: {
    'Content-Type': 'application/json',
  },
});
```

## Available Endpoints

### Device Endpoints

- `GET /api/devices`: Get all devices
- `GET /api/devices/{id}`: Get a device by ID
- `POST /api/devices`: Create a new device
- `PUT /api/devices/{id}`: Update a device
- `DELETE /api/devices/{id}`: Delete a device
- `GET /api/devices/discover`: Discover DLNA devices on the network
- `POST /api/devices/{id}/play`: Play a video on a device
- `POST /api/devices/{id}/stop`: Stop playback on a device
- `POST /api/devices/{id}/pause`: Pause playback on a device
- `POST /api/devices/{id}/seek`: Seek to a position in the current video
- `POST /api/devices/load-config`: Load devices from a configuration file
- `POST /api/devices/save-config`: Save devices to a configuration file

### Video Endpoints

- `GET /api/videos`: Get all videos
- `GET /api/videos/{id}`: Get a video by ID
- `POST /api/videos`: Create a new video
- `PUT /api/videos/{id}`: Update a video
- `DELETE /api/videos/{id}`: Delete a video
- `POST /api/videos/upload`: Upload a video file
- `POST /api/videos/{id}/stream`: Stream a video
- `POST /api/videos/scan-directory`: Scan a directory for video files

### Renderer Endpoints

- `POST /api/renderer/start`: Start a renderer for a scene on a projector
- `POST /api/renderer/stop`: Stop a renderer on a projector
- `GET /api/renderer/status/{projector_id}`: Get the status of a renderer on a projector
- `GET /api/renderer/list`: List all active renderers
- `GET /api/renderer/projectors`: List all available projectors
- `GET /api/renderer/scenes`: List all available scenes
- `POST /api/renderer/start_projector`: Start a projector with its default scene
- `GET /api/renderer/airplay/discover`: Discover AirPlay devices on the network
- `GET /api/renderer/airplay/list`: List AirPlay devices available in System Preferences
- `GET /api/renderer/airplay/devices`: Get all AirPlay devices using both discovery methods

### Depth Processing Endpoints

- `POST /api/depth/upload`: Upload a depth map file (PNG, TIFF, EXR)
- `GET /api/depth/preview/{depth_id}`: Get a preview of the depth map
- `POST /api/depth/segment/{depth_id}`: Segment a depth map using the specified method
- `GET /api/depth/segmentation_preview/{depth_id}`: Get a preview of the segmentation as an overlay on the depth map
- `POST /api/depth/export_masks/{depth_id}`: Export binary masks for the specified segments
- `DELETE /api/depth/{depth_id}`: Delete a depth map and its temporary files
- `GET /api/depth/mask/{depth_id}/{segment_id}`: Get a binary mask for a specific segment
- `POST /api/depth/projection/create`: Create a new projection mapping configuration using LiDAR/depth data
- `GET /api/depth/projection/{config_id}`: Get a projection HTML page
- `DELETE /api/depth/projection/{config_id}`: Delete a projection configuration

### Streaming Endpoints

- `GET /api/streaming/`: Get streaming statistics
- `POST /api/streaming/start`: Start streaming a video to a device
- `GET /api/streaming/sessions`: Get all streaming sessions
- `GET /api/streaming/sessions/{session_id}`: Get a specific streaming session
- `GET /api/streaming/device/{device_name}`: Get streaming sessions for a device
- `POST /api/streaming/sessions/{session_id}/complete`: Mark a streaming session as complete
- `POST /api/streaming/sessions/{session_id}/reset`: Reset a streaming session
- `GET /api/streaming/analytics`: Get streaming analytics
- `GET /api/streaming/health`: Get streaming health status

## Testing the API Endpoints

### Using the Test Script

We've provided a test script that checks if the API endpoints are working correctly. To use it:

1. Make sure both the backend and frontend servers are running.
2. Run the test script:

```bash
cd web
./test_api_endpoints.sh
```

The script will test both the direct backend endpoints and the proxied endpoints through the frontend.

### Manual Testing with curl

You can also test the endpoints manually using curl:

```bash
# Test the backend directly
curl http://localhost:8000/api/devices

# Test through the frontend proxy
curl http://localhost:3000/api/devices
```

### Using the API in the Frontend

The frontend uses the API service defined in `src/services/api.js`. This service provides methods for interacting with the API endpoints. For example:

```javascript
// Get all devices
const devices = await deviceApi.getDevices();

// Discover devices
await deviceApi.discoverDevices();

// Play a video on a device
await deviceApi.playVideo(deviceId, videoId, loop);
```

## Error Handling

The API service includes error handling for common HTTP errors:

- 404 Not Found: The endpoint does not exist
- 500 Internal Server Error: An error occurred on the server
- Network errors: The server is not responding

Error messages are logged to the console and displayed to the user through snackbar notifications.

## Troubleshooting

If you encounter issues with the API endpoints, check the following:

1. Make sure both the backend and frontend servers are running.
2. Check the browser console for error messages.
3. Check the backend logs for error messages.
4. Verify that the proxy configuration is correct in `package.json`.
5. Verify that the API service is using relative URLs in `src/services/api.js`.
6. Try testing the endpoints directly using curl to see if the issue is with the backend or the proxy.

## Recent Changes

We've made the following changes to improve the API endpoints:

1. Updated the API service to use relative URLs that work with the proxy configuration.
2. Enhanced error handling in the API service to provide more specific error messages.
3. Updated the Devices component to handle API errors more gracefully.
4. Added tests to verify that the API endpoints are working correctly.
5. Created a test script to check if the API endpoints are accessible through both the backend and the frontend proxy.
6. Added AirPlay discovery endpoints to find and list AirPlay devices on the network.
7. Created test scripts for AirPlay discovery and integration testing.
