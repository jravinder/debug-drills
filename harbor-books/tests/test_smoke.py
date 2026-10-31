import pytest

from tests.conftest import BIG, SMALL


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["tenants"] == 2


def test_root_redirects_to_a_dashboard(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (302, 307)
    assert r.headers["location"].endswith("/dashboard")


@pytest.mark.parametrize("slug", [SMALL, BIG])
@pytest.mark.parametrize("page", ["dashboard", "stores", "sales", "inventory"])
def test_pages_render(client, slug, page):
    r = client.get(f"/t/{slug}/{page}")
    assert r.status_code == 200
    assert "Harbor Books" in r.text
    assert "X-Query-Count" in r.headers


def test_store_detail_renders(client):
    r = client.get(f"/t/{SMALL}/stores/TW-001")
    assert r.status_code == 200
    assert "Top titles" in r.text


def test_unknown_tenant_404(client):
    assert client.get("/t/nobody/dashboard").status_code == 404
    assert client.get("/api/t/nobody/revenue-series").status_code == 404


def test_unknown_store_404(client):
    assert client.get(f"/t/{SMALL}/stores/XX-999").status_code == 404


def test_tenant_isolation_on_stores_page(client):
    html = client.get(f"/t/{SMALL}/stores").text
    assert "TW-001" in html and "LF-001" not in html


def test_migrations_are_idempotent(conn):
    from migrations.migrate import migrate
    assert migrate(conn) == []


def test_foreign_keys_enforced(conn):
    import sqlite3
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO stores (tenant_id, code, name, city, region, opened_on, sq_ft) "
                     "VALUES (999, 'X', 'X', 'X', 'X', '2020-01-01', 1)")
