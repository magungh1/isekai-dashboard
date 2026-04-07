from services.quests_service import (
    get_all_quests, get_quests_by_category, add_quest,
    toggle_quest, delete_quest, reset_daily_quests, reset_weekly_quests,
)
from core.db import get_shared_connection


def test_add_quest():
    quest = add_quest("Learn PyTorch")
    assert quest.title == "Learn PyTorch"
    assert quest.status == "pending"
    assert quest.category == "daily"
    assert quest.id is not None


def test_add_quest_with_category():
    quest = add_quest("Check PRs", category="weekly")
    assert quest.category == "weekly"


def test_add_quest_with_deadline():
    quest = add_quest("Learn transformers", category="goals", deadline="2026-06-01")
    assert quest.category == "goals"
    assert quest.deadline == "2026-06-01"


def test_get_all_quests():
    add_quest("Quest A")
    add_quest("Quest B")
    quests = get_all_quests()
    assert len(quests) == 2


def test_get_quests_by_category():
    add_quest("Daily task", category="daily")
    add_quest("Weekly task", category="weekly")
    add_quest("Goal task", category="goals")

    daily = get_quests_by_category("daily")
    assert len(daily) == 1
    assert daily[0].title == "Daily task"

    weekly = get_quests_by_category("weekly")
    assert len(weekly) == 1
    assert weekly[0].title == "Weekly task"

    goals = get_quests_by_category("goals")
    assert len(goals) == 1
    assert goals[0].title == "Goal task"


def test_toggle_quest():
    quest = add_quest("Toggle me")
    toggled = toggle_quest(quest.id)
    assert toggled.status == "done"

    toggled_back = toggle_quest(quest.id)
    assert toggled_back.status == "pending"


def test_delete_quest():
    quest = add_quest("Delete me")
    delete_quest(quest.id)
    quests = get_all_quests()
    assert len(quests) == 0


def test_reset_daily_quests():
    q1 = add_quest("Daily A", category="daily")
    q2 = add_quest("Weekly B", category="weekly")
    toggle_quest(q1.id)
    toggle_quest(q2.id)

    # Set last reset to yesterday so reset triggers
    conn = get_shared_connection()
    conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('last_daily_reset', '2020-01-01')")
    conn.commit()

    reset_daily_quests()

    daily = get_quests_by_category("daily")
    assert daily[0].status == "pending"

    # Weekly should remain done
    weekly = get_quests_by_category("weekly", include_done=True)
    assert weekly[0].status == "done"


def test_reset_weekly_quests():
    q1 = add_quest("Weekly A", category="weekly")
    q2 = add_quest("Daily B", category="daily")
    toggle_quest(q1.id)
    toggle_quest(q2.id)

    conn = get_shared_connection()
    conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('last_weekly_reset', '2020-01-01')")
    conn.commit()

    reset_weekly_quests()

    weekly = get_quests_by_category("weekly")
    assert weekly[0].status == "pending"

    # Daily should remain done
    daily = get_quests_by_category("daily", include_done=True)
    assert daily[0].status == "done"


def test_reset_daily_no_double_reset():
    """Reset should not run twice on the same day."""
    q = add_quest("Daily X", category="daily")
    toggle_quest(q.id)

    reset_daily_quests()  # First reset

    # Toggle back to done
    toggle_quest(q.id)

    reset_daily_quests()  # Second reset — should be a no-op

    daily = get_quests_by_category("daily", include_done=True)
    assert daily[0].status == "done"
