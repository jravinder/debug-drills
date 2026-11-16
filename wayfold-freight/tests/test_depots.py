import pytest

from wayfold.services import depots, metrics
from tests.conftest import BIG, SMALL, tenant_id


def ledger_deliveries(conn, tid, days, region=""):
    since, until = metrics.window(days)
    sql = ("SELECT COUNT(*) FROM stops st JOIN depots d ON d.id = st.depot_id WHERE st.tenant_id = ? "
           "AND st.kind = 'delivery' AND st.arrived_at >= ? AND st.arrived_at < ?")
    params = [tid, since, until]
    if region:
        sql += " AND d.region = ?"
        params.append(region)
    return conn.execute(sql, params).fetchone()[0]


def test_every_depot_listed(conn):
    tid = tenant_id(conn, BIG)
    rows = depots.list_depots(conn, tid, 30)
    assert len(rows) == conn.execute("SELECT COUNT(*) FROM depots WHERE tenant_id=?", (tid,)).fetchone()[0]


def test_region_filter(conn):
    tid = tenant_id(conn, BIG)
    rows = depots.list_depots(conn, tid, 30, region="Mountain")
    assert rows and all(r["region"] == "Mountain" for r in rows)
    assert sum(r["deliveries"] for r in rows) == ledger_deliveries(conn, tid, 30, "Mountain")


@pytest.mark.parametrize("slug", [SMALL, BIG])
def test_scorecard_follows_selected_window(conn, slug):
    tid = tenant_id(conn, slug)
    for days in (7, 90, 30):
        rows = depots.list_depots(conn, tid, days)
        assert sum(r["deliveries"] for r in rows) == ledger_deliveries(conn, tid, days), f"{days}-day window"


def test_depots_page_lists_small_tenant(client):
    r = client.get(f"/t/{SMALL}/depots?days=7")
    assert r.status_code == 200
    assert r.text.count('<span class="code">BH-') == 3
