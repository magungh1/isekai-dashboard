# Linux Compatibility Plan
**Branch:** `feat/linux-support` (create from main)

## Context
The dashboard runs on Linux already, but three features are macOS-only no-ops: notifications, calendar, and now playing. This plan adds Linux implementations so those features work on both platforms. No new dependencies needed — `icalevents` is already in pyproject.toml, and `notify-send`/`playerctl` are standard Linux packages.

## Approach: Function-level platform dispatch
Add `sys.platform` checks inside existing functions. No new files, no module splitting. macOS code stays unchanged.

---

### 1. Notifications — `ui/widgets/pomodoro.py`
- Rename `_send_macos_notification` → `_send_notification`
- Add Linux branch: `subprocess.Popen(["notify-send", title, message])` with `shutil.which` guard
- Update two call sites (lines ~211, ~219)
- ~10 lines added

### 2. Now Playing — `clients/media_client.py`
- Add `_IS_LINUX = sys.platform.startswith("linux")` at module level
- **`get_current_track`**: run `playerctl metadata --format "{{title}} - {{artist}}"`
- **`get_playback_progress`**: run `playerctl position` + `playerctl metadata mpris:length`, convert microseconds → seconds
- **`toggle_playback`**: run `playerctl play-pause`
- All return `None`/`False` if playerctl unavailable
- ~60 lines added

### 3. Calendar — `clients/calendar_client.py`
- Extract current icalBuddy logic into `_fetch_events_icalbuddy()`
- Add `_fetch_events_icalevents()` that reads from `ICAL_PATH` env var (comma-separated .ics file paths or CalDAV URLs)
- Uses `icalevents` library (already a dependency) to get today's events
- Maps events to same `{"title", "time", "url"}` dict format
- `fetch_today_events`: try icalevents if `ICAL_PATH` set, else try icalBuddy on macOS
- Update error message in `ui/widgets/calendar.py` to be platform-aware
- ~40 lines added

### 4. Minor UI updates
- `ui/widgets/calendar.py`: error message → "Set ICAL_PATH env var" on Linux, "Install icalBuddy" on macOS
- `ui/widgets/now_playing.py`: mention `playerctl` instead of Apple Events on Linux

### 5. Tests — `tests/test_clients.py`
- Add tests for Linux branches mocking `subprocess.run` and `shutil.which`
- Mock `sys.platform` for platform-specific tests

---

## Files to modify
- `ui/widgets/pomodoro.py` — notification function
- `clients/media_client.py` — all three media functions
- `clients/calendar_client.py` — calendar fetching
- `ui/widgets/calendar.py` — error message
- `ui/widgets/now_playing.py` — error message (if applicable)
- `tests/test_clients.py` — Linux test cases

## Implementation order
1. Notifications (simplest)
2. Now Playing (medium)
3. Calendar (medium, needs icalevents format mapping)
4. Tests

## Linux prerequisites
```bash
# Notifications
sudo apt install libnotify-bin   # provides notify-send

# Now Playing (media control)
sudo apt install playerctl       # MPRIS2 media controller

# Calendar — no system packages needed, just set env var:
export ICAL_PATH="https://calendar.google.com/calendar/ical/.../basic.ics"
# or local file:
export ICAL_PATH="/path/to/calendar.ics"
```

## Verification
- `make test` passes
- On macOS: existing behavior unchanged
- On Linux: `notify-send`, `playerctl`, and `ICAL_PATH` work when available, degrade gracefully when not
