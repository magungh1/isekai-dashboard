"""Schema migration runner for Isekai Dashboard.

Tracks schema version in the 'meta' table and applies numbered migrations.
All migrations must be idempotent and use Supabase-compatible SQL.
"""

import os

from core.db import get_shared_connection, release_connection, _use_supabase


MIGRATIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "migrations")


def _ensure_meta_table(conn):
    conn.execute(
        "CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)"
    )


def get_current_version() -> int:
    """Get current schema version from the meta table."""
    conn = get_shared_connection()
    try:
        _ensure_meta_table(conn)
        row = conn.execute(
            "SELECT value FROM meta WHERE key = 'schema_version'"
        ).fetchone()
        if row and row["value"]:
            return int(row["value"])
        return 0
    finally:
        release_connection(conn)


def set_version(version: int) -> None:
    """Update schema version in the meta table."""
    conn = get_shared_connection()
    try:
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (%s, %s) "
            "ON CONFLICT (key) DO UPDATE SET value = %s",
            ('schema_version', str(version), str(version)),
        )
        conn.commit()
    finally:
        release_connection(conn)


def _read_migration(version: int) -> str:
    """Read the SQL content of a migration file."""
    filepath = os.path.join(MIGRATIONS_DIR, f"{version:03d}.sql")
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"Migration file not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


# In-memory migration SQL for environments without migration files
MIGRATION_SQL = {
    1: """
        -- v1: Add notes table (already existed, made official)
        CREATE TABLE IF NOT EXISTS notes (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            content TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'general',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """,
    2: """
        -- v2: Add review_count to all SRS tables if not exists
        -- (Supabase doesn't support ADD COLUMN IF NOT EXISTS directly,
        --  so we use a DO block)
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'kana_srs' AND column_name = 'review_count'
            ) THEN
                ALTER TABLE kana_srs ADD COLUMN review_count INTEGER NOT NULL DEFAULT 0;
            END IF;
        END $$;

        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'english_srs' AND column_name = 'review_count'
            ) THEN
                ALTER TABLE english_srs ADD COLUMN review_count INTEGER NOT NULL DEFAULT 0;
            END IF;
        END $$;

        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'kanji_srs' AND column_name = 'review_count'
            ) THEN
                ALTER TABLE kanji_srs ADD COLUMN review_count INTEGER NOT NULL DEFAULT 0;
            END IF;
        END $$;
    """,
    3: """
        -- v3: Add indexes for performance
        CREATE INDEX IF NOT EXISTS idx_kana_due ON kana_srs (level ASC, next_review ASC);
        CREATE INDEX IF NOT EXISTS idx_english_due ON english_srs (level ASC, next_review ASC);
        CREATE INDEX IF NOT EXISTS idx_kanji_due ON kanji_srs (level ASC, next_review ASC);
        CREATE INDEX IF NOT EXISTS idx_quests_cat ON quests (category, status, sort_order);
        CREATE INDEX IF NOT EXISTS idx_xp_log_date ON xp_log (created_date);
        CREATE INDEX IF NOT EXISTS idx_notes_category ON notes (category, created_at);
    """,
    4: """
        -- v4: Add toggle_quest RPC function
        CREATE OR REPLACE FUNCTION toggle_quest(qid bigint)
        RETURNS SETOF quests AS $$
          UPDATE quests SET status = CASE WHEN status = 'pending' THEN 'done' ELSE 'pending' END
          WHERE id = qid RETURNING *;
        $$ LANGUAGE sql;
    """,
    5: """
        -- v5: Add habits and habit_log tables
        CREATE TABLE IF NOT EXISTS habits (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            name TEXT NOT NULL,
            icon TEXT NOT NULL DEFAULT '📌',
            category TEXT NOT NULL DEFAULT 'daily',
            xp_reward INTEGER NOT NULL DEFAULT 5,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_date TEXT NOT NULL DEFAULT CURRENT_DATE,
            is_countable INTEGER NOT NULL DEFAULT 0,
            target_count INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS habit_log (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            habit_id BIGINT NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
            date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'done',
            count INTEGER NOT NULL DEFAULT 1,
            note TEXT,
            UNIQUE(habit_id, date)
        );

        CREATE INDEX IF NOT EXISTS idx_habit_log_date ON habit_log (date);
        CREATE INDEX IF NOT EXISTS idx_habit_log_habit ON habit_log (habit_id, date);
        CREATE INDEX IF NOT EXISTS idx_habits_category ON habits (category, sort_order);
    """,
    6: """
        -- v6: Add srs_reviews table (was only in init_schema, not migrations)
        CREATE TABLE IF NOT EXISTS srs_reviews (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            deck TEXT NOT NULL,
            card_id BIGINT NOT NULL,
            rating TEXT NOT NULL,
            prev_level INTEGER NOT NULL DEFAULT 0,
            new_level INTEGER NOT NULL DEFAULT 0,
            reviewed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_srs_reviews_card ON srs_reviews (deck, card_id);
        CREATE INDEX IF NOT EXISTS idx_srs_reviews_date ON srs_reviews (reviewed_at);
    """,
    7: """
        UPDATE quests SET category = 'todo' WHERE category = 'daily';
        UPDATE quests SET category = 'todo' WHERE category = 'weekly';
        UPDATE quests SET category = 'todo' WHERE category = 'goals';
    """,
}


