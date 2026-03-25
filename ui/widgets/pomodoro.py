import random
import subprocess

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Label, Button, ProgressBar
from textual.binding import Binding
from textual.timer import Timer

from services.xp_service import add_xp, XP_POMODORO_COMPLETE, get_today_pomodoro_count

IDLE = "idle"
WORK = "work"
BREAK = "break"

WORK_MINUTES = 25
BREAK_MINUTES = 5

POMO_PRESETS = [
    (25, 5, "25/5"),
    (50, 10, "50/10"),
    (15, 3, "15/3"),
]

FGO_QUOTES = [
    ("King Hassan",
     "The bell of evening tolls thy name. Touch not the sky, for by heaven's will I shall strip thee of thy wings!"),
    ("Dr. Romani Archaman",
     "Nothing is eternal, and pain awaits us all in the end, but that doesn't make life a story of despair. It's a fight against death and separation in what little time we are given."),
    ("Arash",
     "O' Lord of Brightness who bestows all of his power, sanctity, and wisdom to me. Behold my deeds, my death, my spenta armaiti which I must carry out. —STELLA!"),
    ("Gilgamesh (Caster)",
     "Bemoaning the obligations that you chose to uphold dutifully is evil! What should be praised is the triumphs you achieved!"),
    ("Arthur Pendragon",
     "Seal Thirteen... decision start! This is a fight to save the world! Excalibur!!"),
    ("Patxi",
     "Stand up, dammit. Stand up and fight for it... Don't you dare lose to a world like this, a world whose only virtue is strength!"),
    ("Oberon Vortigern",
     "There's still meaning to be found even in the most hackneyed of kingdoms, or the most unsung side characters."),
    ("Jeanne d'Arc",
     "I always strive to be good. I am not stupid, I am not naive. Yes I have been betrayed, but I will not give up being good."),
    ("Dr. Romani Archaman",
     "We don't live in order to create meaning. We live so meaning can be found from our life."),
    ("Miyamoto Musashi",
     "Train humbly and respectfully. One breaches infinity and arrives at zero."),
    ("Hans Christian Andersen",
     "Hell? Why that's the whole work day, you monster! Heaven? Why that's the instant work is over, you fool!"),
    ("Napoleon",
     "The thing about a trump card, it takes everything you got plus a little more."),
    ("Ozymandias",
     "My name is Ozymandias, the King of Kings. Look on my works, ye Mighty, and despair!"),
    ("Hijikata Toshizo",
     "The Shinsengumi's 'Fidelity' will not fall. No matter which battlefield, which hell it is."),
    ("EMIYA",
     "I am the bone of my sword. Steel is my body, and fire is my blood. I have created over a thousand blades. Yet, those hands will never hold anything. So as I pray... Unlimited Blade Works."),
    ("Iskandar",
     "To win, but not destroy; to conquer, but not humiliate: That is what true conquest is!"),
]


