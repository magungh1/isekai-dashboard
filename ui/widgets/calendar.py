from textual import work
from textual.app import ComposeResult
from textual.widgets import Static, Label, ListView, ListItem

from clients.calendar_client import fetch_today_events


class Calendar(Static):
    """Fetches live events from macOS Calendar via icalBuddy."""

    def compose(self) -> ComposeResult:
        yield Label("⏳ [ 予定表 ] TEMPORAL LOG", classes="widget-title")
        yield ListView(id="cal-list")

    def on_mount(self) -> None:
        self.fetch_calendar()

    @work(thread=True)
    def fetch_calendar(self) -> None:
        events = fetch_today_events()

        def update_ui():
            cal_list = self.query_one("#cal-list", ListView)
            cal_list.clear()
            if events is None:
                cal_list.append(ListItem(Label("❌ icalBuddy not available", classes="pr-failed")))
            elif not events:
                cal_list.append(ListItem(Label("✨ No meetings today. 自由！", classes="pr-merged")))
            else:
                for event in events:
                    cal_list.append(ListItem(Label(f"🔹 {event}")))

        self.app.call_from_thread(update_ui)
