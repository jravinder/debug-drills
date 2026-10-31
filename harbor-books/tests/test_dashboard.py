from harbor.services import metrics
from tests.conftest import BIG, SMALL, tenant_id


def test_kpis_match_ledger(conn):
    tid = tenant_id(conn, SMALL)
    k = metrics.kpis(conn, tid, 30)
    since, until = metrics.window(30)
    raw = conn.execute("SELECT SUM(qty*unit_price_cents - discount_cents), SUM(qty) FROM sale_lines "
                       "WHERE tenant_id=? AND sold_at>=? AND sold_at<?", (tid, since, until)).fetchone()
    assert k["revenue_cents"] == raw[0]
    assert k["units"] == raw[1]


def test_category_breakdown_sums_to_revenue(conn):
    tid = tenant_id(conn, SMALL)
    total = sum(c["revenue_cents"] for c in metrics.revenue_by_category(conn, tid, 30))
    assert total == metrics.kpis(conn, tid, 30)["revenue_cents"]


def test_dashboard_query_budget_small_tenant(client):
    r = client.get(f"/t/{SMALL}/dashboard")
    assert int(r.headers["X-Query-Count"]) <= 20


def test_dashboard_query_budget_big_tenant(client):
    # Budget agreed with the Lanternfield account team: the dashboard must not scale with store count.
    r = client.get(f"/t/{BIG}/dashboard")
    assert int(r.headers["X-Query-Count"]) <= 20


def test_revenue_series_payload_budget(client):
    # Perf budget for dashboard API calls: 250 KB.
    r = client.get(f"/api/t/{BIG}/revenue-series")
    assert r.status_code == 200
    assert len(r.content) < 250_000, f"revenue-series payload is {len(r.content):,} bytes"


def test_revenue_series_rejects_unbounded_window(client):
    r = client.get(f"/api/t/{BIG}/revenue-series?days=100000")
    assert r.status_code in (200, 422)
    assert len(r.content) < 250_000
