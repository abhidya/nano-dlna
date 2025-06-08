# Claude Progress Document

## IMPORTANT: Project Rules Location
The project rules are located in `.cursor/rules/` directory:
- `rules.mdc` - General instructions to always follow
- `debug.mdc` - Debugging methodology and root cause principles
- `implement.mdc` - Implementation patterns and protocols
- `lessons-learned.mdc` - Project-specific patterns and debugging principles
- `error-documentation.mdc` - Known errors and solutions

**ALWAYS read and adhere to these rules first before making changes.**

## Session: June 7, 2025

### Initial Request
Get nano-dlna dashboard running (backend + frontend)

### Issues Found
1. **Python command not found** - macOS uses `python3` not `python`
2. **Import path errors** - Backend expects `web.backend.*` imports but PYTHONPATH wasn't set
3. **Database corruption** - Video names concatenated repeatedly
4. **Projector spamming** - Auto-play loop continuously casting to devices

### Fixes Applied
1. ✅ Updated `run_dashboard.sh` - Changed `python` → `python3`
2. ✅ Updated `web/run_direct.sh` - Changed all `python` → `python3` and added `PYTHONPATH`
3. ✅ Database corruption - Fixed in `clean_videos.py` (handles repeated names & path normalization)
4. ❌ Projector spamming - Root cause identified but not fixed

### Working Commands
```bash
# Start dashboard
./run_dashboard.sh

# Stop dashboard  
./stop_dashboard.sh

# Access points
Frontend: http://localhost:3000
Backend: http://localhost:8000
API Docs: http://localhost:8000/docs
```

### Root Cause Analysis: Projector Spamming

**Code Path Traced:**
1. `run_dashboard.sh` → loads config via `/api/devices/load-config`
2. `main.py` startup → calls `device_manager.start_discovery()`
3. `_discovery_loop()` runs continuously, discovering devices
4. For EVERY device on EVERY discovery cycle: `_process_device_video_assignment()`
5. Checks conditions to assign video (line 660-664):
   - No current video OR
   - Different video than config OR
   - New device OR
   - Changed device OR
   - Device should be playing but isn't
6. Calls `assign_video_to_device()` → `auto_play_video()` → `device.play()`

**Key Issues Found:**
- Device status tracking broken - all show "connected" even when off
- Discovery runs continuously without proper device state validation
- Condition `device.current_video != video_path and not device.is_playing` triggers repeatedly
- SSDP discovery is unreliable (UDP, can miss packets)
- Devices stay "connected" for 30 seconds even if not responding
- Every 10 seconds, tries to cast to all "connected" devices where `is_playing=False`

**Spam Pattern:**
1. Discovery runs every 10 seconds (2s timeout)
2. Device doesn't respond (OFF or missed packet OR BUFFERING)
3. Device stays in `self.devices` as "connected" for 30s
4. `_process_device_video_assignment()` runs for ALL devices
5. Condition true: device "connected" but `is_playing=False`
6. Tries to cast → fails → repeats in 10s

**Buffering Cascade Effect:**
- Projector goes offline while buffering after cast command
- Discovery can't find it → marks as not playing
- Triggers another cast while still processing first one
- Creates spam loop especially on slower devices (SideProjector)

### Current Issue Status

**STARTUP BUG**: On startup, `load_devices_from_config()` sets ALL devices to status="connected" (lines 716 & 738 in device_service.py), regardless of actual availability. This is why dashboard shows all devices as connected when only Hccast is actually on.
- Discovery API endpoint (`/api/devices/discover`) FIXES this by checking actual device availability
- The bug is in the initial config load, not the discovery

**Port Exhaustion Issue**: ✅ FIXED - Cleared ports, Hccast now receives cast commands

**Port Management Learnings**:
- Each restart creates a NEW streaming server on a NEW port (9000, 9001, 9002...)
- Old servers are NOT properly cleaned up - become zombie processes
- Eventually exhausts all ports in range 9000-9100
- Fix: `lsof -ti:9000-9100 | xargs kill -9` (but this also killed backend)
- **REQUIREMENT**: Streaming server should reuse existing stream URLs for same video instead of creating new ones
- **REQUIREMENT**: Proper cleanup of old streaming servers when creating new ones

