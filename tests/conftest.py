import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import core.db as db_module
from core.migrations import run_migrations


TABLES = [
    "habit_log",
    "habits",
    "notes",
    "xp_log",
    "srs_reviews",
    "quests",
    "kana_srs",
    "english_srs",
    "kanji_srs",
    "meta",
]


def _truncate_tables(conn):
    """Delete all rows from all tables. Order matters for FK constraints."""
    for table in TABLES:
        try:
            conn.execute(f"DELETE FROM {table}")
        except Exception:
            pass
    conn.commit()


def _ensure_schema(conn):
    """Run migrations to ensure all tables exist (Supabase mode)."""
    applied = run_migrations()
    if applied:
        print(f"Applied test migrations: v{', v'.join(str(v) for v in applied)}")


@pytest.fixture(autouse=True)
def use_supabase_db(tmp_path, monkeypatch):
    """Use real Supabase if credentials available, otherwise SQLite fallback."""
    has_supabase = bool(os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_KEY"))

    if has_supabase:
        db_module._pg_pool = None

        conn = db_module.get_shared_connection()
        _ensure_schema(conn)
        _truncate_tables(conn)
        db_module.release_connection(conn)

        yield

        db_module._pg_pool = None
        conn = db_module.get_shared_connection()
        _truncate_tables(conn)
        db_module.release_connection(conn)
    else:
        test_db = str(tmp_path / "test_isekai.db")

        monkeypatch.setattr(db_module, "_get_db_url", lambda: test_db)
        db_module._pg_pool = None

        conn = db_module.get_shared_connection()
        for table in TABLES:
            conn.execute(f"DROP TABLE IF EXISTS {table}")
        conn.commit()
        db_module.release_connection(conn)

        conn = db_module.get_shared_connection()
        conn.execute('''
            CREATE TABLE IF NOT EXISTS quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                category TEXT DEFAULT 'daily',
                deadline TEXT,
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS kana_srs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL UNIQUE,
                meaning TEXT NOT NULL,
                mnemonic TEXT,
                level INTEGER DEFAULT 0,
                next_review TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                type TEXT DEFAULT 'katakana',
                review_count INTEGER DEFAULT 0,
                last_reviewed TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS english_srs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL UNIQUE,
                definition TEXT NOT NULL,
                example TEXT,
                mnemonic TEXT,
                part_of_speech TEXT DEFAULT 'noun',
                level INTEGER DEFAULT 0,
                next_review TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                review_count INTEGER DEFAULT 0,
                last_reviewed TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS kanji_srs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kanji TEXT NOT NULL UNIQUE,
                kun_reading TEXT,
                on_reading TEXT,
                meaning TEXT NOT NULL,
                mnemonic TEXT,
                level INTEGER DEFAULT 0,
                next_review TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                review_count INTEGER DEFAULT 0,
                last_reviewed TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS srs_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deck TEXT NOT NULL,
                card_id INTEGER NOT NULL,
                rating TEXT NOT NULL,
                prev_level INTEGER NOT NULL,
                new_level INTEGER NOT NULL,
                reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS xp_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                xp INTEGER NOT NULL,
                source TEXT NOT NULL,
                created_date TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'general',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
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
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS habit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL REFERENCES habits(id),
                date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'done',
                count INTEGER NOT NULL DEFAULT 1,
                note TEXT,
                UNIQUE(habit_id, date)
            )
        ''')
        conn.commit()
        db_module.release_connection(conn)

        yield

        db_module._pg_pool = None
        if os.path.exists(test_db):
            os.remove(test_db)
