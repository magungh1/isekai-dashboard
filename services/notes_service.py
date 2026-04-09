from core.db import get_shared_connection, db_lock


def add_note(content: str) -> dict:
    with db_lock:
        conn = get_shared_connection()
        cursor = conn.execute(
            'INSERT INTO notes (content) VALUES (?)',
            (content,)
        )
        conn.commit()
        row = conn.execute('SELECT * FROM notes WHERE id = ?', (cursor.lastrowid,)).fetchone()
        return dict(row)


def get_recent_notes(limit: int = 50) -> list[dict]:
    with db_lock:
        conn = get_shared_connection()
        rows = conn.execute(
            'SELECT * FROM notes ORDER BY created_at DESC LIMIT ?',
            (limit,)
        ).fetchall()
        return [dict(row) for row in rows]


def delete_note(note_id: int) -> None:
    with db_lock:
        conn = get_shared_connection()
        conn.execute('DELETE FROM notes WHERE id = ?', (note_id,))
        conn.commit()
