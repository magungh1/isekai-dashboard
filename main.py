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

from textual.app import App, ComposeResult
from textual.containers import Grid
from textual.widgets import Header, Footer

from ui.widgets.daily_quests import DailyQuests
from ui.widgets.pomodoro import Pomodoro
from ui.widgets.pull_requests import PullRequests
from ui.widgets.calendar import Calendar
from ui.widgets.srs_tabs import SRSTabs
from ui.widgets.now_playing import NowPlaying

DB_PATH = 'isekai.db'

class IsekaiDashboard(App):
    CSS_PATH = "ui/styles.tcss"
    TITLE = "Isekai Dev Dashboard"
    SUB_TITLE = "異世界開発者ダッシュボード"

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Grid(id="dashboard-grid"):
            yield DailyQuests(classes="tool-widget")
            yield Pomodoro(classes="tool-widget")
            yield PullRequests(classes="tool-widget")
            yield Calendar(classes="tool-widget")
            yield SRSTabs(classes="tool-widget")
            yield NowPlaying(classes="tool-widget")
        yield Footer()

    def on_mount(self) -> None:
        if not os.path.exists(DB_PATH):
            self.notify("Database not found. Run: python db_init.py", severity="warning")


if __name__ == "__main__":
    IsekaiDashboard().run()
