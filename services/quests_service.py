from datetime import date, timedelta

from core.db import get_shared_connection, db_lock
from core.models import Quest


def _ensure_meta_table() -> None:
    conn = get_shared_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)')
    conn.commit()


def get_quests_by_category(category: str, include_done: bool = False) -> list[Quest]:
    with db_lock:
        conn = get_shared_connection()
        if include_done:
            rows = conn.execute(
                'SELECT * FROM quests WHERE category = ? ORDER BY sort_order ASC, created_at DESC',
                (category,)
            ).fetchall()
        else:
            rows = conn.execute(
                'SELECT * FROM quests WHERE category = ? AND status != "done" ORDER BY sort_order ASC, created_at DESC',
                (category,)
            ).fetchall()
        return [Quest(**dict(row)) for row in rows]


def get_all_quests() -> list[Quest]:
    with db_lock:
        conn = get_shared_connection()
        rows = conn.execute('SELECT * FROM quests ORDER BY sort_order ASC, created_at DESC').fetchall()
        return [Quest(**dict(row)) for row in rows]


def add_quest(title: str, category: str = 'daily', deadline: str | None = None) -> Quest:
    with db_lock:
        conn = get_shared_connection()
        cursor = conn.execute(
            'INSERT INTO quests (title, status, category, deadline) VALUES (?, ?, ?, ?)',
            (title, 'pending', category, deadline)
        )
        conn.commit()
        row = conn.execute('SELECT * FROM quests WHERE id = ?', (cursor.lastrowid,)).fetchone()
        return Quest(**dict(row))


def toggle_quest(quest_id: int) -> Quest:
    with db_lock:
        conn = get_shared_connection()
        row = conn.execute('SELECT * FROM quests WHERE id = ?', (quest_id,)).fetchone()
        new_status = 'done' if row['status'] == 'pending' else 'pending'
        conn.execute('UPDATE quests SET status = ? WHERE id = ?', (new_status, quest_id))
        conn.commit()
        row = conn.execute('SELECT * FROM quests WHERE id = ?', (quest_id,)).fetchone()
        return Quest(**dict(row))


def update_quest(quest_id: int, title: str, deadline: str | None = None) -> Quest:
    with db_lock:
        conn = get_shared_connection()
        conn.execute(
            'UPDATE quests SET title = ?, deadline = ? WHERE id = ?',
            (title, deadline, quest_id)
        )
        conn.commit()
        row = conn.execute('SELECT * FROM quests WHERE id = ?', (quest_id,)).fetchone()
        return Quest(**dict(row))


def delete_quest(quest_id: int) -> None:
    with db_lock:
        conn = get_shared_connection()
        conn.execute('DELETE FROM quests WHERE id = ?', (quest_id,))
        conn.commit()


def reset_daily_quests() -> None:
    """Reset all daily quests to pending if last reset was before today."""
    with db_lock:
        _ensure_meta_table()
        conn = get_shared_connection()
        today = date.today().isoformat()
        row = conn.execute("SELECT value FROM meta WHERE key = 'last_daily_reset'").fetchone()
        if row and row['value'] >= today:
            return
        conn.execute("UPDATE quests SET status = 'pending' WHERE category = 'daily'")
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES ('last_daily_reset', ?)",
            (today,)
        )
        conn.commit()


def reset_weekly_quests() -> None:
    """Reset all weekly quests to pending if last reset was before this Monday."""
    with db_lock:
        _ensure_meta_table()
        conn = get_shared_connection()
        today = date.today()
        monday = (today - timedelta(days=today.weekday())).isoformat()
        row = conn.execute("SELECT value FROM meta WHERE key = 'last_weekly_reset'").fetchone()
        if row and row['value'] >= monday:
            return
        conn.execute("UPDATE quests SET status = 'pending' WHERE category = 'weekly'")
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES ('last_weekly_reset', ?)",
            (monday,)
        )
        conn.commit()


def update_quests_order(order_updates: list[tuple[int, int]]) -> None:
    """Update sort_order for multiple quests.
    order_updates is a list of (quest_id, sort_order)
    """
    with db_lock:
        conn = get_shared_connection()
        for quest_id, sort_order in order_updates:
            conn.execute(
                'UPDATE quests SET sort_order = ? WHERE id = ?',
                (sort_order, quest_id)
            )
        conn.commit()
