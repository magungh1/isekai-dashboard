from textual.app import ComposeResult
from textual.widgets import Static, TabbedContent, TabPane

from ui.widgets.kana_card import KanaOfTheDay
from ui.widgets.english_card import EnglishVocab


class SRSTabs(Static):
    """Tabbed container for Kana and English SRS flashcards."""

    def compose(self) -> ComposeResult:
        with TabbedContent("🌸 Kana", "📖 English", id="srs-tabs"):
            with TabPane("🌸 Kana", id="tab-kana"):
                yield KanaOfTheDay()
            with TabPane("📖 English", id="tab-english"):
                yield EnglishVocab()
