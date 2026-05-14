"""Seed Supabase from local isekai.db SQLite via REST API.

Usage:
    uv run python seed_supabase.py
"""

import os
import sqlite3
import requests
from dotenv import load_dotenv

load_dotenv()

SQLITE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "isekai.db")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal,resolution=merge-duplicates",
}


def _rest(method, table, payload=None, params=None):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    r = requests.request(method, url, headers=HEADERS, json=payload, params=params, timeout=30)
    r.raise_for_status()
    if r.text:
        return r.json()
    return None


def _delete_all(table):
    _rest("DELETE", table, params={"id": "gt.0"})


def read_table(sqlite_conn, table):
    sqlite_conn.row_factory = sqlite3.Row
    cur = sqlite_conn.cursor()
    cur.execute(f"SELECT * FROM {table}")
    return [dict(row) for row in cur.fetchall()]


def seed_table(name, rows, batch_size=200):
    if not rows:
        print(f"  {name}: 0 rows (skipped)")
        return

    for row in rows:
        row.pop("id", None)
        row.pop("completed_date", None)

    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        _rest("POST", name, payload=batch)

    print(f"  {name}: {len(rows)} rows")


def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        return

    print("Reading SQLite data...")
    sqlite_conn = sqlite3.connect(SQLITE_PATH)

    tables_order = ["meta", "quests", "kana_srs", "english_srs", "kanji_srs", "xp_log", "notes"]
    data = {}
    for t in tables_order:
        data[t] = read_table(sqlite_conn, t)
    sqlite_conn.close()

    print("Clearing existing Supabase data...")
    for t in reversed(tables_order):
        try:
            _delete_all(t)
        except Exception:
            pass

    print("Seeding data...")
    for t in tables_order:
        try:
            seed_table(t, data[t])
        except Exception as e:
            print(f"  {t}: ERROR - {e}")

    print("\nDone!")


if __name__ == "__main__":
    main()
