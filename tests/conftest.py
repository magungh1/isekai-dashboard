import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import core.db as db_module


@pytest.fixture(autouse=True)
def use_temp_db(tmp_path, monkeypatch):
    """Redirect all DB operations to a temporary SQLite file."""
    test_db = str(tmp_path / "test_isekai.db")

    monkeypatch.setattr(db_module, "_get_db_url", lambda: test_db)
    db_module._pg_pool = None

    conn = db_module.get_shared_connection()
    conn.execute("DROP TABLE IF EXISTS srs_reviews")
    conn.execute("DROP TABLE IF EXISTS quests")
    conn.execute("DROP TABLE IF EXISTS meta")
    conn.execute("DROP TABLE IF EXISTS kana_srs")
    conn.execute("DROP TABLE IF EXISTS english_srs")
    conn.execute("DROP TABLE IF EXISTS kanji_srs")
    conn.execute("DROP TABLE IF EXISTS xp_log")
    conn.execute("DROP TABLE IF EXISTS notes")
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
    conn.commit()
    db_module.release_connection(conn)

    yield

    db_module._pg_pool = None
    if os.path.exists(test_db):
        os.remove(test_db)
