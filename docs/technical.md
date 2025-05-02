# Technical Details

This document covers technical implementation details of the `nano-dlna` project.

## Core (`nanodlna` package)

*   **Language:** Python
*   **Key Modules:**
    *   `cli.py`: Command-line interface using `argparse` for processing arguments. Handles subcommands (`discover`, `play`, `seek`) and orchestrates the DLNA functionality.
    *   `dlna.py`: Implements DLNA device discovery via SSDP M-SEARCH broadcasting and manages communication with devices through SOAP requests. Handles actions like `SetAVTransportURI` and `Play`/`Pause`/`Stop`/`Seek` using the UPnP AVTransport service.
    *   `devices.py`: Defines device classes and manages device instances. Stores device information like friendly name, location URL, and control URLs.
    *   `streaming.py`: Implements an HTTP server to serve local media files with support for different content types and byte ranges. Generates URLs for media and subtitle files.
    *   `transcreen.py`: Contains specialized logic for Transcreen devices with custom communication and control methods.
*   **Dependencies:** 
    *   Standard Python libraries
    *   `requests` for SOAP/HTTP communication
    *   `netifaces` for network interface discovery
    *   `socket` for network communication

## Web Dashboard (`web/`)

*   **Backend (`web/backend/`):**
    *   **Framework:** FastAPI (Python)
    *   **Database:** SQLite (via SQLAlchemy ORM)
    *   **Core Components:**
        *   `core/device_manager.py`: Manages device instances and discovery
        *   `core/dlna_device.py`: Implements DLNA device functionality
        *   `core/transcreen_device.py`: Implements Transcreen device functionality
        *   `routers/device_router.py`: API endpoints for device management
        *   `routers/video_router.py`: API endpoints for video management
        *   `services/device_service.py`: Business logic for device operations
        *   `services/video_service.py`: Business logic for video operations
    *   **API:** RESTful API with Swagger UI documentation at `/docs`
    *   **Video Storage:** Uploaded videos stored in `web/uploads/`
    *   **Dependencies:** `fastapi`, `uvicorn`, `sqlalchemy`, `requests`, `pydantic`

*   **Frontend (`web/frontend/`):**
    *   **Framework:** React (JavaScript)
    *   **State Management:** React Hooks and Context API
    *   **API Communication:** `axios` for backend API requests
    *   **Key Components:**
        *   Device management views (discovery, details, control)
        *   Video management (upload, listing, playback)
        *   Playback controls (play, pause, stop, seek)
    *   **Dependencies:** `react`, `react-dom`, `axios`, `react-router-dom`

*   **Deployment:**
    *   **Docker:** `docker-compose.yml` defines services, networks, and volumes
    *   **Shell Scripts:** 
        *   `run_dashboard.sh`: Starts the web dashboard
        *   `stop_dashboard.sh`: Stops the web dashboard
        *   `web/run_direct.sh`: Starts backend and frontend directly (without Docker)
        *   `web/stop_direct.sh`: Stops directly-run services

## Video Looping Implementation

### CLI Looping Implementation
*   Located in `nanodlna/cli.py` under the `play_video_on_device` function
*   When `loop=True`, the CLI tool:
    1. Plays the video with `play` SOAP command
    2. Uses a `while True` loop to monitor playback
    3. Tracks progress using timestamps and device responses
    4. Re-sends the play command before video completion
    5. Handles errors with retry logic and proper connection management

### Web Dashboard Looping Implementation
*   Located in `web/backend/core/dlna_device.py` under the `_setup_loop_monitoring` method
*   When `loop=True` is passed to the `play` method:
    1. The main `play` method calls `_setup_loop_monitoring`
    2. Creates a background daemon thread (`_loop_thread`)
    3. Thread periodically calls `_get_transport_info` using SOAP `GetTransportInfo` action
    4. When playback state is `STOPPED` or `NO_MEDIA_PRESENT`, it restarts the video
    5. Includes fault tolerance with retry logic and consecutive failure tracking
    6. Thread cleanly exits when loop is disabled or playback is stopped

### Known Issues with Looping
*   **Web Dashboard Loop Issue:** 
    *   The loop monitoring thread may not properly detect when videos end on some devices
    *   Some DLNA devices don't return accurate transport state information
    *   The monitoring approach is more fragile than the CLI implementation
    *   The `_loop_thread` might not be properly terminated when navigating away from the UI

## Configuration Management

*   Device configuration files (`my_device_config.json`, `tramscreem+device_config.json`):
    *   JSON format with device objects containing:
        *   `device_name`: Unique identifier for the device
        *   `type`: Device type (`dlna` or `transcreen`)
        *   `hostname`: IP address or hostname of the device
        *   `action_url`: Control URL for sending SOAP commands
        *   `video_path`: Path to the video file for auto-play
    *   Additional fields can include `friendly_name`, `manufacturer`, `location` (from discovery)
    *   The web dashboard can load and save these configuration files

## DLNA Protocol Implementation

*   **Device Discovery:**
    *   Uses SSDP M-SEARCH requests to discover UPnP/DLNA devices
    *   Parses device description XML to extract service endpoints
    *   Timeout and retry logic for reliability

*   **Media Control:**
    *   Uses SOAP XML templates for actions (stored in `templates/action-*.xml`)
    *   Key actions: `SetAVTransportURI`, `Play`, `Pause`, `Stop`, `Seek`, `GetTransportInfo`
    *   Error handling with retry logic for network issues

*   **Media Streaming:**
    *   HTTP server streams media files with proper content types
    *   Supports byte-range requests for seeking
    *   Automatic IP detection for proper server URL generation

## Error Handling and Logging

*   Extensive logging throughout the application using Python's `logging` module
*   Log levels include DEBUG, INFO, WARNING, ERROR
*   Try/except blocks with specific error handling for different scenarios
*   Retry logic with exponential backoff for network operations
