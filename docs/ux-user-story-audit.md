# UX User Story Audit

Date: 2026-06-27

Scope: React dashboard user flows in `web/frontend/src`: dashboard quick actions, layout navigation, device discovery, video library, settings config load/save, renderer controls, and hidden log viewer.

## User Stories

1. As an operator, I can discover devices from the dashboard and immediately see the scan run.
2. As an operator, I can filter device cards and trust that the visible list matches the filter state.
3. As a media manager, I can add, upload, scan, search, play, and delete videos without controls clipping on mobile.
4. As an installer, I can load a config from the dashboard and save dashboard settings without false success messages.
5. As a projection operator, I can see HDMI display status without undefined values and avoid controls that appear to cast but do nothing.
6. As a support user, I can open logs from the main navigation.

## Findings

| Area | What It Looked Like | What Actually Happened | Fix |
| --- | --- | --- | --- |
| Dashboard quick actions | Discover/Add/Scan/Load looked task-specific | Routes rendered generic pages; dialogs/scans did not start | Dashboard passes route state and pages execute the intended story action once per navigation |
| Devices filters | Filter controls implied visible filtering | Device cards always rendered from `devices.map` | Added `filteredDevices` and empty filtered state |
| Layout | Desktop content should align beside drawer | Main content had drawer width plus extra left margin | Removed duplicate main margin and kept responsive drawer width |
| Mobile headers | Buttons should remain reachable | Header/action rows squeezed horizontally | Added responsive stack/wrap layout |
| Settings save | Button said settings saved | No persistence happened | Persisted local dashboard settings in `localStorage` |
| Renderer HDMI displays | Display geometry should be readable | Missing fields rendered as `undefinedxundefined` | Added tolerant display geometry formatter |
| AirPlay discovery | Cast icon implied immediate casting | Icon had no handler | Replaced behavior with setup guidance action |
| Logs | Log viewer existed | No route or nav entry | Added `/logs` route and nav item |
| Dev server | `npm start` should launch | CRA crashed with webpack-dev-server 5 override | Removed incompatible override |

## Review Notes

- Existing backend endpoints were present for device discovery, video scan/upload, renderer control, HDMI display list, and config load/save.
- This pass changed frontend behavior only, except for dependency override cleanup.
- Remaining broad UX risk: several advanced pages (`DepthProcessing`, `ProjectionMapping`, `OverlayProjection`, `ProjectionAnimation`, `LogViewer`) still use mixed interaction patterns and should get their own story-by-story pass before a public release.
