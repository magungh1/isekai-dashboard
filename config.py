import os
import logging

logger = logging.getLogger(__name__)

_defaults = {
    "database":  {"path": "isekai.db"},
    "srs": {
        "intervals": "0,4,24,72,168,720",
        "mastery_level": "4",
        "deck_size": "20",
        "level_count": "6",
        "progress_bar_width": "20",
        "progress_bar_width_stats": "12",
        "badge_refresh_interval": "30",
    },
    "media": {
        "browser": "Brave Browser",
        "poll_interval": "3",
        "url_patterns": "youtube.com/watch,music.youtube.com",
        "title_suffixes": " - YouTube Music, - YouTube",
    },
    "github": {
        "pr_max_age_days": "90",
        "refresh_interval": "300",
        "notification_reasons": "review_requested,mention",
        "notify_timeout": "10",
        "title_snippet_length": "50",
    },
    "calendar": {
        "refresh_interval": "120",
        "soon_threshold": "30",
        "notify_window": "3",
    },
    "pomodoro": {
        "work_minutes": "25",
        "break_minutes": "5",
        "presets": "25:5,50:10,15:3",
        "notification_sound": "Glass",
        "quote_interval": "300",
        "max_sessions": "4",
    },
    "xp": {
        "quest_complete": "10",
        "srs_review": "5",
        "pomodoro_complete": "25",
        "level_base": "50",
        "refresh_interval": "10",
    },
    "habits": {
        "default_xp": "5",
        "streak_bonus_7": "20",
        "streak_bonus_30": "100",
    },
    "db": {
        "pool_min": "2",
        "pool_max": "10",
        "port": "5432",
        "sslmode": "require",
    },
    "llm": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "nvidia/nemotron-3-super-120b-a12b:free",
        "max_tokens": "1000",
    },
    "quests": {
        "completed_limit": "50",
    },
}


def _parse_list(value: str) -> list:
    return [_coerce_item(v.strip()) for v in value.split(",") if v.strip()]


def _coerce_item(value: str):
    try:
        return int(value)
    except (ValueError, TypeError):
        pass
    try:
        return float(value)
    except (ValueError, TypeError):
        pass
    return value


def _coerce(value: str):
    if "," in value:
        return _parse_list(value)
    return _coerce_item(value)


def get(section: str, key: str, default=None):
    env_key = f"SC_{section.upper()}_{key.upper()}"
    env_val = os.environ.get(env_key)
    if env_val is not None:
        logger.debug("Config: %s = %s (from env)", env_key, env_val)
        return _coerce(env_val)
    if default is not None:
        return default
    sect = _defaults.get(section, {})
    val = sect.get(key, "")
    if not val:
        return val
    return _coerce(val)


def get_list(section: str, key: str) -> list:
    val = get(section, key)
    if isinstance(val, list):
        return val
    if isinstance(val, str) and val:
        return [v.strip() for v in val.split(",") if v.strip()]
    return []


def get_int(section: str, key: str, default: int = 0) -> int:
    val = get(section, key)
    if val is None or val == "":
        return default
    return int(val)


def get_float(section: str, key: str, default: float = 0.0) -> float:
    val = get(section, key)
    if val is None or val == "":
        return default
    return float(val)


def get_browser() -> str:
    env = os.environ.get("BROWSER_NAME") or os.environ.get("SC_MEDIA_BROWSER")
    if env:
        return env
    return _defaults["media"]["browser"]


def log_config() -> None:
    logger.info("Config")
    for section, keys in _defaults.items():
        for key in keys:
            val = get(section, key)
            if isinstance(val, list):
                val = ", ".join(str(v) for v in val)
            logger.info("  %s.%s = %s", section, key, val)
    logger.info("  browser = %s", get_browser())
