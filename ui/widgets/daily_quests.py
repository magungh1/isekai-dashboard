import logging

from textual import work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static, Label, ListView, ListItem, Input, TabbedContent, TabPane, Button

from services.quests_service import (
    get_quests_by_category, add_quest, toggle_quest, delete_quest,
    reset_daily_quests, reset_weekly_quests,
)
from core.models import Quest

logger = logging.getLogger(__name__)


class QuestItem(ListItem):
    """A single quest item in the list."""

    def __init__(self, quest: Quest) -> None:
        super().__init__()
        self.quest = quest

    def compose(self) -> ComposeResult:
        prefix = "[x]" if self.quest.is_done else "[ ]"
        css_class = "quest-done" if self.quest.is_done else "quest-pending"
        text = f"{prefix} {self.quest.title}"
        if self.quest.deadline:
            text += f"  ({self.quest.deadline})"
        with Horizontal():
            yield Label(text, classes=css_class)
            yield Button("x", variant="error", classes="quest-delete-btn")


class QuestTab(Container):
    """A single quest tab with its own list and input."""

    def __init__(self, category: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._category = category

    def compose(self) -> ComposeResult:
        placeholder = "+ Add new quest..."
        if self._category == "goals":
            placeholder = "+ Add goal (or: title | 2026-06-01)..."
        yield ListView(id=f"quest-list-{self._category}", classes="quest-list")
        yield Input(placeholder=placeholder, id=f"quest-input-{self._category}",
                    classes="quest-input")

    def on_mount(self) -> None:
        self.set_timer(0.1, self._deferred_load)

    def _deferred_load(self) -> None:
        self.load_quests()

    def load_quests(self) -> None:
        try:
            quests = get_quests_by_category(self._category)
            logger.debug("Loaded %d quests for category=%s", len(quests), self._category)
            self._render_quests(quests)
        except Exception:
            logger.exception("Failed to load quests for category=%s", self._category)

    def _render_quests(self, quests: list[Quest]) -> None:
        list_view = self.query_one(f"#quest-list-{self._category}", ListView)
        list_view.clear()
        logger.debug("Rendering %d quests into %s, list_view=%r", len(quests), f"#quest-list-{self._category}", list_view)
        for quest in quests:
            list_view.append(QuestItem(quest))
        logger.debug("ListView children count: %d", len(list_view.children))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if "quest-delete-btn" in event.button.classes:
            item = event.button.parent
            while item and not isinstance(item, QuestItem):
                item = item.parent
            if item and isinstance(item, QuestItem):
                delete_quest(item.quest.id)
                self._deferred_load()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, QuestItem):
            self._toggle_quest(event.item.quest.id)

    def _toggle_quest(self, quest_id: int) -> None:
        toggle_quest(quest_id)
        self._deferred_load()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != f"quest-input-{self._category}":
            return
        value = event.value.strip()
        if not value:
            return
        deadline = None
        if self._category == "goals" and "|" in value:
            parts = value.rsplit("|", 1)
            value = parts[0].strip()
            deadline = parts[1].strip()
        self._add_quest(value, deadline)
        event.input.value = ""

    def _add_quest(self, title: str, deadline: str | None = None) -> None:
        add_quest(title, category=self._category, deadline=deadline)
        self._deferred_load()


class DailyQuests(Static):
    """Tabbed quest widget: Daily, Weekly, Goals."""

    def compose(self) -> ComposeResult:
        yield Label("📜 [ クエスト ] QUESTS", classes="widget-title")
        with TabbedContent(id="quest-tabs"):
            with TabPane("📜 Daily", id="tab-daily"):
                yield QuestTab(category="daily")
            with TabPane("💼 Weekly", id="tab-weekly"):
                yield QuestTab(category="weekly")
            with TabPane("🎯 Goals", id="tab-goals"):
                yield QuestTab(category="goals")

    def _run_resets(self) -> None:
        reset_daily_quests()
        reset_weekly_quests()

    def on_mount(self) -> None:
        self._run_resets()
