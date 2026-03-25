from textual import work
from textual.app import ComposeResult
from textual.widgets import Static, Label

from services.srs_service import get_detailed_stats as kana_detailed_stats
from services.english_srs_service import get_detailed_stats as english_detailed_stats
from services.kanji_srs_service import get_detailed_stats as kanji_detailed_stats
from ui.widgets.srs_utils import level_badge, progress_bar_text


class SRSStats(Static):
    """SRS statistics overview panel."""

    def compose(self) -> ComposeResult:
        yield Label("📊 [ 統計 ] SRS STATISTICS", classes="widget-title")
        yield Label("Loading...", id="srs-stats-content")

    def on_mount(self) -> None:
        self.load_stats()

    @work(thread=True)
    def load_stats(self) -> None:
        kata = kana_detailed_stats(kana_type="katakana")
        hira = kana_detailed_stats(kana_type="hiragana")
        eng = english_detailed_stats()
        kanji = kanji_detailed_stats()
        self.app.call_from_thread(self._render_stats, kata, hira, eng, kanji)

    def _render_stats(self, kata: dict, hira: dict, eng: dict, kanji: dict) -> None:
        lines = []

        for name, stats in [("Katakana", kata), ("Hiragana", hira), ("English", eng), ("Kanji", kanji)]:
            dist = stats['level_distribution']
            total = stats['total']
            mastered = sum(v for k, v in dist.items() if k >= 4)
            bar = progress_bar_text(mastered, total, width=12)

            lines.append(f"  {name}")
            lines.append(f"    {bar}")
            lines.append(f"    Due now: {stats['due_now']}  |  Due tomorrow: {stats['due_tomorrow']}")

            level_parts = []
            for lvl in range(6):
                count = dist.get(lvl, 0)
                if count > 0:
                    badge = level_badge(lvl)
                    level_parts.append(f"{badge}:{count}")
            if level_parts:
                lines.append(f"    {' '.join(level_parts)}")
            lines.append("")

        # Grand totals
        grand_total = kata['total'] + hira['total'] + eng['total'] + kanji['total']
        grand_due = kata['due_now'] + hira['due_now'] + eng['due_now'] + kanji['due_now']
        grand_tomorrow = kata['due_tomorrow'] + hira['due_tomorrow'] + eng['due_tomorrow'] + kanji['due_tomorrow']
        lines.append(f"  TOTAL: {grand_total} cards  |  Due: {grand_due}  |  Tomorrow: {grand_tomorrow}")

        self.query_one("#srs-stats-content", Label).update("\n".join(lines))
