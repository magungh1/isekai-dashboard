import subprocess
import os
import logging

logger = logging.getLogger(__name__)

def get_media_browser() -> str:
    """Returns the configured media browser, defaulting to Brave Browser."""
    return os.environ.get("MEDIA_BROWSER", "Brave Browser")

def get_current_track() -> str | None:
    """
    Queries the configured browser via AppleScript to find a YouTube or YouTube Music tab.
    Returns the title of the tab if found, otherwise None.
    """
    browser = get_media_browser()
    
    script = f"""
    tell application "{browser}"
        if not (exists window 1) then return ""
        repeat with w in windows
            repeat with t in tabs of w
                set u to URL of t
                if u contains "youtube.com/watch" or u contains "music.youtube.com" then
                    return title of t
                end if
            end repeat
        end repeat
        return ""
    end tell
    """
    try:
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, check=True)
        title = result.stdout.strip()
        if title:
            # Clean up the title a bit (remove " - YouTube" or " - YouTube Music")
            title = title.replace(" - YouTube Music", "").replace(" - YouTube", "")
            return title
        return None
    except subprocess.CalledProcessError as e:
        logger.error(f"Error querying media track: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in get_current_track: {e}")
        return None

def toggle_playback() -> bool:
    """
    Injects JavaScript into the active YouTube/YouTube Music tab to toggle play/pause.
    Requires 'Allow JavaScript from Apple Events' to be enabled in the browser's Developer menu.
    Returns True if the command was sent successfully, False otherwise.
    """
    browser = get_media_browser()
    
    script = f"""
    tell application "{browser}"
        if not (exists window 1) then return "No window"
        repeat with w in windows
            repeat with t in tabs of w
                set u to URL of t
                if u contains "youtube.com/watch" or u contains "music.youtube.com" then
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
