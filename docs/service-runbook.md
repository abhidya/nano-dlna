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

The task runs the backend through a hidden tray host (`nano-dlna-tray.vbs` →
`nano-dlna-tray.ps1`), so there is **no console window**. A tray icon appears
instead; right-click it for:

- **Open Dashboard** — opens `http://localhost:<port>/app`
- **Open Service Log** / **Open Logs Folder**
- **Restart Backend** / **Quit**

If you already installed an older version of the task (visible PowerShell
window), just re-run `install-nano-dlna-task.ps1` — it replaces the task
(`-Force`) with the hidden tray version. Then end the old visible window from
Task Manager or sign out and back in.

Logs:

```text
logs\nano-dlna-service.out.log
logs\nano-dlna-service.err.log
web\backend\dashboard_run.log
```

## Stop Or Remove

Stop from Task Scheduler, or remove:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\uninstall-nano-dlna-task.ps1
```

## Surviving A Power Cycle

The goal: after a reboot or power loss, the projector comes back on its own with
no manual re-projection. There are three independent layers; set up all three.

### 1. Backend auto-resume (already built in)

HDMI projections are persisted to `web/backend/config/renderer_state.json`
whenever they start, stop, or change power state. On startup the backend replays
them (`RendererService.resume_active_projections`, called from `main.py`), with
retries so the HDMI display has time to come up. Nothing to configure — just run
the backend via the logon task above.

- A graceful shutdown does **not** clear the state, so a reboot still resumes.
- Clicking **Stop** on a projector removes it from the resume set (it stays off).
- DLNA casts already self-heal via device config + discovery auto-play.

### 2. Overlay projection window (kiosk browser)

The overlay projection window is opened from the dashboard with `window.open()`,
so the server cannot reopen it. A logon task launches a kiosk browser on the
projector display instead:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-projection-kiosk-task.ps1 -Port 8010 -StartNow
```

By default it targets the first non-primary monitor (the projector). Pin a
specific monitor with `-DisplayIndex 1`, or project a different page with
`-Path "/backend-static/overlay_window.html"`. The launcher waits for the
backend to answer before opening.

### 3. Machine returns to a logged-in desktop

The logon tasks above only fire **after** a user logs in. For a true power cycle:

- **BIOS/UEFI:** set "Restore on AC Power Loss" (a.k.a. "AC Power Recovery") to
  **Power On**, so the box boots itself when power returns.
- **Windows auto-login:** run `netplwiz`, untick "Users must enter a user name
  and password", and enter the account password once. The machine then boots
  straight to the desktop and the logon tasks fire.

With all three in place: power returns → PC boots → auto-login → backend task
starts the server → backend resumes the HDMI projection → kiosk task reopens the
overlay window. No clicks required.

## Why Not Windows Service

A normal Windows service runs in Session 0. That is good for headless APIs, but bad for HDMI projection because the service cannot own the visible desktop or launch Chrome onto the projector. If always-on-before-login is required later, split this into:

- backend Windows service
- tiny user-session projector agent

For now, one user-logon task is the shortest reliable path.
