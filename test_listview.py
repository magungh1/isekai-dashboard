from textual.app import App, ComposeResult
from textual.widgets import ListView, ListItem, Label
import asyncio

class TestApp(App):
    def compose(self) -> ComposeResult:
        yield ListView(id="list")
    
    def on_mount(self) -> None:
        lv = self.query_one("#list", ListView)
        lv.clear()
        lv.append(ListItem(Label("Test Quest 1", id="label1")))
        lv.append(ListItem(Label("Test Quest 2", id="label2")))

if __name__ == "__main__":
    app = TestApp()
    app.run(headless=True, size=(80, 24))
