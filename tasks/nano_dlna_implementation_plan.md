# Nano-DLNA Dashboard Implementation Plan

## System Architecture Overview

### Core Components
1. **CLI Tool (`nanodlna` package)**
   - DLNA device discovery via SSDP protocol
   - SOAP/XML communication for device control
   - HTTP streaming server
   - Playback monitoring and looping

2. **Web Dashboard**
   - **Backend**: FastAPI with SQLAlchemy ORM
   - **Frontend**: React-based UI
   - **Core Services**:
     - DeviceManager: Handles device discovery and management
     - DeviceService: Provides API for device operations
     - RendererService: Manages scene rendering on different display technologies
     - Streaming Service: Handles video streaming to devices

3. **Integration Points**
   - DLNA protocol for device communication
   - AirPlay for Apple device integration
   - Chrome renderer for local display
   - Twisted streaming server for media delivery

## Current Issues and Requirements

### Critical Issues
1. **Thread Monitoring Error**: `'NoneType' object has no attribute 'is_alive'` in DLNA device implementation
   - Occurs in `_setup_loop_monitoring` method in `DLNADevice` class
   - Causes playback monitoring to fail, preventing proper video looping

2. **Renderer Service Issues**: 
   - Chrome renderer tries to play videos on DLNA devices instead of using AirPlay
   - Incorrect device lookup in `_send_to_dlna` method

3. **AirPlay Discovery**: 
   - Frontend has cast symbol but doesn't function
   - Missing proper API integration

4. **500 Internal Server Error**: 
   - When trying to play videos on devices via API
   - Insufficient error handling in `play_video` method

5. **Device Status Tracking**: 
   - Inconsistent device status tracking across components
   - Status not properly synchronized between database and in-memory state

### Functional Requirements
1. **Device Discovery**: 
   - Scan local network for DLNA/AirPlay devices
   - Identify device capabilities and connection methods
   - Store discovered devices in database

2. **Media Streaming**: 
   - Stream local video files to selected devices
   - Support multiple streaming protocols (DLNA, AirPlay)
   - Handle different video formats and resolutions

3. **Playback Control**: 
   - Play, pause, stop, and seek functionality
   - Volume control where supported
   - Status monitoring and feedback

4. **Video Looping**: 
   - Continuous playback of videos
   - Automatic restart when video ends
   - Monitoring and recovery from playback issues

5. **Renderer Service**: 
   - Render scenes on different display technologies
   - Support for HTML, video, and image content
   - Integration with different sender types (DLNA, AirPlay, Direct)

6. **Depth Processing**: 
   - Process depth maps for projection mapping
   - Segment depth images for targeted projection
   - Visualize depth data for debugging

### Non-Functional Requirements
1. **Local-First Execution**: 
   - All processing happens locally
   - No cloud dependencies
   - Works in isolated networks

2. **Low Latency**: 
   - Quick response times for device control (<500ms)
   - Minimal delay in video streaming
   - Responsive UI interactions

3. **Portability**: 
   - Works across different platforms (macOS primary)
   - Minimal external dependencies
   - Containerization support

4. **Hot-Reloading**: 
   - Changes to files are automatically applied
   - No need to restart services
   - Live updates to UI and backend

5. **Concurrency**: 
   - Handles multiple devices simultaneously
   - Thread-safe operations
   - Resource management for streaming

## Implementation Tasks

### Task 1: Fix DLNA Device Thread Monitoring Error
**Objective**: Fix the `'NoneType' object has no attribute 'is_alive'` error in the DLNA device implementation.

**Requirements**:
- Implement proper null checking before accessing thread attributes
- Add defensive programming to handle potential thread-related errors
- Ensure thread cleanup happens properly when stopping playback
- Add comprehensive logging for thread operations

**Definition of Done**:
- No exceptions thrown when accessing thread attributes
- Thread monitoring works correctly for video looping
- Thread cleanup happens properly when stopping playback
- All thread operations are properly logged
- Unit tests pass for thread monitoring functionality

**Implementation Steps**:
1. Analyze the `_setup_loop_monitoring` method in `DLNADevice` class
2. Add thread attribute initialization in `__init__` method
3. Implement thread lock for thread operations
4. Add null checking before accessing thread attributes
5. Implement proper thread cleanup in `stop` method
6. Add comprehensive logging for thread operations
7. Create unit tests for thread monitoring functionality

**Code Location**: `web/backend/core/dlna_device.py`

### Task 2: Fix Renderer Service DLNA Integration
**Objective**: Fix the issue where Chrome renderer tries to play videos on DLNA devices instead of using AirPlay.

**Requirements**:
- Fix device lookup logic to use the correct device name or ID
- Update content URL handling to ensure it works with the DLNA device
- Add proper error handling and logging
- Ensure correct sender type is used for each device

