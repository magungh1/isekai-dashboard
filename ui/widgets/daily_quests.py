import logging

from textual import events, work
from textual.message import Message
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static, Label, ListView, ListItem, Input, TabbedContent, TabPane, Button

from services.quests_service import (
    get_quests_by_category, add_quest, toggle_quest, delete_quest,
    update_quest, reset_daily_quests, reset_weekly_quests, update_quests_order
)
from services.xp_service import add_xp, XP_QUEST_COMPLETE
from core.models import Quest

logger = logging.getLogger(__name__)


CATEGORY_COLORS = {
    'daily': ('📋', 'quest-cat-daily'),
    'weekly': ('💼', 'quest-cat-weekly'),
    'goals': ('🎯', 'quest-cat-goals'),
}


class QuestItem(ListItem):
    """A single quest item in the list."""

    class DragStart(Message):
        def __init__(self, item: "QuestItem", start_y: int) -> None:
            self.item = item
            self.start_y = start_y
            super().__init__()

    class DragEnd(Message):
        def __init__(self, item: "QuestItem", end_x: int, end_y: int) -> None:
            self.item = item
            self.end_x = end_x
            self.end_y = end_y
            super().__init__()

    def __init__(self, quest: Quest) -> None:
        super().__init__()
        self.quest = quest
        self._editing = False
        self._is_dragging = False

    def compose(self) -> ComposeResult:
        toggle_label = "[x]" if self.quest.is_done else "[ ]"
        css_class = "quest-done" if self.quest.is_done else "quest-pending"
        cat_icon, cat_css = CATEGORY_COLORS.get(self.quest.category, ('', 'quest-pending'))
        text = self.quest.title
        if self.quest.deadline:
            text += f"  ({self.quest.deadline})"
        with Horizontal(classes="quest-display"):
            yield Button(toggle_label, classes="quest-toggle-btn")
            yield Label(text, classes=f"{css_class} {cat_css}")
            yield Button("x", variant="error", classes="quest-delete-btn")
        # Edit input (hidden by default)
        edit_value = self.quest.title
        if self.quest.deadline:
            edit_value += f" | {self.quest.deadline}"
        yield Input(
            value=edit_value,
            id=f"quest-edit-{self.quest.id}",
            classes="quest-edit-input",
        )

    def on_mount(self) -> None:
        self.query_one(".quest-edit-input", Input).display = False

    def start_edit(self) -> None:
        self._editing = True
        self.query_one(".quest-display", Horizontal).display = False
        edit_input = self.query_one(".quest-edit-input", Input)
        edit_input.display = True
        edit_input.focus()

    def cancel_edit(self) -> None:
        self._editing = False
        self.query_one(".quest-display", Horizontal).display = True
        self.query_one(".quest-edit-input", Input).display = False

    def on_mouse_down(self, event: events.MouseDown) -> None:
        if event.button == 1 and not self._editing:
            try:
                widget_info = self.app.get_widget_at(event.screen_x, event.screen_y)
                widget_at_click = widget_info[0] if isinstance(widget_info, tuple) else widget_info
                if isinstance(widget_at_click, Button):
                    return
            except Exception:
                pass
            
            self._is_dragging = True
            self.capture_mouse()
            self.post_message(self.DragStart(self, event.screen_y))

    def on_mouse_up(self, event: events.MouseUp) -> None:
        if event.button == 1 and self._is_dragging:
            self._is_dragging = False
            self.release_mouse()
            self.post_message(self.DragEnd(self, event.screen_x, event.screen_y))



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

    def on_key(self, event: events.Key) -> None:
        # Handle Escape to cancel edit
        if event.key == "escape" and isinstance(self.app.focused, Input):
            focused = self.app.focused
            if focused.id and focused.id.startswith("quest-edit-"):
                item = focused.parent
                while item and not isinstance(item, QuestItem):
                    item = item.parent
                if isinstance(item, QuestItem):
                    item.cancel_edit()
                    event.prevent_default()
                    event.stop()
                return

        # Handle 'e' to edit highlighted quest
        if event.key == "e" and not isinstance(self.app.focused, Input):
            list_view = self.query_one(f"#quest-list-{self._category}", ListView)
            if list_view.highlighted_child and isinstance(list_view.highlighted_child, QuestItem):
                list_view.highlighted_child.start_edit()
                event.prevent_default()
                event.stop()
                return

        # Handle 'x' to toggle highlighted quest done/undone
        if event.key == "x" and not isinstance(self.app.focused, Input):
            list_view = self.query_one(f"#quest-list-{self._category}", ListView)
            if list_view.highlighted_child and isinstance(list_view.highlighted_child, QuestItem):
                self._toggle_quest(list_view.highlighted_child.quest.id)
                event.prevent_default()
                event.stop()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        item = event.button.parent
        while item and not isinstance(item, QuestItem):
            item = item.parent
        if not isinstance(item, QuestItem):
            return

        if "quest-toggle-btn" in event.button.classes:
            self._toggle_quest(item.quest.id)
        elif "quest-delete-btn" in event.button.classes:
            delete_quest(item.quest.id)
            self._deferred_load()

    def _toggle_quest(self, quest_id: int) -> None:
        quest = toggle_quest(quest_id)
        if quest.is_done:
            add_xp(XP_QUEST_COMPLETE, "quest")
            self.app.notify(
                f"Quest complete! +{XP_QUEST_COMPLETE} XP ⚔️",
                title="Quest",
            )
            try:
                xp_bar = self.app.query_one("XPBar")
                xp_bar.refresh_xp()
            except Exception:
                pass
        self._deferred_load()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        # Handle edit input submission
        if event.input.id and event.input.id.startswith("quest-edit-"):
            quest_id = int(event.input.id.replace("quest-edit-", ""))
            value = event.value.strip()
            if value:
                deadline = None
                if "|" in value:
                    parts = value.rsplit("|", 1)
                    value = parts[0].strip()
                    deadline = parts[1].strip()
                update_quest(quest_id, value, deadline)
            self._deferred_load()
            return

        # Handle add-quest input
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

    def on_quest_item_drag_start(self, event: QuestItem.DragStart) -> None:
        event.item.add_class("dragging-quest")

    def on_quest_item_drag_end(self, event: QuestItem.DragEnd) -> None:
        event.item.remove_class("dragging-quest")
        try:
            widget_at_drop = self.app.get_widget_at(event.end_x, event.end_y)
        except Exception:
            return

        if isinstance(widget_at_drop, tuple) and len(widget_at_drop) > 0:
            target_item = widget_at_drop[0]
        else:
            target_item = widget_at_drop

        while target_item and not isinstance(target_item, QuestItem):
            target_item = target_item.parent
        
        if not target_item or not isinstance(target_item, QuestItem) or target_item is event.item:
            return

        # Both items must be in the same tab/list
        if target_item.quest.category != event.item.quest.category:
            return

        list_view = self.query_one(f"#quest-list-{self._category}", ListView)
        current_items = [child for child in list_view.children if isinstance(child, QuestItem)]
        
        try:
            old_idx = current_items.index(event.item)
            new_idx = current_items.index(target_item)
        except ValueError:
            return

        # Reorder list
        item_to_move = current_items.pop(old_idx)
        current_items.insert(new_idx, item_to_move)

        # Update sort_order in DB for all items in this category
        updates = []
        for i, child in enumerate(current_items):
            updates.append((child.quest.id, i))
        
        update_quests_order(updates)
        self._deferred_load()



class DailyQuests(Static):
    """Tabbed quest widget: Daily, Weekly, Goals."""

    BINDINGS = []

    can_focus = True

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
