from textual import work
from textual.app import ComposeResult
from textual.widgets import Static, Label
from textual.binding import Binding

from services.srs_service import get_due_cards, review_card, save_mnemonic, get_stats
from clients.llm_client import generate_mnemonic
from core.models import KanaCard as KanaCardModel
from core.kana_romaji import to_romaji, to_hiragana, to_katakana

# States: 0 = front (kana only), 1 = romaji, 2 = meaning + rating
FRONT = 0
ROMAJI = 1
BACK = 2


class KanaOfTheDay(Static):
    """SRS flashcard widget with 3-state flip: kana -> romaji -> meaning."""

    BINDINGS = [
        Binding("space", "flip_card", "Flip Card", show=True),
        Binding("1", "rate_miss", "Miss", show=False),
        Binding("2", "rate_good", "Good", show=False),
    ]

    can_focus = True

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._current_card: KanaCardModel | None = None
        self._state = FRONT
        self._cards: list[KanaCardModel] = []

    def compose(self) -> ComposeResult:
        yield Label("🌸 [ 語彙集 ] KANA OF THE DAY", classes="widget-title")
        yield Label("", id="kana-stats", classes="kana-sub")
        yield Label("Loading...", id="kana-word", classes="kana-large")
        yield Label("", id="kana-alt", classes="kana-mean")
        yield Label("", id="kana-romaji", classes="kana-sub")
        yield Label("", id="kana-meaning", classes="kana-mean")
        yield Label("", id="kana-mnemonic", classes="kana-sub")
        yield Label("SPACE=Flip", id="kana-actions", classes="kana-sub")

    def on_mount(self) -> None:
        self.load_cards()

    @work(thread=True)
    def load_cards(self) -> None:
        cards = get_due_cards(limit=20)
        stats = get_stats()
        self.app.call_from_thread(self._set_cards, cards, stats)

    def _set_cards(self, cards: list[KanaCardModel], stats: dict) -> None:
        self._cards = cards
        self._state = FRONT

        stats_label = self.query_one("#kana-stats", Label)
        stats_label.update(f"Due: {stats['due']} | Mastered: {stats['mastered']}/{stats['total']}")

        if cards:
            self._show_front(cards[0])
        else:
            self.query_one("#kana-word", Label).update("✨ All caught up!")
            self.query_one("#kana-alt", Label).update("")
            self.query_one("#kana-romaji", Label).update("No cards due for review.")
            self.query_one("#kana-meaning", Label).update("")
            self.query_one("#kana-mnemonic", Label).update("")
            self.query_one("#kana-actions", Label).update("")

    def _show_front(self, card: KanaCardModel) -> None:
        """State 0: Show only the kana word."""
        self._current_card = card
        self._state = FRONT
        self.query_one("#kana-word", Label).update(f"  {card.word}  ")
        self.query_one("#kana-alt", Label).update("")
        level_stars = "⭐" * card.level if card.level > 0 else "🆕"
        tag = "カタカナ" if card.type == "katakana" else "ひらがな"
        self.query_one("#kana-romaji", Label).update(f"{tag} | Level: {level_stars}")
        self.query_one("#kana-meaning", Label).update("")
        self.query_one("#kana-mnemonic", Label).update("")
        self.query_one("#kana-actions", Label).update("SPACE=Show Romaji")

    def _show_romaji(self) -> None:
        """State 1: Reveal romaji and the alternate script (katakana↔hiragana)."""
        card = self._current_card
        if not card:
            return
        self._state = ROMAJI
        romaji = to_romaji(card.word)
        if card.type == 'katakana':
            alt = to_hiragana(card.word)
            alt_label = f"ひらがな: {alt}"
        else:
            alt = to_katakana(card.word)
            alt_label = f"カタカナ: {alt}"
        self.query_one("#kana-alt", Label).update(alt_label)
        self.query_one("#kana-romaji", Label).update(f"({romaji})")
        self.query_one("#kana-actions", Label).update("SPACE=Show Meaning")

    def _show_back(self) -> None:
        """State 2: Reveal meaning, mnemonic, and rating buttons."""
        card = self._current_card
        if not card:
            return
        self._state = BACK
        self.query_one("#kana-meaning", Label).update(f"Meaning: {card.meaning}")

        if card.mnemonic:
            self.query_one("#kana-mnemonic", Label).update(f"💡 {card.mnemonic}")
        else:
            self.query_one("#kana-mnemonic", Label).update("🔄 Fetching mnemonic...")
            self._fetch_mnemonic(card.id, card.word, card.meaning)

        self.query_one("#kana-actions", Label).update("1=Miss  2=Good")

    @work(thread=True)
    def _fetch_mnemonic(self, card_id: int, word: str, meaning: str) -> None:
        mnemonic = generate_mnemonic(word, meaning)
        if mnemonic:
            save_mnemonic(card_id, mnemonic)
            self.app.call_from_thread(
                lambda: self.query_one("#kana-mnemonic", Label).update(f"💡 {mnemonic}")
            )
        else:
            self.app.call_from_thread(
                lambda: self.query_one("#kana-mnemonic", Label).update("(No API key set)")
            )

    def action_flip_card(self) -> None:
        if not self._current_card:
            return
        if self._state == FRONT:
            self._show_romaji()
        elif self._state == ROMAJI:
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
