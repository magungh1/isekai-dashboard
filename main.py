import logging
import os
import sys

logging.basicConfig(
    filename=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'isekai.log'),
    level=logging.DEBUG,
    format='%(asctime)s %(name)s %(levelname)s %(message)s',
)
logger = logging.getLogger(__name__)

# Ensure project root is on the path for imports
_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _root)

# Load .env file if present
_env_path = os.path.join(_root, '.env')
logger.info("Looking for .env at: %s (exists=%s)", _env_path, os.path.isfile(_env_path))
if os.path.isfile(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _key, _, _val = _line.partition('=')
                _key = _key.strip()
                _val = _val.strip().strip('"').strip("'")
                os.environ.setdefault(_key, _val)
                logger.info("Loaded env var: %s (length=%d)", _key, len(_val))
else:
    logger.warning(".env file not found at %s", _env_path)

logger.info("OPENROUTER_API_KEY in env: %s", bool(os.environ.get('OPENROUTER_API_KEY')))

from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Grid
from textual.widgets import Header, Footer

from ui.widgets.daily_quests import DailyQuests
from ui.widgets.productivity_tabs import ProductivityTabs
from ui.widgets.pull_requests import PullRequests
from ui.widgets.calendar import Calendar
from ui.widgets.srs_tabs import SRSTabs
from ui.widgets.now_playing import NowPlaying
from ui.widgets.xp_bar import XPBar
from ui.screens.settings_screen import SettingsScreen
from config import get

DB_PATH = get("database", "path", "isekai.db")

class IsekaiDashboard(App):
    CSS_PATH = "ui/styles.tcss"
    TITLE = "Isekai Dev Dashboard"
    SUB_TITLE = "異世界開発者ダッシュボード"

    SCREENS = {"settings": SettingsScreen}

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("a", "quick_add_quest", "Add Quest"),
        Binding("comma", "push_screen('settings')", "Settings"),
    ]

    _widget_classes = [DailyQuests, ProductivityTabs, PullRequests, Calendar, SRSTabs, NowPlaying]
    _pending_g: bool = False

    def on_key(self, event: events.Key) -> None:
        from textual.widgets import Input
        # Don't intercept keys when typing in an input field
        if isinstance(self.focused, Input):
            self._pending_g = False
            return

        if self._pending_g:
            self._pending_g = False
            if event.character and event.character in "123456":
                self.action_focus_widget(int(event.character) - 1)
                event.prevent_default()
                event.stop()
            return

        if event.character == "g":
            self._pending_g = True
            event.prevent_default()
            event.stop()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield XPBar(id="xp-bar")
        with Grid(id="dashboard-grid"):
            yield DailyQuests(classes="tool-widget")
            yield ProductivityTabs(classes="tool-widget")
            yield PullRequests(classes="tool-widget")
            yield Calendar(classes="tool-widget")
            yield SRSTabs(classes="tool-widget")
            yield NowPlaying(classes="tool-widget")
        yield Footer()

    def action_focus_widget(self, index: int) -> None:
        widgets = self.query(".tool-widget")
        if 0 <= index < len(widgets):
            widgets[index].focus()

    def action_quick_add_quest(self) -> None:
        quests = self.query_one(DailyQuests)
        quests.focus()
        try:
            from textual.widgets import TabbedContent
            tabs = quests.query_one("#quest-tabs", TabbedContent)
            active_id = tabs.active
            category = active_id.replace("tab-", "") if active_id else "daily"
            input_widget = quests.query_one(f"#quest-input-{category}")
            input_widget.focus()
        except Exception:
            pass

    def on_mount(self) -> None:
        if not os.path.exists(DB_PATH):
            self.notify("Database not found. Run: python db_init.py", severity="warning")


if __name__ == "__main__":
    IsekaiDashboard().run()
