import random
from datetime import datetime, timedelta

from core.db import get_shared_connection, db_lock
from core.models import KanjiCard

# SRS intervals in hours per level
SRS_INTERVALS = {
    0: 0,       # new — review immediately
    1: 4,       # 4 hours
    2: 24,      # 1 day
    3: 72,      # 3 days
    4: 168,     # 1 week
    5: 720,     # 1 month
}


def get_due_cards(limit: int = 10) -> list[KanjiCard]:
    with db_lock:
        conn = get_shared_connection()
        now = datetime.now().isoformat()
        rows = conn.execute(
            'SELECT * FROM kanji_srs WHERE next_review <= ? ORDER BY level ASC, next_review ASC LIMIT ?',
            (now, limit)
        ).fetchall()
        cards = [KanjiCard(**dict(row)) for row in rows]
        random.shuffle(cards)
        return cards


def get_card_by_id(card_id: int) -> KanjiCard | None:
    conn = get_shared_connection()
    row = conn.execute('SELECT * FROM kanji_srs WHERE id = ?', (card_id,)).fetchone()
    return KanjiCard(**dict(row)) if row else None


def review_card(card_id: int, rating: str) -> KanjiCard:
    """Rate a card: 'again' resets, 'hard' stays, 'good' +1, 'easy' +2."""
    with db_lock:
        conn = get_shared_connection()
        card = get_card_by_id(card_id)
        max_level = max(SRS_INTERVALS.keys())

        if rating in ('miss', 'again'):
            new_level = 0
        elif rating == 'hard':
            new_level = card.level
        elif rating == 'easy':
            new_level = min(card.level + 2, max_level)
        else:  # good
            new_level = min(card.level + 1, max_level)

        interval_hours = SRS_INTERVALS.get(new_level, 720)
        next_review = (datetime.now() + timedelta(hours=interval_hours)).isoformat()

        conn.execute(
            'UPDATE kanji_srs SET level = ?, next_review = ? WHERE id = ?',
            (new_level, next_review, card_id)
        )
        conn.commit()
        return get_card_by_id(card_id)


def save_mnemonic(card_id: int, mnemonic: str) -> None:
    with db_lock:
        conn = get_shared_connection()
        conn.execute('UPDATE kanji_srs SET mnemonic = ? WHERE id = ?', (mnemonic, card_id))
        conn.commit()


def get_stats() -> dict:
    with db_lock:
        conn = get_shared_connection()
        total = conn.execute('SELECT COUNT(*) FROM kanji_srs').fetchone()[0]
        now = datetime.now().isoformat()
        due = conn.execute('SELECT COUNT(*) FROM kanji_srs WHERE next_review <= ?', (now,)).fetchone()[0]
        mastered = conn.execute('SELECT COUNT(*) FROM kanji_srs WHERE level >= 4').fetchone()[0]
        return {'total': total, 'due': due, 'mastered': mastered}


def get_detailed_stats() -> dict:
    with db_lock:
        conn = get_shared_connection()
        now = datetime.now().isoformat()
        tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0).isoformat()

        total = conn.execute('SELECT COUNT(*) FROM kanji_srs').fetchone()[0]
        due = conn.execute('SELECT COUNT(*) FROM kanji_srs WHERE next_review <= ?', (now,)).fetchone()[0]
        due_tomorrow = conn.execute('SELECT COUNT(*) FROM kanji_srs WHERE next_review <= ?', (tomorrow,)).fetchone()[0]

        level_dist = {}
        for row in conn.execute('SELECT level, COUNT(*) FROM kanji_srs GROUP BY level ORDER BY level').fetchall():
            level_dist[row[0]] = row[1]

        return {
            'total': total,
            'due_now': due,
            'due_tomorrow': due_tomorrow,
            'level_distribution': level_dist,
        }
