# Supabase Migration Plan — isekai-dashboard

## Current SQLite Schema Summary

| Table              | Purpose                              | Row Est. |
|--------------------|--------------------------------------|----------|
| `quests`           | Daily/weekly/goals to-do list        | ~6       |
| `meta`             | Key-value app state (reset dates)    | <10      |
| `kana_srs`         | Katakana + Hiragana flashcards       | ~230     |
| `english_srs`      | English vocabulary flashcards        | ~70      |
| `kanji_srs`        | Kanji flashcards (JLPT N5/N4)        | ~50      |
| `xp_log`           | XP event log                         | grows    |
| `notes`            | Free-form notes                      | optional |

---

## Phase 1 — Supabase Table Creation (SQL below)

Run the SQL in **Supabase SQL Editor** (or via `supabase db reset` locally with Supabase CLI).

## Phase 2 — Data Migration Script

A one-shot Python script (`migrate_sqlite_to_supabase.py`) will:
1. Read every row from the local `isekai.db` SQLite file.
2. Insert into Supabase via the REST API (PostgREST) or `psycopg2` direct connection.
3. Preserve all `id` values so foreign-key-style references in service code remain valid.

## Phase 3 — Code Changes

### Files to modify (no structural rewrite needed):

| File                        | Change                                                   |
|-----------------------------|----------------------------------------------------------|
| `core/db.py`                | Replace `sqlite3` with `psycopg2` or Supabase client    |
| `db_init.py`                | Replace with Supabase schema init (or remove entirely)  |
| `import_vocab.py`           | Update `sqlite3.IntegrityError` → `psycopg2.IntegrityError` |
| `ingest_csv.py`             | Same as above + connection method swap                   |
| `tests/conftest.py`         | Use Supabase test DB or keep SQLite for unit tests       |
| `services/*.py`             | Only `db_lock` + connection calls change (see notes)     |

### Key behavioral differences to handle:

1. **AUTOINCREMENT → SERIAL/IDENTITY**  
   Supabase auto-creates `id` as `bigserial`. Explicit inserts must either omit `id` or use `OVERRIDING SYSTEM VALUE`.

2. **Threading / Concurrency**  
   PostgreSQL handles concurrent connections natively — **`db_lock` becomes optional** but harmless to keep. Swap `check_same_thread=False` for a connection pool or `psycopg2.pool.ThreadedConnectionPool`.

3. **Timestamps**  
   `CURRENT_TIMESTAMP` → `NOW()` (identical behavior). Use `TIMESTAMPTZ` for timezone-aware storage.

4. **IntegrityError namespace**  
   `sqlite3.IntegrityError` → `psycopg2.errors.UniqueViolation`.

5. **Row Level Security (RLS)**  
   Enable RLS on all tables. For single-user mode, add a policy granting full access to `anon` key. For future multi-user, add `user_id` column + per-user policies.

6. **Supabase client library**  
   Option A: Use `psycopg2` directly (minimal code change, keeps existing `conn.execute()` pattern).  
   Option B: Use `supabase-py` (`.from_table().select()` etc.) — requires rewriting all queries.  
   **Recommendation:** Option A for migration. Low friction, keeps all service logic intact.

7. **Connection pooling**  
   Supabase provides a Pooler connection string (`?pgbouncer=true`). Use this in production to avoid exhausting serverless connections.

## Phase 4 — Rollback Strategy

- Keep `isekai.db` as fallback. If Supabase connection fails, fall back to SQLite with a config flag.
- `db_init.py` seeds from JSON — this works unchanged for a fresh Supabase DB too (just slower, due to HTTP overhead per insert).

## Prerequisites Before Applying

1. Create a Supabase project (free tier is sufficient: 500 MB DB, plenty for this dataset).
2. Note your **Project URL** and `anon` / `service_role` keys from **Settings → API**.
3. Install locally (optional, for testing): `supabase CLI` → `supabase init` + `supabase db start`.
4. Set environment variables:
   ```bash
   export SUPABASE_URL="https://your-ref.supabase.co"
   export SUPABASE_ANON_KEY="your-anon-key"
   export SUPABASE_SERVICE_KEY="your-service-key"
   ```

---

## Supabase Schema SQL

See `supabase_schema.sql` for the full DDL.