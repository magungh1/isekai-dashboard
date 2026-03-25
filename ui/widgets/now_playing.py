from textual import work
from textual.app import ComposeResult
from textual.widgets import Static, Label, Button, ProgressBar

from clients.media_client import get_current_track, toggle_playback, get_playback_progress


def _format_duration(seconds: float) -> str:
    mins = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{mins}:{secs:02d}"


class NowPlaying(Static):
    """Displays current media from browser and allows play/pause."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._current_track: str | None = None

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
        track = get_current_track()
        progress = get_playback_progress() if track else None
        self.app.call_from_thread(self._set_track, track, progress)

    def _set_track(self, track: str | None, progress: tuple[float, float] | None = None) -> None:
        if track != self._current_track:
            self._current_track = track
            label = self.query_one("#np-track", Label)
            if track:
                label.update(track)
            else:
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
            if self._current_track:
                self.toggle_media()
            else:
                self.app.notify("No active media tab found.", severity="warning")

    @work(thread=True)
    def toggle_media(self) -> None:
        success = toggle_playback()
        if not success:
            from clients.media_client import get_media_browser
            browser = get_media_browser()
            self.app.call_from_thread(
                self.app.notify,
                f"Failed to toggle playback. Ensure 'Allow JavaScript from Apple Events' is enabled in {browser}.",
                severity="error"
            )
