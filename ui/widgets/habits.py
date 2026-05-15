"""Habit tracker widget — weekly heatmap, streaks, keyboard + mouse toggle."""

import logging
from datetime import date, timedelta

from textual import events, work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Label, ListView, ListItem, Input, Button

from services.habits_service import (
    get_all_habits_week, add_habit, delete_habit, update_habit,
    cycle_habit_day, set_habit_count, get_habit_xp_reward,
    get_streak_bonus, get_week_range,
)
from services.xp_service import add_xp

logger = logging.getLogger(__name__)

STATUS_SYMBOLS = {
    "done": "✓",
    "skipped": "○",
    "missed": "✗",
    "": "·",
}

STATUS_CSS = {
    "done": "habit-done",
    "skipped": "habit-skipped",
    "missed": "habit-missed",
    "": "habit-empty",
}

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class DayCell(Button):
    """A single day cell in the habit row."""

    def __init__(self, habit_id: int, date_str: str, status: str, count: int = 0, target: int = 1, is_countable: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self.habit_id = habit_id
        self.date_str = date_str
        self.status = status
        self.count = count
        self.target = target
        self.is_countable = is_countable
        self._update_display()

    def _update_display(self) -> None:
        if self.is_countable and self.status == "done":
            self.label = f"{self.count}/{self.target}"
        else:
            self.label = STATUS_SYMBOLS.get(self.status, "·")
        self.remove_class(*STATUS_CSS.values())
        self.add_class(STATUS_CSS.get(self.status, "habit-empty"))


class HabitItem(ListItem):
    """A single habit row with name, streak, and 7 day cells."""

    def __init__(self, habit_data: dict, week_start: date) -> None:
        super().__init__()
        self.habit_data = habit_data
        self.week_start = week_start

    def compose(self) -> ComposeResult:
        h = self.habit_data
        streak = h["streak"]
        streak_icon = "🔥" if streak > 0 else "  "
        streak_text = f"{streak_icon}{streak}" if streak > 0 else "  "

        with Horizontal(classes="habit-row"):
            yield Label(f" {h['icon']} {h['name']}", classes="habit-name")
            yield Label(streak_text, classes="habit-streak")

            for day_data in h["week"]:
                cell = DayCell(
                    habit_id=h["id"],
                    date_str=day_data["date"],
                    status=day_data["status"],
                    count=day_data["count"],
                    target=h.get("target_count", 1),
                    is_countable=bool(h.get("is_countable", False)),
                    classes="habit-day-cell",
                )
                yield cell

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if isinstance(event.button, DayCell):
            cell = event.button
            if cell.is_countable:
                if cell.status == "done":
                    cell.count = max(0, cell.count - 1)
                    if cell.count == 0:
                        cell.status = ""
                    cell._update_display()
                    self._save_cell(cell)
                else:
                    cell.status = "done"
                    cell.count = 1
                    cell._update_display()
                    self._save_cell(cell)
            else:
                self._cycle_cell(cell)

    def _cycle_cell(self, cell: DayCell) -> None:
        old_status = cell.status
        result = cycle_habit_day(cell.habit_id, cell.date_str)
        cell.status = result["status"]
        cell.count = result.get("count", 0)
        cell._update_display()

        if result["status"] == "done" and old_status != "done":
            self._award_xp(cell.habit_id, cell.date_str)

    def _save_cell(self, cell: DayCell) -> None:
        if cell.status == "done" and cell.count > 0:
            result = set_habit_count(cell.habit_id, cell.date_str, cell.count)
            cell.status = result["status"]
            cell.count = result.get("count", 0)
            cell._update_display()
        elif cell.status == "":
            from core.db import get_shared_connection, release_connection
            conn = get_shared_connection()
            try:
                conn.execute("DELETE FROM habit_log WHERE habit_id = %s AND date = %s", (cell.habit_id, cell.date_str))
                conn.commit()
            finally:
                release_connection(conn)

    def _award_xp(self, habit_id: int, date_str: str) -> None:
        xp = get_habit_xp_reward(habit_id)
        add_xp(xp, "habit")

        streak = self._get_streak_for(habit_id)
        bonus = get_streak_bonus(streak)
        if bonus > 0:
            add_xp(bonus, "habit_streak")

        try:
            xp_bar = self.app.query_one("XPBar")
            xp_bar.refresh_xp()
        except Exception:
            pass

        total_xp = xp + bonus
        msg = f"+{total_xp} XP"
        if bonus > 0:
            msg += f" (🔥{streak}-day streak bonus!)"
        self.app.notify(msg, title="Habit")

    def _get_streak_for(self, habit_id: int) -> int:
        from services.habits_service import get_streak
        return get_streak(habit_id)


class HabitsWidget(Static):
    """Habit tracker with weekly heatmap."""

    can_focus = True

    def compose(self) -> ComposeResult:
        yield Label("📊 [ 習慣 ] HABITS", classes="widget-title")
        yield Label("", id="habit-week-label", classes="habit-week-label")
        yield ListView(id="habit-list", classes="habit-list")
        with Horizontal(classes="habit-actions"):
            yield Input(
                placeholder="+ Add habit (name | icon | xp | countable)...",
                id="habit-input",
                classes="habit-input",
            )
            yield Button("+", id="habit-add-btn", variant="success", classes="habit-add-btn")

    def on_mount(self) -> None:
        self._load_habits()

    def _load_habits(self) -> None:
        self._deferred_load()

    @work(thread=True)
    def _deferred_load(self) -> None:
        week_start, week_end = get_week_range()
        data = get_all_habits_week(week_start)
        self.app.call_from_thread(self._render_habits, data, week_start, week_end)

    def _render_habits(self, data: list[dict], week_start: date, week_end: date) -> None:
        list_view = self.query_one("#habit-list", ListView)
        list_view.clear()

        week_label = self.query_one("#habit-week-label", Label)
        week_label.update(f"{week_start.strftime('%b %d')} — {week_end.strftime('%b %d')}")

        for habit_data in data:
            list_view.append(HabitItem(habit_data, week_start))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "habit-input":
            self._add_habit_from_input(event.value)
            event.input.value = ""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "habit-add-btn":
            input_widget = self.query_one("#habit-input", Input)
            self._add_habit_from_input(input_widget.value)
            input_widget.value = ""

    def _add_habit_from_input(self, value: str) -> None:
        value = value.strip()
        if not value:
            return

        parts = [p.strip() for p in value.split("|")]
        name = parts[0]
        icon = parts[1] if len(parts) > 1 and parts[1] else "📌"
        xp = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None
        countable = len(parts) > 3 and parts[3].lower() in ("count", "countable", "c", "1")

        add_habit(name, icon=icon, xp_reward=xp, is_countable=countable, target_count=8 if countable else 1)
        self._deferred_load()
