from textual import work
from textual.app import ComposeResult
from textual.widgets import Static, Label
from textual.binding import Binding

from services.srs_service import get_due_cards, review_card, save_mnemonic, get_stats
from services.xp_service import add_xp, XP_SRS_REVIEW
from clients.llm_client import generate_mnemonic
from core.models import KanaCard as KanaCardModel
from core.kana_romaji import to_romaji, to_hiragana, to_katakana
from ui.widgets.srs_utils import level_badge, progress_bar_text

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

    def __init__(self, kana_type: str | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._kana_type = kana_type
        self._prefix = kana_type or "kana"
        self._current_card: KanaCardModel | None = None
        self._state = FRONT
        self._cards: list[KanaCardModel] = []

    def _q(self, suffix: str) -> Label:
        return self.query_one(f"#{self._prefix}-{suffix}", Label)

    def compose(self) -> ComposeResult:
        p = self._prefix
        if self._kana_type == "katakana":
            title = "カタカナ KATAKANA"
        elif self._kana_type == "hiragana":
            title = "ひらがな HIRAGANA"
        else:
            title = "🌸 KANA OF THE DAY"
        yield Label(title, classes="widget-title")
        yield Label("", id=f"{p}-stats", classes="kana-sub")
        yield Label("Loading...", id=f"{p}-word", classes="kana-large")
        yield Label("", id=f"{p}-alt", classes="kana-mean")
        yield Label("", id=f"{p}-romaji", classes="kana-sub")
        yield Label("", id=f"{p}-meaning", classes="kana-mean")
        yield Label("", id=f"{p}-mnemonic", classes="kana-sub")
        yield Label("space: Flip", id=f"{p}-actions", classes="kana-sub")

    def on_mount(self) -> None:
        self.load_cards()

    @work(thread=True)
    def load_cards(self) -> None:
        cards = get_due_cards(limit=20, kana_type=self._kana_type)
        stats = get_stats(kana_type=self._kana_type)
        self.app.call_from_thread(self._set_cards, cards, stats)

    def _set_cards(self, cards: list[KanaCardModel], stats: dict) -> None:
        self._cards = cards
        self._state = FRONT

        bar = progress_bar_text(stats['mastered'], stats['total'])
        self._q("stats").update(f"Due: {stats['due']}  {bar}")

        if cards:
            self._show_front(cards[0])
        else:
            self._q("word").update("✨ All caught up!")
            self._q("alt").update("")
            self._q("romaji").update("No cards due for review.")
            self._q("meaning").update("")
            self._q("mnemonic").update("")
            self._q("actions").update("")

    def _show_front(self, card: KanaCardModel) -> None:
        self._current_card = card
        self._state = FRONT
        self._q("word").update(f"  {card.word}  ")
        self._q("alt").update("")
        badge = level_badge(card.level)
        tag = "カタカナ" if card.type == "katakana" else "ひらがな"
        self._q("romaji").update(f"{tag}  |  {badge}")
        self._q("meaning").update("")
        self._q("mnemonic").update("")
        self._q("actions").update("space: Show Romaji")

    def _show_romaji(self) -> None:
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
        self._q("alt").update(alt_label)
        self._q("romaji").update(f"({romaji})")
        self._q("actions").update("space: Show Meaning")

    def _show_back(self) -> None:
        card = self._current_card
        if not card:
            return
        self._state = BACK
        self._q("meaning").update(f"Meaning: {card.meaning}")

        if card.mnemonic:
            self._q("mnemonic").update(f"💡 {card.mnemonic}")
        else:
            self._q("mnemonic").update("🔄 Fetching mnemonic...")
            self._fetch_mnemonic(card.id, card.word, card.meaning)

        self._q("actions").update("1=Miss  2=Good")

    @work(thread=True)
    def _fetch_mnemonic(self, card_id: int, word: str, meaning: str) -> None:
        mnemonic = generate_mnemonic(word, meaning)
        if mnemonic:
            save_mnemonic(card_id, mnemonic)
            self.app.call_from_thread(
                lambda: self._q("mnemonic").update(f"💡 {mnemonic}")
            )
        else:
            self.app.call_from_thread(
                lambda: self._q("mnemonic").update("(No API key set)")
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
        add_xp(XP_SRS_REVIEW, "srs_kana")
        cards = get_due_cards(limit=20, kana_type=self._kana_type)
        stats = get_stats(kana_type=self._kana_type)
        self.app.call_from_thread(self._set_cards, cards, stats)
        self.app.call_from_thread(self._refresh_xp)

    def _refresh_xp(self) -> None:
        try:
            self.app.query_one("XPBar").refresh_xp()
        except Exception:
            pass
