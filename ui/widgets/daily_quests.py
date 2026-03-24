from textual import work
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Static, Label, ListView, ListItem, Input

from services.quests_service import get_all_quests, add_quest, toggle_quest, delete_quest
from core.models import Quest


class QuestItem(ListItem):
    """A single quest item in the list."""

    def __init__(self, quest: Quest) -> None:
        super().__init__()
        self.quest = quest

    def compose(self) -> ComposeResult:
        prefix = "[x]" if self.quest.is_done else "[ ]"
        css_class = "quest-done" if self.quest.is_done else "quest-pending"
        yield Label(f"{prefix} {self.quest.title}", classes=css_class)


class DailyQuests(Static):
    """Interactive quest list backed by SQLite."""

    def compose(self) -> ComposeResult:
        yield Label("📜 [ 進行中のクエスト ] DAILY QUESTS", classes="widget-title")
        yield ListView(id="quest-list")
        yield Input(placeholder="+ Add new quest...", id="quest-input")

    def on_mount(self) -> None:
        self.load_quests()

    @work(thread=True)
    def load_quests(self) -> None:
        quests = get_all_quests()
        self.app.call_from_thread(self._render_quests, quests)

    def _render_quests(self, quests: list[Quest]) -> None:
        list_view = self.query_one("#quest-list", ListView)
        list_view.clear()
        for quest in quests:
            list_view.append(QuestItem(quest))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, QuestItem):
            self._toggle_quest(event.item.quest.id)

    @work(thread=True)
    def _toggle_quest(self, quest_id: int) -> None:
        toggle_quest(quest_id)
        quests = get_all_quests()
        self.app.call_from_thread(self._render_quests, quests)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.value.strip():
            self._add_quest(event.value.strip())
            event.input.value = ""

    @work(thread=True)
    def _add_quest(self, title: str) -> None:
        add_quest(title)
        quests = get_all_quests()
        self.app.call_from_thread(self._render_quests, quests)
