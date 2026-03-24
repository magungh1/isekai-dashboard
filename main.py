import os
import sys

# Ensure project root is on the path for imports
sys.path.insert(0, os.path.dirname(__file__))

from textual.app import App, ComposeResult
from textual.containers import Grid
from textual.widgets import Header, Footer

from ui.widgets.daily_quests import DailyQuests
from ui.widgets.pull_requests import PullRequests
from ui.widgets.calendar import Calendar
from ui.widgets.srs_tabs import SRSTabs

from core.db import DB_PATH


class DevDashboardApp(App):
    CSS_PATH = "ui/styles.tcss"
    TITLE = "⚔️ ISEKAI DEV DASHBOARD"
    SUB_TITLE = "異世界開発者ダッシュボード"

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Grid(id="dashboard-grid"):
            yield DailyQuests(classes="tool-widget")
            yield PullRequests(classes="tool-widget")
            yield Calendar(classes="tool-widget")
            yield SRSTabs(classes="tool-widget")
        yield Footer()

    def on_mount(self) -> None:
        if not os.path.exists(DB_PATH):
            self.notify("Database not found. Run: python db_init.py", severity="warning")


if __name__ == "__main__":
    DevDashboardApp().run()
