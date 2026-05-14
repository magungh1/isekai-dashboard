import json
import subprocess
import logging

from config import get_browser, get_list

logger = logging.getLogger(__name__)

_URL_PATTERNS = None
_TITLE_SUFFIXES = None


def _get_url_patterns() -> list[str]:
    global _URL_PATTERNS
    if _URL_PATTERNS is None:
        _URL_PATTERNS = get_list("media", "url_patterns")
    return _URL_PATTERNS


def _get_title_suffixes() -> list[str]:
    global _TITLE_SUFFIXES
    if _TITLE_SUFFIXES is None:
        _TITLE_SUFFIXES = get_list("media", "title_suffixes")
    return _TITLE_SUFFIXES


def get_media_browser() -> str:
    return get_browser()


def _clean_title(title: str) -> str:
    for suffix in _get_title_suffixes():
        title = title.replace(suffix, "")
    return title


def _url_check_expr() -> str:
    patterns = _get_url_patterns()
    if len(patterns) == 1:
        return f'u contains "{patterns[0]}"'
    parts = " or ".join(f'u contains "{p}"' for p in patterns)
    return f"({parts})"


def get_all_youtube_tabs() -> list[dict]:
    browser = get_media_browser()
    url_check = _url_check_expr()

    script = f"""
    tell application "{browser}"
        if not (exists window 1) then return ""
        set output to ""
        set wIdx to 0
        repeat with w in windows
            set wIdx to wIdx + 1
            set tIdx to 0
            repeat with t in tabs of w
                set tIdx to tIdx + 1
                set u to URL of t
                if {url_check} then
                    try
                        set p to execute t javascript "document.querySelector('video').paused"
                    on error
                        set p to "true"
                    end try
                    set output to output & wIdx & "\t" & tIdx & "\t" & p & "\t" & (title of t) & linefeed
                end if
            end repeat
        end repeat
        return output
    end tell
    """
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True, text=True, check=True,
        )
        output = result.stdout.strip()
        if not output:
            return []
        tabs = []
        for line in output.split('\n'):
            parts = line.split('\t', 3)
            if len(parts) == 4:
                tabs.append({
                    'w': int(parts[0]),
                    't': int(parts[1]),
                    'playing': parts[2] == 'false',
                    'title': _clean_title(parts[3]),
                })
        return tabs
    except Exception as e:
        logger.debug(f"Could not get youtube tabs: {e}")
        return []


def get_current_track() -> str | None:
    tabs = get_all_youtube_tabs()
    if tabs:
        return tabs[0]['title']
    return None


def get_playback_progress(window: int = 0, tab: int = 0) -> tuple[float, float] | None:
    browser = get_media_browser()
    url_check = _url_check_expr()

    if window > 0 and tab > 0:
        script = f"""
        tell application "{browser}"
            if not (exists window {window}) then return ""
            set t to tab {tab} of window {window}
            set u to URL of t
            if {url_check} then
                set res to execute t javascript "JSON.stringify({{c: document.querySelector('video').currentTime, d: document.querySelector('video').duration}})"
                return res
            end if
            return ""
        end tell
        """
    else:
        script = f"""
        tell application "{browser}"
            if not (exists window 1) then return ""
            repeat with w in windows
                repeat with t in tabs of w
                    set u to URL of t
                    if {url_check} then
                        set res to execute t javascript "JSON.stringify({{c: document.querySelector('video').currentTime, d: document.querySelector('video').duration}})"
                        return res
                    end if
                end repeat
            end repeat
            return ""
        end tell
        """
    try:
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        if output and output != "":
            data = json.loads(output)
            current = float(data.get('c', 0))
            duration = float(data.get('d', 0))
            if duration > 0:
                return (current, duration)
    except Exception as e:
        logger.debug(f"Could not get playback progress: {e}")
    return None


