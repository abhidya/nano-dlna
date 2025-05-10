# Task Plan

This document outlines planned tasks for the `nano-dlna` project, organized by priority, category, and implementation phase.

## Priority Tasks

1.  **Task: Implement Video Looping via Play Button**
    *   *Status:* Not Started
    *   *Priority:* High
    *   *Description:* Add functionality to allow users to loop video playback initiated via the UI play button. Current playback logic only plays once. This involves frontend changes (UI toggle), backend API updates (accept loop parameter), and implementing controller-side looping logic (monitoring playback status via device events/polling and restarting playback upon completion).
    *   *Sub-Tasks:* 
        *   Add loop toggle button/checkbox to frontend playback controls.
        *   Update Play API endpoint (e.g., `/devices/{device_id}/play`) to accept `loop: bool` parameter.
        *   Implement playback status monitoring (e.g., using DLNA GetTransportInfo or device-specific methods).
        *   Implement controller-side loop logic in `DeviceManager` or `Device` classes to restart playback.
        *   Add tests for looping functionality.
    *   *Definition of Done:* User can toggle looping in the UI; when play is pressed with loop enabled, the video plays repeatedly on the target device until stopped manually. Playback status is correctly reflected. Looping can be toggled on/off during playback.

2.  **Task: ✅ Improve Auto-Play Reliability During Discovery**
    *   *Status:* ✅ Completed
    *   *Priority:* High
    *   *Description:* Enhance the auto-play-on-discovery feature (driven by device config files) to handle device disconnections and timing issues more robustly. Currently, playback commands might be sent to unavailable devices, failing silently.
    *   *Sub-Tasks:* 
        *   ✅ Add status check (e.g., ping, simple device query) *before* attempting auto-play.
        *   ✅ Implement playback confirmation check *after* sending play command (query status, check playing URI).
        *   ✅ Implement limited retry mechanism with backoff if initial play/confirmation fails.
        *   ✅ Improve error handling and logging for playback failures during auto-play.
        *   ✅ Review and refine device state management (`is_playing`, `current_video`) based on confirmed playback status.
        *   ✅ Add tests for auto-play reliability scenarios.
    *   *Definition of Done:* Auto-play initiated by discovery is less likely to fail silently. The system correctly detects and handles cases where the device disconnects or fails to start playback shortly after discovery. Errors are logged appropriately. Device status accurately reflects playback state.

3.  **Task: Stabilize Backend Test Suite (`tests_backend`)**
    *   *Status:* In Progress
    *   *Priority:* High (Blocker for other tasks)
    *   *Description:* Fix numerous failing tests in the `tests_backend` directory. Failures are due to outdated tests, incorrect fixture usage (especially DB sessions), mocks not matching current interfaces, and mismatches with refactored application logic.
    *   *Sub-Tasks:*
        *   Refactor `tests_backend/test_routers.py` to use DB session fixture correctly. (Current focus)
        *   Fix `TypeError: Can't instantiate abstract class Device` errors in `test_core.py`.
        *   Fix `AttributeError` issues in `test_core.py` for `ConfigService`.
        *   Fix DB-related errors in `test_database.py` (`has_table`, model keyword arguments).
        *   Fix mock assertion errors and other failures in `test_main.py`.
        *   Fix new `AttributeError` and `ValueError` issues identified in `test_services.py` after refactoring.
        *   Fix router 404 errors in `test_routers.py`.
        *   Address warnings (Pydantic, SQLAlchemy, FastAPI, Twisted deprecations).
    *   *Definition of Done:* `pytest --cov=.` runs successfully in `web/backend` with 0 failures. Coverage is reported accurately.