**Definition of Done**:
- Renderer service correctly uses DLNA sender for DLNA devices
- Renderer service correctly uses AirPlay sender for AirPlay devices
- Content URLs are properly handled for each sender type
- Errors are properly handled and logged
- Unit tests pass for renderer service integration

**Implementation Steps**:
1. Analyze the `_send_to_dlna` method in `RendererService` class
2. Fix device lookup logic to use the correct device name or ID
3. Update content URL handling to ensure it works with the DLNA device
4. Add proper error handling and logging
5. Update sender type selection logic in `start_renderer` method
6. Create unit tests for renderer service integration

**Code Location**: `web/backend/core/renderer_service/service.py`

### Task 3: Implement AirPlay Discovery in Frontend
**Objective**: Fix the AirPlay discovery feature in the frontend.

**Requirements**:
- Implement proper API calls to AirPlay discovery endpoints
- Create UI components for AirPlay device selection
- Add error handling and loading states
- Ensure discovered devices can be selected and used

**Definition of Done**:
- AirPlay discovery button works correctly
- Discovered devices are displayed in the UI
- Devices can be selected and used for playback
- Errors are properly handled and displayed
- Loading states are shown during discovery

**Implementation Steps**:
1. Analyze the AirPlay discovery API endpoints in `renderer_router.py`
2. Create React component for AirPlay discovery
3. Implement API calls to discovery endpoints
4. Add UI components for device selection
5. Implement error handling and loading states
6. Add device selection functionality
7. Create unit tests for AirPlay discovery component

**Code Location**: 
- `web/frontend/src/pages/Devices.js`
- `web/frontend/src/components/AirPlayDiscovery.js` (new file)

### Task 4: Fix 500 Internal Server Error in Device Play API
**Objective**: Fix the 500 Internal Server Error when trying to play videos on devices via API.

**Requirements**:
- Implement proper error handling in `play_video` method
- Add validation for device and video path
- Add detailed logging for troubleshooting
- Ensure streaming server is properly initialized

**Definition of Done**:
- No 500 errors when playing videos via API
- Proper error messages returned for invalid inputs
- Detailed logs for troubleshooting
- Streaming server properly initialized
- Unit tests pass for play video functionality

**Implementation Steps**:
1. Analyze the `play_video` method in `DeviceService` class
2. Add validation for device and video path
3. Implement proper error handling
4. Add detailed logging for troubleshooting
5. Ensure streaming server is properly initialized
6. Create unit tests for play video functionality

**Code Location**: `web/backend/services/device_service.py`

### Task 5: Implement Comprehensive Device Status Tracking
**Objective**: Implement consistent device status tracking across the system.

**Requirements**:
- Implement unified approach to status tracking
- Ensure status updates are propagated correctly
- Add comprehensive logging for status changes
- Synchronize status between database and in-memory state

**Definition of Done**:
- Device status is consistent across all components
- Status updates are properly propagated
- Status changes are comprehensively logged
- Status is synchronized between database and in-memory state
- Unit tests pass for status tracking functionality

**Implementation Steps**:
1. Analyze current device status tracking in `DeviceManager` and `DeviceService`
2. Implement unified approach to status tracking
3. Ensure status updates are propagated correctly
4. Add comprehensive logging for status changes
5. Implement status synchronization between database and in-memory state
6. Create unit tests for status tracking functionality

**Code Location**: 
- `web/backend/core/device_manager.py`
- `web/backend/services/device_service.py`

### Task 6: Implement HTML Renderer Component
**Objective**: Implement the HTML renderer component for the renderer service.

**Requirements**:
- Create HTML renderer class that extends base renderer
- Implement methods for rendering HTML content
- Add support for video URL replacement
- Integrate with renderer service

**Definition of Done**:
- HTML renderer correctly renders HTML content
- Video URLs are properly replaced
- Renderer integrates with renderer service
- Unit tests pass for HTML renderer functionality

**Implementation Steps**:
1. Create new HTML renderer class that extends base renderer
2. Implement methods for rendering HTML content
3. Add support for video URL replacement
4. Integrate with renderer service
5. Create unit tests for HTML renderer functionality

**Code Location**: `web/backend/core/renderer_service/renderer/html.py` (new file)

### Task 7: Update Renderer Service to Use HTML Renderer
**Objective**: Update the renderer service to use the new HTML renderer.

**Requirements**:
- Add HTML renderer support to `get_renderer` method
- Update renderer type selection logic
- Add configuration for HTML renderer
- Update renderer service initialization

**Definition of Done**:
- Renderer service correctly uses HTML renderer
- Renderer type selection logic works correctly
- HTML renderer configuration is properly loaded
- Unit tests pass for renderer service with HTML renderer

