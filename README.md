# Isekai Dev Dashboard ⚔️

A terminal-based developer dashboard built with [Textual](https://textual.textualize.io/), designed as a daily driver for ML Engineers. Features interactive to-do quests, SRS Japanese flashcards with AI-generated mnemonics, live GitHub PR tracking, and macOS calendar integration.

## Quick Start

```bash
# Install dependencies
uv sync

# Initialize the database (seeds from vocab_katakana.json if available)
uv run python db_init.py

# Run the dashboard
uv run python main.py
```

## Features

### Daily Quests (To-Do List)
- **Add quests**: Type in the input field at the bottom and press `Enter`
- **Toggle status**: Select a quest and press `Enter` to mark it done/pending
- All quests are persisted in SQLite

### Kana SRS Flashcards
- Shows cards due for review using a spaced repetition algorithm
- **`Space`**: Flip the card to reveal the meaning
- **`1`**: Mark as "Miss" (resets SRS level, card comes back soon)
- **`2`**: Mark as "Good" (advances SRS level, delays next review)
- Automatically generates mnemonics via OpenRouter LLM (if API key is set)
- SRS intervals: New -> 4h -> 1d -> 3d -> 1w -> 1mo

### Pull Requests
- Fetches your open PRs via `gh` CLI
- Press `Enter` on a PR to open it in your browser
- Requires: [GitHub CLI](https://cli.github.com/) (`gh auth login`)

### Calendar
- Shows today's events from macOS Calendar
- Requires: `brew install icalbuddy`

## OpenRouter LLM Setup (Optional)

Set your API key to enable auto-generated mnemonics for flashcards:

```bash
export OPENROUTER_API_KEY="sk-or-..."
```

Uses the free `google/gemini-2.5-pro-exp-03-25:free` model via OpenRouter.

## Architecture

```
isekai-dashboard/
├── main.py                  # App entry point, grid layout
├── db_init.py               # Database schema + seed script
├── core/
│   ├── db.py                # SQLite connection manager
│   └── models.py            # Data classes (Quest, KanaCard)
├── services/
│   ├── quests_service.py    # Quest CRUD operations
│   └── srs_service.py       # SRS review logic + intervals
├── clients/
│   ├── llm_client.py        # OpenRouter API (mnemonic generation)
│   ├── github_client.py     # gh CLI wrapper
│   └── calendar_client.py   # icalBuddy wrapper
└── ui/
    ├── styles.tcss           # Textual CSS theme
    └── widgets/
        ├── daily_quests.py   # Interactive quest ListView + Input
        ├── kana_card.py      # SRS flashcard with flip mechanic
        ├── pull_requests.py  # PR list with browser opening
        └── calendar.py       # Today's events ListView
```

### Key Design Decisions

- **SQLite with `check_same_thread=False`**: Textual uses `@work(thread=True)` for non-blocking I/O. A shared connection with threading disabled avoids creating new connections per query.
- **`call_from_thread`**: All UI updates from background workers go through Textual's thread-safe callback mechanism.
- **Graceful degradation**: Missing `gh`, `icalBuddy`, or OpenRouter API key won't crash the app — each widget shows a fallback message.
- **Domain-driven modules**: `services/` handles business logic, `clients/` wraps external tools, `ui/widgets/` owns presentation.

## Dependencies

- `textual` — TUI framework
- `openai` — OpenRouter API client (via base_url override)
- `icalevents` — Calendar event parsing

## Keyboard Shortcuts

| Key     | Context        | Action                  |
|---------|----------------|-------------------------|
| `Space` | Kana widget    | Flip flashcard          |
| `1`     | Kana (flipped) | Rate as Miss            |
| `2`     | Kana (flipped) | Rate as Good            |
| `Enter` | Quest list     | Toggle quest done/pending |
| `Enter` | PR list        | Open PR in browser      |
| `q`     | Anywhere       | Quit                    |