4. **Task: ✅ Implement Renderer Service for Scene Management**
    * *Status:* ✅ Completed
    * *Priority:* High
    * *Description:* Create a unified Renderer Service for managing scene projection across different display technologies (direct screen, DLNA, AirPlay) based on the design plan in `docs/plan_renderer_service.md`. This service will extract the existing functionality from standalone scripts into a more maintainable and extensible architecture.
    * *Sub-Tasks:*
        * ✅ Create the core Renderer Service architecture with process model and CLI flags
        * ✅ Implement the Sender abstraction layer with interfaces for Different output methods
        * ✅ Develop the AirPlay sender implementation, porting from the existing solution
        * ✅ Implement the DLNA and Direct sender implementations
        * ✅ Create the service API endpoints for renderer management
        * ✅ Implement event publishing for status updates
        * ✅ Develop health monitoring and automatic recovery
        * ✅ Create migration path from standalone launcher
        * ✅ Write comprehensive tests for all components
    * *Definition of Done:* The Renderer Service is able to launch scenes on different projectors using multiple output technologies. It provides a REST API for control, emits status events, and handles health monitoring. All unit and integration tests pass, and the service successfully integrates with the dashboard.
    * *References:* `docs/plan_renderer_service.md`

5. **Task: ✅ Implement Depth Processing Feature**
    * *Status:* ✅ Completed
    * *Priority:* High
    * *Description:* Implement a depth processing feature that allows users to upload depth maps, segment them using different methods, preview segmentations, export masks, and create projection mappings. This feature will enable advanced projection mapping capabilities for the dashboard.
    * *Sub-Tasks:*
        * ✅ Implement the Depth Loader module for loading depth maps from various file formats
        * ✅ Implement the Depth Segmenter module for segmenting depth maps using different methods
        * ✅ Implement the Depth Visualizer module for creating visualizations of depth maps and segmentations
        * ✅ Create the Depth Router module for providing API endpoints for the depth processing feature
        * ✅ Implement the frontend components for the depth processing feature
        * ✅ Create comprehensive tests for all components
    * *Definition of Done:* The Depth Processing feature is fully functional and has comprehensive test coverage. Users can upload depth maps, segment them using different methods, preview segmentations, export masks, and create projection mappings. All unit and integration tests pass, and the feature successfully integrates with the dashboard.
    * *References:* `tasks/renderer_depth_status.md`

## Phase 1: Bug Fixes & Critical Improvements

### Web Dashboard Bugs

1. **[HIGH] ✅ Fix Video Looping Functionality** (COMPLETED)
   * ✅ Review the `_setup_loop_monitoring` method in `web/backend/core/dlna_device.py`
   * ✅ Fix issues with the background thread creation and management:
     * ✅ Ensure proper thread cleanup when navigation occurs in the UI
     * ✅ Add proper locking around thread creation/termination
     * ✅ Improve error handling in the monitoring thread
   * ✅ Enhance transport state detection:
     * ✅ Add fallback detection methods for devices that don't properly report state
     * ✅ Implement position tracking to detect stalled playback
     * ✅ Add timeout-based restart as an additional failsafe
   * ✅ Add comprehensive logging:
     * ✅ Log all transport state changes with timestamps
     * ✅ Add detailed logs for restart attempts and failures
     * ✅ Log different restart triggers (state, position stuck, timeout)
   * ✅ Implement test infrastructure:
     * ✅ Create basic pytest framework
     * ✅ Implement tests for proper thread creation and cleanup
     * ✅ Test different playback failure scenarios

2. **[CRITICAL] ✅ Fix Device Configuration Loading** (COMPLETED)
   * ✅ Audit device discovery and configuration code paths:
     * ✅ Compare CLI vs dashboard discovery mechanisms
     * ✅ Identify sources of duplicate device loading
     * ✅ Map the complete flow from discovery to video assignment
   * ✅ Consolidate configuration loading:
     * ✅ Implement a single source of truth for device configurations
     * ✅ Create a configuration service/singleton
     * ✅ Prevent multiple instances of the same device
   * ✅ Ensure consistent device identification:
     * ✅ Use unique device identifiers consistently
     * ✅ Add validation to prevent duplicate entries
     * ✅ Create proper device equality comparison
   * ✅ Add proper concurrency controls:
     * ✅ Implement locks for device collection modifications
     * ✅ Add transaction-like behavior for config updates
     * ✅ Prevent race conditions in device discovery
   * ✅ Implement comprehensive tests:
     * ✅ Create tests for configuration service
     * ✅ Test thread safety of configuration operations
     * ✅ Verify correct auto-play behavior with configs

