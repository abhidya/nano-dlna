# Video-Projector Relationship Refactoring Plan

## Current Issues

After thorough testing of the nano-dlna system, we've identified several issues with the video-to-projector relationship:

1. **Weak Association Model**: Currently, videos are assigned to projectors in an ad-hoc manner with no persistent relationship.

2. **Configuration Inconsistency**: Configuration files mix device definition with video assignments.

3. **Limited Scheduling**: No built-in scheduling capabilities for sequential playback.

4. **Conflict Resolution**: When multiple videos are assigned to the same device, there's no clear resolution strategy.

5. **No Assignment History**: The system doesn't maintain a history of what videos have been played on which devices.

6. **API Inconsistency**: Endpoints require trailing slashes, leading to silent failures in frontend API calls.

## Proposed Solution

### 1. Enhanced Data Model

Create a structured assignment relationship between videos and projectors:

```python
class VideoAssignment(Base):
    """
    Represents a video assigned to a specific device with scheduling parameters
    """
    __tablename__ = "video_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), index=True)
    
    # Scheduling parameters
    priority = Column(Integer, default=0)  # Higher number = higher priority
    start_time = Column(DateTime, nullable=True)  # Optional scheduled start
    end_time = Column(DateTime, nullable=True)  # Optional scheduled end
    loop = Column(Boolean, default=False)  # Whether to loop the video
    days_of_week = Column(String, nullable=True)  # e.g., "0,1,5" for Sun,Mon,Fri
    
    # Status tracking
    status = Column(String, default="pending")  # pending, active, completed, failed
    last_played = Column(DateTime, nullable=True)
    play_count = Column(Integer, default=0)
    
    # Relationship references
    device = relationship("DeviceModel", back_populates="assignments")
    video = relationship("VideoModel", back_populates="assignments")
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=True)
```

### 2. Assignment Service

Create a dedicated service for managing video assignments:

```python
class AssignmentService:
    def __init__(self, db, device_manager):
        self.db = db
        self.device_manager = device_manager
    
    def assign_video(self, device_id, video_id, priority=0, start_time=None, end_time=None, loop=False, days_of_week=None):
        """Assign a video to a device with scheduling parameters"""
        # Implementation details...
    
    def get_active_assignments(self, device_id=None):
        """Get all active assignments, optionally filtered by device"""
        # Implementation details...
    
    def get_scheduled_assignments(self, start_date, end_date, device_id=None):
        """Get scheduled assignments in a date range"""
        # Implementation details...
    
    def cancel_assignment(self, assignment_id):
        """Cancel a pending or active assignment"""
        # Implementation details...
    
    def handle_assignment_conflicts(self, new_assignment):
        """Resolve conflicts based on priority"""
        # Implementation details...
    
    def process_scheduled_assignments(self):
        """Background task to process scheduled assignments"""
        # Implementation details...
```

### 3. Conflict Resolution Strategy

Implement a clear strategy for handling conflicts:

1. **Priority-Based Resolution**: Higher priority assignments override lower priority ones
2. **Scheduling Precedence**: Scheduled assignments have precedence over manual assignments
3. **Time-Based Queueing**: When priorities are equal, create a playback queue

### 4. Assignment History and Analytics

Track all assignment events for reporting and analytics:

```python
class AssignmentHistory(Base):
    """Tracks historical assignment events"""
    __tablename__ = "assignment_history"
    
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("video_assignments.id"))
    device_id = Column(Integer, ForeignKey("devices.id"))
    video_id = Column(Integer, ForeignKey("videos.id"))
    
    event_type = Column(String)  # started, stopped, paused, completed, failed
    event_time = Column(DateTime(timezone=True), server_default=func.now())
    duration = Column(Integer, nullable=True)  # seconds played
    error = Column(String, nullable=True)  # error message if failed
    
    # References
    assignment = relationship("VideoAssignment")
    device = relationship("DeviceModel")
    video = relationship("VideoModel")
```

### 5. API Enhancements

Create new endpoints for assignment management with consistent path handling:

- `/api/assignments/` - List all assignments
- `/api/assignments/{id}/` - Get, update or delete a specific assignment
- `/api/devices/{id}/assignments/` - List assignments for a device 
- `/api/videos/{id}/assignments/` - List assignments for a video
- `/api/assignments/schedule/` - Schedule assignments
- `/api/assignments/history/` - View assignment history and analytics

### 6. Frontend Changes

Update the frontend to support the new assignment model:

1. Create an Assignment management UI
2. Add scheduling calendar view
3. Implement priority selection
4. Show assignment history and analytics
5. Fix all API path issues to handle trailing slashes correctly

## Renderer Service Implementation

To address these goals, we've implemented a new Renderer Service with the following components:

### 1. Sender Abstraction