def run_migrations() -> list[int]:
    """Run all pending migrations. Returns list of applied version numbers."""
    if not _use_supabase:
        # Local SQLite gets schema from db_init.py; migrations only for Supabase
        return []

    current = get_current_version()
    applied = []

    versions = sorted(MIGRATION_SQL.keys())
    for version in versions:
        if version > current:
            sql = MIGRATION_SQL[version]
            conn = get_shared_connection()
            try:
                # Split by statement and execute each
                for statement in sql.split(";"):
                    statement = statement.strip()
                    if statement and not statement.startswith("--"):
                        # Strip inline comments
                        lines = [
                            line for line in statement.split("\n")
                            if not line.strip().startswith("--")
                        ]
                        clean = " ".join(lines).strip()
                        if clean:
                            conn.execute(clean)
                conn.commit()
                set_version(version)
                applied.append(version)
                logger = __import__("logging").getLogger(__name__)
                logger.info("Applied migration v%d", version)
            finally:
                release_connection(conn)

    return applied


def init_schema(conn=None, *, close=True) -> None:
    """Create all tables from scratch (used by db_init.py)."""
    own_conn = False
    if conn is None:
        conn = get_shared_connection()
        own_conn = True

    # Quests
    conn.execute("""
        CREATE TABLE IF NOT EXISTS quests (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            category TEXT NOT NULL DEFAULT 'todo',
            deadline TIMESTAMPTZ,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # Kana SRS
    conn.execute("""
        CREATE TABLE IF NOT EXISTS kana_srs (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            word TEXT NOT NULL UNIQUE,
            meaning TEXT NOT NULL,
            mnemonic TEXT,
            level INTEGER NOT NULL DEFAULT 0,
            next_review TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            type TEXT NOT NULL DEFAULT 'katakana',
            review_count INTEGER NOT NULL DEFAULT 0,
            last_reviewed TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # English SRS
    conn.execute("""
        CREATE TABLE IF NOT EXISTS english_srs (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            word TEXT NOT NULL UNIQUE,
            definition TEXT NOT NULL,
            example TEXT,
            mnemonic TEXT,
            part_of_speech TEXT NOT NULL DEFAULT 'noun',
            level INTEGER NOT NULL DEFAULT 0,
            next_review TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            review_count INTEGER NOT NULL DEFAULT 0,
            last_reviewed TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # Kanji SRS
    conn.execute("""
        CREATE TABLE IF NOT EXISTS kanji_srs (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            kanji TEXT NOT NULL UNIQUE,
            kun_reading TEXT,
            on_reading TEXT,
            meaning TEXT NOT NULL,
            mnemonic TEXT,
            level INTEGER NOT NULL DEFAULT 0,
            next_review TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            review_count INTEGER NOT NULL DEFAULT 0,
            last_reviewed TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # SRS reviews log
    conn.execute("""
        CREATE TABLE IF NOT EXISTS srs_reviews (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            deck TEXT NOT NULL,
            card_id BIGINT NOT NULL,
            rating TEXT NOT NULL,
            prev_level INTEGER NOT NULL DEFAULT 0,
            new_level INTEGER NOT NULL DEFAULT 0,
            reviewed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # XP log
    conn.execute("""
        CREATE TABLE IF NOT EXISTS xp_log (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            xp INTEGER NOT NULL,
            source TEXT NOT NULL,
            created_date TEXT NOT NULL
        )
    """)

    # Notes (v1 migration)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            content TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'general',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # Indexes
    conn.execute("CREATE INDEX IF NOT EXISTS idx_kana_due ON kana_srs (level ASC, next_review ASC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_english_due ON english_srs (level ASC, next_review ASC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_kanji_due ON kanji_srs (level ASC, next_review ASC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_quests_cat ON quests (category, status, sort_order)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_xp_log_date ON xp_log (created_date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_notes_category ON notes (category, created_at)")

    # Habits (v5 migration)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            icon TEXT NOT NULL DEFAULT '📌',
            category TEXT NOT NULL DEFAULT 'daily',
            xp_reward INTEGER NOT NULL DEFAULT 5,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_date TEXT NOT NULL DEFAULT (date('now')),
            is_countable INTEGER NOT NULL DEFAULT 0,
            target_count INTEGER NOT NULL DEFAULT 1
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS habit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL REFERENCES habits(id),
            date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'done',
            count INTEGER NOT NULL DEFAULT 1,
            note TEXT,
            UNIQUE(habit_id, date)
        )
    """)

    conn.execute("CREATE INDEX IF NOT EXISTS idx_habit_log_date ON habit_log (date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_habit_log_habit ON habit_log (habit_id, date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_habits_category ON habits (category, sort_order)")

    # Set schema version to latest
    if own_conn:
        max_version = max(MIGRATION_SQL.keys()) if MIGRATION_SQL else 0
        conn.execute(
            "INSERT INTO meta (key, value) VALUES ('schema_version', %s) "
            "ON CONFLICT (key) DO UPDATE SET value = %s",
            (str(max_version), str(max_version)),
        )
        conn.commit()
        release_connection(conn)