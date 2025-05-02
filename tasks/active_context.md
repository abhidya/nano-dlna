HS
# Active Development Context

## Environment Setup - CRITICAL INFORMATION

### Running the Backend Server CORRECTLY
The backend server MUST be run from the web/backend directory using its specific virtual environment:

```bash
cd web/backend
source venv/bin/activate
python run.py
```

DO NOT attempt to run run.py from the project root directory as this file ONLY exists in web/backend.

### Virtual Environment Usage - CRITICAL
The project has multiple separate virtual environments - EACH must be used for its specific component:

- `web/backend/venv/` - **ONLY for the FastAPI backend** - contains uvicorn, fastapi, etc.
- `nanodlna_venv/` - For core nanodlna CLI functionality 
- `auto_play_venv/` - For the automatic play feature
- Project root `venv/` - For general project utilities

NEVER try to run a component with the wrong virtual environment as it will be missing the required dependencies.

### Starting the Dashboard
Use the provided script only after ensuring correct environment setup:
```bash
./run_dashboard.sh
```

This script will:
1. Use the correct environment for each component
2. Start backend and frontend servers
3. Load configuration and discover devices

## Current Project Status

The nano-dlna project is a Python-based tool that enables video playback on DLNA-enabled devices. The project includes both a CLI interface and a web dashboard for device management and playback control.

### Recent Achievements

1. **Fixed Device Discovery and Auto-Play Logic**: We've improved device discovery to properly handle existing devices:
   - Fixed device discovery to properly mark offline devices as "disconnected"
   - Implemented selective auto-play that only plays videos on newly discovered devices
   - Prevented auto-play on already connected devices to avoid restarting videos
   - Improved device status detection with multiple checks (streaming registry, core device state, database)
   - Added proper error handling with traceback for better debugging
   - Updated ConfigService integration to get device configurations correctly

2. **Enhanced Device Status Tracking**: We've implemented robust device status tracking with:
   - Thread-safe status updates using proper locking
   - Comprehensive health monitoring system
   - Multiple validation methods for device state
   - Proper clean-up of disconnected devices
   - Clear distinction between operational states in the UI

3. **Improved Video Assignment System**: We've enhanced video assignment with:
   - Priority-based assignment system
   - Proper cleanup before new assignments
   - Retry logic with exponential backoff
   - Conflict resolution through priorities
   - Assignment history tracking

4. **Implemented Health Check Monitoring**: We've added comprehensive health checks:
   - Background monitoring threads per device
   - Regular state validation
   - Automatic recovery attempts
   - Proper thread cleanup
   - Streaming session tracking

5. **Fixed Video Looping Functionality**: We've implemented robust video looping with:
   - Reliable background thread monitoring
   - Multiple fallback detection methods for playback status
   - Position tracking to detect stalled playback
   - Proper thread cleanup and management

6. **Fixed Device Configuration Loading**: We've created a thread-safe configuration management system:
   - Implemented ConfigService singleton for centralized configuration
   - Added proper locking around all configuration operations
   - Prevented duplicate device loading
   - Created comprehensive tests for thread safety

7. **Improved Video Assignment Logic**: We've enhanced the video assignment system with:
   - Priority-based video assignments (higher priority videos take precedence)
   - Device type-specific assignment strategies
   - Better error handling for failed assignments
   - More detailed logging and status tracking

8. **Fixed Media Container Not Supported Errors**: We've solved DLNA streaming issues:
   - Replaced SimpleHTTPRequestHandler with Twisted-based streaming
   - Implemented proper handling for DLNA's dual-request pattern
   - Added correct DLNA HTTP headers and metadata
   - Unified the dashboard and CLI approaches to streaming

9. **Implemented Streaming State Management**: We've developed a comprehensive streaming management system:
   - Created a streaming session registry to track all active streaming sessions
   - Implemented client connection monitoring and bandwidth tracking
   - Added automatic health checking and recovery for stalled streams
   - Created endpoints to monitor streaming statistics

