from textual.app import App, ComposeResult
from textual.widgets import ListView, ListItem, Label
from textual import events
import sys

class DragApp(App):
    def compose(self) -> ComposeResult:
        yield ListView(
            ListItem(Label("Item 1")),
            ListItem(Label("Item 2")),
            ListItem(Label("Item 3")),
            id="my-list"
        )
    
    def on_ready(self) -> None:
        lv = self.query_one("#my-list", ListView)
        for child in lv.children:
            print(f"Child: {child}, screen_region: {child.region.y}")
        self.exit()

if __name__ == "__main__":
    app = DragApp()
    app.run()
