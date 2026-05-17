from core.db import get_shared_connection, release_connection
from core.models import Quest
from config import get_int


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


def get_completed_quests(limit: int | None = None) -> list[Quest]:
    if limit is None:
        limit = get_int("quests", "completed_limit", default=50)
    conn = get_shared_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM quests WHERE status = %s ORDER BY created_at DESC LIMIT %s",
            ("done", limit),
        ).fetchall()
        return [Quest(**dict(row)) for row in rows]
    finally:
        release_connection(conn)


def add_quest(title: str, category: str = "todo", deadline: str | None = None) -> Quest:
    conn = get_shared_connection()
    try:
        cur = conn.execute(
            "INSERT INTO quests (title, status, category, deadline) VALUES (%s, %s, %s, %s) RETURNING *",
            (title, "pending", category, deadline),
        )
        row = dict(cur.fetchone())
        conn.commit()
        return Quest(**row)
    finally:
        release_connection(conn)


def toggle_quest(quest_id: int) -> Quest:
    conn = get_shared_connection()
    try:
        cur = conn.execute("SELECT * FROM toggle_quest(%s)", (quest_id,))
        row = dict(cur.fetchone())
        conn.commit()
        return Quest(**row)
    finally:
        release_connection(conn)


def update_quest(quest_id: int, title: str, deadline: str | None = None) -> Quest:
    conn = get_shared_connection()
    try:
        cur = conn.execute(
            "UPDATE quests SET title = %s, deadline = %s WHERE id = %s RETURNING *",
            (title, deadline, quest_id),
        )
        row = dict(cur.fetchone())
        conn.commit()
        return Quest(**row)
    finally:
        release_connection(conn)


def delete_quest(quest_id: int) -> None:
    conn = get_shared_connection()
    try:
        conn.execute("DELETE FROM quests WHERE id = %s", (quest_id,))
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