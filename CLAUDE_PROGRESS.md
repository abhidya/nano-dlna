# Claude Progress Document

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

### Next Steps Needed
1. ~~Fix database corruption (clean duplicate entries)~~ ✅ DONE
2. Fix discovery API bug that marks all devices as "connected"
3. Clean up port exhaustion (51 ports in use 9050-9100)
4. Disable or rate-limit auto-play feature
5. Fix thread monitoring in `dlna_device.py` (error was in test mocks, not production)
6. Implement proper cleanup on shutdown

### Additional Fixes Made
- **NoneType errors**: Found to be in test mocks with exhausted `side_effect` lists, not production code
- **Database cleanup**: Enhanced to handle path normalization and prevent future corruption

### Key Code Paths & Files
**Discovery & Auto-play:**
- `web/backend/main.py:180` - `device_manager.start_discovery()`
- `web/backend/core/device_manager.py:511` - `_discovery_loop()` (runs every 10s)
- `web/backend/core/device_manager.py:617` - `_process_device_video_assignment()`
- `web/backend/core/device_manager.py:673` - `assign_video_to_device()`
- `web/backend/core/device_manager.py:903` - `auto_play_video()`

**Frontend/Backend Mismatch:**
- Frontend shows database state via `GET /api/devices`
- Backend tracks in-memory state in `device_manager.devices`
- Database updates are inconsistent/missing

### Architecture Assessment
**Original nano-dlna**: Simple, focused CLI tool
**This implementation**: Over-engineered with problematic auto-play

**Better alternatives**:
- Simple needs: Use original nano-dlna
- Web UI needs: Jellyfin or Gerbera
- Custom needs: Strip out auto-play, simplify threading