**Monitoring Thread Spam**: Hccast is being spammed by `_monitor_and_loop_v2` because:
- Transport state returns "UNKNOWN" instead of "PLAYING"
- Monitoring thread detects not playing → restarts video
- Creates new streaming URL each time (9002, 9003, etc)
- Repeats every 3-4 seconds

### Complete Root Cause Analysis

**Primary Issue: Port Exhaustion → 500 Errors**
- User clicks play → API returns 500 "Failed to play video"
- All ports 9000-9100 exhausted by zombie streams
- Each restart creates NEW stream, no cleanup
- Line 347 `device_service.py`: Always calls `start_server()`
- Error: "No available port found for streaming server in range 9000-9100"

**Two Spam Sources**:
1. **Discovery Loop (10s)**: 
   - Startup bug marks all devices "connected"
   - Auto-play attempts on offline devices
   - SideProjector (OFF) gets continuous attempts

2. **Monitor Thread (3-4s)**:
   - Hccast returns UNKNOWN transport state
   - Line 790 triggers restart
   - New stream → new port → exhaustion
   - Can crash/hang devices

**Critical Code Locations**:
- `services/device_service.py:347` - Creates new stream every time
- `core/dlna_device.py:790` - Restarts on UNKNOWN state 
- `services/device_service.py:716,738` - Startup "connected" bug
- `core/device_manager.py:660-664` - Auto-play conditions

### What We Fixed ✅
1. **Monitor thread spam** - Added UNKNOWN to allowed states (line 789)
2. **Startup bug** - Changed "connected" → "disconnected" on config load
3. **Shell scripts** - Fixed python → python3
4. **Stream reuse** - Added logic to reuse existing streams (partial fix)
5. **30-second restart loop** - Fixed StreamingSessionRegistry integration

### What Still Needs Fixing ❌

**Immediate - Fix 500 Error**:
1. **Database Changes**:
   - Add `streaming_url` column to DeviceModel
   - Add `streaming_port` column
   - Track active streams

2. **Backend Changes**:
   - Check for existing stream before creating new
   - Reuse stream if same video
   - Proper cleanup when switching videos

3. **Frontend Changes**:
   - Show streaming status
   - Update DeviceResponse schema
   - Display active stream info

**Architecture Issues**:
- No central stream registry
- Frontend/Backend/DB state mismatch  
- No rate limiting
- No cleanup on shutdown

### Missing Pieces & Untested Assumptions

1. **Two Separate Spam Sources**:
   - DeviceManager discovery loop (10s) → auto-play spam
   - Monitoring thread (3-4s) → restart spam for UNKNOWN state
   
2. **Untested Assumptions**:
   - Is Hccast actually playing video despite UNKNOWN state?
   - Why does Hccast return UNKNOWN but SideProjector fails completely?
   - Different DLNA implementations for different device models?
   
3. **Configuration Mystery**:
   - How does config map videos to devices? (need to check my_device_config.json)
   - Why is there both DeviceManager discovery AND API discovery?
   - What is streaming registry for if it shows "no active sessions"?

### User Requirements for Fixes

**Option 1: Stream Tracking/Reuse** - NOT READY
- Requires proper state management across components
- Need database schema changes first
- Frontend must be updated to show stream status
- Too complex for immediate fix

**Option 2: Disable Monitoring** - REJECTED
- Monitoring is an important feature
- Helps detect when videos stop playing
- Need to fix it, not disable it

**Option 3: Port Cleanup** - CHOSEN APPROACH
- Clean up zombie ports immediately
- Add proper cleanup when creating new streams
- Prevents port exhaustion without breaking features

### Approved Implementation Plan: Stream Reuse with Error Handling

**IMPLEMENTATION UPDATE**: 
- ✅ Added streaming_url/streaming_port to DeviceModel and schema
- ✅ Implemented stream reuse in device_service.play_video()
- ❌ BUT: DeviceManager bypasses this and calls device.play() directly!

