"""Tiny migration runner: applies migrations/NNN_*.sql in order, once each.

Usage: python -m migrations.migrate [db_path]
"""
import glob
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def applied(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
    return {r[0] for r in conn.execute("SELECT version FROM schema_migrations")}


def migrate(conn):
    done = applied(conn)
    ran = []
    for path in sorted(glob.glob(os.path.join(HERE, "[0-9][0-9][0-9]_*.sql"))):
        version = os.path.basename(path).split("_", 1)[0]
        if version in done:
            continue
        with open(path) as f:
            conn.executescript(f.read())
        conn.execute("INSERT INTO schema_migrations VALUES (?, datetime('now'))", (version,))
        conn.commit()
        ran.append(version)
    return ran


def current_version(conn):
    row = conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()
    return row[0] if row else None


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(HERE))
    import settings

    db = sys.argv[1] if len(sys.argv) > 1 else settings.DB_PATH
    c = sqlite3.connect(db)
    c.execute("PRAGMA foreign_keys = ON")
    print("applied:", migrate(c) or "nothing to do")
