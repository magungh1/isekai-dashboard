from textual import work
from textual.app import ComposeResult
from textual.widgets import Static, Label
from textual.binding import Binding

from services.kanji_srs_service import get_due_cards, review_card, save_mnemonic, get_stats
from services.xp_service import add_xp, XP_SRS_REVIEW
from clients.llm_client import generate_kanji_mnemonic
from core.models import KanjiCard as KanjiCardModel
from core.kana_romaji import to_romaji
from ui.widgets.srs_utils import level_badge, progress_bar_text

FRONT = 0
BACK = 1


class KanjiVocab(Static):
    """SRS flashcard widget for kanji: character -> readings + meaning."""

    BINDINGS = [
        Binding("space", "flip_card", "Flip Card", show=True),
        Binding("1", "rate_again", "Again", show=False),
        Binding("2", "rate_hard", "Hard", show=False),
        Binding("3", "rate_good", "Good", show=False),
        Binding("4", "rate_easy", "Easy", show=False),
    ]

    can_focus = True

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._current_card: KanjiCardModel | None = None
        self._state = FRONT
        self._cards: list[KanjiCardModel] = []

    def compose(self) -> ComposeResult:
        yield Label("漢字 KANJI", classes="widget-title")
        yield Label("", id="kanji-stats", classes="kana-sub")
        yield Label("Loading...", id="kanji-char", classes="kana-large")
        yield Label("", id="kanji-level", classes="kana-sub")
        yield Label("", id="kanji-kun", classes="kana-mean")
        yield Label("", id="kanji-on", classes="kana-mean")
        yield Label("", id="kanji-meaning", classes="kana-mean")
        yield Label("", id="kanji-mnemonic", classes="kana-sub")
        yield Label("space: Flip", id="kanji-actions", classes="kana-sub")

    def on_mount(self) -> None:
        self.load_cards()

    @work(thread=True)
    def load_cards(self) -> None:
        cards = get_due_cards(limit=20)
        stats = get_stats()
        self.app.call_from_thread(self._set_cards, cards, stats)

    def _set_cards(self, cards: list[KanjiCardModel], stats: dict) -> None:
        self._cards = cards
        self._state = FRONT

        bar = progress_bar_text(stats['mastered'], stats['total'])
        self.query_one("#kanji-stats", Label).update(f"Due: {stats['due']}  {bar}")

        if cards:
            self._show_front(cards[0])
        else:
            self.query_one("#kanji-char", Label).update("✨ All caught up!")
            self.query_one("#kanji-level", Label).update("No cards due for review.")
            self.query_one("#kanji-kun", Label).update("")
            self.query_one("#kanji-on", Label).update("")
            self.query_one("#kanji-meaning", Label).update("")
            self.query_one("#kanji-mnemonic", Label).update("")
            self.query_one("#kanji-actions", Label).update("")

    def _show_front(self, card: KanjiCardModel) -> None:
        self._current_card = card
        self._state = FRONT
        self.query_one("#kanji-char", Label).update(f"  {card.kanji}  ")
        badge = level_badge(card.level)
        self.query_one("#kanji-level", Label).update(f"漢字  |  {badge}")
        self.query_one("#kanji-kun", Label).update("")
        self.query_one("#kanji-on", Label).update("")
        self.query_one("#kanji-meaning", Label).update("")
        self.query_one("#kanji-mnemonic", Label).update("")
        self.query_one("#kanji-actions", Label).update("space: Flip")

    def _show_back(self) -> None:
        card = self._current_card
        if not card:
            return
        self._state = BACK

        if card.kun_reading:
            romaji = to_romaji(card.kun_reading)
            self.query_one("#kanji-kun", Label).update(f"訓: {card.kun_reading} ({romaji})")
        else:
            self.query_one("#kanji-kun", Label).update("")

        if card.on_reading:
            romaji = to_romaji(card.on_reading)
            self.query_one("#kanji-on", Label).update(f"音: {card.on_reading} ({romaji})")
        else:
            self.query_one("#kanji-on", Label).update("")

        self.query_one("#kanji-meaning", Label).update(f"Meaning: {card.meaning}")

        if card.mnemonic:
            self.query_one("#kanji-mnemonic", Label).update(f"💡 {card.mnemonic}")
        else:
            self.query_one("#kanji-mnemonic", Label).update("🔄 Fetching mnemonic...")
            self._fetch_mnemonic(card.id, card.kanji, card.meaning,
                                 card.kun_reading, card.on_reading)

        self.query_one("#kanji-actions", Label).update("1=Again  2=Hard  3=Good  4=Easy")

    @work(thread=True)
    def _fetch_mnemonic(self, card_id: int, kanji: str, meaning: str,
                        kun: str | None, on: str | None) -> None:
        mnemonic = generate_kanji_mnemonic(kanji, meaning, kun, on)
        if mnemonic:
            save_mnemonic(card_id, mnemonic)
            self.app.call_from_thread(
                lambda: self.query_one("#kanji-mnemonic", Label).update(f"💡 {mnemonic}")
            )
        else:
            self.app.call_from_thread(
                lambda: self.query_one("#kanji-mnemonic", Label).update("(No API key set)")
            )

    def action_flip_card(self) -> None:
        if not self._current_card:
            return
        if self._state == FRONT:
            self._show_back()

    def action_rate_again(self) -> None:
        if self._state == BACK and self._current_card:
            self._rate_card(self._current_card.id, 'again')

    def action_rate_hard(self) -> None:
        if self._state == BACK and self._current_card:
            self._rate_card(self._current_card.id, 'hard')

    def action_rate_good(self) -> None:
        if self._state == BACK and self._current_card:
            self._rate_card(self._current_card.id, 'good')

    def action_rate_easy(self) -> None:
        if self._state == BACK and self._current_card:
            self._rate_card(self._current_card.id, 'easy')

    @work(thread=True)
    def _rate_card(self, card_id: int, rating: str) -> None:
        review_card(card_id, rating)
        add_xp(XP_SRS_REVIEW, "srs_kanji")
        cards = get_due_cards(limit=20)
        stats = get_stats()
        self.app.call_from_thread(self._set_cards, cards, stats)
        self.app.call_from_thread(self._refresh_xp)

    def _refresh_xp(self) -> None:
        try:
            self.app.query_one("XPBar").refresh_xp()
        except Exception:
            pass
