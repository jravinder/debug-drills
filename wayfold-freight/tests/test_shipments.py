from wayfold.services import shipments
from tests.conftest import BIG, SMALL, tenant_id


def relay_shipment(conn, tid):
    return conn.execute("""
        SELECT shipment_id FROM legs WHERE tenant_id = ? GROUP BY shipment_id HAVING COUNT(*) >= 3
         ORDER BY shipment_id DESC LIMIT 1""", (tid,)).fetchone()[0]


def test_route_returns_legs_in_order(conn):
    tid = tenant_id(conn, BIG)
    sid = relay_shipment(conn, tid)
    legs = shipments.route(conn, tid, sid)
    assert [l["hop"] for l in legs] == list(range(1, len(legs) + 1))
    assert all(a["to_code"] == b["from_code"] for a, b in zip(legs, legs[1:]))


def test_route_lookup_work_budget(conn):
    # Customer tracking widget calls this on every page view; cost must not grow with the account.
    tid = tenant_id(conn, BIG)
    sid = relay_shipment(conn, tid)
    steps = [0]

    def tick():
        steps[0] += 1
        return 0

    conn.set_progress_handler(tick, 100)
    try:
        legs = shipments.route(conn, tid, sid)
    finally:
        conn.set_progress_handler(None, 0)
    assert len(legs) >= 3
    assert steps[0] * 100 < 50_000, f"route lookup ran ~{steps[0] * 100:,} VM steps"


def test_search_by_pro(conn):
    res = shipments.list_shipments(conn, tenant_id(conn, SMALL), 1, 50, q="10000042")
    assert [r["pro"] for r in res["rows"]] == ["10000042"]


def test_route_api(client):
    r = client.get(f"/api/t/{SMALL}/shipments/10000001/route")
    assert r.status_code == 200
    assert len(r.json()["legs"]) == 1
