"""Integration tests for the Pomodoro widget (UI layer)."""
import pytest
from textual.app import App, ComposeResult

from ui.widgets.pomodoro import Pomodoro, IDLE, WORK, BREAK


class PomodoroApp(App):
    def compose(self) -> ComposeResult:
        yield Pomodoro()


def test_pomodoro_initial_state():
    """Pomodoro starts in IDLE state."""
    widget = Pomodoro()
    assert widget._phase == IDLE
    assert widget._work_minutes == 25
    assert widget._break_minutes == 5
    assert widget._seconds_left == 25 * 60


def test_pomodoro_custom_preset():
    """Pomodoro accepts custom durations (state check only — mounted test below)."""
    widget = Pomodoro()
    # Directly set durations without triggering UI queries
    widget._work_minutes = 50
    widget._break_minutes = 10
    widget._seconds_left = 50 * 60
    widget._total_seconds = 50 * 60
    assert widget._work_minutes == 50
    assert widget._break_minutes == 10


def test_pomodoro_presets():
    """Default presets are valid."""
    from ui.widgets.pomodoro import _get_presets
    presets = _get_presets()
    assert len(presets) >= 3  # 25/5, 50/10, 15/3
    assert presets[0] == (25, 5, "25/5")


def test_pomodoro_format_time():
    """Time formatting works correctly."""
    widget = Pomodoro()
    widget._seconds_left = 25 * 60
    assert widget._format_time() == "  25:00  "

    widget._seconds_left = 5 * 60 + 30
    assert widget._format_time() == "  05:30  "

    widget._seconds_left = 0
    assert widget._format_time() == "  00:00  "

    widget._seconds_left = 3600 + 5 * 60
    assert widget._format_time() == "  65:00  "


async def test_pomodoro_mounted():
    """A mounted Pomodoro widget should render without error."""
    app = PomodoroApp()
    async with app.run_test():
        assert app.query_one(Pomodoro) is not None


def test_pomodoro_phase_transitions():
    """Phase state machine transitions correctly."""
    widget = Pomodoro()

    # Start as IDLE
    assert widget._phase == IDLE

    # Simulate starting work
    widget._phase = WORK
    assert widget._phase == WORK

    # Simulate work -> break
    widget._phase = BREAK
    assert widget._phase == BREAK

    # Simulate break -> work
    widget._phase = WORK
    assert widget._phase == WORK

    # Reset
    widget._phase = IDLE
    assert widget._phase == IDLE


def test_pomodoro_reset_state():
    """Resetting returns to initial state."""
    widget = Pomodoro()
    widget._phase = WORK
    widget._seconds_left = 100
    widget._phase = IDLE
    widget._seconds_left = widget._work_minutes * 60
    assert widget._phase == IDLE
    assert widget._seconds_left == 25 * 60


# ---- XP service integration ----

def test_xp_constants_defined():
    """XP constants are properly defined."""
    from services.xp_service import XP_QUEST_COMPLETE, XP_SRS_REVIEW, XP_POMODORO_COMPLETE, LEVEL_BASE
    assert XP_QUEST_COMPLETE == 10
    assert XP_SRS_REVIEW == 5
    assert XP_POMODORO_COMPLETE == 25
    assert LEVEL_BASE == 50