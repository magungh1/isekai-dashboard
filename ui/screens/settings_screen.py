from __future__ import annotations

import tomli_w
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Label, ListItem, ListView

import config

# Human-readable descriptions for each setting key
_HINTS: dict[str, dict[str, str]] = {
    "database": {
        "path": "SQLite database filename",
    },
    "srs": {
        "intervals": "Review interval hours per level (comma-separated: new,4h,1d,3d,1w,1mo)",
        "mastery_level": "Minimum level to count a card as mastered",
    },
    "xp": {
        "quest_complete": "XP awarded for completing a quest",
        "srs_review": "XP awarded for each SRS review",
        "pomodoro_complete": "XP awarded for completing a pomodoro session",
        "level_base": "Base XP for level formula: LEVEL_BASE x N^1.5",
    },
    "github": {
        "pr_max_age_days": "Max age of PRs to fetch (days)",
    },
    "llm": {
        "base_url": "OpenRouter API base URL",
        "model": "Model identifier for mnemonic generation",
        "max_tokens": "Max tokens per LLM response",
        "api_key": "OpenRouter API key (overrides OPENROUTER_API_KEY env var if set)",
    },
}

_SECTIONS = list(_HINTS.keys())


def _value_to_str(val) -> str:
    if isinstance(val, list):
        return ",".join(str(v) for v in val)
    return str(val)


def _str_to_value(key: str, section: str, raw: str):
    """Parse raw string back to appropriate Python type."""
    defaults = config._DEFAULTS.get(section, {}).get(key)
    if isinstance(defaults, list):
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        return [int(p) if p.isdigit() else p for p in parts]
    if isinstance(defaults, int):
        try:
            return int(raw)
        except ValueError:
            return defaults
    return raw


class SettingsScreen(Screen):
    CSS_PATH = "../styles_settings.tcss"

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", show=True),
        Binding("s", "save", "Save", show=True),
        Binding("r", "reset_section", "Reset section", show=True),
    ]

    def __init__(self):
        super().__init__()
        self._section = _SECTIONS[0]
        self._pending: dict[str, dict[str, str]] = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Horizontal(id="settings-layout"):
            with ListView(id="settings-nav"):
                for s in _SECTIONS:
                    yield ListItem(Label(s), id=f"nav-{s}")
            with VerticalScroll(id="settings-content"):
                pass
        yield Footer()

    async def on_mount(self) -> None:
        await self._render_section(self._section)

    async def _render_section(self, section: str) -> None:
        content = self.query_one("#settings-content", VerticalScroll)
        await content.remove_children()

        widgets: list = []
        for key, hint in _HINTS.get(section, {}).items():
            pending_val = self._pending.get(section, {}).get(key)
            current = pending_val if pending_val is not None else _value_to_str(config.get(section, key))
            widgets.append(Label(f"[bold #58a6ff]{key}[/]", classes="settings-field-label"))
            widgets.append(Label(hint, classes="settings-field-hint"))
            widgets.append(Input(
                value=current,
                id=f"field-{section}-{key}",
                classes="settings-input",
            ))

        await content.mount(*widgets)

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id or ""
        if item_id.startswith("nav-"):
            self._section = item_id[4:]
            await self._render_section(self._section)

    def on_input_changed(self, event: Input.Changed) -> None:
        field_id = event.input.id or ""
        if not field_id.startswith("field-"):
            return
        _, section, key = field_id.split("-", 2)
        self._pending.setdefault(section, {})[key] = event.value

    def action_save(self) -> None:
        merged = config.all_sections()
        for section, changes in self._pending.items():
            for key, raw in changes.items():
                merged.setdefault(section, {})[key] = _str_to_value(key, section, raw)

        config._CONFIG_PATH.write_bytes(tomli_w.dumps(merged).encode())
        config.reload()
        self._pending.clear()
        self.app.notify("Settings saved — restart for timer/interval changes to take effect")
        self.app.pop_screen()

    async def action_reset_section(self) -> None:
        """Reset all fields in the current section to defaults."""
        self._pending.pop(self._section, None)
        await self._render_section(self._section)
        self.app.notify(f"Reset [{self._section}] to defaults")