**Implementation Steps**:
1. Add HTML renderer support to `get_renderer` method
2. Update renderer type selection logic
3. Add configuration for HTML renderer in `renderer_config.json`
4. Update renderer service initialization
5. Create unit tests for renderer service with HTML renderer

**Code Location**: 
- `web/backend/core/renderer_service/service.py`
- `web/backend/config/renderer_config.json`

### Task 8: Update Projector Configuration for Hccast Device
**Objective**: Update the projector configuration for the Hccast device to use the correct sender type.

**Requirements**:
- Analyze current configuration for Hccast device
- Determine correct sender type based on device capabilities
- Update configuration in `renderer_config.json`
- Test configuration with Hccast device

**Definition of Done**:
- Hccast device uses correct sender type
- Configuration is properly loaded
- Device works correctly with renderer service
- Unit tests pass for Hccast device configuration

**Implementation Steps**:
1. Analyze current configuration for Hccast device
2. Determine correct sender type based on device capabilities
3. Update configuration in `renderer_config.json`
4. Test configuration with Hccast device
5. Create unit tests for Hccast device configuration

**Code Location**: `web/backend/config/renderer_config.json`

### Task 9: Implement Playback Progress Monitoring
**Objective**: Implement comprehensive playback progress monitoring for all device types.

**Requirements**:
- Implement playback progress tracking for DLNA devices
- Implement playback progress tracking for AirPlay devices
- Add API endpoints for retrieving playback progress
- Update frontend to display playback progress

**Definition of Done**:
- Playback progress is correctly tracked for all device types
- API endpoints return accurate playback progress
- Frontend displays playback progress
- Progress updates are real-time
- Unit tests pass for playback progress functionality

**Implementation Steps**:
1. Implement playback progress tracking in `DLNADevice` class
2. Implement playback progress tracking in AirPlay sender
3. Add API endpoints for retrieving playback progress
4. Update frontend to display playback progress
5. Create unit tests for playback progress functionality

**Code Location**: 
- `web/backend/core/dlna_device.py`
- `web/backend/core/renderer_service/sender/airplay.py`
- `web/backend/routers/device_router.py`
- `web/frontend/src/pages/DeviceDetail.js`

### Task 10: Implement Depth Processing Integration
**Objective**: Integrate depth processing with renderer service for projection mapping.

**Requirements**:
- Implement depth processing service
- Add API endpoints for depth processing
- Integrate depth processing with renderer service
- Add UI components for depth visualization

**Definition of Done**:
- Depth processing service correctly processes depth maps
- API endpoints return processed depth data
- Renderer service integrates with depth processing
- UI displays depth visualization
- Unit tests pass for depth processing functionality

**Implementation Steps**:
1. Implement depth processing service
2. Add API endpoints for depth processing
3. Integrate depth processing with renderer service
4. Add UI components for depth visualization
5. Create unit tests for depth processing functionality

**Code Location**: 
- `web/backend/core/depth_processing/`
- `web/backend/routers/depth_router.py`
- `web/frontend/src/pages/DepthVisualization.js` (new file)

## Testing Strategy

### Unit Testing
- Each component should have comprehensive unit tests
- Mock external dependencies for isolated testing
- Test edge cases and error handling
- Use pytest for backend testing
- Use Jest for frontend testing

### Integration Testing
- Test interactions between components
- Test API endpoints with real data
- Test database operations
- Test streaming functionality

### End-to-End Testing
- Test complete user workflows
- Test device discovery and control
- Test video playback and looping
- Test renderer service with different device types

### Performance Testing
- Test streaming performance with different video sizes
- Test concurrent device control
- Test UI responsiveness with many devices

### Test Automation
- Automate unit tests with CI/CD pipeline
- Automate integration tests where possible
- Create test fixtures for common test scenarios

## Deployment Strategy

### Local Development
- Use virtual environments for Python dependencies
- Use npm for frontend dependencies
- Use Docker for containerized development

### Production Deployment
- Package backend as Python package
- Package frontend as static assets
- Create Docker container for complete application
- Provide installation scripts for different platforms

### Monitoring and Logging
- Implement comprehensive logging
- Add monitoring for device status
- Add alerts for critical errors
- Implement log rotation and archiving

## Maintenance Plan

### Bug Fixes
- Prioritize critical bugs affecting core functionality
- Implement regression tests for fixed bugs
- Document bug fixes in changelog

### Feature Enhancements
- Maintain feature backlog
- Prioritize features based on user feedback
- Document feature requirements and design

### Code Quality
- Implement code reviews
- Maintain code style guidelines
- Use static analysis tools
- Refactor code as needed

### Documentation
- Maintain user documentation
- Update API documentation
- Document architecture decisions
- Create troubleshooting guides
