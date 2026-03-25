import random
import subprocess

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static, Label, Button
from textual.binding import Binding
from textual.timer import Timer

from services.xp_service import add_xp, XP_POMODORO_COMPLETE

IDLE = "idle"
WORK = "work"
BREAK = "break"

WORK_MINUTES = 25
BREAK_MINUTES = 5

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
        self._seconds_left = WORK_MINUTES * 60
        self._timer: Timer | None = None
        self._current_quote = random.choice(FGO_QUOTES)
        self._sessions_today = 0

    def compose(self) -> ComposeResult:
        yield Label("⏱ [ 修行 ] POMODORO", classes="widget-title")
        yield Label("", id="pomo-sessions")
        yield Label(self._format_time(), id="pomo-timer", classes="kana-large")
        yield Label("READY", id="pomo-phase", classes="kana-sub")
        yield Label("", id="pomo-quote", classes="kana-mean")
        yield Label("", id="pomo-author", classes="kana-sub")
        with Horizontal(id="pomo-actions"):
            yield Button("Start", id="pomo-start-btn", variant="success")
            yield Button("Reset", id="pomo-reset-btn", variant="error")

    def on_mount(self) -> None:
        self._show_quote()
        self._update_session_display()
        self.set_interval(300, self._change_quote)

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

    def _update_display(self) -> None:
        self.query_one("#pomo-timer", Label).update(self._format_time())

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
            # Refresh XP bar
            try:
                xp_bar = self.app.query_one("XPBar")
                xp_bar.refresh_xp()
            except Exception:
                pass

            self._phase = BREAK
            self._seconds_left = BREAK_MINUTES * 60
            self._change_quote()
            self.app.notify(f"Session #{self._sessions_today} complete! +{XP_POMODORO_COMPLETE} XP. Break time!", title="Pomodoro")
            _send_macos_notification("Pomodoro Complete!", f"Session #{self._sessions_today} done. Take a break!")
        elif self._phase == BREAK:
            self._phase = WORK
            self._seconds_left = WORK_MINUTES * 60
            self._change_quote()
            self.app.notify("Focus time! ⚔️", title="Pomodoro")
            _send_macos_notification("Break Over!", "Time to focus again!")

        self._update_display()
        self._timer = self.set_interval(1, self._tick)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "pomo-start-btn":
            self.action_toggle_timer()
        elif event.button.id == "pomo-reset-btn":
            self.action_reset_timer()

    def action_toggle_timer(self) -> None:
        btn = self.query_one("#pomo-start-btn", Button)
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
            btn.label = "Resume"
        else:
            if self._phase == IDLE:
                self._phase = WORK
            self._timer = self.set_interval(1, self._tick)
            self._update_display()
            btn.label = "Pause"

    def action_reset_timer(self) -> None:
        if self._timer:
            self._timer.stop()
            self._timer = None
        self._phase = IDLE
        self._seconds_left = WORK_MINUTES * 60
        self._change_quote()
        self._update_display()
        self.query_one("#pomo-start-btn", Button).label = "Start"
