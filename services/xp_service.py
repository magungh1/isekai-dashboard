from datetime import date, timedelta

from core.db import get_shared_connection, db_lock
from config import get

# XP rewards
XP_QUEST_COMPLETE = get("xp", "quest_complete", 10)
XP_SRS_REVIEW = get("xp", "srs_review", 5)
XP_POMODORO_COMPLETE = get("xp", "pomodoro_complete", 25)

# Level thresholds: level N requires LEVEL_BASE * N^1.5 total XP
LEVEL_BASE = get("xp", "level_base", 50)


def _ensure_xp_table() -> None:
    conn = get_shared_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS xp_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            xp INTEGER NOT NULL,
            source TEXT NOT NULL,
            created_date TEXT NOT NULL
        )
    ''')
    conn.commit()


def add_xp(amount: int, source: str) -> None:
    with db_lock:
        _ensure_xp_table()
        conn = get_shared_connection()
        today = date.today().isoformat()
        conn.execute(
            'INSERT INTO xp_log (xp, source, created_date) VALUES (?, ?, ?)',
            (amount, source, today)
        )
        conn.commit()


def get_total_xp() -> int:
    with db_lock:
        _ensure_xp_table()
        conn = get_shared_connection()
        row = conn.execute('SELECT COALESCE(SUM(xp), 0) FROM xp_log').fetchone()
        return row[0]


def get_today_xp() -> int:
    with db_lock:
        _ensure_xp_table()
        conn = get_shared_connection()
        today = date.today().isoformat()
        row = conn.execute(
            'SELECT COALESCE(SUM(xp), 0) FROM xp_log WHERE created_date = ?',
            (today,)
        ).fetchone()
        return row[0]


def xp_for_level(level: int) -> int:
    """Total XP required to reach a given level."""
    if level <= 0:
        return 0
    return int(LEVEL_BASE * (level ** 1.5))


def get_today_pomodoro_count() -> int:
    """Return how many pomodoro sessions were completed today."""
    with db_lock:
        _ensure_xp_table()
        conn = get_shared_connection()
        today = date.today().isoformat()
        row = conn.execute(
            "SELECT COUNT(*) FROM xp_log WHERE source = 'pomodoro' AND created_date = ?",
            (today,)
        ).fetchone()
        return row[0]


def get_streak() -> int:
    """Return number of consecutive days with XP activity, ending today or yesterday."""
    with db_lock:
        _ensure_xp_table()
        conn = get_shared_connection()
        rows = conn.execute(
            'SELECT DISTINCT created_date FROM xp_log ORDER BY created_date DESC'
        ).fetchall()
    if not rows:
        return 0
    dates = [date.fromisoformat(r[0]) for r in rows]
    today = date.today()
    # Streak must include today or yesterday to be active
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
    """Returns current level, XP within level, and XP needed for next level."""
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
