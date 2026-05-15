"""Habit tracker service — CRUD, logging, streaks, weekly data."""

from datetime import date, timedelta

from core.db import get_shared_connection, release_connection
from config import get_int


STATUS_CYCLE = ["", "done", "skipped", "missed"]


def get_habits(category: str | None = None) -> list[dict]:
    conn = get_shared_connection()
    try:
        if category:
            rows = conn.execute(
                "SELECT * FROM habits WHERE category = %s ORDER BY sort_order ASC, id ASC",
                (category,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM habits ORDER BY sort_order ASC, id ASC"
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        release_connection(conn)


def add_habit(
    name: str,
    icon: str = "📌",
    category: str = "daily",
    xp_reward: int | None = None,
    is_countable: bool = False,
    target_count: int = 1,
) -> dict:
    if xp_reward is None:
        xp_reward = get_int("habits", "default_xp", default=5)
    conn = get_shared_connection()
    try:
        cur = conn.execute(
            "INSERT INTO habits (name, icon, category, xp_reward, is_countable, target_count, created_date) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *",
            (name, icon, category, xp_reward, int(is_countable), target_count, date.today().isoformat()),
        )
        row = dict(cur.fetchone())
        conn.commit()
        return row
    finally:
        release_connection(conn)


def delete_habit(habit_id: int) -> None:
    conn = get_shared_connection()
    try:
        conn.execute("DELETE FROM habits WHERE id = %s", (habit_id,))
        conn.commit()
    finally:
        release_connection(conn)


def update_habit(
    habit_id: int,
    name: str | None = None,
    icon: str | None = None,
    xp_reward: int | None = None,
    is_countable: bool | None = None,
    target_count: int | None = None,
    sort_order: int | None = None,
) -> dict:
    conn = get_shared_connection()
    try:
        existing = conn.execute("SELECT * FROM habits WHERE id = %s", (habit_id,)).fetchone()
        if not existing:
            raise ValueError(f"Habit {habit_id} not found")
        existing = dict(existing)

        name = name if name is not None else existing["name"]
        icon = icon if icon is not None else existing["icon"]
        xp_reward = xp_reward if xp_reward is not None else existing["xp_reward"]
        is_countable = is_countable if is_countable is not None else existing["is_countable"]
        target_count = target_count if target_count is not None else existing["target_count"]
        sort_order = sort_order if sort_order is not None else existing["sort_order"]

        cur = conn.execute(
            "UPDATE habits SET name = %s, icon = %s, xp_reward = %s, is_countable = %s, "
            "target_count = %s, sort_order = %s WHERE id = %s RETURNING *",
            (name, icon, xp_reward, int(is_countable), target_count, sort_order, habit_id),
        )
        row = dict(cur.fetchone())
        conn.commit()
        return row
    finally:
        release_connection(conn)


def get_habit_log(habit_id: int, date_str: str) -> dict | None:
    conn = get_shared_connection()
    try:
        row = conn.execute(
            "SELECT * FROM habit_log WHERE habit_id = %s AND date = %s",
            (habit_id, date_str),
        ).fetchone()
        return dict(row) if row else None
    finally:
        release_connection(conn)


def cycle_habit_day(habit_id: int, date_str: str) -> dict:
    """Cycle: empty → done → skipped → missed → empty. Returns the new log entry."""
    conn = get_shared_connection()
    try:
        existing = conn.execute(
            "SELECT * FROM habit_log WHERE habit_id = %s AND date = %s",
            (habit_id, date_str),
        ).fetchone()

        habit = conn.execute("SELECT * FROM habits WHERE id = %s", (habit_id,)).fetchone()
        is_countable = habit["is_countable"] if habit else False

        if existing:
            current_status = existing["status"]
            current_count = existing["count"]
            idx = STATUS_CYCLE.index(current_status)
            next_status = STATUS_CYCLE[(idx + 1) % len(STATUS_CYCLE)]

            if next_status == "":
                conn.execute("DELETE FROM habit_log WHERE habit_id = %s AND date = %s", (habit_id, date_str))
                conn.commit()
                return {"habit_id": habit_id, "date": date_str, "status": "", "count": 0}
            else:
                if is_countable and next_status == "done":
                    new_count = current_count + 1 if current_status == "done" else 1
                else:
                    new_count = 1

                cur = conn.execute(
                    "UPDATE habit_log SET status = %s, count = %s WHERE habit_id = %s AND date = %s RETURNING *",
                    (next_status, new_count, habit_id, date_str),
                )
                row = dict(cur.fetchone())
                conn.commit()
                return row
        else:
            cur = conn.execute(
                "INSERT INTO habit_log (habit_id, date, status, count) VALUES (%s, %s, %s, %s) RETURNING *",
                (habit_id, date_str, "done", 1),
            )
            row = dict(cur.fetchone())
            conn.commit()
            return row
    finally:
        release_connection(conn)


def set_habit_count(habit_id: int, date_str: str, count: int) -> dict:
    """Increment or decrement count for a countable habit."""
    conn = get_shared_connection()
    try:
        habit = conn.execute("SELECT * FROM habits WHERE id = %s", (habit_id,)).fetchone()
        if not habit:
            raise ValueError(f"Habit {habit_id} not found")
        target = habit["target_count"]

        existing = conn.execute(
            "SELECT * FROM habit_log WHERE habit_id = %s AND date = %s",
            (habit_id, date_str),
        ).fetchone()

        if existing:
            new_count = max(0, min(existing["count"] + count, target))
            new_status = "done" if new_count > 0 else ""
            if new_status == "":
                conn.execute("DELETE FROM habit_log WHERE habit_id = %s AND date = %s", (habit_id, date_str))
                conn.commit()
                return {"habit_id": habit_id, "date": date_str, "status": "", "count": 0}
            cur = conn.execute(
                "UPDATE habit_log SET count = %s, status = %s WHERE habit_id = %s AND date = %s RETURNING *",
                (new_count, new_status, habit_id, date_str),
            )
            row = dict(cur.fetchone())
            conn.commit()
            return row
        else:
            new_count = max(1, min(count, target))
            cur = conn.execute(
                "INSERT INTO habit_log (habit_id, date, status, count) VALUES (%s, %s, %s, %s) RETURNING *",
                (habit_id, date_str, "done", new_count),
            )
            row = dict(cur.fetchone())
            conn.commit()
            return row
    finally:
        release_connection(conn)


def get_streak(habit_id: int) -> int:
    """Current consecutive days with status='done'."""
    conn = get_shared_connection()
    try:
        rows = conn.execute(
            "SELECT date FROM habit_log WHERE habit_id = %s AND status = %s ORDER BY date DESC",
            (habit_id, "done"),
        ).fetchall()
        if not rows:
            return 0

        dates = [date.fromisoformat(r["date"]) for r in rows]
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
    finally:
        release_connection(conn)


def get_week_range() -> tuple[date, date]:
    """Return (monday, sunday) for the current week."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def get_habit_week(habit_id: int, week_start: date) -> list[dict]:
    """Return 7 day entries for a habit starting from week_start."""
    conn = get_shared_connection()
    try:
        results = []
        for i in range(7):
            d = (week_start + timedelta(days=i)).isoformat()
            log = conn.execute(
                "SELECT * FROM habit_log WHERE habit_id = %s AND date = %s",
                (habit_id, d),
            ).fetchone()
            results.append({
                "date": d,
                "status": log["status"] if log else "",
                "count": log["count"] if log else 0,
                "day_name": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][i],
            })
        return results
    finally:
        release_connection(conn)


def get_all_habits_week(week_start: date) -> list[dict]:
    """Return all habits with their 7-day data."""
    habits = get_habits()
    results = []
    for habit in habits:
        week_data = get_habit_week(habit["id"], week_start)
        streak = get_streak(habit["id"])
        results.append({
            **habit,
            "week": week_data,
            "streak": streak,
        })
    return results


def get_habit_xp_reward(habit_id: int) -> int:
    conn = get_shared_connection()
    try:
        row = conn.execute("SELECT xp_reward FROM habits WHERE id = %s", (habit_id,)).fetchone()
        return row["xp_reward"] if row else get_int("habits", "default_xp", default=5)
    finally:
        release_connection(conn)


def get_streak_bonus(streak: int) -> int:
    """Return bonus XP for streak milestones."""
    if streak >= 30:
        return get_int("habits", "streak_bonus_30", default=100)
    if streak == 7:
        return get_int("habits", "streak_bonus_7", default=20)
    return 0
