"""SQLite access. One connection per request; statements are counted for the X-Query-Count header."""
import contextvars
import sqlite3

import settings

# Mutable box so the count survives the hop into FastAPI's threadpool.
_query_box = contextvars.ContextVar("query_box", default=None)


def start_request_counter():
    box = [0]
    _query_box.set(box)
    return box


def _count(_sql):
    box = _query_box.get()
    if box is not None:
        box[0] += 1


def connect(path=None):
    conn = sqlite3.connect(path or settings.DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.set_trace_callback(_count)
    return conn


def get_conn():
    """FastAPI dependency."""
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


def tenant_by_slug(conn, slug):
    return conn.execute("SELECT * FROM tenants WHERE slug = ?", (slug,)).fetchone()


def all_tenants(conn):
    return conn.execute("SELECT id, slug, name FROM tenants ORDER BY name").fetchall()