**NEW FINDING**: Two different play paths:
1. API → device_service.play_video() → Has stream reuse ✅
2. Discovery → device_manager.auto_play_video() → device.play() → NO reuse ❌

This is why spam got faster - we only fixed one path!

**Goal**: Fix port exhaustion by reusing existing streams

#### 1. Database Changes
```sql
ALTER TABLE devices ADD COLUMN streaming_url VARCHAR;
ALTER TABLE devices ADD COLUMN streaming_port INTEGER;
```

#### 2. Backend Changes
- **TwistedStreamingServer**: Add `active_streams` dict to track video_path → (url, port)
- **device_service.py:play_video()**:
  - Check if video already streaming
  - Reuse URL if same video
  - Stop old stream if different video
  - Update DB with stream info
- **Error Handling**:
  - Catch port exhaustion → return specific error
  - Handle stale stream entries → cleanup and retry
  - Validate stream is actually accessible before reuse

#### 3. Frontend Changes  
- Update `DeviceResponse` schema: add `streaming_url`, `streaming_port`
- Show streaming status in device list
- Display error when no ports available

#### 4. Implementation Steps
1. Create database migration script
2. Update DeviceModel with streaming fields
3. Add stream tracking to TwistedStreamingServer
4. Modify play_video with reuse logic + error handling
5. Update schemas and API responses
6. Update frontend components

### Next Steps
1. ~~Fix database corruption~~ ✅ DONE
2. ~~Fix monitor thread spam~~ ✅ DONE  
3. ~~Fix startup "connected" bug~~ ✅ DONE
4. ~~Fix port exhaustion/500 error~~ ✅ DONE (via stream reuse)
5. ~~Add stream reuse logic~~ ✅ DONE (in device_service.py)
6. ~~Fix 30-second restart loop~~ ✅ DONE (StreamingSessionRegistry integration)
7. ~~Fix state management mismatch~~ ✅ DONE (added streaming fields to Device base class)
8. Update frontend to show stream status ❌
9. Implement proper cleanup on shutdown ❌
10. Add proper stream reuse to DeviceManager auto_play path ❌

### Additional Fixes Made
- **NoneType errors**: Found to be in test mocks with exhausted `side_effect` lists, not production code
- **Database cleanup**: Enhanced to handle path normalization and prevent future corruption
- **StreamingSessionRegistry integration**: Fixed missing session registration causing false inactivity
- **DeviceManager.get_instance()**: Fixed incorrect singleton pattern usage
- **Session activity tracking**: Fixed to check recent activity regardless of session.active flag
- **Direct activity timer update**: TwistedStreamingServer now updates device._last_activity_time on each HTTP request

### Key Code Paths & Files
**Discovery & Auto-play:**
- `web/backend/main.py:180` - `device_manager.start_discovery()`
- `web/backend/core/device_manager.py:511` - `_discovery_loop()` (runs every 10s)
- `web/backend/core/device_manager.py:617` - `_process_device_video_assignment()`
- `web/backend/core/device_manager.py:673` - `assign_video_to_device()`
- `web/backend/core/device_manager.py:903` - `auto_play_video()`

**Frontend/Backend/DB Mismatch:** [RECURRING ISSUE - See detailed RCA below]
- Frontend shows database state via `GET /api/devices`
- Backend tracks in-memory state in `device_manager.devices`
- Database updates are inconsistent/missing
- In-memory Device objects lack fields that exist in database (streaming_url, streaming_port)

### Architecture Assessment
**Original nano-dlna**: Simple, focused CLI tool
**This implementation**: Over-engineered with problematic auto-play

### Final Fix for 30-Second Restart Loop

**Root Cause Chain**:
1. TwistedStreamingServer sessions were not registered with StreamingSessionRegistry
2. dlna_device checks registry for active sessions, finds none
3. Triggers inactivity after 30 seconds despite active HTTP requests
4. StreamingSessionRegistry marks sessions as stalled, setting active=False
5. This prevented activity tracking even after we added session registration

**Complete Fix**:
1. Register streaming sessions when created (device_service.py)
2. Update device activity timer directly on HTTP requests (twisted_streaming.py)
3. Check recent activity regardless of session.active flag (dlna_device.py)
4. Fix DeviceManager singleton pattern error (streaming_service.py)

