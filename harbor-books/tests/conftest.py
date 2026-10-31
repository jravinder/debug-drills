import os
import sys
import tempfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# Tests run against their own small database, never harbor.db.
_TMP = tempfile.mkdtemp(prefix="harbor-test-")
os.environ["HARBOR_DB_PATH"] = os.path.join(_TMP, "test.db")
os.environ["HARBOR_LOG_DIR"] = os.path.join(_TMP, "logs")
os.environ["HARBOR_EXPORT_DIR"] = os.path.join(_TMP, "out")

SMALL, BIG = "tidewater-books", "lanternfield"


@pytest.fixture(scope="session", autouse=True)
def database():
    import seed
    seed.build(os.environ["HARBOR_DB_PATH"], profile="test")
    yield os.environ["HARBOR_DB_PATH"]


@pytest.fixture(scope="session")
def client(database):
    from fastapi.testclient import TestClient
    from harbor.app import app
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def conn(database):
    from harbor import db
    c = db.connect()
    yield c
    c.close()


def tenant_id(conn, slug):
    return conn.execute("SELECT id FROM tenants WHERE slug = ?", (slug,)).fetchone()[0]
