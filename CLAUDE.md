# Isekai Dev Dashboard

Terminal-based developer dashboard built with Textual + SQLite, managed with `uv`.

## Running

```bash
make run       # Run the dashboard
make init      # Initialize DB and seed vocab
make test      # Run all tests
make clean     # Clean caches
```

See `make help` for all available commands.

## Features

- **Daily Quests** — To-do list with categories (daily/weekly/goals), persisted in SQLite. Daily quests auto-reset each day.
- **Pomodoro Timer** — 25min work / 5min break with FGO motivational quotes.
- **SRS Flashcards** — Tabbed widget with 4 tabs:
  - **Katakana** — 3-state flip (kana → romaji + alternate script → meaning + mnemonic)
  - **Hiragana** — Same 3-state flip, 190+ native Japanese words
  - **English** — 2-state flip (word + POS → definition + example + mnemonic), 70 GRE-level words
  - **Kanji** — 2-state flip (kanji → readings + meaning + mnemonic), JLPT N5/N4
  - SRS intervals: New → 4h → 1d → 3d → 1w → 1mo
- **Pull Requests** — Fetches open PRs via `gh` CLI, opens in browser on Enter.
- **Calendar** — Today's macOS calendar events via `icalBuddy`, with meeting link support.
- **Now Playing** — Shows current YouTube/YouTube Music track from browser (AppleScript), with play/pause toggle.
- **LLM Mnemonics** — Auto-generates mnemonics via OpenRouter API (optional, set `OPENROUTER_API_KEY`).

## CSV Data Import

### Ingesting vocabulary from CSV

```bash
make ingest FILE=vocab.csv
```

CSV format (no header row, `#` lines are comments):

**Kana (katakana/hiragana):**
```
word,type,meaning
コーヒー,katakana,coffee
さくら,hiragana,cherry blossom
```

**Kanji (5 columns):**
```
kanji,kanji,meaning,kun_reading,on_reading
山,kanji,mountain,やま,サン
```

The `type` column determines the target table: `kanji` → `kanji_srs`, anything else → `kana_srs`. Duplicates are silently skipped.

### Extracting vocabulary from text

```bash
make extract FILE=novel.md
```

Uses LLM to extract Japanese vocabulary from a text/markdown file, deduplicates against existing DB and CSV entries, and outputs a CSV ready for ingestion.
