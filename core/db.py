import os
import re
import sqlite3
import logging
import requests
from contextlib import contextmanager

logger = logging.getLogger(__name__)

_use_supabase = bool(os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_KEY"))


class _Row(dict):
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(super().values())[key]
        return super().__getitem__(key)


def _wrap_rows(data):
    if isinstance(data, list):
        return [_Row(r) if isinstance(r, dict) else r for r in data]
    if isinstance(data, dict):
        return _Row(data)
    return data


_sqlite_path = None

def _get_db_url():
    return _sqlite_path

_SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
_SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
_SUPABASE_HEADERS = {
    "apikey": _SUPABASE_KEY,
    "Authorization": f"Bearer {_SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}


class _SupabaseRestCursor:
    def __init__(self):
        self._results = []
        self._rowcount = 0

    def execute(self, query, params=None):
        query = query.strip()
        upper = query.upper()

        if upper.startswith("CREATE"):
            return self

        if upper.startswith("SELECT"):
            return self._select(query, params)

        if upper.startswith("INSERT"):
            return self._insert(query, params)

        if upper.startswith("UPDATE"):
            return self._update(query, params)

        if upper.startswith("DELETE"):
            return self._delete(query, params)

        return self

    @property
    def lastrowid(self):
        if self._results:
            return self._results[-1].get("id")
        return None

    def fetchone(self):
        return self._results[0] if self._results else None

    def fetchall(self):
        return self._results

    def _parse_table(self, sql):
        m = re.search(r'\bFROM\s+(\w+)', sql, re.I)
        return m.group(1) if m else None

    def _parse_into_table(self, sql):
        m = re.search(r'\bINTO\s+(\w+)', sql, re.I)
        return m.group(1) if m else None

    def _parse_update_table(self, sql):
        m = re.match(r'UPDATE\s+(\w+)', sql, re.I)
        return m.group(1) if m else None

    def _parse_where(self, sql):
        m = re.search(r'\bWHERE\s+(.*?)(?:\s+ORDER|\s+GROUP|\s+LIMIT|\s+RETURNING|\s*$)', sql, re.I | re.DOTALL)
        return m.group(1).strip() if m else None

    def _parse_order(self, sql):
        m = re.search(r'\bORDER\s+BY\s+(.*?)(?:\s+LIMIT|\s*$)', sql, re.I)
        if not m:
            return []
        clause = re.sub(r',?\s*RANDOM\(\)', '', m.group(1)).strip().rstrip(',')
        if not clause:
            return []
        parts = []
        for p in clause.split(","):
            p = p.strip()
            if not p:
                continue
            desc = p.upper().endswith("DESC")
            col = p.split()[0].strip()
            parts.append((col, desc))
        return parts

    def _parse_limit(self, sql, params):
        m = re.search(r'\bLIMIT\s+%s', sql, re.I)
        if m and params:
            return params.pop()
        return None

    def _apply_where(self, query, where_clause, params):
        where_clause = re.sub(r'\b1\s*=\s*1\s+AND\s+', '', where_clause).strip()
        where_clause = re.sub(r'\s+AND\s+1\s*=\s*1', '', where_clause).strip()
        where_clause = re.sub(r'^1\s*=\s*1$', '', where_clause).strip()
        if not where_clause:
            return query

        parts = re.split(r'\s+AND\s+', where_clause)
        for part in parts:
            part = part.strip()
            if not part or part == "1=1":
                continue

            m = re.match(r"(\w+)\s*=\s*%s", part)
            if m:
                query = query.eq(m.group(1), params.pop(0))
                continue

            m = re.match(r"(\w+)\s*=\s*'([^']*)'", part)
            if m:
                query = query.eq(m.group(1), m.group(2))
                continue

            m = re.match(r'(\w+)\s*!=\s*%s', part)
            if m:
                query = query.neq(m.group(1), params.pop(0))
                continue

            m = re.match(r'(\w+)\s*<=\s*%s', part)
            if m:
                query = query.lte(m.group(1), params.pop(0))
                continue

            m = re.match(r'(\w+)\s*>=\s*%s', part)
            if m:
                query = query.gte(m.group(1), params.pop(0))
                continue

        return query

    def _select(self, sql, params):
        params = list(params or [])

        rpc_match = re.match(r'SELECT\s+\*\s+FROM\s+(\w+)\s*\(([^)]*)\)', sql, re.I)
        if rpc_match:
            return self._rpc(rpc_match.group(1), params)

        table = self._parse_table(sql)
        if not table:
            return self

        is_count = bool(re.match(r'SELECT\s+COUNT\(\*\)', sql, re.I))
        is_sum = bool(re.match(r'SELECT\s+COALESCE\(SUM\((\w+)\)', sql, re.I))
        is_distinct = bool(re.match(r'SELECT\s+DISTINCT\s+(\w+)', sql, re.I))
        is_group = bool(re.search(r'\bGROUP\s+BY\b', sql, re.I))

        sum_col = None
        if is_sum:
            sum_col = re.match(r'SELECT\s+COALESCE\(SUM\((\w+)\)', sql, re.I).group(1)
        dist_col = None
        if is_distinct:
            dist_col = re.match(r'SELECT\s+DISTINCT\s+(\w+)', sql, re.I).group(1)
        group_col = None
        if is_group:
            gm = re.search(r'\bGROUP\s+BY\s+(\w+)', sql, re.I)
            if gm:
                group_col = gm.group(1)
            sel_m = re.match(r'SELECT\s+(\w+),\s*COUNT\(\*\)', sql, re.I)
            group_col = sel_m.group(1) if sel_m else group_col

        url = f"{_SUPABASE_URL}/rest/v1/{table}"
        req_params = {"select": "*"}

        if is_count:
            req_params["select"] = "*"
        elif is_sum and sum_col:
            req_params["select"] = sum_col
        elif is_distinct and dist_col:
            req_params["select"] = dist_col
        elif is_group and group_col:
            req_params["select"] = group_col

        where = self._parse_where(sql)
        filters = []
        if where:
            remaining = list(params)
            filters = self._build_filters(where, remaining)
            params = remaining

        for f in filters:
            req_params[f[0]] = f[1]

        order_parts = self._parse_order(sql)
        if order_parts:
            req_params["order"] = ",".join(
                f"{col}.desc" if desc else col for col, desc in order_parts
            )

        limit = self._parse_limit(sql, params)
        if limit is not None:
            req_params["limit"] = limit

        get_headers = {k: v for k, v in _SUPABASE_HEADERS.items() if k != "Content-Type"}
        if is_count:
            get_headers["Prefer"] = "count=exact"
            req_params["select"] = "id"

        r = requests.get(url, headers=get_headers, params=req_params, timeout=30)
        r.raise_for_status()

        if is_count:
            cr = r.headers.get("content-range", "*/0")
            total = cr.split("/")[1].strip()
            count = int(total) if total != "*" else 0
            self._results = _wrap_rows([{"count": count}])
        elif is_sum:
            total = sum(row.get(sum_col, 0) or 0 for row in r.json())
            self._results = _wrap_rows([{sum_col: total}])
        elif is_group:
            groups = {}
            for row in r.json():
                key = row.get(group_col)
                groups[key] = groups.get(key, 0) + 1
            self._results = _wrap_rows([{group_col: k, "count": v} for k, v in sorted(groups.items())])
        elif is_distinct:
            seen = list(dict.fromkeys(row.get(dist_col) for row in r.json()))
            self._results = _wrap_rows([{dist_col: v} for v in seen])
        else:
            self._results = _wrap_rows(r.json())

        return self

    def _rpc(self, func_name, params):
        url = f"{_SUPABASE_URL}/rest/v1/rpc/{func_name}"
        payload = {"qid": params[0]} if len(params) == 1 else params
        r = requests.post(url, headers=_SUPABASE_HEADERS, json=payload, timeout=30)
        if not r.ok:
            logger.error("RPC %s failed [%d]: %s", func_name, r.status_code, r.text)
        r.raise_for_status()
        data = r.json() if r.text else []
        self._results = _wrap_rows(data if isinstance(data, list) else [data])
        return self

    def _build_filters(self, where_clause, params):
        where_clause = re.sub(r'\b1\s*=\s*1\s+AND\s+', '', where_clause).strip()
        where_clause = re.sub(r'\s+AND\s+1\s*=\s*1', '', where_clause).strip()
        where_clause = re.sub(r'^1\s*=\s*1$', '', where_clause).strip()
        if not where_clause:
            return []

        filters = []
        parts = re.split(r'\s+AND\s+', where_clause)
        for part in parts:
            part = part.strip()
            if not part or part == "1=1":
                continue

            m = re.match(r"(\w+)\s*=\s*%s", part)
            if m:
                filters.append((m.group(1), f"eq.{params.pop(0)}"))
                continue

            m = re.match(r"(\w+)\s*=\s*'([^']*)'", part)
            if m:
                filters.append((m.group(1), f"eq.{m.group(2)}"))
                continue

            m = re.match(r'(\w+)\s*!=\s*%s', part)
            if m:
                filters.append((m.group(1), f"neq.{params.pop(0)}"))
                continue

            m = re.match(r'(\w+)\s*<=\s*%s', part)
            if m:
                filters.append((m.group(1), f"lte.{params.pop(0)}"))
                continue

            m = re.match(r'(\w+)\s*>=\s*%s', part)
            if m:
                filters.append((m.group(1), f"gte.{params.pop(0)}"))
                continue

        return filters

    def _insert(self, sql, params):
        params = list(params or [])
        is_upsert = "ON CONFLICT" in sql.upper()
        table = self._parse_into_table(sql)
        if not table:
            return self

        cols_match = re.search(r'\(([^)]+)\)\s*(?:VALUES|ON CONFLICT)', sql, re.I)
        if not cols_match:
            return self
        cols = [c.strip() for c in cols_match.group(1).split(",")]

        returning = bool(re.search(r'\bRETURNING\b', sql, re.I))

        row = {}
        for col in cols:
            row[col] = params.pop(0)

        url = f"{_SUPABASE_URL}/rest/v1/{table}"

        if is_upsert:
            conflict_match = re.search(r'ON CONFLICT\s*\((\w+)\)', sql, re.I)
            upsert_headers = {**_SUPABASE_HEADERS, "Prefer": "resolution=merge-duplicates"}
            if conflict_match:
                req_params = {"on_conflict": conflict_match.group(1)}
                r = requests.post(url, headers=upsert_headers, json=row, params=req_params, timeout=30)
            else:
                r = requests.post(url, headers=_SUPABASE_HEADERS, json=row, timeout=30)
        else:
            r = requests.post(url, headers=_SUPABASE_HEADERS, json=row, timeout=30)

        r.raise_for_status()
        self._results = _wrap_rows(r.json()) if r.text else []
        return self

    def _insert_batch(self, table, rows):
        url = f"{_SUPABASE_URL}/rest/v1/{table}"
        r = requests.post(url, headers=_SUPABASE_HEADERS, json=rows, timeout=30)
        r.raise_for_status()
        return r.json() if r.text else []

    def _update(self, sql, params):
        params = list(params or [])
        table = self._parse_update_table(sql)
        if not table:
            return self

        set_match = re.search(r'\bSET\s+(.*?)(?:\s+WHERE|\s+RETURNING)', sql, re.I | re.DOTALL)
        if not set_match:
            return self

        set_parts = [s.strip() for s in set_match.group(1).split(",")]
        update_data = {}
        for part in set_parts:
            placeholders = re.findall(r'%s', part)
            if len(placeholders) == 1:
                col = part.split("=")[0].strip()
                update_data[col] = params.pop(0)
            else:
                raise NotImplementedError("CASE WHEN in UPDATE not supported over PostgREST REST API")

        where = self._parse_where(sql)
        url = f"{_SUPABASE_URL}/rest/v1/{table}"

        req_params = {}
        if where:
            filters = self._build_filters(where, params)
            for f in filters:
                req_params[f[0]] = f[1]

        r = requests.patch(url, headers=_SUPABASE_HEADERS, json=update_data, params=req_params, timeout=30)
        r.raise_for_status()
        self._results = _wrap_rows(r.json()) if r.text else []
        return self

    def _delete(self, sql, params):
        params = list(params or [])
        m = re.search(r'\bFROM\s+(\w+)', sql, re.I)
        if not m:
            return self
        table = m.group(1)

        where = self._parse_where(sql)
        url = f"{_SUPABASE_URL}/rest/v1/{table}"

        req_params = {}
        if where:
            filters = self._build_filters(where, params)
            for f in filters:
                req_params[f[0]] = f[1]

        r = requests.delete(url, headers={k: v for k, v in _SUPABASE_HEADERS.items() if k != "Content-Type"}, params=req_params, timeout=30)
        r.raise_for_status()
        self._results = _wrap_rows(r.json()) if r.text else []
        return self


class _SupabaseRestWrapper:
    def __init__(self):
        pass

    def execute(self, query, params=None):
        cur = _SupabaseRestCursor()
        cur.execute(query, params)
        return cur

    def commit(self):
        pass

    def close(self):
        pass


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


def _get_sqlite_conn(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_shared_connection():
    """Return a database connection wrapper (Supabase in production, SQLite for local dev)."""
    if _use_supabase:
        return _SupabaseRestWrapper()
    db_path = _get_db_url() if _get_db_url() else os.environ.get("DATABASE_PATH", "isekai.db")
    conn = _get_sqlite_conn(db_path)
    return _SqliteWrapper(conn)


def release_connection(conn):
    """Release a database connection (no-op for Supabase, closes for SQLite/PG)."""
    if isinstance(conn, _SupabaseRestWrapper):
        return
    try:
        conn._conn.close()
    except Exception:
        pass


@contextmanager
def get_connection():
    """Context manager that yields a database connection and handles cleanup."""
    conn = get_shared_connection()
    try:
        yield conn
    finally:
        release_connection(conn)
