from textual import work
from textual.app import ComposeResult
from textual.widgets import Static, Label
from textual.binding import Binding

from services.english_srs_service import get_due_cards, review_card, save_mnemonic, get_stats
from clients.llm_client import generate_english_mnemonic
from core.models import VocabCard

FRONT = 0
BACK = 1


class EnglishVocab(Static):
    """SRS flashcard widget for advanced English vocabulary."""

    BINDINGS = [
        Binding("space", "flip_card", "Flip Card", show=True),
        Binding("1", "rate_miss", "Miss", show=False),
        Binding("2", "rate_good", "Good", show=False),
    ]

    can_focus = True

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._current_card: VocabCard | None = None
        self._state = FRONT
        self._cards: list[VocabCard] = []

    def compose(self) -> ComposeResult:
        yield Label("", id="eng-stats", classes="kana-sub")
        yield Label("Loading...", id="eng-word", classes="kana-large")
        yield Label("", id="eng-pos", classes="kana-sub")
        yield Label("", id="eng-definition", classes="kana-mean")
        yield Label("", id="eng-example", classes="kana-sub")
        yield Label("", id="eng-mnemonic", classes="kana-sub")
        yield Label("space: Flip", id="eng-actions", classes="kana-sub")

    def on_mount(self) -> None:
        self.load_cards()

    @work(thread=True)
    def load_cards(self) -> None:
        cards = get_due_cards(limit=20)
        stats = get_stats()
        self.app.call_from_thread(self._set_cards, cards, stats)

    def _set_cards(self, cards: list[VocabCard], stats: dict) -> None:
        self._cards = cards
        self._state = FRONT

        self.query_one("#eng-stats", Label).update(
            f"Due: {stats['due']} | Mastered: {stats['mastered']}/{stats['total']}"
        )

        if cards:
            self._show_front(cards[0])
        else:
            self.query_one("#eng-word", Label).update("✨ All caught up!")
            self.query_one("#eng-pos", Label).update("No cards due for review.")
            self.query_one("#eng-definition", Label).update("")
            self.query_one("#eng-example", Label).update("")
            self.query_one("#eng-mnemonic", Label).update("")
            self.query_one("#eng-actions", Label).update("")

    def _show_front(self, card: VocabCard) -> None:
        self._current_card = card
        self._state = FRONT
        self.query_one("#eng-word", Label).update(f"  {card.word}  ")
        level_stars = "⭐" * card.level if card.level > 0 else "🆕"
        self.query_one("#eng-pos", Label).update(f"({card.part_of_speech}) | Level: {level_stars}")
        self.query_one("#eng-definition", Label).update("")
        self.query_one("#eng-example", Label).update("")
        self.query_one("#eng-mnemonic", Label).update("")
        self.query_one("#eng-actions", Label).update("space: Flip")

    def _show_back(self) -> None:
        card = self._current_card
        if not card:
            return
        self._state = BACK
        self.query_one("#eng-definition", Label).update(f"Definition: {card.definition}")

        if card.example:
            self.query_one("#eng-example", Label).update(f'Example: "{card.example}"')

        if card.mnemonic:
            self.query_one("#eng-mnemonic", Label).update(f"💡 {card.mnemonic}")
        else:
            self.query_one("#eng-mnemonic", Label).update("🔄 Fetching mnemonic...")
            self._fetch_mnemonic(card.id, card.word, card.definition)

        self.query_one("#eng-actions", Label).update("1=Miss  2=Good")

    @work(thread=True)
    def _fetch_mnemonic(self, card_id: int, word: str, definition: str) -> None:
        mnemonic = generate_english_mnemonic(word, definition)
        if mnemonic:
            save_mnemonic(card_id, mnemonic)
            self.app.call_from_thread(
                lambda: self.query_one("#eng-mnemonic", Label).update(f"💡 {mnemonic}")
            )
        else:
            self.app.call_from_thread(
                lambda: self.query_one("#eng-mnemonic", Label).update("(No API key set)")
            )

    def action_flip_card(self) -> None:
        if not self._current_card:
            return
        if self._state == FRONT:
            self._show_back()

    def action_rate_miss(self) -> None:
        if self._state == BACK and self._current_card:
            self._rate_card(self._current_card.id, 'miss')

    def action_rate_good(self) -> None:
        if self._state == BACK and self._current_card:
            self._rate_card(self._current_card.id, 'good')

    @work(thread=True)
    def _rate_card(self, card_id: int, rating: str) -> None:
        review_card(card_id, rating)
        cards = get_due_cards(limit=20)
        stats = get_stats()
        self.app.call_from_thread(self._set_cards, cards, stats)
