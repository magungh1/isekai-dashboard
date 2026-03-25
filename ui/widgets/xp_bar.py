from textual import work
from textual.app import ComposeResult
from textual.widgets import Static, Label, ProgressBar
from textual.containers import Horizontal

from services.xp_service import get_level_info


class XPBar(Static):
    """Persistent XP / Level progress bar."""

    def compose(self) -> ComposeResult:
        with Horizontal(id="xp-bar-container"):
            yield Label("", id="xp-level-label")
            yield ProgressBar(id="xp-progress", total=100, show_eta=False, show_percentage=False)
            yield Label("", id="xp-detail-label")

    def on_mount(self) -> None:
        self.refresh_xp()
        self.set_interval(10, self.refresh_xp)

    @work(thread=True)
    def refresh_xp(self) -> None:
        info = get_level_info()
        self.app.call_from_thread(self._update_display, info)

    def _update_display(self, info: dict) -> None:
        level = info['level']
        xp_in = info['xp_in_level']
        xp_needed = info['xp_needed']
        today = info['today_xp']
        total = info['total_xp']

        self.query_one("#xp-level-label", Label).update(
            f" Lv.{level} "
        )

        progress = self.query_one("#xp-progress", ProgressBar)
        progress.total = max(xp_needed, 1)
        progress.progress = xp_in

        self.query_one("#xp-detail-label", Label).update(
            f" {xp_in}/{xp_needed} XP  |  Today: +{today}  |  Total: {total} "
        )
