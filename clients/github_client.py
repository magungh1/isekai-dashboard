import json
import subprocess
from datetime import datetime, timedelta, timezone

from config import get_int, get_list

PR_MAX_AGE_DAYS = 90
_NOTIFICATION_REASONS = None


def _created_after() -> str:
    days = get_int("github", "pr_max_age_days", default=90)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return f">={cutoff.strftime('%Y-%m-%d')}"


def _get_notification_reasons() -> set[str]:
    global _NOTIFICATION_REASONS
    if _NOTIFICATION_REASONS is None:
        _NOTIFICATION_REASONS = set(get_list("github", "notification_reasons"))
    return _NOTIFICATION_REASONS


def fetch_open_prs() -> list[dict] | None:
    try:
        result = subprocess.run(
            ['gh', 'search', 'prs', '--author=@me', '--state=open',
             '--created', _created_after(),
             '--json', 'title,number,repository,url,createdAt'],
            capture_output=True, text=True, check=True
        )
        prs = json.loads(result.stdout)
        for pr in prs:
            pr['_kind'] = 'authored'
        return prs
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def fetch_review_requested_prs() -> list[dict] | None:
    try:
        result = subprocess.run(
            ['gh', 'search', 'prs', '--review-requested=@me', '--state=open',
             '--created', _created_after(),
             '--json', 'title,number,repository,url,createdAt'],
            capture_output=True, text=True, check=True
        )
        prs = json.loads(result.stdout)
        for pr in prs:
            pr['_kind'] = 'review_requested'
        return prs
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def fetch_assigned_prs() -> list[dict] | None:
    try:
        result = subprocess.run(
            ['gh', 'search', 'prs', '--assignee=@me', '--state=open',
             '--created', _created_after(),
             '--json', 'title,number,repository,url,createdAt,author'],
            capture_output=True, text=True, check=True
        )
        prs = json.loads(result.stdout)
        for pr in prs:
            pr['_kind'] = 'assigned'
        return prs
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def fetch_review_decision(repo_fullname: str, number: int) -> str:
    try:
        result = subprocess.run(
            ['gh', 'pr', 'view', str(number), '-R', repo_fullname,
             '--json', 'reviewDecision'],
            capture_output=True, text=True, check=True
        )
        data = json.loads(result.stdout)
        return data.get('reviewDecision', '')
    except (FileNotFoundError, subprocess.CalledProcessError):
        return ''


def enrich_prs_with_review_status(prs: list[dict]) -> None:
    for pr in prs:
        repo = pr.get('repository', {})
        fullname = repo.get('nameWithOwner') or f"{repo.get('owner', {}).get('login', '')}/{repo['name']}"
        pr['reviewDecision'] = fetch_review_decision(fullname, pr['number'])


def approve_pr(repo_fullname: str, number: int) -> bool:
    try:
        subprocess.run(
            ['gh', 'pr', 'review', str(number), '--approve', '-R', repo_fullname],
            capture_output=True, text=True, check=True
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def merge_pr(repo_fullname: str, number: int) -> bool:
    try:
        subprocess.run(
            ['gh', 'pr', 'merge', str(number), '--squash', '-R', repo_fullname],
            capture_output=True, text=True, check=True
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def format_pr_age(created_at: str) -> str:
    try:
        created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        delta = datetime.now(timezone.utc) - created
        if delta.days > 0:
            return f"{delta.days}d"
        hours = delta.seconds // 3600
        if hours > 0:
            return f"{hours}h"
        return f"{delta.seconds // 60}m"
    except (ValueError, TypeError):
        return ""


def get_ci_status(pr: dict) -> str:
    checks = pr.get('statusCheckRollup') or []
    if not checks:
        return ""
    states = {c.get('conclusion') or c.get('status', '') for c in checks}
    if 'FAILURE' in states or 'failure' in states:
        return "fail"
    if 'PENDING' in states or 'pending' in states or 'IN_PROGRESS' in states:
        return "pending"
    if 'SUCCESS' in states or 'success' in states:
        return "pass"
    return ""


def close_pr(repo_fullname: str, number: int) -> bool:
    try:
        subprocess.run(
            ['gh', 'pr', 'close', str(number), '-R', repo_fullname],
            capture_output=True, text=True, check=True
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def open_pr_in_browser(url: str) -> None:
    import webbrowser
    webbrowser.open(url)


def _api_url_to_html(api_url: str) -> str:
    if not api_url:
        return ""
    url = api_url.replace("https://api.github.com/repos/", "https://github.com/")
    url = url.replace("/pulls/", "/pull/")
    return url


def fetch_notifications() -> list[dict] | None:
    try:
        result = subprocess.run(
            ['gh', 'api', 'notifications'],
            capture_output=True, text=True, check=True
        )
        raw = json.loads(result.stdout)
        notifications = []
        allowed_reasons = _get_notification_reasons()
        for n in raw:
            if not n.get('unread', False):
                continue
            if n.get('reason', '') not in allowed_reasons:
                continue
            repo = n.get('repository', {})
            subject = n.get('subject', {})
            notifications.append({
                'id': n['id'],
                'reason': n.get('reason', ''),
                'title': subject.get('title', ''),
                'type': subject.get('type', ''),
                'url': _api_url_to_html(subject.get('url', '')),
                'repo': repo.get('name', ''),
                'repo_full': repo.get('full_name', ''),
                'updated_at': n.get('updated_at', ''),
            })
        return notifications
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def mark_notification_read(thread_id: str) -> bool:
    try:
        subprocess.run(
            ['gh', 'api', '--method', 'PATCH', f'notifications/threads/{thread_id}'],
            capture_output=True, text=True, check=True
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False
