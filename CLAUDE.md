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

- **Daily Quests** — To-do list with categories (daily/weekly/goals), color-coded by category, persisted in SQLite. Daily quests auto-reset each day.
- **XP / Level System** — Earn XP from quests (+10), SRS reviews (+5), and pomodoro sessions (+25). Level progress bar shown below header. Includes daily streak tracker.
- **Keyboard Navigation** — `g`+`1`-`6` (vim-style) to jump between widgets. `a` for quick-add quest. `[`/`]` to cycle SRS tabs. `n`/`p` to cycle YouTube tabs when Now Playing is focused.
- **Pomodoro Timer** — Customizable durations (25/5, 50/10, 15/3 presets) with FGO motivational quotes. Tracks daily sessions (persisted across restarts), awards XP, sends macOS notifications on completion. Visual countdown progress bar with phase-colored background tint.
- **SRS Flashcards** — Tabbed widget with 5 tabs:
  - **Katakana** — 3-state flip (kana → romaji + alternate script → meaning + mnemonic)
  - **Hiragana** — Same 3-state flip, 190+ native Japanese words
  - **English** — 2-state flip (word + POS → definition + example + mnemonic), 70 GRE-level words
  - **Kanji** — 2-state flip (kanji → readings + meaning + mnemonic), JLPT N5/N4
  - **Stats** — Overview of all SRS decks: level distribution, due counts, forecast
  - SRS intervals: New → 4h → 1d → 3d → 1w → 1mo
  - 4-level grading: Again (reset) / Hard (stay) / Good (+1) / Easy (+2)
  - Color-coded level badges and progress bars on each card
- **Pull Requests** — Fetches open PRs and review-requested PRs via `gh` CLI (auto-refreshes every 5 min). Shows CI status and PR age. `a` to approve review-requested PRs. Opens in browser on Enter.
- **Calendar** — Today's macOS calendar events via `icalBuddy` (auto-refreshes every 2 min). Time-relative coloring (green=now, yellow=soon, gray=past). Shows countdown to next meeting. Green "Meet" button on events with Google Meet/Zoom/Teams links.
- **Now Playing** — Shows current YouTube/YouTube Music track from browser (AppleScript), with play/pause toggle and playback progress bar. Supports multiple YouTube tabs: auto-prioritizes the playing tab, with `n`/`p` to cycle between tabs.
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
