from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static, Label, ListView, ListItem, Button

from clients.github_client import (
    fetch_open_prs, fetch_review_requested_prs,
    open_pr_in_browser, approve_pr, close_pr, format_pr_age, get_ci_status,
    fetch_notifications, mark_notification_read,
)


CI_ICONS = {"pass": "✅", "fail": "❌", "pending": "🔄", "": ""}

REASON_ICONS = {
    "comment": "💬",
    "review_requested": "👀",
    "assign": "📌",
    "mention": "📣",
    "ci_activity": "⚙️",
    "state_change": "🔄",
    "author": "✍️",
    "approval_requested": "👀",
    "security_alert": "🚨",
}


class PRItem(ListItem):
    """A single PR item that can be opened in browser."""

    def __init__(self, pr: dict) -> None:
        super().__init__()
        self.pr = pr

    def compose(self) -> ComposeResult:
        repo_name = self.pr['repository']['name']
        title = self.pr['title']

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
        with Horizontal():
            yield Label(
                f"  {icon} \\[#{self.pr['number']}] {title} ({repo_name}){age_str}{ci_str}",
                classes=css_class,
            )
            if kind == 'review_requested':
                yield Button("✓", classes="pr-approve-btn")
                yield Button("✕", classes="pr-close-btn")
            else:
                yield Button("✕", classes="pr-close-btn")


class NotificationItem(ListItem):
    """A single GitHub notification item."""

    def __init__(self, notif: dict) -> None:
        super().__init__()
        self.notif = notif

    def compose(self) -> ComposeResult:
        reason = self.notif.get('reason', '')
        icon = REASON_ICONS.get(reason, "🔔")
        title = self.notif['title']
        repo = self.notif.get('repo', '')
        age = format_pr_age(self.notif.get('updated_at', ''))
        age_str = f" {age}" if age else ""
        with Horizontal():
            yield Label(
                f"  {icon} {title} ({repo}){age_str}",
                classes="notif-text",
            )
            yield Button("✓", classes="notif-dismiss-btn")


class PullRequests(Static):
    """Fetches live GitHub PRs with interactive list."""

    can_focus = True

    def compose(self) -> ComposeResult:
        yield Label("⚔️ [ 通信網 ] PULL REQUESTS", id="pr-title", classes="widget-title")
        yield ListView(id="pr-list")

    def on_mount(self) -> None:
        self._last_pr_keys: set[tuple] = set()
        self._last_notif_ids: set[str] = set()
        self.fetch_prs()
        self.set_interval(10, self.fetch_prs)

    @work(thread=True)
    def fetch_prs(self) -> None:
        my_prs = fetch_open_prs()
        review_prs = fetch_review_requested_prs()
        notifications = fetch_notifications()

        new_keys = set()
        for pr in (review_prs or []):
            new_keys.add((pr['number'], pr['repository']['name'], 'review_requested'))
        for pr in (my_prs or []):
            new_keys.add((pr['number'], pr['repository']['name'], 'authored'))

        new_notif_ids = {n['id'] for n in (notifications or [])}

        if (new_keys == self._last_pr_keys and self._last_pr_keys
                and new_notif_ids == self._last_notif_ids):
            return
        self._last_pr_keys = new_keys
        self._last_notif_ids = new_notif_ids

        def update_ui():
            pr_list = self.query_one("#pr-list", ListView)
            pr_list.clear()

            title_label = self.query_one("#pr-title", Label)

            if my_prs is None and review_prs is None:
                pr_list.append(ListItem(Label("❌ GitHub CLI not available", classes="pr-failed")))
                title_label.update("⚔️ [ 通信網 ] PULL REQUESTS")
                return

            has_items = False

            # Notifications section
            if notifications:
                pr_list.append(ListItem(Label(
                    f"  🔔 NOTIFICATIONS ({len(notifications)})",
                    classes="pr-section-header notif-section-header",
                )))
                for notif in notifications:
                    pr_list.append(NotificationItem(notif))
                has_items = True
                title_label.update(
                    f"⚔️ [ 通信網 ] PULL REQUESTS ({len(notifications)} 🔔)"
                )
            else:
                title_label.update("⚔️ [ 通信網 ] PULL REQUESTS")

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
        elif isinstance(event.item, NotificationItem):
            notif = event.item.notif
            if notif.get('url'):
                open_pr_in_browser(notif['url'])
            self._do_mark_read(notif['id'])
            event.item.remove()
            self._last_notif_ids.discard(notif['id'])

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # Handle notification dismiss
        if "notif-dismiss-btn" in event.button.classes:
            item = event.button.parent
            while item and not isinstance(item, NotificationItem):
                item = item.parent
            if isinstance(item, NotificationItem):
                self._do_mark_read(item.notif['id'])
                item.remove()
                self._last_notif_ids.discard(item.notif['id'])
            return

        # Handle PR buttons
        item = event.button.parent
        while item and not isinstance(item, PRItem):
            item = item.parent
        if not isinstance(item, PRItem):
            return
        pr = item.pr
        repo = pr['repository']
        fullname = repo.get('nameWithOwner') or f"{repo.get('owner', {}).get('login', '')}/{repo['name']}"
        if "pr-approve-btn" in event.button.classes:
            self._do_approve(fullname, pr['number'])
        elif "pr-close-btn" in event.button.classes:
            self._do_close(fullname, pr['number'])
        item.remove()
        self._last_pr_keys.discard((pr['number'], pr['repository']['name'], pr.get('_kind', 'authored')))

    @work(thread=True)
    def _do_mark_read(self, thread_id: str) -> None:
        success = mark_notification_read(thread_id)
        if success:
            self.app.call_from_thread(
                self.app.notify, "Notification dismissed ✓", title="GitHub"
            )

    @work(thread=True)
    def _do_approve(self, repo: str, number: int) -> None:
        success = approve_pr(repo, number)
        if success:
            self.app.call_from_thread(
                self.app.notify, f"Approved PR #{number}! ✅", title="PR"
            )
        else:
            self.app.call_from_thread(
                self.app.notify, f"Failed to approve PR #{number}", severity="error"
            )

    @work(thread=True)
    def _do_close(self, repo: str, number: int) -> None:
        success = close_pr(repo, number)
        if success:
            self.app.call_from_thread(
                self.app.notify, f"Closed PR #{number}! 🔒", title="PR"
            )
        else:
            self.app.call_from_thread(
                self.app.notify, f"Failed to close PR #{number}", severity="error"
            )
