"""Command Palette — fuzzy-finder modal for quick actions."""

import logging
from textual import events
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Input, ListView, ListItem, Label
from textual.containers import Horizontal

logger = logging.getLogger(__name__)


class CmdItem(ListItem):
    """A single command in the palette list."""

    def __init__(self, command: dict) -> None:
        super().__init__()
        self.command = command

    def compose(self) -> ComposeResult:
        with Horizontal(classes="cmd-item-row"):
            yield Label(f"{self.command['icon']} {self.command['name']}", classes="cmd-name")
            yield Label(f"[{self.command['source']}]", classes="cmd-source")


class CommandPaletteScreen(Screen):
    """Modal overlay with fuzzy command search."""

    BINDINGS = [
        ("escape", "dismiss", "Close"),
    ]

    def __init__(self, commands: list[dict], **kwargs) -> None:
        super().__init__(**kwargs)
        self._commands = commands

    def compose(self) -> ComposeResult:
        with Container(id="cmd-palette"):
            yield Input(placeholder="Type a command...", id="cmd-input")
            yield ListView(id="cmd-list")

    def on_mount(self) -> None:
        self.query_one("#cmd-input", Input).focus()
        self._update_results("")

    def on_input_changed(self, event: Input.Changed) -> None:
        self._update_results(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._execute_first()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, CmdItem):
            self._execute(event.item.command)

    def _update_results(self, query: str) -> None:
        list_view = self.query_one("#cmd-list", ListView)
        list_view.clear()

        if not query.strip():
            for cmd in self._commands[:8]:
                list_view.append(CmdItem(cmd))
            return

        scored = self._score_commands(query.lower(), self._commands)
        scored.sort(key=lambda x: x[1], reverse=True)

        for cmd, _score in scored[:8]:
            list_view.append(CmdItem(cmd))

    def _score_commands(self, query: str, commands: list[dict]) -> list[tuple[dict, int]]:
        results = []
        for cmd in commands:
            score = 0
            name_lower = cmd["name"].lower()
            keywords = [k.lower() for k in cmd.get("keywords", [])]

            if name_lower == query:
                score = 100
            elif name_lower.startswith(query):
                score = 80
            elif query in name_lower:
                score = 50

            for kw in keywords:
                if kw == query:
                    score = max(score, 60)
                elif kw.startswith(query):
                    score = max(score, 55)
                elif query in kw:
                    score = max(score, 40)

            if score > 0:
                results.append((cmd, score))

        return results

    def _execute_first(self) -> None:
        list_view = self.query_one("#cmd-list", ListView)
        if list_view.children:
            first = list_view.children[0]
            if isinstance(first, CmdItem):
                self._execute(first.command)

    def _execute(self, command: dict) -> None:
        try:
            command["action"]()
        except Exception:
            logger.exception("Failed to execute command: %s", command["name"])
        self.dismiss()

    def action_dismiss(self) -> None:
        self.dismiss()