3. **[HIGH] ✅ Improve Video Assignment Logic** (COMPLETED)
   * ✅ Implement safeguards against multiple video assignments:
     * ✅ Track current video assignment state
     * ✅ Add validation before new assignments
     * ✅ Implement proper cleanup of previous assignments
   * ✅ Create a proper queue system for video playback:
     * ✅ Allow videos to be queued for a device
     * ✅ Handle transitions between videos cleanly
     * ✅ Support priority levels for video assignments
   * ✅ Add device status tracking:
     * ✅ Create a state machine for device playback status
     * ✅ Implement proper status transitions
     * ✅ Add locking to prevent conflicting operations
   * ✅ Enhance error recovery:
     * ✅ Add automatic retry logic for failed assignments
     * ✅ Implement fallback mechanisms
     * ✅ Add comprehensive logging for diagnosis

4. **[HIGH] ✅ Implement Streaming State Management** (COMPLETED)
   * ✅ Track active streaming sessions:
     * ✅ Create a streaming session registry
     * ✅ Monitor active connections and bandwidth
     * ✅ Detect and report streaming errors
   * ✅ Use streaming data for device state management:
     * ✅ Track client connection status
     * ✅ Use streaming metrics to validate device state
     * ✅ Implement health checks based on streaming activity
   * ✅ Implement advanced streaming analytics:
     * ✅ Record bitrate, buffer status, and playback quality
     * ✅ Track streaming duration and completion
     * ✅ Detect streaming anomalies
   * ✅ Improve streaming reliability:
     * ✅ Add reconnection logic for dropped streams
     * ✅ Implement adaptive quality based on network conditions
     * ✅ Support multiple streaming protocols for different devices
   * ✅ Fixed related issues:
     * ✅ Corrected DeviceModel attribute errors in device_service.py
     * ✅ Removed temporary scripts and streamlined repository
     * ✅ Added comprehensive testing to verify streaming functionality

5. **[HIGH] ✅ Improve Dashboard Error Handling (COMPLETED)**
   * ✅ Added comprehensive documentation about path management:
     * ✅ Updated error-documentation.mdc with MANDATORY path rules
     * ✅ Created lessons-learned guidelines for script paths
     * ✅ Updated active_context.md with critical path management section
   * ✅ Fixed DLNA "Media Container Not Supported" errors:
     * ✅ Replaced SimpleHTTPRequestHandler with Twisted-based streaming implementation
     * ✅ Implemented web/backend/core/twisted_streaming.py for reliable DLNA streaming
     * ✅ Added proper DLNA-specific HTTP headers for better compatibility
     * ✅ Updated dlna_device.py to use the Twisted-based streaming
   * ✅ Improved error logging in streaming service:
     * ✅ Added better debug logging for file not found errors
     * ✅ Added tracking for recently served files
     * ✅ Added error documentation for common DLNA issues
   * ✅ Updated configuration handling:
     * ✅ Improved configuration file search logic
     * ✅ Added better error messages for missing config files
     * ✅ Updated documentation about config file formats

### Core Functionality Issues

7. **[MEDIUM] Refactor `nanodlna play` CLI Logic**
   * Extract playback logic into a dedicated module separate from CLI interface
   * Refactor threading model:
     * Replace direct thread creation with a proper thread pool
     * Implement clean shutdown mechanisms for all threads
     * Add proper thread synchronization with locks/events
   * Improve error handling:
     * Create specific exception classes for different failure types
     * Implement exponential backoff for retries
     * Add recovery procedures for common error scenarios
   * Enhance code structure:
     * Break down long functions into smaller, focused ones
     * Create a clear separation between CLI options and playback logic
     * Use dependency injection for better testability
   * Document the core playback logic with detailed comments

