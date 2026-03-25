import random
from datetime import datetime, timedelta

from core.db import get_shared_connection, db_lock
from core.models import KanaCard

# SRS intervals in hours per level
SRS_INTERVALS = {
    0: 0,       # new — review immediately
    1: 4,       # 4 hours
    2: 24,      # 1 day
    3: 72,      # 3 days
    4: 168,     # 1 week
    5: 720,     # 1 month
}


def get_due_cards(limit: int = 10, kana_type: str | None = None) -> list[KanaCard]:
    with db_lock:
        conn = get_shared_connection()
        now = datetime.now().isoformat()
        if kana_type:
            rows = conn.execute(
                'SELECT * FROM kana_srs WHERE next_review <= ? AND type = ? ORDER BY level ASC, next_review ASC LIMIT ?',
                (now, kana_type, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                'SELECT * FROM kana_srs WHERE next_review <= ? ORDER BY level ASC, next_review ASC LIMIT ?',
                (now, limit)
            ).fetchall()
        cards = [KanaCard(**dict(row)) for row in rows]
        random.shuffle(cards)
        return cards


def get_card_by_id(card_id: int) -> KanaCard | None:
    conn = get_shared_connection()
    row = conn.execute('SELECT * FROM kana_srs WHERE id = ?', (card_id,)).fetchone()
    return KanaCard(**dict(row)) if row else None


def review_card(card_id: int, rating: str) -> KanaCard:
    """Rate a card: 'miss' resets level, 'good' advances level."""
    with db_lock:
        conn = get_shared_connection()
        card = get_card_by_id(card_id)

        if rating == 'miss':
            new_level = 0
        else:  # good
            new_level = min(card.level + 1, max(SRS_INTERVALS.keys()))

        interval_hours = SRS_INTERVALS.get(new_level, 720)
        next_review = (datetime.now() + timedelta(hours=interval_hours)).isoformat()

        conn.execute(
            'UPDATE kana_srs SET level = ?, next_review = ? WHERE id = ?',
            (new_level, next_review, card_id)
        )
        conn.commit()
        return get_card_by_id(card_id)


def save_mnemonic(card_id: int, mnemonic: str) -> None:
    with db_lock:
        conn = get_shared_connection()
        conn.execute('UPDATE kana_srs SET mnemonic = ? WHERE id = ?', (mnemonic, card_id))
        conn.commit()


def get_stats(kana_type: str | None = None) -> dict:
    with db_lock:
        conn = get_shared_connection()
        now = datetime.now().isoformat()
        if kana_type:
            total = conn.execute('SELECT COUNT(*) FROM kana_srs WHERE type = ?', (kana_type,)).fetchone()[0]
            due = conn.execute('SELECT COUNT(*) FROM kana_srs WHERE next_review <= ? AND type = ?', (now, kana_type)).fetchone()[0]
            mastered = conn.execute('SELECT COUNT(*) FROM kana_srs WHERE level >= 4 AND type = ?', (kana_type,)).fetchone()[0]
        else:
            total = conn.execute('SELECT COUNT(*) FROM kana_srs').fetchone()[0]
            due = conn.execute('SELECT COUNT(*) FROM kana_srs WHERE next_review <= ?', (now,)).fetchone()[0]
            mastered = conn.execute('SELECT COUNT(*) FROM kana_srs WHERE level >= 4').fetchone()[0]
        return {'total': total, 'due': due, 'mastered': mastered}
