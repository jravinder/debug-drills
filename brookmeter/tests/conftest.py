import datetime as dt
import os
import sys
import tempfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# Tests run against their own small database, never brookmeter.db.
_TMP = tempfile.mkdtemp(prefix="brookmeter-test-")
os.environ["BROOK_DB_PATH"] = os.path.join(_TMP, "test.db")
os.environ["BROOK_LOG_DIR"] = os.path.join(_TMP, "logs")

SMALL, BIG = "pinecrest-labs", "halvard"


def billing_days(n, after=None):
    """The next n dates (after `after`, default today) that are billing anchor days (1-28)."""
    d = after or dt.date.today()
    out = []
    while len(out) < n:
        d += dt.timedelta(days=1)
        if d.day <= 28:
            out.append(d)
    return out


@pytest.fixture(scope="session", autouse=True)
def database():
    import seed
    seed.build(os.environ["BROOK_DB_PATH"], profile="test")
    yield os.environ["BROOK_DB_PATH"]


@pytest.fixture(scope="session")
def client(database):
    from fastapi.testclient import TestClient
    from brookmeter.app import app
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def conn(database):
    from brookmeter import db
    c = db.connect()
    yield c
    c.close()


def tenant_id(conn, slug):
    return conn.execute("SELECT id FROM tenants WHERE slug = ?", (slug,)).fetchone()[0]
