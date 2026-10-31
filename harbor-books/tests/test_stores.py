import math
import re

from harbor.services import stores
from tests.conftest import BIG, SMALL, tenant_id

ROW_CODE = re.compile(r'<span class="code">(LF-\d{3})</span>')


def test_filter_by_region(conn):
    tid = tenant_id(conn, BIG)
    res = stores.list_stores(conn, tid, region="Mountain", per_page=500)
    assert res["stores"] and all(s["region"] == "Mountain" for s in res["stores"])


def test_search_by_code(conn):
    tid = tenant_id(conn, BIG)
    res = stores.list_stores(conn, tid, q="LF-007")
    assert [s["code"] for s in res["stores"]] == ["LF-007"]


def test_small_tenant_single_page(conn):
    res = stores.list_stores(conn, tenant_id(conn, SMALL))
    assert res["page_count"] == 1 and len(res["stores"]) == 3


def test_every_store_is_reachable_through_pagination(conn):
    tid = tenant_id(conn, BIG)
    total = conn.execute("SELECT COUNT(*) FROM stores WHERE tenant_id=?", (tid,)).fetchone()[0]
    first = stores.list_stores(conn, tid)
    assert first["page_count"] == math.ceil(total / first["per_page"])
    seen = set()
    for p in range(1, first["page_count"] + 1):
        seen |= {s["code"] for s in stores.list_stores(conn, tid, page=p)["stores"]}
    assert len(seen) == total


def test_sort_by_revenue_ranks_across_all_pages(conn):
    tid = tenant_id(conn, BIG)
    everything = stores.list_stores(conn, tid, sort="revenue", per_page=1000)["stores"]
    best = max(everything, key=lambda s: s["revenue_cents"])
    page1 = stores.list_stores(conn, tid, sort="revenue", page=1)["stores"]
    assert page1[0]["code"] == best["code"]


def test_stores_page_query_budget(client):
    r = client.get(f"/t/{BIG}/stores?sort=revenue")
    assert r.status_code == 200
    assert len(ROW_CODE.findall(r.text)) == 25
    assert int(r.headers["X-Query-Count"]) <= 10
