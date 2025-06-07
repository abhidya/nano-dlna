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
3. ❌ Database corruption - Not fixed (needs cleanup script)
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
- Auto-play feature triggers on device discovery
- Failed thread monitoring (`'NoneType' object has no attribute 'is_alive'`)
- System thinks playback stopped → restarts continuously
- Multiple config files loaded → duplicate triggers

### Next Steps Needed
1. Fix database corruption (clean duplicate entries)
2. Disable or rate-limit auto-play feature
3. Fix thread monitoring in `dlna_device.py`
4. Implement proper cleanup on shutdown

### Architecture Assessment
**Original nano-dlna**: Simple, focused CLI tool
**This implementation**: Over-engineered with problematic auto-play

**Better alternatives**:
- Simple needs: Use original nano-dlna
- Web UI needs: Jellyfin or Gerbera
- Custom needs: Strip out auto-play, simplify threading