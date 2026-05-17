from services.quests_service import (
    get_all_quests, get_quests_by_category, add_quest,
    toggle_quest, delete_quest,
)


def test_add_quest():
    quest = add_quest("Learn PyTorch")
    assert quest.title == "Learn PyTorch"
    assert quest.status == "pending"
    assert quest.category == "todo"
    assert quest.id is not None


def test_add_quest_with_category():
    quest = add_quest("Check PRs", category="todo")
    assert quest.category == "todo"


def test_add_quest_with_deadline():
    quest = add_quest("Learn transformers", category="todo", deadline="2026-06-01")
    assert quest.category == "todo"
    assert quest.deadline.startswith("2026-06-01")


def test_get_all_quests():
    add_quest("Quest A")
    add_quest("Quest B")
    quests = get_all_quests()
    assert len(quests) == 2


def test_get_quests_by_category():
    add_quest("Todo task", category="todo")
    add_quest("Other task", category="other")

    todo = get_quests_by_category("todo")
    assert len(todo) == 1
    assert todo[0].title == "Todo task"


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
