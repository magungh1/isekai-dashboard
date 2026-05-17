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
from textual.containers import Grid
from textual.widgets import Header, Footer

from ui.widgets.daily_quests import DailyQuests
from ui.widgets.pomo_notes_tabs import PomoNotesTabs
from ui.widgets.pull_requests import PullRequests
from ui.widgets.calendar import Calendar
from ui.widgets.srs_tabs import SRSTabs
from ui.widgets.now_playing import NowPlaying
from ui.widgets.xp_bar import XPBar
from ui.widgets.command_palette import CommandPaletteScreen

from config import get, get_browser, log_config
from core.db import _use_supabase


class IsekaiDashboard(App):
    CSS_PATH = "ui/styles.tcss"
    TITLE = "Isekai Dev Dashboard"
    SUB_TITLE = "異世界開発者ダッシュボード"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("a", "quick_add_quest", "Add Quest"),
        ("ctrl+p", "command_palette", "Commands"),
    ]

    _widget_classes = [DailyQuests, PomoNotesTabs, PullRequests, Calendar, SRSTabs, NowPlaying]
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
            yield PomoNotesTabs(classes="tool-widget")
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
            category = active_id.replace("tab-", "") if active_id else "todo"
            input_widget = quests.query_one(f"#quest-input-{category}")
            input_widget.focus()
        except Exception:
            pass

    def action_command_palette(self) -> None:
        commands = self._build_commands()
        self.push_screen(CommandPaletteScreen(commands))

    def _build_commands(self) -> list[dict]:
        from ui.widgets.srs_tabs import SRSTabs, TAB_IDS as SRS_TAB_IDS
        from ui.widgets.pomo_notes_tabs import PomoNotesTabs
        from ui.widgets.daily_quests import DailyQuests
        from ui.widgets.pull_requests import PullRequests
        from ui.widgets.now_playing import NowPlaying
        from ui.widgets.calendar import Calendar
        from textual.widgets import TabbedContent

        def focus_widget(cls):
            def _inner():
                try:
                    w = self.query_one(cls)
                    w.focus()
                except Exception:
                    pass
            return _inner

        def switch_tab(widget_cls, tab_id):
            def _inner():
                try:
                    w = self.query_one(widget_cls)
                    w.focus()
                    tabs = w.query_one(TabbedContent)
                    tabs.active = tab_id
                except Exception:
                    pass
            return _inner

        def start_pomodoro():
            def _inner():
                try:
                    pomo_tabs = self.query_one(PomoNotesTabs)
                    pomo_tabs.focus()
                    tabs = pomo_tabs.query_one(TabbedContent)
                    tabs.active = "tab-pomodoro"
                    pomo = self.query_one("Pomodoro")
                    pomo.action_toggle_timer()
                except Exception:
                    pass
            return _inner

        def refresh_prs():
            def _inner():
                try:
                    pr = self.query_one(PullRequests)
                    pr.fetch_prs()
                except Exception:
                    pass
            return _inner

        def toggle_playback():
            def _inner():
                try:
                    np = self.query_one(NowPlaying)
                    np.toggle_media()
                except Exception:
                    pass
            return _inner

        def next_video():
            def _inner():
                try:
                    np = self.query_one(NowPlaying)
                    np.next_media()
                except Exception:
                    pass
            return _inner

        def focus_habits():
            def _inner():
                try:
                    quests = self.query_one(DailyQuests)
                    quests.focus()
                    tabs = quests.query_one(TabbedContent)
                    tabs.active = "tab-habits"
                except Exception:
                    pass
            return _inner

        def focus_notes():
            def _inner():
                try:
                    pomo_tabs = self.query_one(PomoNotesTabs)
                    pomo_tabs.focus()
                    tabs = pomo_tabs.query_one(TabbedContent)
                    tabs.active = "tab-notes"
                except Exception:
                    pass
            return _inner

        def quit_app():
            def _inner():
                self.action_quit()
            return _inner

        return [
            {"name": "Start Pomodoro", "keywords": ["pomo", "timer", "focus", "start"], "icon": "⏱", "source": "Pomodoro", "action": start_pomodoro()},
            {"name": "Pause Pomodoro", "keywords": ["pomo", "pause", "stop"], "icon": "⏸", "source": "Pomodoro", "action": start_pomodoro()},
            {"name": "Add Quest", "keywords": ["quest", "task", "todo", "add"], "icon": "📜", "source": "Quests", "action": lambda: self.action_quick_add_quest()},
            {"name": "Switch to SRS Stats", "keywords": ["srs", "stats", "flashcard", "study"], "icon": "📊", "source": "SRS", "action": switch_tab(SRSTabs, "tab-srs-stats")},
            {"name": "Switch to Katakana", "keywords": ["katakana", "study", "flashcard"], "icon": "カタ", "source": "SRS", "action": switch_tab(SRSTabs, "tab-katakana")},
            {"name": "Switch to Hiragana", "keywords": ["hiragana", "study", "flashcard"], "icon": "ひら", "source": "SRS", "action": switch_tab(SRSTabs, "tab-hiragana")},
            {"name": "Switch to English", "keywords": ["english", "vocab", "study"], "icon": "📖", "source": "SRS", "action": switch_tab(SRSTabs, "tab-english")},
            {"name": "Switch to Kanji", "keywords": ["kanji", "study", "flashcard"], "icon": "漢", "source": "SRS", "action": switch_tab(SRSTabs, "tab-kanji")},
            {"name": "Refresh PRs", "keywords": ["pr", "github", "refresh"], "icon": "🔄", "source": "PRs", "action": refresh_prs()},
            {"name": "Toggle Playback", "keywords": ["music", "play", "pause", "youtube"], "icon": "⏯", "source": "Now Playing", "action": toggle_playback()},
            {"name": "Next Video", "keywords": ["next", "youtube", "skip"], "icon": "⏭", "source": "Now Playing", "action": next_video()},
            {"name": "Jump to Calendar", "keywords": ["calendar", "meeting", "event"], "icon": "⏳", "source": "Calendar", "action": focus_widget(Calendar)},
            {"name": "View Habit Tracker", "keywords": ["habit", "tracker", "streak"], "icon": "📊", "source": "Habits", "action": focus_habits()},
            {"name": "Add Quick Note", "keywords": ["note", "memo", "quick"], "icon": "📝", "source": "Notes", "action": focus_notes()},
            {"name": "Quit", "keywords": ["quit", "exit", "close"], "icon": "🚪", "source": "App", "action": quit_app()},
        ]

    def on_mount(self) -> None:
        db_path = get("database", "path", default="isekai.db")
        log_config()
        browser = get_browser()
        logger.info("Browser configured: %s", browser)
        if not os.path.exists(db_path):
            self.notify("Database not found. Run: python db_init.py", severity="warning")

        # Run pending Supabase migrations on startup
        if _use_supabase:
            from core.migrations import run_migrations
            applied = run_migrations()
            if applied:
                self.notify(f"Migrated: v{', v'.join(str(v) for v in applied)}", severity="information")


if __name__ == "__main__":
    IsekaiDashboard().run()
