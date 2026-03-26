# Isekai Dev Dashboard ⚔️

A terminal-based developer dashboard built with [Textual](https://textual.textualize.io/), designed as a daily driver for ML Engineers. Features interactive to-do quests, a Pomodoro timer, SRS flashcards for Japanese and English vocabulary with AI-generated mnemonics, live GitHub PR tracking, and macOS calendar integration.

## Quick Start

```bash
# Install dependencies
uv sync

# Initialize the database (seeds kana + English vocab)
make init

# Run the dashboard
make run
```

## Features

### Daily Quests (To-Do List)
- **Add quests**: Type in the input field at the bottom and press `Enter`
- **Toggle status**: Select a quest and press `Enter` to mark it done/pending
- All quests are persisted in SQLite

### Pomodoro Timer
- 25-minute work / 5-minute break timer
- Features motivational quotes from Fate/Grand Order (FGO)
- `s`: Start/Pause, `r`: Reset

### SRS Flashcards (Tabbed Widget)

The bottom-right panel has four tabs: **Katakana**, **Hiragana**, **English**, and **Kanji**.

#### Kana SRS
- 3-state flip: **kana word** → **romaji + alternate script** → **meaning + mnemonic**
- Supports both katakana and hiragana with 450+ words
- Shows katakana↔hiragana conversion and romaji transliteration
- `space`: Flip card, `1`: Miss, `2`: Good

#### English Vocab SRS
- 2-state flip: **word + part of speech** → **definition + example + mnemonic**
- 70 advanced English words seeded (ephemeral, ubiquitous, perspicacious, etc.)
- `space`: Flip card, `1`: Miss, `2`: Good

#### Kanji SRS
- 2-state flip: **Kanji** → **Onyomi/Kunyomi + Meaning + Mnemonic**
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

## Vocabulary Import & Extraction

### Japanese Vocabulary

Extract from a text or markdown file:
```bash
make extract FILE=novel.md
```

Extract from direct text input:
```bash
make extract-text TEXT="日本語の文です"
```

### English Vocabulary

Extract from a text or markdown file:
```bash
make extract-english FILE=article.md
```

Extract from direct text input:
```bash
make extract-english-text TEXT="The ephemeral nature of clouds"
```

### Ingest Custom Vocabulary

Ingest CSV files into the DB:
```bash
# Auto-detect format
make ingest FILE=vocab.csv
```

*(Legacy support)* Force specific formats using `import_vocab.py`:
```bash
uv run python import_vocab.py --type kana kana_words.csv
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
├── Makefile                     # Make commands for easy execution
├── db_init.py                   # Database schema + seed script
├── import_vocab.py              # Legacy CSV vocabulary importer
├── ingest_csv.py                # CSV vocabulary ingestion script
├── vocab_extractor.py           # Japanese vocabulary extraction from text/files
├── english_vocab_extractor.py   # English vocabulary extraction from text/files
├── core/
│   ├── db.py                    # SQLite connection manager
│   ├── models.py                # Data classes (Quest, KanaCard, VocabCard, KanjiCard)
│   └── kana_romaji.py           # Kana↔romaji transliteration + script conversion
├── services/
│   ├── quests_service.py        # Quest CRUD operations
│   ├── srs_service.py           # Kana SRS review logic + intervals
│   ├── english_srs_service.py   # English SRS review logic + intervals
│   └── kanji_srs_service.py     # Kanji SRS review logic + intervals
├── clients/
│   ├── llm_client.py            # OpenRouter API (mnemonic generation)
│   ├── github_client.py         # gh CLI wrapper
│   └── calendar_client.py       # icalBuddy wrapper
├── ui/
│   ├── styles.tcss              # Textual CSS theme
│   └── widgets/
│       ├── daily_quests.py      # Interactive quest ListView + Input
│       ├── kana_card.py         # 3-state kana flashcard
│       ├── english_card.py      # 2-state English flashcard
│       ├── kanji_card.py        # 2-state Kanji flashcard
│       ├── srs_tabs.py          # Tabbed container for SRS flashcards
│       ├── pull_requests.py     # PR list with browser opening
│       ├── calendar.py          # Today's events ListView
│       └── pomodoro.py          # Pomodoro timer with FGO quotes
└── tests/
    ├── conftest.py              # Temp DB fixture
    ├── test_quests_service.py   # Quest CRUD tests
    ├── test_srs_service.py      # Kana SRS tests
    ├── test_english_srs_service.py  # English SRS tests
    ├── test_kanji_srs_service.py    # Kanji SRS tests
    └── test_clients.py          # Client mock tests
```

### Key Design Decisions

- **SQLite with `check_same_thread=False`**: Textual uses `@work(thread=True)` for non-blocking I/O. A shared connection with threading disabled avoids creating new connections per query.
- **`call_from_thread`**: All UI updates from background workers go through Textual's thread-safe callback mechanism.
- **Graceful degradation**: Missing `gh`, `icalBuddy`, or OpenRouter API key won't crash the app — each widget shows a fallback message.
- **Domain-driven modules**: `services/` handles business logic, `clients/` wraps external tools, `ui/widgets/` owns presentation.

## Running Tests

```bash
make test
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
| `Tab`   | SRS widget        | Switch tabs               |
| `s`     | Pomodoro          | Start / Pause timer       |
| `r`     | Pomodoro          | Reset timer               |
| `Enter` | Quest list        | Toggle quest done/pending |
| `Enter` | PR list           | Open PR in browser        |
| `q`     | Anywhere          | Quit                      |
