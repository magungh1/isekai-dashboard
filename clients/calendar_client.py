import re
import shutil
import subprocess
from datetime import datetime


_MEET_URL_RE = re.compile(
    r'https?://(?:meet\.google\.com|[\w.]*zoom\.us|teams\.microsoft\.com)\S+'
)

_TIME_RANGE_RE = re.compile(r'(\d{1,2})[.:](\d{2})\s*[-–]\s*(\d{1,2})[.:](\d{2})')


def _find_icalbuddy() -> str | None:
    path = shutil.which('icalBuddy')
    if path:
        return path
    # Common Homebrew locations
    for candidate in ['/opt/homebrew/bin/icalBuddy', '/usr/local/bin/icalBuddy']:
        import os
        if os.path.isfile(candidate):
            return candidate
    return None


def parse_time_range(time_str: str | None) -> tuple[datetime | None, datetime | None]:
    """Parse a time string like '17.00 - 18.00' into start/end datetimes for today."""
    if not time_str:
        return None, None
    match = _TIME_RANGE_RE.search(time_str)
    if not match:
        return None, None
    today = datetime.now().date()
    start = datetime(today.year, today.month, today.day,
                     int(match.group(1)), int(match.group(2)))
    end = datetime(today.year, today.month, today.day,
                   int(match.group(3)), int(match.group(4)))
    return start, end


def get_event_time_status(time_str: str | None) -> str:
    """Return time status: 'now', 'soon' (within 30min), 'past', or 'future'."""
    start, end = parse_time_range(time_str)
    if start is None or end is None:
        return "future"
    now = datetime.now()
    if start <= now <= end:
        return "now"
    if now > end:
        return "past"
    minutes_until = (start - now).total_seconds() / 60
    if minutes_until <= 30:
        return "soon"
    return "future"


def event_starts_within_minutes(event: dict, minutes: int) -> bool:
    """Check if an event starts within the specified minutes from now."""
    start, _ = parse_time_range(event.get('time'))
    if start is None:
        return False
    now = datetime.now()
    minutes_until = (start - now).total_seconds() / 60
    return 0 <= minutes_until <= minutes


def get_next_meeting_countdown(events: list[dict]) -> str | None:
    """Return countdown text for the next upcoming event, or None."""
    now = datetime.now()
    best = None
    best_start = None
    for event in events:
        start, _ = parse_time_range(event.get('time'))
        if start and start > now:
            if best_start is None or start < best_start:
                best = event
                best_start = start
    if best is None or best_start is None:
        return None
    minutes = int((best_start - now).total_seconds() / 60)
    if minutes >= 60:
        hours = minutes // 60
        mins = minutes % 60
        time_str = f"{hours}h{mins}m" if mins else f"{hours}h"
    else:
        time_str = f"{minutes}m"
    return f"Next: {best['title']} in {time_str}"


def fetch_today_events() -> list[dict] | str | None:
    """Return list of event dicts, an error string if command fails, or None if icalBuddy is missing."""
    ical_path = _find_icalbuddy()
    if not ical_path:
        return None
    try:
        result = subprocess.run(
            [ical_path, '-nc', 'eventsToday'],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return result.stderr.strip() or result.stdout.strip() or f"icalBuddy failed with code {result.returncode}"

        output = result.stdout.strip()
        if not output:
            return []
        events = []
        current = None
        for line in output.split('\n'):
            if line.startswith('•'):
                current = {
                    'title': line.replace('• ', '').strip(),
                    'time': None,
                    'url': None,
                }
                events.append(current)
            elif current is None:
                continue
            elif line.strip().startswith(('0', '1', '2')):
                current['time'] = line.strip()
            elif current['url'] is None:
                match = _MEET_URL_RE.search(line)
                if match:
                    current['url'] = match.group(0)
        return events
    except FileNotFoundError:
        return None
