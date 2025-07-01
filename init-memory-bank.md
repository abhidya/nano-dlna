# Initialize Memory Bank for nano-dlna

To use the memory bank with Claude Code, simply ask Claude to:

1. "Create a memory bank for this project"
2. "Document the main code patterns in the memory bank"
3. "Update memory bank with streaming service architecture"

The memory bank will create these files:
- systemPatterns.md - Architecture and code patterns
- techContext.md - Technology stack details
- codebaseContext.md - Project structure and entry points
- activeContext.md - Current development focus

Example prompts:
- "Remember that streaming authentication is in web/backend/core/streaming_service.py"
- "Update memory bank: DLNA discovery uses upnp library in services/discovery.py"
- "What do you remember about the streaming implementation?"