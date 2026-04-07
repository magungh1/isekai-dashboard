import pytest
from textual.app import App, ComposeResult
from ui.widgets.daily_quests import DailyQuests, QuestItem
from services.quests_service import get_quests_by_category, delete_quest


class DummyApp(App):
    def compose(self) -> ComposeResult:
        yield DailyQuests()


@pytest.mark.asyncio
async def test_create_and_delete_quest():
    # Ensure starting clean
    for q in get_quests_by_category("daily"):
        delete_quest(q.id)

    app = DummyApp()
    async with app.run_test() as pilot:
        # Wait for the initial quests to load
        await pilot.pause()

        # Target the daily quests input
        input_widget = app.query_one("#quest-input-daily")
        
        # 1. Create a quest
        # We need to focus it and type
        input_widget.focus()
        await pilot.press(*"My Test Quest")
        await pilot.press("enter")
        
        # Wait for the deferred load to complete
        await pilot.pause(0.2)

        # Check that it was created
        quests = get_quests_by_category("daily")
        assert len(quests) == 1
        assert quests[0].title == "My Test Quest"

        # Check that it exists in the UI
        quest_items = app.query(QuestItem)
        assert len(quest_items) == 1

        # 2. Delete the quest
        # Target the delete button
        delete_btn = quest_items[0].query_one(".quest-delete-btn")
        
        # Click the delete button
        await pilot.click(delete_btn)
        
        # Wait for the deferred load to complete
        await pilot.pause(0.2)

        # Check that it was deleted
        quests = get_quests_by_category("daily")
        assert len(quests) == 0
        
        quest_items = app.query(QuestItem)
        assert len(quest_items) == 0
