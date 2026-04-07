import random
from datetime import datetime, timedelta

from core.db import get_shared_connection, db_lock
from core.models import KanaCard
from config import get

# SRS intervals in hours per level
SRS_INTERVALS = {
    i: v for i, v in enumerate(get("srs", "intervals", [0, 4, 24, 72, 168, 720]))
}


def get_due_cards(limit: int = 10, kana_type: str | None = None) -> list[KanaCard]:
    with db_lock:
        conn = get_shared_connection()
        now = datetime.now().isoformat()
        if kana_type:
            rows = conn.execute(
                'SELECT * FROM kana_srs WHERE next_review <= ? AND type = ? ORDER BY level ASC, RANDOM() LIMIT ?',
                (now, kana_type, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                'SELECT * FROM kana_srs WHERE next_review <= ? ORDER BY level ASC, RANDOM() LIMIT ?',
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
            mastered = conn.execute('SELECT COUNT(*) FROM kana_srs WHERE level >= ? AND type = ?', (get("srs", "mastery_level", 4), kana_type)).fetchone()[0]
        else:
            total = conn.execute('SELECT COUNT(*) FROM kana_srs').fetchone()[0]
            due = conn.execute('SELECT COUNT(*) FROM kana_srs WHERE next_review <= ?', (now,)).fetchone()[0]
            mastered = conn.execute('SELECT COUNT(*) FROM kana_srs WHERE level >= ?', (get("srs", "mastery_level", 4),)).fetchone()[0]
        return {'total': total, 'due': due, 'mastered': mastered}


def get_detailed_stats(kana_type: str | None = None) -> dict:
    """Extended stats for the statistics panel."""
    with db_lock:
        conn = get_shared_connection()
        now = datetime.now().isoformat()
        tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0).isoformat()

        type_filter = "AND type = ?" if kana_type else ""
        params_base = (kana_type,) if kana_type else ()

        total = conn.execute(f'SELECT COUNT(*) FROM kana_srs WHERE 1=1 {type_filter}', params_base).fetchone()[0]
        due = conn.execute(f'SELECT COUNT(*) FROM kana_srs WHERE next_review <= ? {type_filter}', (now, *params_base)).fetchone()[0]
        due_tomorrow = conn.execute(f'SELECT COUNT(*) FROM kana_srs WHERE next_review <= ? {type_filter}', (tomorrow, *params_base)).fetchone()[0]

        level_dist = {}
        for row in conn.execute(f'SELECT level, COUNT(*) FROM kana_srs WHERE 1=1 {type_filter} GROUP BY level ORDER BY level', params_base).fetchall():
            level_dist[row[0]] = row[1]

        return {
            'total': total,
            'due_now': due,
            'due_tomorrow': due_tomorrow,
            'level_distribution': level_dist,
        }
