-- ============================================================
-- Supabase Schema for isekai-dashboard
-- Run in: Supabase SQL Editor (or locally via supabase db reset)
-- ============================================================

-- Enable UUID extension (needed for Supabase auth if you add user_id later)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- TABLE: quests
-- Daily/weekly/goals to-do list
-- ============================================================
CREATE TABLE IF NOT EXISTS quests (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    category TEXT NOT NULL DEFAULT 'daily',  -- 'daily', 'weekly', 'goals'
    deadline TIMESTAMPTZ,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLE: meta
-- Key-value app state (reset dates, settings, etc.)
-- ============================================================
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- ============================================================
-- TABLE: kana_srs
-- Katakana + Hiragana flashcards with SRS scheduling
-- ============================================================
CREATE TABLE IF NOT EXISTS kana_srs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    word TEXT NOT NULL UNIQUE,
    meaning TEXT NOT NULL,
    mnemonic TEXT,
    level INTEGER NOT NULL DEFAULT 0,
    next_review TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    type TEXT NOT NULL DEFAULT 'katakana'  -- 'katakana' or 'hiragana'
);

-- ============================================================
-- TABLE: english_srs
-- English vocabulary flashcards (GRE-level words)
-- ============================================================
CREATE TABLE IF NOT EXISTS english_srs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    word TEXT NOT NULL UNIQUE,
    definition TEXT NOT NULL,
    example TEXT,
    mnemonic TEXT,
    part_of_speech TEXT NOT NULL DEFAULT 'noun',
    level INTEGER NOT NULL DEFAULT 0,
    next_review TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLE: kanji_srs
-- Kanji flashcards with readings and SRS scheduling
-- ============================================================
CREATE TABLE IF NOT EXISTS kanji_srs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    kanji TEXT NOT NULL UNIQUE,
    kun_reading TEXT,
    on_reading TEXT,
    meaning TEXT NOT NULL,
    mnemonic TEXT,
    level INTEGER NOT NULL DEFAULT 0,
    next_review TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLE: xp_log
-- Experience points event log (quest completion, reviews, etc.)
-- ============================================================
CREATE TABLE IF NOT EXISTS xp_log (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    xp INTEGER NOT NULL,
    source TEXT NOT NULL,
    created_date TEXT NOT NULL  -- ISO date string (YYYY-MM-DD), not TIMESTAMPTZ, to match app logic
);

-- ============================================================
-- TABLE: notes
-- Free-form user notes
-- ============================================================
CREATE TABLE IF NOT EXISTS notes (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- INDEXES — Optimize common query patterns
-- ============================================================

-- SRS: fetch due cards by level (ascending) and type
CREATE INDEX IF NOT EXISTS idx_kana_srs_next_review ON kana_srs (level ASC, next_review ASC);
CREATE INDEX IF NOT EXISTS idx_kana_srs_type ON kana_srs (type);

-- SRS: fetch due English cards by level
CREATE INDEX IF NOT EXISTS idx_english_srs_next_review ON english_srs (level ASC, next_review ASC);

-- SRS: fetch due Kanji cards by level
CREATE INDEX IF NOT EXISTS idx_kanji_srs_next_review ON kanji_srs (level ASC, next_review ASC);

-- Quests: category + status + sort_order (used in list queries)
CREATE INDEX IF NOT EXISTS idx_quests_category_status ON quests (category, status, sort_order);

-- XP: date-based aggregation
CREATE INDEX IF NOT EXISTS idx_xp_log_created_date ON xp_log (created_date);

-- ============================================================
-- RLS (Row Level Security) — Enable for future multi-user support
-- ============================================================
-- Uncomment when you add user_id columns and want per-user isolation.
-- For now, leave RLS off so the anon key has full access (single-user app).

-- ALTER TABLE quests ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE meta ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE kana_srs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE english_srs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE kanji_srs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE xp_log ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE notes ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- SEED DATA (optional — run only on fresh DB)
-- ============================================================
-- The Python db_init.py script handles seeding. If you prefer
-- SQL seeding, paste the INSERT statements here or use Supabase
-- Dashboard → Table Editor → Insert Row.

-- Example minimal seeds:
-- INSERT INTO quests (title, status, category) VALUES
--   ('Review Katakana Flashcards', 'pending', 'daily'),
--   ('Review Hiragana Flashcards', 'pending', 'daily'),
--   ('Read an ML paper', 'pending', 'daily'),
--   ('Check GitHub PRs', 'pending', 'weekly'),
--   ('Review English Vocabulary', 'pending', 'weekly'),
--   ('Catch up on ML training/inference fundamentals', 'pending', 'goals');

-- INSERT INTO meta (key, value) VALUES ('last_daily_reset', ''), ('last_weekly_reset', '');

-- ============================================================
-- DONE
-- Verify with: SELECT * FROM information_schema.tables WHERE table_schema = 'public';
-- ============================================================