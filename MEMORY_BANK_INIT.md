# Memory Bank Initialization for nano-dlna

## Quick Start

In a new Claude Code session, use these prompts:

### 1. Initialize Memory Bank
```
Create a memory bank for this project with the following key information:
- Main entry: web/backend/main.py (FastAPI application)
- Streaming service: web/backend/core/streaming_service.py
- Frontend: web/frontend (React + Vite)
- Tech stack: FastAPI, DLNA/UPnP, SQLite, React
```

### 2. Test Memory Retrieval
```
What do you remember about the streaming implementation?
```

### 3. Add Specific Memories
```
Remember these code patterns:
- Authentication uses JWT tokens with @jwt_required decorator
- DLNA discovery is handled by upnp library
- All API routes are in web/backend/api/
- Database models in web/backend/models/
```

### 4. Query Specific Info
```
Where is the DLNA streaming logic implemented?
```

## Expected Memory Bank Structure

After initialization, you should have:
```
.memory-bank/
├── systemPatterns.md      # Code patterns and conventions
├── techContext.md         # Technology decisions
├── codebaseContext.md     # File structure and entry points
├── activeContext.md       # Current development focus
├── projectRoadmap.md      # Future plans
└── errata.md             # Known issues and workarounds
```

## Verification

Check if memory bank was created:
```bash
ls -la .memory-bank/
```

## Benefits

1. **No more re-discovery**: Claude remembers file locations
2. **Persistent context**: Survives between sessions
3. **Team knowledge**: Can be shared via git
4. **Faster responses**: No need to search for common info