7A. **[HIGH] Fix CLI Argument Handling and Configuration Issues**
   * Correct the CLI arguments handling in the nanodlna play command:
     * Fix the config file requirement that was added recently
     * Make the config file optional with direct video playback as an alternative
     * Update help documentation to match actual implementation
   * Improve error messages when required parameters are missing
   * Properly handle the looping functionality:
     * Document the --loop flag behavior across different playing modes
     * Fix the potentially confusing "restarting 5 seconds before finishing" behavior
   * Create consistent usage patterns across all commands
   * Add detailed documentation on how to use the CLI with examples
   * Update test suite to cover all the CLI options and commands
   * Integrate properly with the streaming state management system
   * Implementation details:
     * Update argument parser to make config_file optional
     * Restore previous behavior for direct video playback
     * Add better error handling with user-friendly messages
     * Create comprehensive CLI tests
     * Ensure backward compatibility with existing scripts

8. **[MEDIUM] Review & Fix Progress Tracking**
   * Rewrite progress tracking for CLI playback:
     * Replace manual timing calculations with proper duration-based tracking
     * Fix race conditions in progress updates
     * Add proper checks for video duration availability
     * Implement fallback duration estimation when metadata isn't available
   * Improve UI feedback:
     * Show meaningful information about current state
     * Add ETA calculation based on duration and position
     * Display buffer status when available

## Phase 2: Code Quality & Structure Improvements

### Code Organization

9. **[MEDIUM] Consolidate Utility Scripts**
   * Create a central script management system:
     * Implement a unified CLI entry point for all utilities
     * Add proper argument parsing with help documentation
     * Create consistent logging across all scripts
   * Refactor shell scripts:
     * Replace repetitive code with shared functions
     * Create a library of common shell operations
     * Add error handling and validation to all scripts
   * Update documentation:
     * Create a comprehensive guide to all scripts and utilities
     * Document common usage patterns and examples
     * Add troubleshooting information for script failures

10. **[MEDIUM] Refactor DLNA Communication Logic**
    * Create a dedicated DLNA client module:
      * Extract SOAP message creation logic from multiple locations
      * Implement proper request/response abstraction
      * Add protocol-level validation for all messages
    * Improve error handling:
      * Create specific exception types for different DLNA errors
      * Add detailed error information from SOAP responses
      * Implement device-specific error handling where needed
    * Enhance reliability:
      * Add connection pooling for multiple requests
      * Implement proper timeout handling
      * Add request signing and validation where supported

### Testing & Quality Assurance

11. **[HIGH] ⏳ Implement Testing Framework** (PARTIALLY COMPLETED)
    * ✅ Set up basic pytest infrastructure:
      * ✅ Configure pytest with proper test discovery
      * ✅ Set up test execution script
      * ✅ Add mocking utilities for tests
    * Create comprehensive test utilities:
      * Create mock DLNA device server for testing
      * Build fixtures for common test scenarios
      * Add helpers for setting up test environments
    * Implement test data management:
      * Add sample media files for testing
      * Create fixture generators for device configurations
      * Build test database seeding utilities

