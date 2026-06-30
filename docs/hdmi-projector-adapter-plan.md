# HDMI Projector Adapter Plan

## Goal

Add first-class support for a projector connected by HDMI as a local display target. The user should be able to see whether the display is attached, identify it, mark ambiguous power state, launch structured-light patterns, launch overlays, blank the output, and inspect whether the projection process is healthy.

## High-Level Plan

1. Keep HDMI at the renderer sender seam.
   - HDMI is not a DLNA media renderer and should not be registered as a network `Device`.
   - The adapter should satisfy the existing renderer `Sender` interface and hide OS display enumeration, browser launch, process state, and ambiguous power state.

2. Make projector state explicit.
   - `connection_state`: `attached` or `detached`.
   - `projection_state`: `idle`, `launching`, `projecting`, `degraded`, or `unresponsive`.
   - `power_state`: `unknown`, `manual_on`, or `manual_off`.
   - This avoids pretending HDMI can always report true projector lamp power.

3. Treat structured lighting, overlays, blanking, and normal scenes as content modes.
   - The HDMI adapter only places content on the correct display.
   - Structured-light sequencing remains content, not display transport.

4. Put the UX on the existing Renderer page first.
   - Existing navigation already exposes Renderer/Projection/Overlay.
   - A focused HDMI panel can list displays, identify a projector, choose a content mode, mark power state, and show current health without a broad navigation redesign.

5. Preserve existing DLNA/AirPlay behavior.
   - Existing projectors still work through the old paths.
   - HDMI adds sender-backed local display support and can gradually replace the thin `direct` path later.

## Low-Level Plan

1. Backend sender
   - Add `core.renderer_service.sender.hdmi.HDMISender`.
   - Enumerate displays with optional `screeninfo`; fall back to a primary virtual display if unavailable.
   - Launch Chrome/Chromium/Firefox on the selected display bounds with kiosk/fullscreen arguments.
   - Track process state, content URL, display metadata, last heartbeat, last error, and manual power state.

2. Backend service
   - Add sender creation for `hdmi`.
   - Add `list_hdmi_displays()`.
   - Add `start_projector_mode(projector_id, mode, options)`.
   - Add `identify_projector(projector_id)`.
   - Add `set_projector_power_state(projector_id, power_state)`.
   - Add `record_projector_heartbeat(projector_id)`.
   - Make the renderer lock reentrant so restarts cannot deadlock.

3. Backend routes
   - `GET /api/renderer/hdmi/displays`
   - `POST /api/renderer/projectors/{projector_id}/mode`
   - `POST /api/renderer/projectors/{projector_id}/identify`
   - `POST /api/renderer/projectors/{projector_id}/power-state`
   - `POST /api/renderer/heartbeat/{projector_id}`

4. Static content
   - Add `static/structured_light.html` with deterministic test patterns and heartbeat.
   - Add `static/hdmi_identify.html` with display identity pattern and heartbeat.
   - Reuse `static/overlay_window.html` and `static/blank.html`.

5. Frontend
   - Extend `rendererApi`.
   - Add an HDMI panel to `Renderer.js`:
     - display list
     - content mode selector
     - pattern selector / timing fields
     - identify/start/blank buttons
     - mark on/off controls
     - state chips on projector cards

6. Tests
   - Unit test display enumeration and sender state transitions.
   - Unit test renderer service mode launch with a fake sender.
   - Route-level smoke tests for HDMI display list and heartbeat.
   - Run focused backend tests, compile, frontend tests/build.

## Assumption Audit

1. HDMI cannot reliably prove projector power over the cable alone.
   - Evidence: this repo has no CEC, serial, USB, or vendor network control module.
   - Decision: expose `power_state` as user-marked unless a future hardware power adapter is added.

2. Display attachment is not the same as projector light output.
   - Evidence: OS display enumeration can report an HDMI sink while the projector is asleep or blanked.
   - Decision: keep `connection_state` separate from `power_state`.

3. Browser process health is useful but not enough.
   - Evidence: the existing direct sender only knows whether a process is running.
   - Decision: add heartbeat support for new static HDMI pages and fall back to process state for file-rendered scenes.

4. Structured lighting needs deterministic output.
   - Evidence: structured-light capture depends on known pattern order and timing.
   - Decision: implement stable patterns, interval timing, and safe black frames as content options.

5. The initial UX should live in Renderer.
   - Evidence: `Renderer.js` already lists projectors, scenes, active renderers, and AirPlay discovery.
   - Decision: add HDMI setup and mode controls there, then split into a dedicated Projectors page later if it grows.

6. Adding `screeninfo` should be optional at runtime.
   - Evidence: the overlay discovery backend already handles missing `screeninfo`.
   - Decision: the HDMI adapter works without it by exposing a fallback primary display target.

## Completion Checklist

- HDMI sender implemented at the sender seam.
- Projector state reports connection, projection, and power separately.
- Renderer endpoints expose display discovery, identify, content modes, heartbeat, and power marking.
- Static structured-light and identify pages exist.
- Renderer UX can operate HDMI content modes.
- Tests cover adapter and service/router behavior.
- Backend and frontend verification pass.
