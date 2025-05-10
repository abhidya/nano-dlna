# Chrome Renderer to AirPlay Integration

This document describes how to use the Chrome renderer with AirPlay to display content on AirPlay-compatible devices.

## Overview

The AirPlay integration allows you to:

- Render HTML content using Chrome in headless mode
- Mirror the rendered content to AirPlay-compatible devices (Apple TV, AirPlay-enabled TVs, etc.)
- Control the rendering and mirroring through the API

This integration uses AppleScript to control AirPlay mirroring on macOS, allowing the dashboard to programmatically connect to AirPlay devices.

## Requirements

- macOS (AppleScript is required for AirPlay control)
- Chrome browser installed
- AirPlay-compatible devices on the same network
- System Preferences accessibility permissions for AppleScript

## Configuration

### 1. Configure AirPlay Sender

The AirPlay sender is configured in `web/backend/config/renderer_config.json` under the `senders` section:

```json
"senders": {
  "airplay": {
    "enabled": true,
    "script_path": "auto",
    "connect_timeout": 10
  }
}
```

Parameters:
- `enabled`: Set to `true` to enable AirPlay support
- `script_path`: Path to the AppleScript file (use `"auto"` to use the default script)
- `connect_timeout`: Timeout in seconds for connection attempts

### 2. Configure AirPlay Projectors

Projectors are configured in the same file under the `projectors` section:

```json
"projectors": {
  "proj-airplay": {
    "sender": "airplay",
    "target_name": "Living Room Apple TV",
    "fallback_sender": "dlna",
    "fallback_target": "AppleTV_DLNA"
  }
}
```

Parameters:
- `sender`: Set to `"airplay"` to use AirPlay
- `target_name`: The name of the AirPlay device as it appears in the AirPlay menu
- `fallback_sender` (optional): Alternative sender type if AirPlay fails
- `fallback_target` (optional): Target name for the fallback sender

### 3. Configure Scenes

Scenes define the content to be displayed:

```json
"scenes": {
  "welcome-screen": {
    "template": "welcome/index.html",
    "data": {
      "title": "Welcome",
      "background_color": "#000000",
      "video_file": "/path/to/video.mp4"
    }
  }
}
```

## Usage

### API Endpoints

The renderer service provides the following API endpoints for controlling AirPlay projectors:

- `POST /api/renderer/start` - Start a renderer for a scene on a projector
- `POST /api/renderer/stop` - Stop a renderer on a projector
- `GET /api/renderer/status/{projector_id}` - Get the status of a renderer on a projector
- `GET /api/renderer/list` - List all active renderers
- `GET /api/renderer/projectors` - List all available projectors
- `GET /api/renderer/scenes` - List all available scenes
- `POST /api/renderer/start_projector` - Start a projector with its default scene

### AirPlay Discovery API Endpoints

The renderer service also provides the following API endpoints for discovering and listing AirPlay devices:

- `GET /api/renderer/airplay/discover` - Discover AirPlay devices on the network using dns-sd
- `GET /api/renderer/airplay/list` - List AirPlay devices available in System Preferences
- `GET /api/renderer/airplay/devices` - Get all AirPlay devices using both discovery methods

### Example: Starting a Renderer

To start a renderer for a scene on an AirPlay projector:

```bash
curl -X POST "http://localhost:8000/api/renderer/start" \
  -H "Content-Type: application/json" \
  -d '{"scene": "welcome-screen", "projector": "proj-airplay"}'
```

### Example: Stopping a Renderer

To stop a renderer on an AirPlay projector:

```bash
curl -X POST "http://localhost:8000/api/renderer/stop" \
  -H "Content-Type: application/json" \
  -d '{"projector": "proj-airplay"}'
```

## Frontend Integration

The frontend integration for AirPlay has been implemented in the Renderer page. The following components are now available:

1. **AirPlay Device Discovery UI**: A user interface for discovering and selecting AirPlay devices is available in the Renderer page. Click the "Discover AirPlay Devices" button to open the discovery dialog.

2. **AirPlay Device Listing**: The discovery dialog shows AirPlay devices from multiple sources:
   - "All Devices" tab: Shows all discovered AirPlay devices
   - "Network Discovery" tab: Shows devices discovered on the network using dns-sd
   - "System Preferences" tab: Shows devices available in System Preferences

