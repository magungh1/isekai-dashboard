from textual.app import ComposeResult
from textual.widgets import Static, TabbedContent, TabPane
from textual.binding import Binding

from ui.widgets.pomodoro import Pomodoro
from ui.widgets.notes import Notes

TAB_IDS = ["tab-pomodoro", "tab-notes"]


class ProductivityTabs(Static):
    BINDINGS = [
        Binding("[", "prev_tab", "[ Prev Tab", show=True),
        Binding("]", "next_tab", "] Next Tab", show=True),
    ]

    can_focus = True

    def compose(self) -> ComposeResult:
        with TabbedContent(id="productivity-tabs"):
            with TabPane("⏱ Pomodoro", id="tab-pomodoro"):
                yield Pomodoro()
            with TabPane("📝 Notes", id="tab-notes"):
                yield Notes()

    def _get_current_index(self) -> int:
        tabs = self.query_one("#productivity-tabs", TabbedContent)
        active = tabs.active
        if active in TAB_IDS:
            return TAB_IDS.index(active)
        return 0

    def action_prev_tab(self) -> None:
        idx = (self._get_current_index() - 1) % len(TAB_IDS)
        self.query_one("#productivity-tabs", TabbedContent).active = TAB_IDS[idx]

    def action_next_tab(self) -> None:
        idx = (self._get_current_index() + 1) % len(TAB_IDS)
        self.query_one("#productivity-tabs", TabbedContent).active = TAB_IDS[idx]