12. **[HIGH] Write Core Tests**
    *   *Status:* In Progress
    *   *Priority:* High
    *   *Description:* Expand test coverage significantly by implementing comprehensive unit and integration tests for core backend functionality. This ensures reliability and prevents regressions.
    *   *Sub-Tasks:*
        *   **Implement comprehensive API endpoint tests using `TestClient`:**
            *   ✅ Cover all endpoints in `renderer_router.py`.
            *   ✅ Cover all endpoints in `depth_router.py`.
            *   Cover all endpoints in `device_router.py`.
            *   Cover all endpoints in `video_router.py`.
            *   Cover all endpoints in `streaming_router.py`.
            *   Include tests for success (2xx), failure (4xx), and edge cases.
        *   **Implement unit tests for core service components:**
            *   ✅ Test `RendererService` logic (mocking dependencies).
            *   Test `DeviceService` logic (mocking DB and DeviceManager).
            *   Test `VideoService` logic (mocking DB and StreamingService).
        *   **Implement unit tests for core logic components:**
            *   ✅ Test Depth Processing components (Loader, Segmenter, Visualizer).
            *   Test `DeviceManager` functionality.
            *   Test `StreamingSessionRegistry` operations.
            *   Test `DLNADevice` and `TranscreenDevice` methods (mocking network calls).
        *   **Implement unit tests for database models and interactions:**
            *   Test model creation, relationships, and methods.
            *   Test database utility functions if any.
        *   **Implement integration tests:**
            *   ✅ Created `test_integration.py` with comprehensive integration tests.
            *   Test end-to-end flows (e.g., API call -> Service -> DB).
            *   Verify interactions between different components.
            *   Use real database sessions via fixtures where appropriate.
        *   **Add regression tests for known issues:**
            *   Test specific scenarios related to previously fixed bugs (e.g., path issues, looping).
    *   *Definition of Done:* A comprehensive suite of unit and integration tests exists, covering critical backend components and API endpoints. Tests pass reliably. Test coverage significantly increased (tracked by Task: Increase Backend Test Coverage).

12A. **[HIGH] Implement End-to-End Testing for Renderer and Depth Processing**
    *   *Status:* ✅ Completed
    *   *Priority:* High
    *   *Description:* Create comprehensive end-to-end tests for the renderer and depth processing features to ensure they work correctly together and with other components of the system.
    *   *Sub-Tasks:*
        *   ✅ Create a shell script for testing renderer and depth processing API endpoints.
        *   ✅ Implement tests for the renderer workflow (start, status, stop).
        *   ✅ Implement tests for the depth processing workflow (upload, segment, preview, export).
        *   ✅ Implement tests for the integration between renderer and depth processing.
        *   ✅ Test both direct API endpoints and proxied endpoints.
        *   ✅ Add proper error handling and reporting to the test script.
    *   *Definition of Done:* A comprehensive end-to-end test script exists for the renderer and depth processing features. The script tests all API endpoints and workflows, and reports success or failure clearly.
    *   *References:* `web/test_renderer_depth_e2e.sh`

12B. **[HIGH] Create Comprehensive Test Plan**
    *   *Status:* ✅ Completed
    *   *Priority:* High
    *   *Description:* Create a comprehensive test plan for the nano-dlna dashboard, with a focus on the renderer and depth processing features. This plan will guide future testing efforts and ensure that all aspects of these features are properly tested.
    *   *Sub-Tasks:*
        *   ✅ Define testing strategy (levels, approaches, tools).
        *   ✅ Identify test coverage requirements for backend, frontend, and API.
        *   ✅ Create detailed test cases for renderer and depth processing features.
        *   ✅ Define test environment requirements.
        *   ✅ Establish test execution process and automation.
        *   ✅ Define test maintenance procedures.
        *   ✅ Identify risks and mitigations.
    *   *Definition of Done:* A comprehensive test plan document exists that covers all aspects of testing for the nano-dlna dashboard, with a focus on the renderer and depth processing features.
    *   *References:* `tasks/test_plan.md`

13. **[CRITICAL] Increase Backend Test Coverage**
   * **Status:** Pending
   * **Goal:** Significantly increase test coverage for the FastAPI backend (`web/backend/`).
   * **Definition of Done:**
     * Run backend coverage report (`pytest --cov=web.backend`).
     * Analyze report for low-coverage modules (core, services, routers, models, database).
     * Write new tests in `web/backend/tests` or `web/backend/tests_backend` to cover critical untested code paths.
     * Achieve a target coverage percentage (e.g., >80%) for the `web/backend/` directory.
     * Ensure all backend tests pass.
   * **Notes:** Focus on unit and integration tests for API endpoints, service logic, and database interactions. Refactor code for testability if needed.

### Configuration & Dependencies

