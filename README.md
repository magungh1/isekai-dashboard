# Isekai Dev Dashboard ⚔️

A terminal-based developer dashboard built with [Textual](https://textual.textualize.io/), designed as a daily driver for ML Engineers. Features interactive to-do quests, SRS flashcards for Japanese and English vocabulary with AI-generated mnemonics, live GitHub PR tracking, and macOS calendar integration.

## Quick Start

```bash
# Install dependencies
uv sync

# Initialize the database (seeds kana + English vocab)
uv run python db_init.py

# Run the dashboard
uv run python main.py
```

## Features

### Daily Quests (To-Do List)
- **Add quests**: Type in the input field at the bottom and press `Enter`
- **Toggle status**: Select a quest and press `Enter` to mark it done/pending
- All quests are persisted in SQLite

### SRS Flashcards (Tabbed Widget)

The bottom-right panel has two tabs: **Kana** and **English**.

#### Kana SRS
- 3-state flip: **kana word** → **romaji + alternate script** → **meaning + mnemonic**
- Supports both katakana and hiragana with 450+ words
- Shows katakana↔hiragana conversion and romaji transliteration
- `space`: Flip card, `1`: Miss, `2`: Good

#### English Vocab SRS
- 2-state flip: **word + part of speech** → **definition + example + mnemonic**
- 70 advanced English words seeded (ephemeral, ubiquitous, perspicacious, etc.)
- `space`: Flip card, `1`: Miss, `2`: Good

#### SRS Intervals
New → 4h → 1d → 3d → 1w → 1mo

### Pull Requests
- Fetches your open PRs via `gh` CLI
- Press `Enter` on a PR to open it in your browser
- Requires: [GitHub CLI](https://cli.github.com/) (`gh auth login`)

### Calendar
- Shows today's events from macOS Calendar
- Requires: `brew install icalbuddy`

## Vocabulary Import

Import custom vocabulary from CSV files:

```bash
# Auto-detect format
uv run python import_vocab.py vocab.csv

# Force kana format (word,type,meaning)
uv run python import_vocab.py --type kana kana_words.csv

# Force english format (word,part_of_speech,definition[,example])
uv run python import_vocab.py --type english english_words.csv
```

See `example_vocab.csv` and `example_english_vocab.csv` for format examples.

## OpenRouter LLM Setup (Optional)

Set your API key to enable auto-generated mnemonics for flashcards:

```bash
export OPENROUTER_API_KEY="sk-or-..."
```

Uses the free `google/gemini-2.5-pro-exp-03-25:free` model via OpenRouter.

## Architecture

```
isekai-dashboard/
├── main.py                      # App entry point, 2x2 grid layout
├── db_init.py                   # Database schema + seed script
├── import_vocab.py              # CSV vocabulary importer
├── core/
│   ├── db.py                    # SQLite connection manager
│   ├── models.py                # Data classes (Quest, KanaCard, VocabCard)
│   └── kana_romaji.py           # Kana↔romaji transliteration + script conversion
├── services/
│   ├── quests_service.py        # Quest CRUD operations
│   ├── srs_service.py           # Kana SRS review logic + intervals
│   └── english_srs_service.py   # English SRS review logic + intervals
├── clients/
│   ├── llm_client.py            # OpenRouter API (mnemonic generation)
│   ├── github_client.py         # gh CLI wrapper
│   └── calendar_client.py       # icalBuddy wrapper
├── ui/
│   ├── styles.tcss              # Textual CSS theme
│   └── widgets/
│       ├── daily_quests.py      # Interactive quest ListView + Input
│       ├── kana_card.py         # 3-state kana flashcard (word→romaji→meaning)
│       ├── english_card.py      # 2-state English flashcard (word→definition)
│       ├── srs_tabs.py          # Tabbed container for Kana + English SRS
│       ├── pull_requests.py     # PR list with browser opening
│       └── calendar.py          # Today's events ListView
└── tests/
    ├── conftest.py              # Temp DB fixture
    ├── test_quests_service.py   # Quest CRUD tests
    ├── test_srs_service.py      # Kana SRS tests
    ├── test_english_srs_service.py  # English SRS tests
    └── test_clients.py          # Client mock tests
```

### Key Design Decisions

- **SQLite with `check_same_thread=False`**: Textual uses `@work(thread=True)` for non-blocking I/O. A shared connection with threading disabled avoids creating new connections per query.
- **`call_from_thread`**: All UI updates from background workers go through Textual's thread-safe callback mechanism.
- **Graceful degradation**: Missing `gh`, `icalBuddy`, or OpenRouter API key won't crash the app — each widget shows a fallback message.
- **Domain-driven modules**: `services/` handles business logic, `clients/` wraps external tools, `ui/widgets/` owns presentation.

## Running Tests

```bash
uv run pytest tests/ -v
```

## Dependencies

- `textual` — TUI framework
- `openai` — OpenRouter API client (via base_url override)

## Keyboard Shortcuts

| Key     | Context           | Action                    |
|---------|-------------------|---------------------------|
| `space` | SRS widget        | Flip flashcard            |
| `1`     | SRS (flipped)     | Rate as Miss              |
| `2`     | SRS (flipped)     | Rate as Good              |
| `Tab`   | SRS widget        | Switch Kana/English tabs  |
| `Enter` | Quest list        | Toggle quest done/pending |
| `Enter` | PR list           | Open PR in browser        |
| `q`     | Anywhere          | Quit                      |
