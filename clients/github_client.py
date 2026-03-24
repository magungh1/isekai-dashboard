import json
import subprocess


def fetch_open_prs(limit: int = 5) -> list[dict] | None:
    try:
        result = subprocess.run(
            ['gh', 'search', 'prs', '--author=@me', '--state=open',
             '--json', 'title,number,repository,url'],
            capture_output=True, text=True, check=True
        )
        prs = json.loads(result.stdout)
        return prs[:limit]
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def open_pr_in_browser(url: str) -> None:
    import webbrowser
    webbrowser.open(url)
