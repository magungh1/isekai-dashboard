from datetime import datetime

from textual.app import ComposeResult
from textual.widgets import Static, Label, ListView, ListItem, Input, Button
from textual.containers import Horizontal, VerticalScroll

from services.notes_service import add_note, get_recent_notes, delete_note


class NoteItem(ListItem):
    def __init__(self, note: dict) -> None:
        super().__init__()
        self.note = note

    def compose(self) -> ComposeResult:
        ts = self.note['created_at']
        try:
            dt = datetime.fromisoformat(ts)
            time_str = dt.strftime("%H:%M")
        except (ValueError, TypeError):
            time_str = "??:??"
        with Horizontal(classes="note-row"):
            yield Label(f"[{time_str}]", classes="note-time")
            yield Label(self.note['content'], classes="note-text")
            yield Button("x", variant="error", classes="note-delete-btn")


class Notes(Static):
    BINDINGS = []

    can_focus = True

    def compose(self) -> ComposeResult:
        yield Label("📝 [ メモ ] NOTES", classes="widget-title")
        yield Input(placeholder="Dump a thought... (Enter to save)", id="note-input", classes="note-input")
        with VerticalScroll(id="note-list-scroll"):
            yield ListView(id="note-list", classes="note-list")

    def on_mount(self) -> None:
        self._load_notes()

    def _load_notes(self) -> None:
        notes = get_recent_notes()
        note_list = self.query_one("#note-list", ListView)
        note_list.clear()
        if not notes:
            note_list.append(ListItem(Label("No notes yet. Start typing!", classes="note-empty")))
        else:
            for note in notes:
                note_list.append(NoteItem(note))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "note-input":
            return
        value = event.value.strip()
        if not value:
            return
        add_note(value)
        event.input.value = ""
        self._load_notes()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if "note-delete-btn" not in event.button.classes:
            return
        item = event.button.parent
        while item and not isinstance(item, NoteItem):
            item = item.parent
        if isinstance(item, NoteItem):
            delete_note(item.note['id'])
            self._load_notes()
