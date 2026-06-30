# Nano-DLNA Service Runbook

## Decision

Do not run the HDMI projector adapter in Docker on Windows.

Docker is fine for CLI-only or HTTP-only work, but this HDMI adapter must enumerate Windows displays and launch Chrome on the logged-in desktop. Windows containers and normal Windows services run outside the interactive desktop session, so they cannot reliably project to the HDMI display.

Best current shape:

1. Build the React frontend once.
2. Run the FastAPI backend natively in the logged-in user's session.
3. Let FastAPI serve the built frontend at `/app`.
4. Start it with Windows Task Scheduler at user logon.

## Ports

Port `8000` may already be used by Postgres on this machine. Use `8010` for Nano-DLNA.

The service runner sets:

```powershell
NANO_DLNA_SERVER_BASE_URL=http://localhost:8010
```

This keeps HDMI pages, heartbeat calls, and structured-light URLs pointed at the correct backend.

## Install As User-Session Task

From repo root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-nano-dlna-task.ps1 -Port 8010 -InstallDeps -StartNow
```

Open:

```text
http://localhost:8010/app
```

Check API:

```text
http://localhost:8010/api/renderer/hdmi/displays
```

Logs:

```text
logs\nano-dlna-service.log
web\backend\dashboard_run.log
```

## Stop Or Remove

Stop from Task Scheduler, or remove:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\uninstall-nano-dlna-task.ps1
```

## Why Not Windows Service

A normal Windows service runs in Session 0. That is good for headless APIs, but bad for HDMI projection because the service cannot own the visible desktop or launch Chrome onto the projector. If always-on-before-login is required later, split this into:

- backend Windows service
- tiny user-session projector agent

For now, one user-logon task is the shortest reliable path.
