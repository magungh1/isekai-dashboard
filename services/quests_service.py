from datetime import date, timedelta

from core.db import get_shared_connection, release_connection
from core.models import Quest


def _ensure_meta_table(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")
    conn.commit()


def get_quests_by_category(category: str, include_done: bool = False) -> list[Quest]:
    conn = get_shared_connection()
    try:
        if include_done:
            rows = conn.execute(
                "SELECT * FROM quests WHERE category = %s ORDER BY sort_order ASC, created_at DESC",
                (category,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM quests WHERE category = %s AND status != %s ORDER BY sort_order ASC, created_at DESC",
                (category, "done"),
            ).fetchall()
        return [Quest(**dict(row)) for row in rows]
    finally:
        release_connection(conn)


def get_all_quests() -> list[Quest]:
    conn = get_shared_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM quests ORDER BY sort_order ASC, created_at DESC"
        ).fetchall()
        return [Quest(**dict(row)) for row in rows]
    finally:
        release_connection(conn)


def get_completed_quests(limit: int = 50) -> list[Quest]:
    conn = get_shared_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM quests WHERE status = %s ORDER BY created_at DESC LIMIT %s",
            ("done", limit),
        ).fetchall()
        return [Quest(**dict(row)) for row in rows]
    finally:
        release_connection(conn)


def add_quest(title: str, category: str = "daily", deadline: str | None = None) -> Quest:
    conn = get_shared_connection()
    try:
        cur = conn.execute(
            "INSERT INTO quests (title, status, category, deadline) VALUES (%s, %s, %s, %s) RETURNING *",
            (title, "pending", category, deadline),
        )
        conn.commit()
        return Quest(**dict(cur.fetchone()))
    finally:
        release_connection(conn)


def toggle_quest(quest_id: int) -> Quest:
    conn = get_shared_connection()
    try:
        cur = conn.execute(
            "UPDATE quests SET status = CASE WHEN status = %s THEN %s ELSE %s END WHERE id = %s RETURNING *",
            ("pending", "done", "pending", quest_id),
        )
        conn.commit()
        return Quest(**dict(cur.fetchone()))
    finally:
        release_connection(conn)


def update_quest(quest_id: int, title: str, deadline: str | None = None) -> Quest:
    conn = get_shared_connection()
    try:
        cur = conn.execute(
            "UPDATE quests SET title = %s, deadline = %s WHERE id = %s RETURNING *",
            (title, deadline, quest_id),
        )
        conn.commit()
        return Quest(**dict(cur.fetchone()))
    finally:
        release_connection(conn)


def delete_quest(quest_id: int) -> None:
    conn = get_shared_connection()
    try:
        conn.execute("DELETE FROM quests WHERE id = %s", (quest_id,))
        conn.commit()
    finally:
        release_connection(conn)


def reset_daily_quests() -> None:
    conn = get_shared_connection()
    try:
        _ensure_meta_table(conn)
        today = date.today().isoformat()
        row = conn.execute("SELECT value FROM meta WHERE key = 'last_daily_reset'").fetchone()
        if row and row["value"] >= today:
            return
        conn.execute("UPDATE quests SET status = %s WHERE category = %s", ("pending", "daily"))
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value = %s",
            ("last_daily_reset", today, today),
        )
        conn.commit()
    finally:
        release_connection(conn)


def reset_weekly_quests() -> None:
    conn = get_shared_connection()
    try:
        _ensure_meta_table(conn)
        today = date.today()
        monday = (today - timedelta(days=today.weekday())).isoformat()
        row = conn.execute("SELECT value FROM meta WHERE key = 'last_weekly_reset'").fetchone()
        if row and row["value"] >= monday:
            return
        conn.execute("UPDATE quests SET status = %s WHERE category = %s", ("pending", "weekly"))
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value = %s",
            ("last_weekly_reset", monday, monday),
        )
        conn.commit()
    finally:
        release_connection(conn)


def update_quests_order(order_updates: list[tuple[int, int]]) -> None:
    conn = get_shared_connection()
    try:
        for quest_id, sort_order in order_updates:
            conn.execute("UPDATE quests SET sort_order = %s WHERE id = %s", (sort_order, quest_id))
        conn.commit()
    finally:
        release_connection(conn)