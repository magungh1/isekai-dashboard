from textual import work
from textual.app import ComposeResult
from textual.widgets import Static, Label, ListView, ListItem

from clients.github_client import fetch_open_prs, open_pr_in_browser


class PRItem(ListItem):
    """A single PR item that can be opened in browser."""

    def __init__(self, pr: dict) -> None:
        super().__init__()
        self.pr = pr

    def compose(self) -> ComposeResult:
        repo_name = self.pr['repository']['name']
        yield Label(f"🟡 [#{self.pr['number']}] {self.pr['title']} ({repo_name})", classes="pr-review")


class PullRequests(Static):
    """Fetches live GitHub PRs with interactive list."""

    def compose(self) -> ComposeResult:
        yield Label("⚔️ [ 通信網 ] PULL REQUESTS", classes="widget-title")
        yield ListView(id="pr-list")

    def on_mount(self) -> None:
        self.fetch_prs()

    @work(thread=True)
    def fetch_prs(self) -> None:
        prs = fetch_open_prs()

        def update_ui():
            pr_list = self.query_one("#pr-list", ListView)
            pr_list.clear()
            if prs is None:
                pr_list.append(ListItem(Label("❌ GitHub CLI not available", classes="pr-failed")))
            elif not prs:
                pr_list.append(ListItem(Label("✨ No open PRs. 完璧！", classes="pr-merged")))
            else:
                for pr in prs:
                    pr_list.append(PRItem(pr))

        self.app.call_from_thread(update_ui)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, PRItem) and 'url' in event.item.pr:
            open_pr_in_browser(event.item.pr['url'])
