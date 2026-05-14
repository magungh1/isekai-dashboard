"""Notes service — CRUD operations for the notes table."""

from datetime import datetime

from core.db import get_shared_connection, release_connection


def get_notes(category: str | None = None) -> list[dict]:
    """Fetch notes, optionally filtered by category."""
    conn = get_shared_connection()
    try:
        if category:
            rows = conn.execute(
                "SELECT * FROM notes WHERE category = %s ORDER BY updated_at DESC",
                (category,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM notes ORDER BY updated_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]
    finally:
        release_connection(conn)


def get_note(note_id: int) -> dict | None:
    """Fetch a single note by ID."""
    conn = get_shared_connection()
    try:
        row = conn.execute("SELECT * FROM notes WHERE id = %s", (note_id,)).fetchone()
        return dict(row) if row else None
    finally:
        release_connection(conn)


def add_note(content: str, category: str = "general") -> dict:
    """Create a new note."""
    conn = get_shared_connection()
    try:
        now = datetime.now().isoformat()
        cur = conn.execute(
            "INSERT INTO notes (content, category, created_at, updated_at) VALUES (%s, %s, %s, %s) RETURNING *",
            (content, category, now, now),
        )
        row = dict(cur.fetchone())
        conn.commit()
        return row
    finally:
        release_connection(conn)


def update_note(note_id: int, content: str, category: str | None = None) -> dict | None:
    """Update an existing note's content and optionally its category."""
    conn = get_shared_connection()
    try:
        now = datetime.now().isoformat()
        if category:
            conn.execute(
                "UPDATE notes SET content = %s, category = %s, updated_at = %s WHERE id = %s",
                (content, category, now, note_id),
            )
        else:
            conn.execute(
                "UPDATE notes SET content = %s, updated_at = %s WHERE id = %s",
                (content, now, note_id),
            )
        conn.commit()
        return get_note(note_id)
    finally:
        release_connection(conn)


def delete_note(note_id: int) -> None:
    """Delete a note by ID."""
    conn = get_shared_connection()
    try:
        conn.execute("DELETE FROM notes WHERE id = %s", (note_id,))
        conn.commit()
    finally:
        release_connection(conn)


CATEGORIES = ["general", "pomodoro", "study", "ideas", "personal"]