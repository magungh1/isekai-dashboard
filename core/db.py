import os
import sqlite3
import logging

logger = logging.getLogger(__name__)

_use_supabase = bool(os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_KEY"))

_pg_pool = None
_sqlite_path = None


def _get_db_url():
    return _sqlite_path


class _Psycopg2Wrapper:
    def __init__(self, conn):
        self._conn = conn
        self._cur = None

    def execute(self, query, params=None):
        self._cur = self._conn.cursor()
        if params is not None:
            self._cur.execute(query, params)
        else:
            self._cur.execute(query)
        return self

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    def commit(self):
        self._conn.commit()

    @property
    def autocommit(self):
        return self._conn.autocommit

    @autocommit.setter
    def autocommit(self, value):
        self._conn.autocommit = value


class _SqliteWrapper:
    def __init__(self, conn):
        self._conn = conn

    def execute(self, query, params=None):
        translated = query.replace("%s", "?")
        self._cursor = self._conn.cursor()
        if params is not None:
            self._cursor.execute(translated, params)
        else:
            self._cursor.execute(translated)
        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def commit(self):
        if hasattr(self, '_cursor'):
            try:
                self._cursor.fetchall()
            except Exception:
                pass
        self._conn.commit()

    @property
    def autocommit(self):
        return self._conn.isolation_level is None

    @autocommit.setter
    def autocommit(self, value):
        if value:
            self._conn.isolation_level = None
        else:
            self._conn.isolation_level = ""


def _get_pg_pool():
    global _pg_pool
    if _pg_pool is None:
        from config import get_int, get
        import psycopg2
        import psycopg2.pool
        import psycopg2.extras

        host = (os.environ.get('SUPABASE_URL', '')
                .replace('https://', '').replace('http://', '').rstrip('/'))
        password = os.environ.get('SUPABASE_SERVICE_KEY', '')
        port = get_int("db", "port", default=5432)
        sslmode = get("db", "sslmode") or "require"

        db_url = (
            f"host={host}"
            f" dbname=postgres user=postgres"
            f" password={password}"
            f" port={port} sslmode={sslmode}"
        )

        pool_min = get_int("db", "pool_min", default=2)
        pool_max = get_int("db", "pool_max", default=10)
        _pg_pool = psycopg2.pool.ThreadedConnectionPool(
            pool_min, pool_max, db_url,
            cursor_factory=psycopg2.extras.RealDictCursor
        )
        logger.info("Created psycopg2 connection pool (%d-%d)", pool_min, pool_max)
    return _pg_pool


def _get_sqlite_conn(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_shared_connection():
    if _use_supabase:
        pool = _get_pg_pool()
        conn = pool.getconn()
        conn.autocommit = False
        return _Psycopg2Wrapper(conn)

    db_path = _get_db_url()
    if db_path is None:
        db_path = os.environ.get("DATABASE_PATH", "isekai.db")
    conn = _get_sqlite_conn(db_path)
    return _SqliteWrapper(conn)


def release_connection(conn):
    if _use_supabase and _pg_pool:
        _pg_pool.putconn(conn._conn)
    else:
        try:
            conn._conn.close()
        except Exception:
            pass
