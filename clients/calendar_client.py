import shutil
import subprocess


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


def fetch_today_events() -> list[str] | None:
    ical_path = _find_icalbuddy()
    if not ical_path:
        return None
    try:
        result = subprocess.run(
            [ical_path, '-nc', '-n', '-ps', '|', 'eventsToday'],
            capture_output=True, text=True
        )
        output = result.stdout.strip()
        if not output:
            return []
        # Parse icalBuddy output: event titles start with '•',
        # indented lines are metadata (notes, attendees) — skip those
        events = []
        current_event = None
        for line in output.split('\n'):
            if line.startswith('•'):
                current_event = line.replace('• ', '').strip()
                events.append(current_event)
            elif current_event and line.strip().startswith(('0', '1', '2')):
                # Time line like "18.00 - 18.15" — append to current event
                time_str = line.strip()
                events[-1] = f"{current_event} ({time_str})"
        return events
    except FileNotFoundError:
        return None