13. **[LOW] Standardize Configuration Management**
    * Create a unified configuration system:
      * Implement a single configuration class/module
      * Support multiple configuration sources (files, env vars, CLI)
      * Add validation for all configuration parameters
    * Improve configuration documentation:
      * Create comprehensive configuration reference
      * Document default values and acceptable ranges
      * Add examples for common configurations
    * Add configuration utilities:
      * Create config validation tools
      * Add migration support for older config formats
      * Implement config export/import functionality

14. **[LOW] Clean Up Dependencies**
    * Audit and update all dependencies:
      * Pin all dependency versions with proper constraints
      * Separate development and production dependencies
      * Remove unused dependencies
    * Enhance dependency management:
      * Create proper setup.py with all dependencies
      * Add dependency verification scripts
      * Document purpose of each dependency
    * Implement dependency isolation:
      * Use virtual environments consistently
      * Add containerization for better isolation
      * Document system dependencies separately

## Phase 3: Feature Enhancements

### New Features

15. **[MEDIUM] Add Video Preview in Dashboard**
    * Add in-browser video playback:
      * Implement HTML5 video player component
      * Create streaming API endpoints compatible with browsers
      * Support common video formats (MP4, WebM)
    * Add thumbnail generation:
      * Implement thumbnail extraction from videos
      * Create a thumbnail cache system
      * Generate thumbnails at different resolutions
    * Improve video management UI:
      * Add preview functionality in video list
      * Create a dedicated preview modal/page
      * Implement video editing features (trim, crop)
    * Support subtitle preview:
      * Display subtitles in preview player
      * Allow subtitle selection/toggle
      * Support multiple subtitle formats

16. **[MEDIUM] Add Device Statistics and Monitoring**
    * Implement persistent tracking of device metrics:
      * Last seen timestamps
      * Device uptime and availability
      * Loop count for videos
      * Success/failure statistics
    * Create a statistics dashboard:
      * Design overview dashboard with key metrics
      * Add detailed drill-down views
      * Implement filtering and sorting of statistics
    * Add data visualization:
      * Create charts for usage patterns
      * Display network performance metrics
      * Show historical trends
    * Implement real-time monitoring:
      * Add live status updates
      * Create alerts for anomalies
      * Support notification mechanisms

17. **[MEDIUM] Implement Playlist Support**
    * Design core playlist functionality:
      * Create playlist data model with proper schema
      * Implement playlist storage (file-based and database)
      * Add playlist validation and normalization
    * Add CLI support:
      * Create commands for playlist management
      * Implement playlist playback functionality
      * Add playlist export/import features
    * Implement web dashboard support:
      * Create UI for playlist creation and editing
      * Add drag-and-drop ordering functionality
      * Implement playlist playback controls
    * Enhance device integration:
      * Support device-native playlists where available
      * Implement client-side playlist management as fallback
      * Add automatic playlist resumption after errors

18. **[LOW] Improve CLI Progress Visualization**
    * Enhance progress display:
      * Add rich text formatting for better visuals
      * Implement multi-line progress display
      * Show multiple metrics (time, position, buffer)
    * Add interactive controls:
      * Implement keyboard shortcuts for playback control
      * Add real-time seeking support
      * Create volume control interface
    * Implement advanced features:
      * Add video metadata display
      * Show thumbnail frames if available
      * Implement adaptive display based on terminal capabilities

### User Experience Improvements

19. **[MEDIUM] Enhance Web Dashboard UI**
    * Improve overall design:
      * Implement consistent design language
      * Add responsive layouts for mobile/tablet
      * Create better visual hierarchy for information
    * Enhance device management:
      * Add device grouping and tagging
      * Implement better device status visualization
      * Create device configuration editor
    * Improve media management:
      * Add media library organization features
      * Implement media tagging and categorization
      * Create better media search functionality
    * Enhance playback controls:
      * Add more intuitive control interface
      * Implement keyboard shortcuts
      * Create better playback status visualization

