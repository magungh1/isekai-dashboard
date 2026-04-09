from textual.app import App, ComposeResult
from textual.widgets import ListView, ListItem, Label
from textual import events
from textual.message import Message

class DragItem(ListItem):
    class DragStart(Message):
        def __init__(self, item: "DragItem", start_y: int):
            self.item = item
            self.start_y = start_y
            super().__init__()

    class DragEnd(Message):
        def __init__(self, item: "DragItem", end_y: int):
            self.item = item
            self.end_y = end_y
            super().__init__()

    def __init__(self, label_text: str, **kwargs):
        super().__init__(**kwargs)
        self.label_text = label_text

    def compose(self) -> ComposeResult:
        yield Label(self.label_text)

    def on_mouse_down(self, event: events.MouseDown) -> None:
        if event.button == 1:
            self.capture_mouse()
            self.post_message(self.DragStart(self, event.screen_y))
            # self.set_class(True, "-dragging") # maybe some visual feedback

    def on_mouse_up(self, event: events.MouseUp) -> None:
        if self.has_pseudo_class("focus") or self.has_class("-dragging") or hasattr(self, "_dragging") or event.button == 1:
            if self.has_pseudo_class("focus") or True: # assume true
                self.release_mouse()
                self.post_message(self.DragEnd(self, event.screen_y))

class DragApp(App):
    CSS = """
    DragItem.-drag-over {
        background: $accent 30%;
    }
    """
    def compose(self) -> ComposeResult:
        yield ListView(
            DragItem("Item 1"),
            DragItem("Item 2"),
            DragItem("Item 3"),
            DragItem("Item 4"),
            id="my-list"
        )

    def on_drag_item_drag_start(self, event: DragItem.DragStart) -> None:
        self.bell()

    def on_drag_item_drag_end(self, event: DragItem.DragEnd) -> None:
        lv = self.query_one("#my-list", ListView)
        target = None
        for child in lv.children:
            if isinstance(child, DragItem):
                y = child.region.y
                h = child.region.height
                if y <= event.end_y < y + h:
                    target = child
                    break
        if target and target is not event.item:
            self.bell()
            # logic to reorder

if __name__ == "__main__":
    app = DragApp()
    app.run()
