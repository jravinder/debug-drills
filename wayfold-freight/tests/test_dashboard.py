import datetime as dt

import pytest

from wayfold.services import metrics
from tests.conftest import BIG, SMALL, tenant_id

FMT = "%Y-%m-%d %H:%M:%S"


def ledger_on_time(conn, tid, days):
    """Reference count straight from the stop ledger: promised-by is the depot's wall clock."""
    since, until = metrics.window(days)
    rows = conn.execute("""
        SELECT st.window_end, st.arrived_at, d.utc_offset_min
          FROM stops st JOIN depots d ON d.id = st.depot_id
         WHERE st.tenant_id = ? AND st.kind = 'delivery' AND st.arrived_at >= ? AND st.arrived_at < ?""",
                        (tid, since, until)).fetchall()
    on_time = 0
    for r in rows:
        deadline = dt.datetime.strptime(r["window_end"], FMT) - dt.timedelta(minutes=r["utc_offset_min"])
        on_time += dt.datetime.strptime(r["arrived_at"], FMT) <= deadline
    return len(rows), on_time


def test_stop_events_kpi_matches_ledger(conn):
    tid = tenant_id(conn, SMALL)
    since, until = metrics.window(30)
    raw = conn.execute("SELECT COUNT(*) FROM stops WHERE tenant_id=? AND arrived_at>=? AND arrived_at<?",
                       (tid, since, until)).fetchone()[0]
    assert metrics.kpis(conn, tid, 30)["stop_events"] == raw


@pytest.mark.parametrize("slug", [SMALL, BIG])
def test_on_time_rate_matches_stop_ledger(conn, slug):
    tid = tenant_id(conn, slug)
    deliveries, on_time = ledger_on_time(conn, tid, 30)
    k = metrics.kpis(conn, tid, 30)
    assert k["deliveries"] == deliveries
    assert k["on_time"] == on_time, f"dashboard {k['on_time_pct']}% vs ledger {on_time / deliveries * 100:.1f}%"


def test_on_time_series_payload_is_small(client):
    r = client.get(f"/api/t/{BIG}/on-time-series?days=365")
    assert r.status_code == 200
    assert len(r.content) < 60_000


def test_dashboard_query_budget(client):
    for slug in (SMALL, BIG):
        r = client.get(f"/t/{slug}/dashboard")
        assert int(r.headers["X-Query-Count"]) <= 20
