import random
from datetime import datetime, timedelta

from core.db import get_shared_connection, release_connection
from core.models import KanaCard
from config import get

SRS_INTERVALS = {i: v for i, v in enumerate(get("srs", "intervals", [0, 4, 24, 72, 168, 720]))}


def get_due_cards(limit: int = 10, kana_type: str | None = None) -> list[KanaCard]:
    conn = get_shared_connection()
    try:
        now = datetime.now().isoformat()
        if kana_type:
            rows = conn.execute(
                "SELECT * FROM kana_srs WHERE next_review <= %s AND type = %s ORDER BY level ASC, RANDOM() LIMIT %s",
                (now, kana_type, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM kana_srs WHERE next_review <= %s ORDER BY level ASC, RANDOM() LIMIT %s",
                (now, limit),
            ).fetchall()
        cards = [KanaCard(**dict(row)) for row in rows]
        random.shuffle(cards)
        return cards
    finally:
        release_connection(conn)


def get_card_by_id(card_id: int) -> KanaCard | None:
    conn = get_shared_connection()
    try:
        row = conn.execute("SELECT * FROM kana_srs WHERE id = %s", (card_id,)).fetchone()
        return KanaCard(**dict(row)) if row else None
    finally:
        release_connection(conn)


def review_card(card_id: int, rating: str) -> KanaCard:
    conn = get_shared_connection()
    try:
        card = get_card_by_id(card_id)
        max_level = max(SRS_INTERVALS.keys())

        if rating in ("miss", "again"):
            new_level = 0
        elif rating == "hard":
            new_level = card.level
        elif rating == "easy":
            new_level = min(card.level + 2, max_level)
        else:
            new_level = min(card.level + 1, max_level)

        interval_hours = SRS_INTERVALS.get(new_level, 720)
        next_review = (datetime.now() + timedelta(hours=interval_hours)).isoformat()

        conn.execute(
            "UPDATE kana_srs SET level = %s, next_review = %s WHERE id = %s",
            (new_level, next_review, card_id),
        )
        conn.commit()
        return get_card_by_id(card_id)
    finally:
        release_connection(conn)


def save_mnemonic(card_id: int, mnemonic: str) -> None:
    conn = get_shared_connection()
    try:
        conn.execute("UPDATE kana_srs SET mnemonic = %s WHERE id = %s", (mnemonic, card_id))
        conn.commit()
    finally:
        release_connection(conn)


def get_stats(kana_type: str | None = None) -> dict:
    conn = get_shared_connection()
    try:
        now = datetime.now().isoformat()
        if kana_type:
            total = conn.execute("SELECT COUNT(*) FROM kana_srs WHERE type = %s", (kana_type,)).fetchone()[0]
            due = conn.execute("SELECT COUNT(*) FROM kana_srs WHERE next_review <= %s AND type = %s", (now, kana_type)).fetchone()[0]
            mastered = conn.execute("SELECT COUNT(*) FROM kana_srs WHERE level >= %s AND type = %s", (4, kana_type)).fetchone()[0]
        else:
            total = conn.execute("SELECT COUNT(*) FROM kana_srs").fetchone()[0]
            due = conn.execute("SELECT COUNT(*) FROM kana_srs WHERE next_review <= %s", (now,)).fetchone()[0]
            mastered = conn.execute("SELECT COUNT(*) FROM kana_srs WHERE level >= %s", (4,)).fetchone()[0]
        return {"total": total, "due": due, "mastered": mastered}
    finally:
        release_connection(conn)


def get_detailed_stats(kana_type: str | None = None) -> dict:
    conn = get_shared_connection()
    try:
        now = datetime.now().isoformat()
        tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0).isoformat()

        type_filter = "AND type = %s" if kana_type else ""
        params_base = (kana_type,) if kana_type else ()

        total = conn.execute(f"SELECT COUNT(*) FROM kana_srs WHERE 1=1 {type_filter}", params_base).fetchone()[0]
        due = conn.execute(f"SELECT COUNT(*) FROM kana_srs WHERE next_review <= %s {type_filter}", (now, *params_base)).fetchone()[0]
        due_tomorrow = conn.execute(f"SELECT COUNT(*) FROM kana_srs WHERE next_review <= %s {type_filter}", (tomorrow, *params_base)).fetchone()[0]

        level_dist = {}
        for row in conn.execute(f"SELECT level, COUNT(*) FROM kana_srs WHERE 1=1 {type_filter} GROUP BY level ORDER BY level", params_base).fetchall():
            level_dist[row["level"]] = row["count"]

        return {
            "total": total,
            "due_now": due,
            "due_tomorrow": due_tomorrow,
            "level_distribution": level_dist,
        }
    finally:
        release_connection(conn)