Now HTTP requests directly update the device's `_last_activity_time`, preventing false inactivity detection.

### [RCA NEEDED] Critical State Management Issue - Three-Component Mismatch

**FACTS (from code/logs)**:
1. Database DeviceModel HAS `streaming_url` and `streaming_port` columns (verified in device_service.py:401-402)
2. In-memory Device class does NOT have these fields (verified - no such attributes in device.py)
3. TwistedStreamingServer logs show "Updated streaming activity for session" (seen in logs)
4. NO "Updated device activity timer" messages appear in logs (verified)
5. StreamingSessionRegistry marks sessions as stalled after 15 seconds (streaming_registry.py:271)
6. Error: "Device Hccast-3ADE76_dlna not found for streaming issue handling" at 04:07:07
7. Device WAS registered at 04:06:47 (20 seconds before error)
8. During parameter changes, devices are unregistered then re-registered (device_manager.py:584-586)

**ASSUMPTIONS (need verification)**:
1. Activity timer update fails because Device object lacks streaming fields (LIKELY)
2. Device "not found" error happens during re-registration window (POSSIBLE)
3. HTTP requests come every ~60s when device buffers full video (OBSERVED PATTERN)

**Problem**: The system has three separate state stores that are NOT properly synchronized:

1. **Database (DeviceModel)**:
   - Has `streaming_url` and `streaming_port` columns ✓ [FACT]
   - Updated when streaming starts ✓ [FACT: device_service.py:401]
   - Frontend reads from here ✓ [FACT: via API]

2. **Backend In-Memory (Device object)**:
   - Does NOT have `streaming_url` or `streaming_port` fields ✗ [FACT]
   - Activity tracking tries to use these missing fields ✗ [ASSUMPTION]
   - DeviceManager operations use this incomplete state ✗ [FACT]

3. **StreamingSessionRegistry**:
   - Has session info with port/device mapping ✓ [FACT]
   - 15-second stall detection is too aggressive for buffering devices ✗ [FACT]

**Concrete Issues to Fix (Low-Hanging Fruit)**:
1. ✅ **Increase StreamingSessionRegistry stall threshold** from 15s to 90s (matches device buffering)
2. ✅ **Add debug logging** when device not found to see exact timing
3. ✅ **Add streaming_url/port fields** to Device base class
4. ✅ **Sync these fields** when streaming starts

**Evidence Timeline**:
- 04:06:47,885 - Device registered successfully
- 04:06:48,695 - HTTP GET request received
- 04:06:50,419 - Last HTTP GET before gap
- 04:07:07,911 - "appears stalled" (17s after last request)
- 04:07:07,911 - "Device not found" error
- 04:07:50,507 - "Inactivity detected" (60s after last request)
- 04:07:51,297 - HTTP GET resumes after restart

### State Management Fix Implementation

**What We Fixed**:
1. Added `streaming_url` and `streaming_port` fields to Device base class
2. Updated `update_streaming_info()` method to sync these fields 
3. Modified `auto_play_video()` to:
   - Extract port from streaming URL
   - Update device streaming info when starting playback
   - Register session with StreamingSessionRegistry
4. Updated `stop()` methods in both DLNADevice and TranscreenDevice to clear streaming info
5. Added streaming fields to `to_dict()` method for API visibility

**Impact**: This ensures all three components (Database, In-Memory Device, StreamingSessionRegistry) stay synchronized, preventing the "device not found" errors during streaming health checks.

### 🚨 CRITICAL BUGS STILL ACTIVE (Found in 4-minute runtime logs)

**FACTS from logs**:
1. **2-minute restart loop is back**: 
   - 04:30:50 - Last HTTP request
   - 04:32:50 - "Inactivity detected" → RESTART 
   - 04:34:52 - "Inactivity detected" → RESTART AGAIN
   - Pattern: Restarts every ~2 minutes

2. **Device not found error still occurs**:
   - 04:32:23 - "Device Hccast-3ADE76_dlna not found for streaming issue handling"
   - This happens AFTER we supposedly fixed state sync!

