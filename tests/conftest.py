import sqlite3
import sys
import os

import pytest

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import core.db as db_module


@pytest.fixture(autouse=True)
def use_temp_db(tmp_path):
    """Redirect all DB operations to a temporary in-memory-like SQLite file."""
    test_db = str(tmp_path / "test_isekai.db")
    db_module.DB_PATH = test_db
    # Reset shared connection so it reconnects to the new path
    db_module._conn = None

    # Create tables
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
            type TEXT DEFAULT 'katakana'
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
            next_review TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            next_review TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

    yield

    db_module._conn = None
