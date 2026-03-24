from core.db import get_shared_connection
from core.models import Quest


def get_all_quests() -> list[Quest]:
    conn = get_shared_connection()
    rows = conn.execute('SELECT * FROM quests ORDER BY created_at DESC').fetchall()
    return [Quest(**dict(row)) for row in rows]


def add_quest(title: str) -> Quest:
    conn = get_shared_connection()
    cursor = conn.execute(
        'INSERT INTO quests (title, status) VALUES (?, ?)',
        (title, 'pending')
    )
    conn.commit()
    row = conn.execute('SELECT * FROM quests WHERE id = ?', (cursor.lastrowid,)).fetchone()
    return Quest(**dict(row))


def toggle_quest(quest_id: int) -> Quest:
    conn = get_shared_connection()
    row = conn.execute('SELECT * FROM quests WHERE id = ?', (quest_id,)).fetchone()
    new_status = 'done' if row['status'] == 'pending' else 'pending'
    conn.execute('UPDATE quests SET status = ? WHERE id = ?', (new_status, quest_id))
    conn.commit()
    row = conn.execute('SELECT * FROM quests WHERE id = ?', (quest_id,)).fetchone()
    return Quest(**dict(row))


def delete_quest(quest_id: int) -> None:
    conn = get_shared_connection()
    conn.execute('DELETE FROM quests WHERE id = ?', (quest_id,))
    conn.commit()