3. **AirPlay Device Management**: The discovery dialog allows you to:
   - Refresh the list of AirPlay devices
   - View device details (name, type, status)
   - Connect to AirPlay devices (future enhancement)

4. **API Integration**: The frontend uses the following API methods to interact with AirPlay devices:
   - `rendererApi.discoverAirPlayDevices()`: Discover AirPlay devices on the network
   - `rendererApi.listAirPlayDevices()`: List AirPlay devices from System Preferences
   - `rendererApi.getAllAirPlayDevices()`: Get all AirPlay devices from both sources

To access the AirPlay discovery UI:
1. Navigate to the Renderer page
2. Scroll down to the "AirPlay Devices" section
3. Click the "Discover AirPlay Devices" button
4. Use the tabs to view devices from different sources
5. Click the refresh button to update the device list

## Testing

### AirPlay Integration Test

A test script is provided to verify the AirPlay integration:

```bash
./web/test_airplay_integration.sh
```

This script will:
1. Find an AirPlay projector in your configuration
2. Render a scene using Chrome
3. Connect to the AirPlay device and display the content

When the content appears on your AirPlay device, press Enter to stop the test.

### AirPlay Discovery Test

A test script is provided to verify the AirPlay discovery and listing functionality:

```bash
./web/test_airplay_discovery.sh
```

This script will:
1. Discover AirPlay devices on the network using dns-sd
2. List AirPlay devices available in System Preferences
3. Get all AirPlay devices using both discovery methods

The script will display the results of each step, showing the AirPlay devices found.

### AirPlay API Test

A test script is provided to verify the AirPlay API endpoints:

```bash
./web/test_airplay_api.sh
```

This script will:
1. Test the `/api/renderer/airplay/discover` endpoint
2. Test the `/api/renderer/airplay/list` endpoint
3. Test the `/api/renderer/airplay/devices` endpoint

The script will display the results of each API call, showing the AirPlay devices found.

## Troubleshooting

### Common Issues

1. **AppleScript Permission Issues**
   - Error: "AppleScript execution failed"
   - Solution: Grant accessibility permissions to Terminal/Python in System Preferences > Security & Privacy > Accessibility

2. **AirPlay Device Not Found**
   - Error: "AirPlay device not found: [device name]"
   - Solution: Verify the device name matches exactly as it appears in the AirPlay menu
   - Solution: Ensure the device is on the same network and available for AirPlay

3. **Chrome Issues**
   - Error: "Failed to start renderer"
   - Solution: Verify Chrome is installed at the expected path
   - Solution: Check Chrome process for errors in the logs

4. **Connection Issues**
   - Error: "Failed to connect to AirPlay device"
   - Solution: Ensure the Mac and AirPlay device are on the same network
   - Solution: Try connecting manually first to verify it works
   - Solution: Restart the AirPlay device

### Debugging

To enable more detailed logging:

1. Set the log level to DEBUG in `web/backend/main.py`:
   ```python
   logging.basicConfig(level=logging.DEBUG)
   ```

2. Run the test script with more verbose output:
   ```bash
   PYTHONPATH=web/backend python -m tests.test_airplay_integration
   ```

3. Check the AppleScript execution by running it manually:
   ```bash
   osascript web/backend/core/renderer_service/sender/scripts/airplay_mirror.scpt start "Device Name"
   ```

## Technical Details

### AppleScript Implementation

The AirPlay integration uses AppleScript to control AirPlay mirroring. The script:

1. Opens System Preferences > Displays
2. Clicks the AirPlay dropdown
3. Selects the target device by name
4. To disconnect, it selects "This Mac" from the dropdown

### AirPlay Sender Class

The `AirPlaySender` class in `web/backend/core/renderer_service/sender/airplay.py` implements the Sender interface for AirPlay devices. It:

1. Manages the connection to AirPlay devices
2. Executes the AppleScript to start/stop mirroring
3. Monitors the connection status
4. Provides status information

### Integration with Renderer Service

The Renderer Service in `web/backend/core/renderer_service/service.py` coordinates between the Chrome renderer and AirPlay sender:

1. Renders the scene using Chrome
2. Connects to the AirPlay device
3. Manages the lifecycle of renderers and senders
4. Provides status information through the API
