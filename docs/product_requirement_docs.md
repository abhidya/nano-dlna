# Product Requirements

This document outlines the functional requirements for the `nano-dlna` project.

## Core Functionality (CLI & Web)

1.  **Device Discovery:**
    *   The system MUST scan the local network using SSDP to find compatible UPnP/DLNA media renderers.
    *   The system MUST display a list of discovered devices, including relevant information (e.g., friendly name, location URL, control URL).
    *   The discovery timeout MUST be configurable (default: 5 seconds).
    *   The system MUST support manually adding devices with custom IP/hostname and control URLs.
    *   The system SHOULD support retry logic for discovery to handle unreliable network conditions.

2.  **Media Streaming:**
    *   The system MUST be able to stream local video files to a selected DLNA renderer.
    *   The system MUST be able to stream local audio files to a selected DLNA renderer.
    *   The system MUST serve the media file over HTTP with appropriate content types.
    *   The system MUST support byte-range requests for seeking.
    *   The system SHOULD support streaming external subtitles (e.g., `.srt` files) alongside video files.
    *   The system SHOULD automatically determine the best server IP to use based on the target device's network.

3.  **Playback Control:**
    *   The system MUST allow users to initiate playback (`Play`) on a selected device.
    *   The system MUST allow users to stop playback (`Stop`) on a device.
    *   The system MUST allow users to seek (`Seek`) to a specific time position during playback.
    *   The system MUST allow users to pause (`Pause`) playback on a device.
    *   The system MUST support video looping, allowing continuous playback of a video.
    *   The CLI looping implementation MUST use a monitoring approach to track playback and restart videos.
    *   The Web Dashboard looping implementation MUST use a background thread to monitor playback state and restart videos when they end.

4.  **Device Communication:**
    *   The system MUST communicate with DLNA devices using standard SOAP/XML messages.
    *   The system MUST handle communication errors with retry logic and appropriate timeouts.
    *   The system MUST support different device types with specialized handling where needed (e.g., Transcreen devices).
    *   The system SHOULD validate device responses and handle unexpected formats gracefully.

## Web Dashboard Specific Requirements

1.  **Device Management:**
    *   The dashboard MUST display a list of discovered devices with key information.
    *   Users MUST be able to view detailed information for each device.
    *   Users MUST be able to manually add, edit, and delete devices.
    *   The dashboard MUST show device connection status (connected/disconnected).
    *   The dashboard MUST show device playback status (playing/not playing).
    *   Users MUST be able to load device configurations from JSON files.
    *   Users MUST be able to save the current device list to JSON configuration files.

2.  **Video Management:**
    *   Users MUST be able to upload video files through the web interface.
    *   The dashboard MUST list available video files with metadata (name, size, duration if available).
    *   Users MUST be able to delete videos from the system.
    *   The dashboard SHOULD provide previews or thumbnails for videos where possible.
    *   The dashboard SHOULD support filtering and searching videos.
    *   The dashboard SHOULD provide mechanisms to clean up the video database (remove missing/duplicate files).

3.  **Playback Management:**
    *   Users MUST be able to manually select a device and video to play.
    *   Users MUST be able to control playback (play, pause, stop) via the web interface.
    *   Users MUST be able to seek to specific positions in the video.
    *   Users MUST be able to enable/disable video looping.
    *   The dashboard SHOULD display current playback status and progress.
    *   The dashboard SHOULD provide visual feedback for successful and failed operations.

4.  **User Interface:**
    *   The dashboard MUST provide a responsive web interface using React.
    *   The UI MUST be organized into logical sections for devices, videos, and playback.
    *   The UI MUST include proper error messages and loading indicators.
    *   The UI SHOULD be aesthetically pleasing with a consistent design language.
    *   The UI SHOULD support both desktop and mobile browsers.

5.  **Backend API:**
    *   The backend MUST provide a RESTful API for all dashboard functionality.
    *   The API MUST include authentication for secure access (if deployed publicly).
    *   API endpoints MUST be documented using OpenAPI/Swagger.
    *   The API MUST return standardized error responses with meaningful messages.
    *   The API SHOULD include rate limiting to prevent abuse.

## Auto-Play Feature

1.  **Configuration:**
    *   The system MUST support device configuration via JSON files (e.g., `my_device_config.json`).
    *   Configuration files MUST define mappings between device identifiers and video file paths.
    *   The system MUST support multiple configurations for different scenarios.
    *   The system SHOULD support advanced configuration options (looping, scheduling, etc.).

2.  **Automatic Playback:**
    *   Upon discovering a configured device, the system MUST automatically initiate playback of the associated video.
    *   This feature MUST be available in both CLI mode and Web Dashboard.
    *   The system MUST handle connection errors during auto-play with appropriate retries.
    *   The system SHOULD provide logging when auto-play is triggered.
    *   The system SHOULD support conditional auto-play based on time of day or other factors.

## Deployment & Installation

1.  **CLI Installation:**
    *   The CLI tool MUST be installable via `pip install .` from source.
    *   The CLI tool SHOULD be published to PyPI for installation via `pip install nano-dlna`.
    *   The CLI tool MUST support installation in virtual environments.
    *   The CLI tool MUST have clearly defined dependencies in `setup.py` or `requirements.txt`.

2.  **Web Dashboard Deployment:**
    *   The Web Dashboard MUST be deployable using Docker/Docker Compose.
    *   The system MUST include helper scripts for starting and stopping the dashboard.
    *   The system MUST support direct deployment without Docker for development.
    *   The system SHOULD include instructions for deploying behind a reverse proxy.

## Non-Functional Requirements

1.  **Performance:**
    *   Device discovery SHOULD complete within 5 seconds under normal network conditions.
    *   Video playback SHOULD start within 3 seconds of user request.
    *   The web interface SHOULD load and respond to user actions within 1 second.

2.  **Reliability:**
    *   The system MUST handle network interruptions gracefully.
    *   The looping functionality MUST be robust against device-specific quirks.
    *   The system SHOULD recover automatically from most error conditions.

3.  **Logging:**
    *   The system MUST log all significant operations with appropriate detail.
    *   Logs MUST include timestamps and severity levels.
    *   The system SHOULD support configurable log levels (DEBUG, INFO, WARNING, ERROR).

4.  **Security:**
    *   The system SHOULD validate all user inputs to prevent injection attacks.
    *   The system SHOULD use secure connections (HTTPS) if deployed publicly.
    *   The system SHOULD implement access controls if deployed in multi-user environments.