20. **[LOW] Improve Documentation**
    * Enhance user documentation:
      * Create comprehensive user guide
      * Add tutorial videos for common tasks
      * Implement interactive examples
    * Improve developer documentation:
      * Create detailed API reference
      * Add architectural documentation
      * Implement contribution guidelines
    * Enhance troubleshooting:
      * Create problem-solution database
      * Add diagnostic tools documentation
      * Implement self-help wizards for common issues

## Phase 4: Advanced Features & Optimizations

21. **[LOW] Add Support for Advanced Media Features**
    * Implement enhanced media capabilities:
      * Add chapter support with navigation
      * Implement multiple audio track selection
      * Add support for various subtitle formats
    * Enhance media information:
      * Extract and display comprehensive metadata
      * Add media analysis for better compatibility
      * Implement content-based recommendations
    * Improve media processing:
      * Add on-the-fly transcoding for better compatibility
      * Implement adaptive streaming based on network conditions
      * Add support for more media containers and codecs

22. **[LOW] Performance Optimizations**
    * Conduct thorough performance analysis:
      * Profile application for CPU and memory bottlenecks
      * Measure network utilization and latency
      * Analyze database performance (web dashboard)
    * Implement optimizations:
      * Add caching for frequently accessed resources
      * Optimize DLNA message processing
      * Improve concurrent operations with async code
      * Enhance media streaming with partial loading
    * Add performance monitoring:
      * Implement telemetry for ongoing monitoring
      * Add performance logging
      * Create performance dashboards

- [x] Fix device status sync in dashboard: Ensure /api/devices/discover marks missing devices as disconnected and present devices as connected. (Definition of Done: Device list always matches real network state after discovery.)

## Test Coverage Policy

- Confirmation is NOT required for any test coverage expansion, backend test writing, or related tasks. Agents should proceed autonomously until 100% test coverage is achieved, updating the memory bank and documentation as needed.

## Completed Tasks
- [x] Fix depth processing module import errors
- [x] Make dashboard start successfully with depth_router included
- [x] Update memory bank with current state

## High Priority Tasks
- [ ] Debug and fix 500 Internal Server Error in device play API
- [ ] Test depth map upload and segmentation API endpoints
- [ ] Test projection mapping with DLNA devices
- [ ] Fix device disconnection/reconnection issues

## Medium Priority Tasks
- [ ] Create test depth maps for testing segmentation
- [ ] Improve error handling in depth_router.py
- [ ] Add better logging in depth processing module
- [ ] Document depth processing API endpoints

## Low Priority Tasks
- [ ] Create a simpler UI for depth processing and projection
- [ ] Optimize depth segmentation algorithms
- [ ] Add more depth processing algorithms
- [ ] Add export formats for segmented masks

## Documentation Tasks
- [ ] Document depth processing module usage
- [ ] Document projection mapping capabilities
- [ ] Create example workflow for depth-based projection

## Phase X: Maintenance & Cleanup

23. **[MEDIUM] Clean Up Unnecessary Project Files**
    *   *Status:* Not Started
    *   *Priority:* Medium
    *   *Description:* Review the project structure and remove any files that are no longer needed. This includes old test files, unused scripts in `alternatives/`, potentially outdated documentation or configuration examples, build artifacts not covered by `.gitignore`, etc.
    *   *Sub-Tasks:*
        *   Review files in the root directory.
        *   Review files/folders in `alternatives/`.
        *   Review files in `tests/` and `web/backend/tests/` / `web/backend/tests_backend/` for outdated/unused test files.
        *   Review `docs/` and `tasks/` for outdated markdown files.
        *   Check build directories (`build/`, `nanodlna.egg-info/`) and ensure `.gitignore` is effective.
        *   Verify no critical files are accidentally removed.
    *   *Definition of Done:* Unnecessary files are removed from the repository, reducing clutter and potential confusion. The project structure is cleaner.

## Definition of Done
- Code must pass all tests
- API endpoints must return correct responses
- Documentation must be updated
- Changes must be reviewed and approved