10. **Fixed Path Handling Issues**: We've improved path handling throughout the codebase:
   - Unified path handling logic across the application
   - Added proper error handling for invalid paths
   - Created utility functions for path normalization
   - Removed temporary scripts and cleaned up repository

11. **Implemented reliable E2E testing protocol for dashboard components**: We've developed a protocol to ensure end-to-end testing of dashboard functionality.

12. **Fixed import path issues in backend core modules**: We've addressed issues related to importing modules in the backend.

13. **Created comprehensive testing documentation in error-documentation.mdc**: We've documented error handling and testing procedures.

14. **Established best practices for dashboard testing in lessons-learned.mdc**: We've established guidelines for effective testing.

### Current Focus

We are currently working on:

1. Fixing the device discovery endpoint to properly update device status without disrupting playing videos
   - ✅ Add proper status tracking for all devices
   - ✅ Fix the auto-play logic to respect already playing streams
   - ✅ Ensure device discovery endpoint works with both GET and POST methods

2. Implementing robust error handling throughout the application
   - ✅ Add comprehensive error logging
   - ✅ Create error recovery mechanisms
   - ✅ Provide user-friendly error messages
   - ✅ Add retries for transient issues
   - ✅ Document error patterns and solutions

### Completed Tasks

- ✅ Implement device discovery
- ✅ Fix device status tracking
- ✅ Implement auto-play on startup
- ✅ Fix video streaming issues
- ✅ Fix device discovery to avoid restarting videos on already connected devices

### Recent Learnings

- Thread safety is critical for reliable operation, especially with multiple devices and concurrent operations
- Proper state tracking prevents race conditions and improves system reliability
- Exponential backoff for retries provides more robust error recovery
- Health check monitoring is essential for ensuring continuous playback
- Priority-based assignment provides more control and predictability for video playback

### Technical Improvements

1. **Enhanced Thread Safety**: All device and configuration operations now use proper locking.
2. **Improved Logging**: Comprehensive logging for all video assignment operations.
3. **Better State Management**: Clear state transitions with validation.
4. **Automatic Recovery**: Self-healing for common playback issues.
5. **Performance Enhancements**: Optimized video assignment with prioritization.

## Next Steps

1. Fix CLI Argument Handling and Configuration Issues (HIGH)
2. Improve dashboard error handling
3. Identify and fix broken paths in web dashboard
4. Refactor `nanodlna play` CLI logic
5. Continue extending the test coverage

## Project Overview

*   **Name:** `nano-dlna`
*   **Goal:** A minimal UPnP/DLNA media streamer that allows streaming local video files to DLNA-compatible devices (TVs, media players, etc.) through both CLI and Web Dashboard interfaces.
*   **Key Features:** 
    * Device discovery via SSDP
    * Media streaming (video, audio, with subtitle support)
    * Playback control (play, pause, stop, seek)
    * Video looping
    * Web dashboard for device/video management and playback control
    * Auto-play based on device-specific configuration

*   **Technology Stack:** 
    * Core: Python (CLI tool)
    * Web Backend: FastAPI with SQLAlchemy ORM
    * Web Frontend: React
    * Deployment: Docker/Docker Compose
    * Communication: SOAP/XML for DLNA control

## Current Status

*   Core CLI functionality is working with support for:
    * Device discovery (`nanodlna discover`)
    * Media playback (`nanodlna play`)
    * Video looping via CLI (`nanodlna play --loop`)
    * Seeking (`nanodlna seek`)
    * Automatic subtitle detection and loading
    * Configuration-based auto-play

*   Web Dashboard implementation:
    * Device discovery and management 
    * Video upload and management 
    * Playback controls (play, pause, stop, seek)
    * Configuration import/export
    * Both Docker and direct deployment options
    * Video looping functionality fixed and working
    * Device configuration loading fixed and working