The Renderer Service introduces the concept of "Senders" - adapters for different display technologies:

- `Sender` (abstract base class): Defines the interface for all senders
- `DLNASender`: Handles DLNA device output
- `AirPlaySender`: Handles AirPlay screen mirroring
- `DirectSender`: Handles local display output

Each sender implements the following interface:
- `connect(target_id)`: Connect to the target device/display
- `disconnect()`: Disconnect from the target device/display
- `send_content(content_url)`: Send content to the target device/display
- `is_connected()`: Check if still connected to target device/display
- `get_status()`: Get current status information

### 2. Scene Management

The Renderer Service introduces the concept of "Scenes" - configurations for content to be displayed:

- Each scene has a `template` (the content URL or file path)
- Each scene has optional `data` (parameters for the template)
- Scenes can be defined in a configuration file

### 3. Projector Configuration

The Renderer Service introduces the concept of "Projectors" - configurations for display targets:

- Each projector has a `sender` type (e.g., "dlna", "airplay", "direct")
- Each projector has a `target_name` for the sender to connect to
- Optional fallback configurations can be defined

### 4. API Endpoints

The Renderer Service provides the following API endpoints:

- `POST /renderer/start`: Start a renderer for a scene on a projector
- `POST /renderer/stop`: Stop a renderer for a projector
- `GET /renderer/status`: Get status information for renderers
- `GET /renderer/list`: List all active renderers

### 5. Health Monitoring

The Renderer Service includes a health monitoring system:

- Background thread checks health of active renderers periodically
- Detects disconnections and other issues
- Can be extended to implement automatic recovery

## Implementation Status

The Renderer Service implementation includes:

- [x] Sender abstraction with implementations for DLNA, AirPlay, and Direct display
- [x] Configuration file-based scene and projector management
- [x] API endpoints for renderer control
- [x] Basic health monitoring
- [x] Unit tests for the Renderer Service
- [x] AppleScript for AirPlay screen mirroring
- [x] Integration with the existing FastAPI backend

## Migration Plan

To fully integrate the Renderer Service into the dashboard, the following steps are planned:

1. Create a frontend page for managing scenes and projectors
2. Update the frontend to use the new Renderer Service API
3. Migrate existing functionality to use the Renderer Service
4. Update documentation for the new approach

## Benefits of the New Approach

The new Renderer Service approach provides several benefits:

1. **Modularity**: Each display technology is encapsulated in its own Sender implementation
2. **Extensibility**: New display technologies can be added by implementing new Senders
3. **Centralization**: All renderer management is handled by a single service
4. **Reliability**: Health monitoring and error recovery improve reliability
5. **Flexibility**: Scene and projector configurations allow for more complex setups

## Future Work

While the initial implementation addresses the core requirements, several enhancements are planned:

1. **Browser-based Renderer**: Implement ChromeDriver-based renderer for web content
2. **Renderer Process Management**: Improve lifecycle management for renderer processes
3. **Event System**: Implement a WebSocket-based event system for real-time status updates
4. **Advanced Scheduling**: Add time-based scheduling for scenes
5. **Scene Templates**: Support more complex scene templates with dynamic content
6. **Logging and Metrics**: Add comprehensive logging and metrics for monitoring

## Implementation Plan

### Phase 1: Core Data Model (2 days)
- Create the VideoAssignment model
- Implement database migrations
- Update existing device and video models

### Phase 2: Assignment Service (2 days)
- Implement the AssignmentService
- Create conflict resolution logic
- Implement scheduling background task

### Phase 3: API Development (1 day)
- Create new API endpoints
- Ensure consistent path handling
- Update documentation

### Phase 4: Frontend Updates (2 days)
- Create assignment management UI
- Implement scheduling calendar
- Update device and video pages

### Phase 5: Testing & Integration (2 days)
- Develop unit and integration tests
- Test conflict resolution scenarios
- Validate scheduling functionality

## Expected Benefits

1. **Improved Organization**: Clear relationship between videos and devices
2. **Better Planning**: Schedule video content in advance
3. **Enhanced Reliability**: Avoid conflicts through priority system
4. **Deeper Insights**: Track assignment history and analytics
5. **Simplified Management**: UI for managing all assignments

## Risks and Mitigations

1. **Database Migration**: Ensure proper backup before schema changes
2. **Backward Compatibility**: Maintain support for existing configuration files
3. **Performance Impact**: Index all query fields for assignment lookups
4. **UI Complexity**: Design intuitive scheduling interface with drag-and-drop

## Success Criteria

1. Videos can be scheduled for specific devices with priorities
2. Conflicts are automatically resolved based on priority
3. Assignment history is tracked and reportable
4. API paths are consistent with or without trailing slashes
5. Frontend can manage all aspects of assignments with an intuitive UI 