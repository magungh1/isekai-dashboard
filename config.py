"""Simple config loader — reads from environment variables, with fallback defaults."""

import os

_defaults = {
    "database":  {"path": "isekai.db"},
    "srs":       {"intervals": "0,4,24,72,168,720", "mastery_level": "4"},
}


def _parse_list(value: str) -> list:
    return [v.strip() for v in value.split(",")]


def get(section: str, key: str, default=None):
    env_key = f"SC_{section.upper()}_{key.upper()}"
    env_val = os.environ.get(env_key)
    if env_val is not None:
        return env_val

    if default is not None:
        return default

    sect = _defaults.get(section, {})
    val = sect.get(key, "")

    if "," in val:
        return _parse_list(val)

    try:
        return int(val)
    except (ValueError, TypeError):
        pass

    return val