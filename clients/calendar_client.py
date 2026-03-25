import re
import shutil
import subprocess


_MEET_URL_RE = re.compile(
    r'https?://(?:meet\.google\.com|[\w.]*zoom\.us|teams\.microsoft\.com)\S+'
)


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


def fetch_today_events() -> list[dict] | None:
    """Return list of event dicts with keys: title, time (optional), url (optional)."""
    ical_path = _find_icalbuddy()
    if not ical_path:
        return None
    try:
        result = subprocess.run(
            [ical_path, '-nc', 'eventsToday'],
            capture_output=True, text=True
        )
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