*   **Resolved Issues:**
    * **Video Looping in Web Dashboard:** ✓ FIXED
      * Implemented thread-safe operations using a lock to prevent race conditions
      * Added multiple detection methods (transport state, position tracking, inactivity timeout)
      * Added proper thread cleanup when stopping/pausing/changing videos
      * Improved error handling and logging
      * Added comprehensive tests to verify the fix works

    * **Device Configuration Loading Issues** ✓ FIXED
      * Created a dedicated ConfigService class with singleton pattern for managing configurations
      * Implemented thread-safe access to all configuration data with locks
      * Added prevention of duplicate configurations from the same source
      * Ensured proper tracking of configuration sources
      * Added thread synchronization for all device management operations
      * Implemented comprehensive tests to verify the fix works
      * Fixed auto-play behavior to correctly handle video assignments

*   **Identified Issues (Still Pending):**
    * **Video Assignment Logic Issues** ⚠️ HIGH
      * Multiple videos being assigned to the same device
      * No proper state tracking for current assignments
      * Insufficient cleanup when switching videos
      * No queue system for sequential playback
      * Missing safeguards against conflicting operations

    * **Streaming Management Issues** ⚠️ HIGH
      * No proper tracking of active streaming sessions
      * Streaming data not used effectively for device state management
      * Missing metrics for streaming health and quality
      * Insufficient error handling for streaming failures
      * No recovery mechanisms for dropped connections

    * **Web Dashboard Error Handling Issues** ⚠️ HIGH
      * Dashboard crashes when streaming fails
      * Insufficient error handling for network operations
      * No user-friendly error messages
      * Missing recovery procedures
      * Cascading failures when components error out

    * **Missing Dashboard Features** ⚠️ MEDIUM
      * No video preview capability in the dashboard
      * Missing device statistics (uptime, loop count, etc.)
      * No historical data or trend analysis
      * Limited monitoring capabilities

    * **Web Dashboard UI Issues:**
      * Potential path construction issues in frontend-backend communication
      * Inconsistent URL handling between different components
      * Possible resource loading failures without clear error messages

    * **Code Quality Concerns:**
      * Complex threading model in CLI playback logic
      * Duplicate functionality between CLI and web implementations
      * Inconsistent error handling approaches
      * Need to expand comprehensive test coverage to other components
      * Configuration disparity between components

## Current Issues
- The backend server sometimes fails to start due to import errors, especially with the streaming_router.py file which has relative import issues.
- The scan endpoint returns 405 Method Not Allowed when called, indicating implementation issues.
- The CLI command interface has been recently modified to require a config file parameter, making direct video playback without a config file impossible. This is causing friction in the testing workflow and needs to be fixed.
- Directory navigation issues when running scripts, particularly when attempting to run the dashboard from different directories.
- There are path construction issues in API endpoints where requests fail without trailing slashes.

## CRITICAL PATH MANAGEMENT

To prevent script execution failures, the following rules MUST be followed:

1. ALWAYS capture the root directory at script start:
   ```bash
   ROOT_DIR="$(pwd)"
   ```

2. ALWAYS use absolute paths with ROOT_DIR for ALL script calls:
   ```bash
   "$ROOT_DIR/script_name.sh"  # CORRECT
   ./script_name.sh            # WRONG - Will fail if directory changes
   ```

3. After changing directories with `cd`, ALWAYS use ROOT_DIR for paths:
   ```bash
   cd web/backend
   # Then use ROOT_DIR for any script calls
   "$ROOT_DIR/stop_dashboard.sh"
   # Always return to root when needed
   cd "$ROOT_DIR"
   ```

4. Use appropriate conditional checks with absolute paths:
   ```bash
   if [ -f "$ROOT_DIR/stop_dashboard.sh" ]; then
       "$ROOT_DIR/stop_dashboard.sh"
   fi
   ```

These path management practices have been documented in:
- .cursor/rules/error-documentation.mdc (critical issues and solutions)
- .cursor/rules/lessons-learned.mdc (best practices and patterns)

### CLI Issues Discovered
During the implementation of the streaming state management, several issues with the CLI were identified:

1. The `nanodlna play` command now requires a config file (`-c` or `--config-file` argument), which is a breaking change from previous behavior
2. Direct video playback without a config file is no longer possible
3. The help text doesn't properly reflect the actual behavior
4. The device selection mechanism is inconsistent between commands
5. The config file and loop flag interactions are not well documented

