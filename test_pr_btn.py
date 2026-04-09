import pytest
from textual.app import App, ComposeResult
from ui.widgets.pull_requests import PullRequests
from textual.widgets import Button

class DummyApp(App):
    def compose(self) -> ComposeResult:
        yield PullRequests()

@pytest.mark.asyncio
async def test_pr_refresh_btn():
    app = DummyApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        pr_widget = app.query_one(PullRequests)
        
        # We replace fetch_prs to see if it's called
        called = False
        def mock_fetch():
            nonlocal called
            called = True
            
        pr_widget.fetch_prs = mock_fetch
        
        btn = app.query_one("#pr-refresh-btn", Button)
        await pilot.click(btn)
        await pilot.pause()
        
        assert called, "fetch_prs was not called!"

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_pr_refresh_btn())
    print("Test passed!")
