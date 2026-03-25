import webbrowser

from textual import work
from textual.app import ComposeResult
from textual.widgets import Static, Label, ListView, ListItem

from clients.calendar_client import (
    fetch_today_events, get_event_time_status, get_next_meeting_countdown,
)

STATUS_CSS = {
    "now": "cal-now",
    "soon": "cal-soon",
    "past": "cal-past",
    "future": "cal-future",
}


class CalendarItem(ListItem):
    """A single calendar event that may have a meeting link."""

    def __init__(self, event: dict) -> None:
        super().__init__()
        self.event = event

    def compose(self) -> ComposeResult:
        icon = "🔗" if self.event['url'] else "🔹"
        title = self.event['title']
        if self.event['time']:
            title = f"{title} ({self.event['time']})"
        status = get_event_time_status(self.event.get('time'))
        css_class = STATUS_CSS.get(status, "cal-future")
        yield Label(f"{icon} {title}", classes=css_class)


class Calendar(Static):
    """Fetches live events from macOS Calendar via icalBuddy."""

    def compose(self) -> ComposeResult:
        yield Label("⏳ [ 予定表 ] CALENDAR", classes="widget-title")
        yield Label("", id="cal-next-meeting")
        yield ListView(id="cal-list")

    def on_mount(self) -> None:
        self.fetch_calendar()
        self.set_interval(120, self.fetch_calendar)

    @work(thread=True)
    def fetch_calendar(self) -> None:
        events = fetch_today_events()

        def update_ui():
            cal_list = self.query_one("#cal-list", ListView)
            cal_list.clear()

            countdown_label = self.query_one("#cal-next-meeting", Label)

            if events is None:
                cal_list.append(ListItem(Label("❌ icalBuddy not available", classes="pr-failed")))
                countdown_label.update("")
            elif not events:
                cal_list.append(ListItem(Label("✨ No meetings today. 自由！", classes="pr-merged")))
                countdown_label.update("")
            else:
                countdown = get_next_meeting_countdown(events)
                countdown_label.update(countdown or "")

                for event in events:
                    cal_list.append(CalendarItem(event))

        self.app.call_from_thread(update_ui)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, CalendarItem) and event.item.event.get('url'):
            webbrowser.open(event.item.event['url'])