def toggle_playback(window: int = 0, tab: int = 0) -> bool:
    browser = get_media_browser()
    url_check = _url_check_expr()

    if window > 0 and tab > 0:
        script = f"""
        tell application "{browser}"
            if not (exists window {window}) then return "No window"
            set t to tab {tab} of window {window}
            set u to URL of t
            if {url_check} then
                execute t javascript "document.querySelector('video').paused ? document.querySelector('video').play() : document.querySelector('video').pause()"
                return "Success"
            end if
            return "No tab found"
        end tell
        """
    else:
        script = f"""
        tell application "{browser}"
            if not (exists window 1) then return "No window"
            repeat with w in windows
                repeat with t in tabs of w
                    set u to URL of t
                    if {url_check} then
                        execute t javascript "document.querySelector('video').paused ? document.querySelector('video').play() : document.querySelector('video').pause()"
                        return "Success"
                    end if
                end repeat
            end repeat
            return "No tab found"
        end tell
        """
    try:
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        if output == "Success":
            return True
        else:
            logger.warning(f"Toggle playback returned: {output}")
            return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Error toggling playback: {e.stderr}. Is 'Allow JavaScript from Apple Events' enabled in {browser}?")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in toggle_playback: {e}")
        return False


def next_video(window: int = 0, tab: int = 0) -> bool:
    browser = get_media_browser()
    url_check = _url_check_expr()

    if window > 0 and tab > 0:
        script = f"""
        tell application "{browser}"
            if not (exists window {window}) then return "No window"
            set t to tab {tab} of window {window}
            set u to URL of t
            if {url_check} then
                execute t javascript "var btn = document.querySelector('.ytp-next-button'); if (btn) btn.click(); else throw 'No next button'"
                return "Success"
            end if
            return "No tab found"
        end tell
        """
    else:
        script = f"""
        tell application "{browser}"
            if not (exists window 1) then return "No window"
            repeat with w in windows
                repeat with t in tabs of w
                    set u to URL of t
                    if {url_check} then
                        execute t javascript "var btn = document.querySelector('.ytp-next-button'); if (btn) btn.click(); else throw 'No next button'"
                        return "Success"
                    end if
                end repeat
            end repeat
            return "No tab found"
        end tell
        """
    try:
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        if output == "Success":
            return True
        else:
            logger.warning(f"Next video returned: {output}")
            return False
    except subprocess.CalledProcessError as e:
        logger.debug(f"Could not go to next video (may be end of playlist): {e.stderr}")
        return False
    except Exception as e:
        logger.debug(f"Unexpected error in next_video: {e}")
        return False


def previous_video(window: int = 0, tab: int = 0) -> bool:
    browser = get_media_browser()
    url_check = _url_check_expr()

    if window > 0 and tab > 0:
        script = f"""
        tell application "{browser}"
            if not (exists window {window}) then return "No window"
            set t to tab {tab} of window {window}
            set u to URL of t
            if {url_check} then
                execute t javascript "var btn = document.querySelector('.ytp-prev-button'); if (btn) btn.click(); else throw 'No prev button'"
                return "Success"
            end if
            return "No tab found"
        end tell
        """
    else:
        script = f"""
        tell application "{browser}"
            if not (exists window 1) then return "No window"
            repeat with w in windows
                repeat with t in tabs of w
                    set u to URL of t
                    if {url_check} then
                        execute t javascript "var btn = document.querySelector('.ytp-prev-button'); if (btn) btn.click(); else throw 'No prev button'"
                        return "Success"
                    end if
                end repeat
            end repeat
            return "No tab found"
        end tell
        """
    try:
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        if output == "Success":
            return True
        else:
            logger.warning(f"Previous video returned: {output}")
            return False
    except subprocess.CalledProcessError as e:
        logger.debug(f"Could not go to previous video: {e.stderr}")
        return False
    except Exception as e:
        logger.debug(f"Unexpected error in previous_video: {e}")
        return False
