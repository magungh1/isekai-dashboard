from datetime import date, timedelta

from core.db import get_shared_connection, release_connection

XP_QUEST_COMPLETE = 10
XP_SRS_REVIEW = 5
XP_POMODORO_COMPLETE = 25
LEVEL_BASE = 50


def _ensure_xp_table():
    conn = get_shared_connection()
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS xp_log (
                id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                xp INTEGER NOT NULL,
                source TEXT NOT NULL,
                created_date TEXT NOT NULL
            )
        ''')
        conn.commit()
    finally:
        release_connection(conn)


def add_xp(amount: int, source: str) -> None:
    _ensure_xp_table()
    conn = get_shared_connection()
    try:
        today = date.today().isoformat()
        conn.execute(
            'INSERT INTO xp_log (xp, source, created_date) VALUES (%s, %s, %s)',
            (amount, source, today),
        )
        conn.commit()
    finally:
        release_connection(conn)


def get_total_xp() -> int:
    _ensure_xp_table()
    conn = get_shared_connection()
    try:
        row = conn.execute('SELECT COALESCE(SUM(xp), 0) FROM xp_log').fetchone()
        return row[0]
    finally:
        release_connection(conn)


def get_today_xp() -> int:
    _ensure_xp_table()
    conn = get_shared_connection()
    try:
        today = date.today().isoformat()
        row = conn.execute(
            'SELECT COALESCE(SUM(xp), 0) FROM xp_log WHERE created_date = %s',
            (today,),
        ).fetchone()
        return row[0]
    finally:
        release_connection(conn)


def xp_for_level(level: int) -> int:
    if level <= 0:
        return 0
    return int(LEVEL_BASE * (level ** 1.5))


def get_today_pomodoro_count() -> int:
    _ensure_xp_table()
    conn = get_shared_connection()
    try:
        today = date.today().isoformat()
        row = conn.execute(
            "SELECT COUNT(*) FROM xp_log WHERE source = %s AND created_date = %s",
            ('pomodoro', today),
        ).fetchone()
        return row[0]
    finally:
        release_connection(conn)


def get_streak() -> int:
    _ensure_xp_table()
    conn = get_shared_connection()
    try:
        rows = conn.execute(
            'SELECT DISTINCT created_date FROM xp_log ORDER BY created_date DESC'
        ).fetchall()
    finally:
        release_connection(conn)

    if not rows:
        return 0
    dates = [date.fromisoformat(r['created_date']) for r in rows]
    today = date.today()
    if dates[0] != today and dates[0] != today - timedelta(days=1):
        return 0
    streak = 1
    for i in range(1, len(dates)):
        if dates[i - 1] - dates[i] == timedelta(days=1):
            streak += 1
        else:
            break
    return streak


def get_level_info() -> dict:
    total_xp = get_total_xp()
    level = 0
    while xp_for_level(level + 1) <= total_xp:
        level += 1
    current_threshold = xp_for_level(level)
    next_threshold = xp_for_level(level + 1)
    xp_in_level = total_xp - current_threshold
    xp_needed = next_threshold - current_threshold
    return {
        'level': level,
        'total_xp': total_xp,
        'xp_in_level': xp_in_level,
        'xp_needed': xp_needed,
        'today_xp': get_today_xp(),
        'streak': get_streak(),
    }