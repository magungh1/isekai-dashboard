import os
import psycopg2
import psycopg2.pool

# ── Supabase connection ─────────────────────────────────────────
DB_URL = (
    f"host={os.environ['SUPABASE_URL'].replace('https://', '').replace('http://', '').rstrip('/')}"
    f" dbname=postgres user=postgres"
    f" password={os.environ['SUPABASE_SERVICE_KEY']}"
    f" port=5432 sslmode=require"
)

_pool = psycopg2.pool.ThreadedConnectionPool(2, 10, DB_URL)


def get_shared_connection():
    conn = _pool.getconn()
    conn.autocommit = False
    return conn


def release_connection(conn):
    _pool.putconn(conn)