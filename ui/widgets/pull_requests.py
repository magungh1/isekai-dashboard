from textual import work
from textual.app import ComposeResult
from textual.widgets import Static, Label, ListView, ListItem
from textual.binding import Binding

from clients.github_client import (
    fetch_open_prs, fetch_review_requested_prs,
    open_pr_in_browser, approve_pr, format_pr_age, get_ci_status,
)


CI_ICONS = {"pass": "✅", "fail": "❌", "pending": "🔄", "": ""}


class PRItem(ListItem):
    """A single PR item that can be opened in browser."""

    def __init__(self, pr: dict) -> None:
        super().__init__()
        self.pr = pr

    def compose(self) -> ComposeResult:
        repo_name = self.pr['repository']['name']
        title = self.pr['title']
        max_len = 38
        if len(title) > max_len:
            title = title[:max_len - 1] + "…"

        age = format_pr_age(self.pr.get('createdAt', ''))
        ci = CI_ICONS.get(get_ci_status(self.pr), "")

        kind = self.pr.get('_kind', 'authored')
        if kind == 'review_requested':
            icon = "👀"
            css_class = "pr-needs-review"
        else:
            icon = "🟡"
            css_class = "pr-review"

        age_str = f" {age}" if age else ""
        ci_str = f" {ci}" if ci else ""
        yield Label(
            f"  {icon} \\[#{self.pr['number']}] {title} ({repo_name}){age_str}{ci_str}",
            classes=css_class,
        )


class PullRequests(Static):
    """Fetches live GitHub PRs with interactive list."""

    BINDINGS = [
        Binding("a", "approve_pr", "Approve", show=True),
    ]

    can_focus = True

    def compose(self) -> ComposeResult:
        yield Label("⚔️ [ 通信網 ] PULL REQUESTS", classes="widget-title")
        yield ListView(id="pr-list")

    def on_mount(self) -> None:
        self.fetch_prs()
        self.set_interval(300, self.fetch_prs)

    @work(thread=True)
    def fetch_prs(self) -> None:
        my_prs = fetch_open_prs()
        review_prs = fetch_review_requested_prs()

        def update_ui():
            pr_list = self.query_one("#pr-list", ListView)
            pr_list.clear()
            if my_prs is None and review_prs is None:
                pr_list.append(ListItem(Label("❌ GitHub CLI not available", classes="pr-failed")))
                return

            has_items = False

            if review_prs:
                pr_list.append(ListItem(Label("  NEEDS YOUR REVIEW", classes="pr-section-header")))
                for pr in review_prs:
                    pr_list.append(PRItem(pr))
                has_items = True

            if my_prs:
                if has_items:
                    pr_list.append(ListItem(Label("  MY PULL REQUESTS", classes="pr-section-header")))
                for pr in my_prs:
                    pr_list.append(PRItem(pr))
                has_items = True

            if not has_items:
                pr_list.append(ListItem(Label("✨ No open PRs. 完璧！", classes="pr-merged")))

        self.app.call_from_thread(update_ui)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, PRItem) and 'url' in event.item.pr:
            open_pr_in_browser(event.item.pr['url'])

    def action_approve_pr(self) -> None:
        pr_list = self.query_one("#pr-list", ListView)
        if pr_list.highlighted_child and isinstance(pr_list.highlighted_child, PRItem):
            pr = pr_list.highlighted_child.pr
            if pr.get('_kind') == 'review_requested':
                repo = pr['repository']
                fullname = repo.get('nameWithOwner') or f"{repo.get('owner', {}).get('login', '')}/{repo['name']}"
                self._do_approve(fullname, pr['number'])
            else:
                self.app.notify("This is your own PR", severity="warning")

    @work(thread=True)
    def _do_approve(self, repo: str, number: int) -> None:
        success = approve_pr(repo, number)
        if success:
            self.app.call_from_thread(
                self.app.notify, f"Approved PR #{number}! ✅", title="PR"
            )
            self.fetch_prs()
        else:
            self.app.call_from_thread(
                self.app.notify, f"Failed to approve PR #{number}", severity="error"
            )