def _send_macos_notification(title: str, message: str) -> None:
    try:
        subprocess.Popen([
            'osascript', '-e',
            f'display notification "{message}" with title "{title}" sound name "Glass"'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


class Pomodoro(Static):
    """Pomodoro timer with FGO motivational quotes and session tracking."""

    BINDINGS = [
        Binding("s", "toggle_timer", "Start/Pause", show=True),
        Binding("r", "reset_timer", "Reset", show=True),
    ]

    can_focus = True

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._phase = IDLE
        self._work_minutes = WORK_MINUTES
        self._break_minutes = BREAK_MINUTES
        self._seconds_left = WORK_MINUTES * 60
        self._total_seconds = WORK_MINUTES * 60
        self._timer: Timer | None = None
        self._current_quote = random.choice(FGO_QUOTES)
        self._sessions_today = 0
        self._preset_index = 0

    def compose(self) -> ComposeResult:
        yield Label("⏱ [ 修行 ] POMODORO", classes="widget-title")
        yield Label("", id="pomo-sessions")
        with Horizontal(id="pomo-status-row"):
            yield Label("READY", id="pomo-phase")
            yield Label(self._format_time(), id="pomo-timer", classes="kana-large")
        yield ProgressBar(id="pomo-progress", total=100, show_eta=False, show_percentage=False)
        with Horizontal(id="pomo-presets"):
            for work_m, brk, label in POMO_PRESETS:
                yield Button(label, id=f"pomo-preset-{work_m}-{brk}", classes="pomo-preset-btn")
        with Horizontal(id="pomo-actions"):
            yield Button("Start", id="pomo-start-btn", variant="success")
            yield Button("Reset", id="pomo-reset-btn", variant="error")
        yield Label("", id="pomo-quote", classes="kana-mean")
        yield Label("", id="pomo-author", classes="kana-sub")

    def on_mount(self) -> None:
        self._load_sessions()
        self._show_quote()
        self._update_session_display()
        self._update_active_preset()
        self._update_phase_class()
        self._update_progress()
        self.set_interval(300, self._change_quote)

    @work(thread=True)
    def _load_sessions(self) -> None:
        count = get_today_pomodoro_count()
        self.app.call_from_thread(self._set_sessions, count)

    def _set_sessions(self, count: int) -> None:
        self._sessions_today = count
        self._update_session_display()

    def _update_active_preset(self) -> None:
        for btn in self.query(".pomo-preset-btn"):
            btn.remove_class("active")
        for work_m, brk, _label in POMO_PRESETS:
            if work_m == self._work_minutes and brk == self._break_minutes:
                try:
                    self.query_one(f"#pomo-preset-{work_m}-{brk}", Button).add_class("active")
                except Exception:
                    pass

    def _change_quote(self) -> None:
        self._current_quote = random.choice(FGO_QUOTES)
        self._show_quote()

    def _format_time(self) -> str:
        mins, secs = divmod(self._seconds_left, 60)
        return f"  {mins:02d}:{secs:02d}  "

    def _show_quote(self) -> None:
        author, quote = self._current_quote
        self.query_one("#pomo-quote", Label).update(f'"{quote}"')
        self.query_one("#pomo-author", Label).update(f"— {author}")

    def _update_session_display(self) -> None:
        pips = "●" * self._sessions_today + "○" * max(0, 4 - self._sessions_today)
        self.query_one("#pomo-sessions", Label).update(
            f"Sessions: {pips} ({self._sessions_today} today)"
        )

    def _update_progress(self) -> None:
        progress = self.query_one("#pomo-progress", ProgressBar)
        progress.total = max(self._total_seconds, 1)
        elapsed = self._total_seconds - self._seconds_left
        progress.progress = elapsed

    def _update_phase_class(self) -> None:
        self.remove_class("pomo-phase-idle", "pomo-phase-work", "pomo-phase-break")
        if self._phase == WORK:
            self.add_class("pomo-phase-work")
        elif self._phase == BREAK:
            self.add_class("pomo-phase-break")
        else:
            self.add_class("pomo-phase-idle")

    def _update_display(self) -> None:
        self.query_one("#pomo-timer", Label).update(self._format_time())
        self._update_progress()

        if self._phase == WORK:
            self.query_one("#pomo-phase", Label).update("⚔️ FOCUS TIME")
        elif self._phase == BREAK:
            self.query_one("#pomo-phase", Label).update("🌸 BREAK TIME")
        else:
            self.query_one("#pomo-phase", Label).update("READY")

    def _tick(self) -> None:
        if self._seconds_left > 0:
            self._seconds_left -= 1
            self._update_display()
        else:
            self._phase_complete()

    def _phase_complete(self) -> None:
        if self._timer:
            self._timer.stop()
            self._timer = None

        if self._phase == WORK:
            self._sessions_today += 1
            self._update_session_display()
            add_xp(XP_POMODORO_COMPLETE, "pomodoro")
            try:
                xp_bar = self.app.query_one("XPBar")
                xp_bar.refresh_xp()
            except Exception:
                pass

            self._phase = BREAK
            self._seconds_left = self._break_minutes * 60
            self._total_seconds = self._break_minutes * 60
            self._change_quote()
            self._update_phase_class()
            self.app.notify(f"Session #{self._sessions_today} complete! +{XP_POMODORO_COMPLETE} XP. Break time!", title="Pomodoro")
            _send_macos_notification("Pomodoro Complete!", f"Session #{self._sessions_today} done. Take a break!")
        elif self._phase == BREAK:
            self._phase = WORK
            self._seconds_left = self._work_minutes * 60
            self._total_seconds = self._work_minutes * 60
            self._change_quote()
            self._update_phase_class()
            self.app.notify("Focus time! ⚔️", title="Pomodoro")
            _send_macos_notification("Break Over!", "Time to focus again!")

        self._update_display()
        self._timer = self.set_interval(1, self._tick)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "pomo-start-btn":
            self.action_toggle_timer()
        elif event.button.id == "pomo-reset-btn":
            self.action_reset_timer()
        elif event.button.id and event.button.id.startswith("pomo-preset-"):
            parts = event.button.id.replace("pomo-preset-", "").split("-")
            if len(parts) == 2:
                self._set_duration(int(parts[0]), int(parts[1]))

    def action_toggle_timer(self) -> None:
        btn = self.query_one("#pomo-start-btn", Button)
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
            btn.label = "Resume"
        else:
            if self._phase == IDLE:
                self._phase = WORK
                self._total_seconds = self._work_minutes * 60
                self._update_phase_class()
            self._timer = self.set_interval(1, self._tick)
            self._update_display()
            btn.label = "Pause"

    def _set_duration(self, work: int, brk: int) -> None:
        if self._phase != IDLE:
            return
        self._work_minutes = work
        self._break_minutes = brk
        self._seconds_left = work * 60
        self._total_seconds = work * 60
        self._update_display()
        self._update_active_preset()

    def action_reset_timer(self) -> None:
        if self._timer:
            self._timer.stop()
            self._timer = None
        self._phase = IDLE
        self._seconds_left = self._work_minutes * 60
        self._total_seconds = self._work_minutes * 60
        self._change_quote()
        self._update_display()
        self._update_phase_class()
        self.query_one("#pomo-start-btn", Button).label = "Start"
