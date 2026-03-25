from textual import work
from textual.app import ComposeResult
from textual.widgets import Static, TabbedContent, TabPane
from textual.binding import Binding

from ui.widgets.kana_card import KanaOfTheDay
from ui.widgets.english_card import EnglishVocab
from ui.widgets.kanji_card import KanjiVocab
from ui.widgets.srs_stats import SRSStats
from services.srs_service import get_stats as kana_stats
from services.english_srs_service import get_stats as english_stats
from services.kanji_srs_service import get_stats as kanji_stats

TAB_IDS = ["tab-katakana", "tab-hiragana", "tab-english", "tab-kanji", "tab-srs-stats"]

TAB_BASE_LABELS = {
    "tab-katakana": "カタ Katakana",
    "tab-hiragana": "ひら Hiragana",
    "tab-english": "📖 English",
    "tab-kanji": "漢 Kanji",
    "tab-srs-stats": "📊 Stats",
}


class SRSTabs(Static):
    """Tabbed container for Katakana, Hiragana, English, Kanji SRS flashcards, and Stats."""

    BINDINGS = [
        Binding("bracketleft", "prev_tab", "Prev Tab", show=False),
        Binding("bracketright", "next_tab", "Next Tab", show=False),
    ]

    can_focus = True

    def compose(self) -> ComposeResult:
        with TabbedContent(id="srs-tabs"):
            with TabPane("カタ Katakana", id="tab-katakana"):
                yield KanaOfTheDay(kana_type="katakana")
            with TabPane("ひら Hiragana", id="tab-hiragana"):
                yield KanaOfTheDay(kana_type="hiragana")
            with TabPane("📖 English", id="tab-english"):
                yield EnglishVocab()
            with TabPane("漢 Kanji", id="tab-kanji"):
                yield KanjiVocab()
            with TabPane("📊 Stats", id="tab-srs-stats"):
                yield SRSStats()

    def on_mount(self) -> None:
        self._refresh_due_badges()
        self.set_interval(30, self._refresh_due_badges)

    @work(thread=True)
    def _refresh_due_badges(self) -> None:
        kata = kana_stats(kana_type="katakana")
        hira = kana_stats(kana_type="hiragana")
        eng = english_stats()
        kan = kanji_stats()
        self.app.call_from_thread(self._update_tab_labels, kata, hira, eng, kan)

    def _update_tab_labels(self, kata: dict, hira: dict, eng: dict, kan: dict) -> None:
        due_counts = {
            "tab-katakana": kata['due'],
            "tab-hiragana": hira['due'],
            "tab-english": eng['due'],
            "tab-kanji": kan['due'],
        }
        tabs = self.query_one("#srs-tabs", TabbedContent)
        for tab_id, base_label in TAB_BASE_LABELS.items():
            due = due_counts.get(tab_id)
            if due is not None and due > 0:
                label = f"{base_label} ({due})"
            else:
                label = base_label
            try:
                tab = tabs.get_tab(tab_id)
                tab.label = label
            except Exception:
                pass

    def _get_current_index(self) -> int:
        tabs = self.query_one("#srs-tabs", TabbedContent)
        active = tabs.active
        if active in TAB_IDS:
            return TAB_IDS.index(active)
        return 0

    def action_prev_tab(self) -> None:
        idx = (self._get_current_index() - 1) % len(TAB_IDS)
        self.query_one("#srs-tabs", TabbedContent).active = TAB_IDS[idx]

    def action_next_tab(self) -> None:
        idx = (self._get_current_index() + 1) % len(TAB_IDS)
        self.query_one("#srs-tabs", TabbedContent).active = TAB_IDS[idx]