When trying to send a video to a device directly, the current CLI interface is causing friction. The system is detecting devices correctly but there's no straightforward way to send a video directly from the command line without creating a config file first.

These issues should be addressed as part of a high-priority CLI refactoring task.

## Development Guidelines

* **Code Organization:**
  * Follow existing module structure and naming conventions
  * Maintain separation between CLI and web components when appropriate
  * Reuse core functionality through proper abstraction
  * Use consistent patterns for similar operations

* **Error Handling:**
  * Implement comprehensive try/except blocks
  * Use specific exception types for different error scenarios
  * Add proper logging with appropriate severity levels
  * Include retry logic with exponential backoff for network operations

* **State Management:**
  * Use a consistent approach to state tracking
  * Implement proper locking for shared state
  * Create clear state transition paths
  * Add validation to prevent invalid state transitions
  * Use events for state change notifications

* **Streaming & Device Management:**
  * Use streaming connections data to validate device state
  * Track client connectivity for better error detection
  * Implement proper session management
  * Add metrics collection for performance analysis
  * Create clear separation between streaming and control operations

* **Testing Approach:**
  * Use pytest with mocking where appropriate
  * Ensure thread-safety in tests by using locks when modifying shared state
  * Write specific tests for different failure scenarios
  * Use parameterized tests for different device types when possible

* **Documentation Standards:**
  * Use clear, concise language
  * Include code examples for complex functionality
  * Document all configuration options and their effects
  * Add troubleshooting information for common error scenarios

## Key System Components
- Dashboard frontend (React, port 3000)
- Dashboard backend (FastAPI, port 8000)
- DLNA device discovery and control
- Video streaming services
- Database for device and video management

## Testing Infrastructure
- Clean process management with run_dashboard.sh and stop_dashboard.sh
- API testing via curl commands to various endpoints
- Log monitoring through redirected output and grep filtering
- Multi-component validation through sequential testing steps

## Known Issues
- Import path sensitivity in Python modules
- Process termination requires explicit cleanup
- API endpoints have specific format requirements (trailing slashes)
- Video scanning may fail on corrupted video files

## Next API Testing and Refactoring Plan

1. **API Testing Protocol**:
   - Test all backend endpoints for correct functionality
   - Verify proper error handling in API responses
   - Check frontend requests for path construction issues
   - Document API coverage and any gaps or inconsistencies

2. **Video-Projector Relationship Refactoring**:
   - Design improved data model for video-to-projector assignments
   - Develop stronger association between videos and specific projectors
   - Create scheduling capabilities for sequential playback
   - Implement improved conflict resolution for multiple assignments
   - Add persistent history of video assignments

3. **Dashboard Path Fixes**:
   - Address URL construction issues in frontend API calls
   - Standardize path handling for consistent behavior 
   - Add proper error handling for network issues
   - Implement retry mechanisms for transient failures

## Current Status
- Frontend is running on port 3000
- Backend is failing to start due to ModuleNotFoundError: No module named 'fastapi'
- Device discovery is working with nanodlna
- Device config was updated but backend needs to load it correctly
- Video files (kitchendoorv2.mp4, door6.mp4, Untitled.mp4) exist and are properly registered
- Proxy errors indicate backend is not accessible (ECONNREFUSED)
- The nanodlna CLI tool appears to have different syntax than what's being used in the dashboard code

## Priority Issues
1. Backend environment is not properly activated - need to use the correct virtual environment
2. The dashboard needs to properly match discovered devices to configured devices
3. The streaming service needs to use the proper video path for the right device
4. The frontend needs a working backend connection

## Recent Debug Findings
- The backend is not starting due to missing dependencies despite showing as installed in the requirements
- The run_dashboard.sh script is failing with "./stop_dashboard.sh: No such file or directory" error
- The device config format has been updated but isn't being loaded properly
- nanodlna direct casting shows command syntax errors with the "--subtitle-url" parameter

## Next Steps
1. Fix the backend environment setup
2. Ensure backend starts correctly
3. Verify device configuration loading
4. Test casting through the dashboard API
5. Verify frontend device controls
6. Create proper e2e testing procedure

