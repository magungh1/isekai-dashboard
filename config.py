from __future__ import annotations
import tomllib
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent / "config.toml"

_DEFAULTS: dict = {
    "database": {"path": "isekai.db"},
    "srs": {"intervals": [0, 4, 24, 72, 168, 720], "mastery_level": 4},
    "xp": {"quest_complete": 10, "srs_review": 5, "pomodoro_complete": 25, "level_base": 50},
    "github": {"pr_max_age_days": 90},
    "llm": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "nvidia/nemotron-3-super-120b-a12b:free",
        "max_tokens": 1000,
        "api_key": "",
    },
}


def _load() -> dict:
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, "rb") as f:
            return tomllib.load(f)
    return {}


_cfg = _load()


def get(section: str, key: str, default=None):
    fallback = _DEFAULTS.get(section, {}).get(key, default)
    return _cfg.get(section, {}).get(key, fallback)


def reload() -> None:
    global _cfg
    _cfg = _load()


def all_sections() -> dict:
    """Return merged config (defaults + user overrides) for all sections."""
    merged = {}
    for section, keys in _DEFAULTS.items():
        merged[section] = {k: get(section, k) for k in keys}
    return merged
