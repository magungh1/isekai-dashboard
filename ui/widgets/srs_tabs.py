from textual.app import ComposeResult
from textual.widgets import Static, TabbedContent, TabPane

from ui.widgets.kana_card import KanaOfTheDay
from ui.widgets.english_card import EnglishVocab
from ui.widgets.kanji_card import KanjiVocab


class SRSTabs(Static):
    """Tabbed container for Katakana, Hiragana, English, and Kanji SRS flashcards."""

    def compose(self) -> ComposeResult:
        with TabbedContent("カタ Katakana", "ひら Hiragana", "📖 English", "漢 Kanji", id="srs-tabs"):
            with TabPane("カタ Katakana", id="tab-katakana"):
                yield KanaOfTheDay(kana_type="katakana")
            with TabPane("ひら Hiragana", id="tab-hiragana"):
                yield KanaOfTheDay(kana_type="hiragana")
            with TabPane("📖 English", id="tab-english"):
                yield EnglishVocab()
            with TabPane("漢 Kanji", id="tab-kanji"):
                yield KanjiVocab()
