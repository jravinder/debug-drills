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
@pytest.mark.parametrize("page", ["dashboard", "subscriptions", "invoices", "usage"])
def test_pages_render(client, slug, page):
    r = client.get(f"/t/{slug}/{page}")
    assert r.status_code == 200
    assert "Brookmeter" in r.text
    assert "X-Query-Count" in r.headers


def test_invoice_detail_renders(client, conn):
    number = conn.execute("SELECT i.number FROM invoices i JOIN tenants t ON t.id = i.tenant_id "
                          "WHERE t.slug = ? ORDER BY i.id DESC LIMIT 1", (SMALL,)).fetchone()[0]
    r = client.get(f"/t/{SMALL}/invoices/{number}")
    assert r.status_code == 200
    assert number in r.text


def test_unknown_tenant_404(client):
    assert client.get("/t/nobody/dashboard").status_code == 404
    assert client.get("/api/t/nobody/usage-daily").status_code == 404


def test_unknown_invoice_404(client):
    assert client.get(f"/t/{SMALL}/invoices/PCL-9999999").status_code == 404


def test_tenant_isolation_on_invoices_page(client):
    html = client.get(f"/t/{SMALL}/invoices").text
    assert "PCL-" in html and "HVD-" not in html


def test_usage_api_window_is_bounded(client):
    assert client.get(f"/api/t/{BIG}/usage-daily?days=100000").status_code == 422
    body = client.get(f"/api/t/{BIG}/usage-daily?days=7").json()
    assert len(body["series"]) == 7


def test_migrations_are_idempotent(conn):
    from migrations.migrate import migrate
    assert migrate(conn) == []


def test_foreign_keys_enforced(conn):
    import sqlite3
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO customers (tenant_id, name, email, country, created_at) "
                     "VALUES (999, 'X', 'x@example.com', 'US', '2024-01-01')")
