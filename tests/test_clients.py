from unittest.mock import patch, MagicMock
import json

from clients.github_client import fetch_open_prs
from clients.calendar_client import fetch_today_events
from clients.llm_client import generate_mnemonic


def test_fetch_open_prs_success():
    mock_prs = [
        {"title": "Fix bug", "number": 42, "repository": {"name": "myrepo"}, "url": "https://github.com/..."}
    ]
    mock_result = MagicMock()
    mock_result.stdout = json.dumps(mock_prs)

    with patch("clients.github_client.subprocess.run", return_value=mock_result):
        prs = fetch_open_prs()
        assert len(prs) == 1
        assert prs[0]["number"] == 42


def test_fetch_open_prs_gh_not_installed():
    with patch("clients.github_client.subprocess.run", side_effect=FileNotFoundError):
        assert fetch_open_prs() is None


def test_fetch_today_events_success():
    mock_result = MagicMock()
    mock_result.stdout = "• Team standup\n• 1:1 with manager\n"

    with patch("clients.calendar_client.subprocess.run", return_value=mock_result):
        events = fetch_today_events()
        assert len(events) == 2
        assert events[0]['title'] == "Team standup"
        assert events[0]['url'] is None


def test_fetch_today_events_with_meet_link():
    mock_result = MagicMock()
    mock_result.stdout = (
        "• Daily Sync\n"
        "    notes: Join with Google Meet: https://meet.google.com/abc-defg-hij\n"
        "    18.00 - 18.15\n"
    )

    with patch("clients.calendar_client.subprocess.run", return_value=mock_result):
        events = fetch_today_events()
        assert len(events) == 1
        assert events[0]['title'] == "Daily Sync"
        assert events[0]['url'] == "https://meet.google.com/abc-defg-hij"
        assert events[0]['time'] == "18.00 - 18.15"


def test_fetch_today_events_no_events():
    mock_result = MagicMock()
    mock_result.stdout = ""

    with patch("clients.calendar_client.subprocess.run", return_value=mock_result):
        events = fetch_today_events()
        assert events == []


def test_fetch_today_events_not_installed():
    with patch("clients.calendar_client.subprocess.run", side_effect=FileNotFoundError):
        assert fetch_today_events() is None


def test_generate_mnemonic_no_api_key():
    with patch.dict("os.environ", {"OPENROUTER_API_KEY": ""}, clear=False):
        result = generate_mnemonic("テスト", "Test")
        assert result is None


def test_generate_mnemonic_success():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test like a test suite!"
    mock_client.chat.completions.create.return_value = mock_response

    with patch("clients.llm_client.get_client", return_value=mock_client):
        result = generate_mnemonic("テスト", "Test")
        assert result == "Test like a test suite!"
