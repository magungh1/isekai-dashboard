from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Static, Label, Button, ProgressBar

from clients.media_client import (
    get_all_youtube_tabs, get_playback_progress, toggle_playback,
)


def _format_duration(seconds: float) -> str:
    mins = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{mins}:{secs:02d}"


class NowPlaying(Static):
    """Displays current media from browser and allows play/pause."""

    can_focus = True

    BINDINGS = [
        Binding("n", "next_tab", "Next tab", show=False),
        Binding("p", "prev_tab", "Prev tab", show=False),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._current_track: str | None = None
        self._tabs: list[dict] = []
        self._active_idx: int = 0
        self._user_selected: bool = False

    def compose(self) -> ComposeResult:
        yield Label("🎵 [ 再生中 ] NOW PLAYING", classes="widget-title")
        yield Label("Looking for media...", id="np-track", classes="np-track-text")
        yield Label("No browser detected", id="np-browser", classes="kana-sub")
        yield ProgressBar(id="np-progress", total=100, show_eta=False, show_percentage=False)
        yield Label("", id="np-time", classes="kana-sub")
        yield Button("⏯ Play / Pause", id="np-toggle")

    def on_mount(self) -> None:
        from clients.media_client import get_media_browser
        browser = get_media_browser()
        self.query_one("#np-browser", Label).update(f"Source: {browser}")

        self.set_interval(3.0, self.update_track_info)
        self.update_track_info()

    @work(thread=True)
    def update_track_info(self) -> None:
        tabs = get_all_youtube_tabs()

        active_tab = None
        active_idx = 0

        if tabs:
            # Auto-prioritize: if user hasn't manually selected, pick the playing tab
            if not self._user_selected:
                for i, t in enumerate(tabs):
                    if t.get('playing'):
                        active_idx = i
                        break
            else:
                # Keep user's selection if still valid
                active_idx = min(self._active_idx, len(tabs) - 1)

            active_tab = tabs[active_idx]

        progress = None
        if active_tab:
            progress = get_playback_progress(active_tab['w'], active_tab['t'])

        self.app.call_from_thread(self._set_state, tabs, active_idx, progress)

    def _set_state(
        self,
        tabs: list[dict],
        active_idx: int,
        progress: tuple[float, float] | None = None,
    ) -> None:
        old_tab_count = len(self._tabs)
        self._tabs = tabs
        self._active_idx = active_idx

        # Reset user selection if tab list changed (tab opened/closed)
        if len(tabs) != old_tab_count:
            self._user_selected = False

        label = self.query_one("#np-track", Label)
        if tabs:
            track = tabs[active_idx]['title']
            if len(tabs) > 1:
                track = f"[{active_idx + 1}/{len(tabs)}] {track}"
            if track != self._current_track:
                self._current_track = track
                label.update(track)
        else:
            if self._current_track is not None:
                self._current_track = None
                label.update("No media playing")

        progress_bar = self.query_one("#np-progress", ProgressBar)
        time_label = self.query_one("#np-time", Label)
        if progress:
            current, duration = progress
            progress_bar.total = max(int(duration), 1)
            progress_bar.progress = int(current)
            time_label.update(f"  {_format_duration(current)} / {_format_duration(duration)}")
        else:
            progress_bar.total = 100
            progress_bar.progress = 0
            time_label.update("")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "np-toggle":
            if self._tabs:
                self.toggle_media()
            else:
                self.app.notify("No active media tab found.", severity="warning")

    @work(thread=True)
    def toggle_media(self) -> None:
        if self._tabs and self._active_idx < len(self._tabs):
            tab = self._tabs[self._active_idx]
            success = toggle_playback(tab['w'], tab['t'])
        else:
            success = toggle_playback()
        if not success:
            from clients.media_client import get_media_browser
            browser = get_media_browser()
            self.app.call_from_thread(
                self.app.notify,
                f"Failed to toggle playback. Ensure 'Allow JavaScript from Apple Events' "
                f"is enabled in {browser}.",
                severity="error",
            )

    def action_next_tab(self) -> None:
        if len(self._tabs) > 1:
            self._user_selected = True
            self._active_idx = (self._active_idx + 1) % len(self._tabs)
            self.update_track_info()

    def action_prev_tab(self) -> None:
        if len(self._tabs) > 1:
            self._user_selected = True
            self._active_idx = (self._active_idx - 1) % len(self._tabs)
            self.update_track_info()
