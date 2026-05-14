"""Notes widget — interactive note-taking with category tabs."""

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Label, ListView, ListItem, Input, TabbedContent, TabPane, Button

from services.notes_service import get_notes, add_note, update_note, delete_note, CATEGORIES


class NoteItem(ListItem):
    """A single note in the list."""

    def __init__(self, note: dict) -> None:
        super().__init__()
        self.note = note

    def compose(self) -> ComposeResult:
        content = self.note["content"]
        if len(content) > 80:
            content = content[:77] + "..."
        cat = self.note.get("category", "general")
        yield Label(f"[{cat}] {content}", classes="note-text")


class NoteInput(Container):
    """Input area for new/editing notes."""

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Input(placeholder="Write a note...", id="note-input", classes="note-input")
            yield Button("Save", id="note-save-btn", variant="success", classes="note-save-btn")


class NotesWidget(Static):
    """Notes panel with category tabs and quick note support."""

    BINDINGS = [
        ("e", "edit_note", "Edit note"),
        ("d", "delete_note", "Delete note"),
    ]

    can_focus = True

    def compose(self) -> ComposeResult:
        yield Label("📝 [ メモ ] NOTES", classes="widget-title")
        with TabbedContent(id="notes-tabs"):
            for cat in CATEGORIES:
                with TabPane(cat.capitalize(), id=f"tab-{cat}"):
                    yield ListView(id=f"note-list-{cat}", classes="note-list")
        yield Label("", id="note-count", classes="note-count")
        with Horizontal(id="note-actions"):
            yield Input(placeholder="Quick note...", id="note-quick-input", classes="note-quick-input")
            yield Button("+", id="note-add-btn", variant="success", classes="note-add-btn")

    def on_mount(self) -> None:
        self.load_notes()

    @work(thread=True)
    def load_notes(self, category: str | None = None) -> None:
        notes = get_notes(category=category)
        self.app.call_from_thread(self._render_notes, notes, category)

    def _render_notes(self, notes: list[dict], category: str | None = None) -> None:
        if category:
            cats = [category]
        else:
            cats = CATEGORIES

        for cat in cats:
            try:
                lv = self.query_one(f"#note-list-{cat}", ListView)
                lv.clear()
                cat_notes = [n for n in notes if n.get("category", "general") == cat]
                for note in cat_notes:
                    lv.append(NoteItem(note))
            except Exception:
                pass

        # Update count
        total = len(notes) if not category else len([n for n in notes if n.get("category") == category])
        try:
            self.query_one("#note-count", Label).update(f"Total: {total} notes")
        except Exception:
            pass

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, NoteItem):
            # Focus the quick input and pre-fill with note content for editing
            input_widget = self.query_one("#note-quick-input", Input)
            input_widget.value = event.item.note["content"]
            input_widget.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "note-quick-input":
            content = event.input.value.strip()
            if content:
                # Determine active tab category
                tabs = self.query_one("#notes-tabs", TabbedContent)
                cat = tabs.active.replace("tab-", "") if tabs.active else "general"
                add_note(content, category=cat)
                event.input.value = ""
                self.load_notes(category=cat)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "note-add-btn":
            input_widget = self.query_one("#note-quick-input", Input)
            content = input_widget.value.strip()
            if content:
                tabs = self.query_one("#notes-tabs", TabbedContent)
                cat = tabs.active.replace("tab-", "") if tabs.active else "general"
                add_note(content, category=cat)
                input_widget.value = ""
                self.load_notes(category=cat)

    def action_edit_note(self) -> None:
        """Edit the currently focused/selected note."""
        for cat in CATEGORIES:
            try:
                lv = self.query_one(f"#note-list-{cat}", ListView)
                if lv.highlighted_child and isinstance(lv.highlighted_child, NoteItem):
                    note = lv.highlighted_child.note
                    input_widget = self.query_one("#note-quick-input", Input)
                    input_widget.value = note["content"]
                    input_widget.focus()
                    # Tag the input with the note id for save-on-enter
                    input_widget.id = f"note-edit-{note['id']}"
                    return
            except Exception:
                pass

    def action_delete_note(self) -> None:
        """Delete the currently focused/selected note."""
        for cat in CATEGORIES:
            try:
                lv = self.query_one(f"#note-list-{cat}", ListView)
                if lv.highlighted_child and isinstance(lv.highlighted_child, NoteItem):
                    note = lv.highlighted_child.note
                    delete_note(note["id"])
                    self.load_notes()
                    return
            except Exception:
                pass