## Device Discovery and Status Sync Fix (May 2025)

- Problem: Devices not present on the network remained marked as "connected" in the dashboard.
- Root Cause: The /api/devices/discover endpoint did not update the status of missing devices.
- Solution: The endpoint now marks missing devices as "disconnected" in both the DB and in-memory, and marks found devices as "connected".
- Definition of Done: When /api/devices/discover is called, the device list accurately reflects the real network state, with only present devices marked as "connected".
- Implementation: Added sync_device_status_with_discovery to DeviceService and updated the endpoint to call it after discovery.

## Test Coverage Policy

- As of now, confirmation is NOT required for any test coverage expansion, backend test writing, or related tasks. The agent should proceed autonomously until 100% test coverage is achieved, updating the memory bank and documentation as needed.

## Active Context

**High Priority Issues Identified:**
- The user reported that the UI play button does not loop videos.
- The user reported that the auto-play feature triggered by device discovery is unreliable, sometimes failing silently if the device disconnects or timing is off.
- These two issues (Looping Playback, Auto-Play Reliability) are now the highest priority tasks.

**Current Focus:**
- Refactoring the backend test suite (`tests_backend`) to fix numerous failures caused by outdated tests, incorrect fixture usage (especially database sessions), and mismatches with current application logic.
- Specifically working on correcting `TypeError: 'Session' object is not an iterator` in `test_routers.py`.

**Recent Actions:**
- Added initial tests for `main.py` (`/` and `/health` endpoints).
- Investigated and fixed multiple `ImportError` issues in the test suite (`database.crud`, `DeviceModel`, `VideoModel`).
- Refactored `tests_backend/test_models.py` and `tests_backend/test_services.py` to correctly handle database sessions using fixtures and context managers, and updated tests to align with current models/services.
- Analyzed logs showing both "No match found for door6.mp4" errors (config mismatch) and successful streaming of `kitchendoorv2.mp4`.

**Next Steps:**
- Refactor `tests_backend/test_routers.py` to fix database session usage.
- Address remaining test failures in `test_core.py`, `test_database.py`, and `test_main.py`.
- Once tests are stable, proceed with implementing the high-priority looping and auto-play reliability features.

# Active Context for nano-dlna Dashboard

## Current State
The nano-dlna dashboard is functional and running. The web interface is accessible at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Fixed Issues
- We identified and resolved import path issues in the depth processing module
- Modified import statements to use relative imports instead of absolute imports in:
  - web/backend/core/depth_processing/__init__.py
  - web/backend/core/depth_processing/core/__init__.py
  - web/backend/core/depth_processing/utils/__init__.py
  - web/backend/routers/depth_router.py
  - web/backend/core/depth_processing/ui/depth_segmentation_app.py

## Current Issues
- The API has several 500 Internal Server Errors when trying to play videos on devices
- Error observed in dashboard_run.log: "POST /api/devices/1/play HTTP/1.1" 500 Internal Server Error
- The depth processing module is installed but may need further testing

## Functionality
- Device discovery is working - devices are shown in the API
- Video listing is working
- DLNA devices are being discovered on the network
- Streaming API endpoints are accessible
- Depth processing API endpoints are accessible

## Next Steps
- Debug and fix the video playback issues (500 errors)
- Test the depth processing functionality with actual depth maps
- Test the projection mapping capability with DLNA devices
- Consider creating a simpler UI for depth mask segmentation and projection

## Technical Architecture
The system consists of:
1. FastAPI backend with multiple routers:
   - device_router: Manages DLNA and Transcreen devices
   - video_router: Manages video files and metadata
   - streaming_router: Handles streaming sessions
   - depth_router: Handles depth map processing and projection mapping

2. React frontend:
   - Communicates with the backend API
   - Provides UI for device management and control

3. Core Services:
   - DeviceManager: Manages device discovery and status
   - StreamingSessionRegistry: Tracks streaming sessions
   - TwistedStreamingServer: Handles video streaming to devices
   - DepthProcessing: Processes depth maps for projection mapping