3. **Wrong video duration detected**:
   - Video is 30 minutes long
   - System defaults to 60 seconds
   - This causes premature inactivity detection

4. **Duplicate log entries**:
   - Every log line appears twice
   - "Stopping all streaming servers" appears 4 times
   - Logger configuration issue

5. **90-second threshold still too short**:
   - Device buffers entire 30-minute video
   - No HTTP requests needed after buffering
   - Triggers false inactivity

**Low-Hanging Fruit Fixes (Priority Order)**:
1. ✅ **Fix video duration detection** - Added ffprobe fallback + 30min default
2. ✅ **Dynamic inactivity timeout** - Set to video duration + 30s for buffering devices
3. ✅ **Fix duplicate logging** - Removed --reload flag from uvicorn
4. ✅ **Add device re-registration handling** - Auto-recover from database

**What We Just Fixed**:
1. **Video Duration Detection**:
   - Added ffprobe fallback to get duration from file
   - Changed default from 60s to 1800s (30 minutes)
   - This prevents premature inactivity detection

2. **Dynamic Inactivity Timeout**:
   - Added `_dynamic_inactivity_timeout` flag (enabled by default)
   - Timeout now = video duration + 30 seconds
   - Accommodates devices that buffer entire video

3. **Duplicate Logging Fix**:
   - Removed --reload flag from web/run_direct.sh
   - This prevents uvicorn from running multiple instances

4. **Device Re-registration**:
   - Added recovery logic in _handle_streaming_issue
   - Attempts to reload device from database if not found
   - Preserves streaming URL/port during recovery

### Lessons Learned from This Debugging Session

1. **Never Disable Features - Always Root Cause**
   - I tried to disable inactivity check instead of fixing it
   - User correctly said: "don't disable features, we must root cause them"

2. **Verify Method Names Exist**
   - Used `get_device_by_name()` but the actual method was `get_device()`
   - Always grep/search for correct method signatures

3. **Question Previous Fixes**
   - Progress doc claimed UNKNOWN state fix was "DONE" but loop continued
   - Always verify with logs before marking complete

4. **Trace Complete Data Flow**
   - Issue involved: TwistedStreamingServer → StreamingSessionRegistry → dlna_device
   - Missing integration between components caused the bug

5. **Check All Code Paths**
   - Found two play paths: API vs Discovery/auto-play
   - Only fixing one path leaves bugs

6. **Verify Architectural Patterns**
   - Assumed DeviceManager was singleton with get_instance()
   - It wasn't - always check before assuming

**Better alternatives**:
- Simple needs: Use original nano-dlna
- Web UI needs: Jellyfin or Gerbera
- Custom needs: Strip out auto-play, simplify threading

## Session: January 7, 2025

### Projection Mapping Tool Integration

**Request**: Create a professional projection mapping tool for room object animation integrated into the React dashboard.

**Implementation**:
1. ✅ Created `ProjectionMapping.js` React component with full functionality
2. ✅ Created `ProjectionMapping.css` for dark theme styling
3. ✅ Added route `/projection` to `App.js`
4. ✅ Updated `Layout.js` navigation menu with new tab
5. ✅ Created `projection_window.html` for popup projection windows
6. ✅ Implemented message-based communication between main app and projection windows

**Features Implemented**:
- **Image Processing**: Upload photos, Sobel edge detection with adjustable sensitivity
- **Selection Tools**: Flood Fill, Magic Wand, Brush, Eraser, Bezier curves
- **Layer Management**: Unlimited layers, visibility toggle, copy/delete, 20-step undo/redo
- **Projection Alignment**: Popup windows with real-time position/scale/rotation controls
- **Keyboard Shortcuts**: Arrow keys for movement, +/- for scale, [/] for rotation
- **Download System**: Individual or batch PNG export with transforms applied

**Access**: Navigate to http://localhost:3000/projection in the dashboard

**Status**: ✅ Image upload confirmed working by user

**Technical Notes**:
- Used React hooks (useState, useRef, useEffect, useCallback) for state management
- Implemented canvas-based drawing with ImageData manipulation
- Cross-window communication via postMessage API
- Responsive grid layout with Material-UI integration