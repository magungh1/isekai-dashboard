from textual.app import App, ComposeResult
from textual.widgets import Button, ListItem, ListView
from textual import events

class MyItem(ListItem):
    def compose(self) -> ComposeResult:
        yield Button("Click Me")

    def on_mouse_down(self, event: events.MouseDown) -> None:
        widget = self.app.get_widget_at(event.screen_x, event.screen_y)[0]
        print("MouseDown on", type(widget).__name__)

class MyApp(App):
    def compose(self) -> ComposeResult:
        yield ListView(MyItem())

if __name__ == "__main__":
    app = MyApp()
    app.run()
