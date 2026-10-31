"""Store listing, per-store performance and store detail."""
import datetime as dt

import settings
from harbor.services.metrics import NET, window

SORTS = {
    "name": ("name", False),
    "code": ("code", False),
    "region": ("region", False),
    "revenue": ("revenue_cents", True),
    "units": ("units", True),
    "low_stock": ("low_stock", True),
}


def store_performance(conn, tenant_id, store_id, days):
    """Rolling sales + stock health for one store."""
    since, until = window(days)
    sales = conn.execute(f"""
        SELECT COALESCE(SUM({NET}), 0) AS revenue_cents, COALESCE(SUM(sl.qty), 0) AS units
          FROM sale_lines sl
         WHERE sl.tenant_id = ? AND sl.store_id = ? AND sl.sold_at >= ? AND sl.sold_at < ?""",
                         (tenant_id, store_id, since, until)).fetchone()
    stock = conn.execute("""
        SELECT COUNT(*) AS skus, COALESCE(SUM(on_hand <= reorder_point), 0) AS low_stock
          FROM inventory WHERE store_id = ?""", (store_id,)).fetchone()
    return {"revenue_cents": sales["revenue_cents"], "units": sales["units"],
            "skus": stock["skus"], "low_stock": stock["low_stock"]}


def _with_performance(conn, tenant_id, rows, days):
    out = []
    for r in rows:
        d = dict(r)
        d.update(store_performance(conn, tenant_id, r["id"], days))
        out.append(d)
    return out


def regions(conn, tenant_id):
    return [r[0] for r in conn.execute(
        "SELECT DISTINCT region FROM stores WHERE tenant_id = ? ORDER BY region", (tenant_id,))]


def list_stores(conn, tenant_id, q="", region="", sort="name", direction="", page=1,
                per_page=None, days=None):
    per_page = per_page or settings.STORES_PER_PAGE
    days = days or settings.KPI_WINDOW_DAYS
    where, params = ["tenant_id = ?"], [tenant_id]
    if q:
        where.append("(name LIKE ? OR city LIKE ? OR code LIKE ?)")
        params += [f"%{q}%"] * 3
    if region:
        where.append("region = ?")
        params.append(region)
    clause = " AND ".join(where)

    total = conn.execute(f"SELECT COUNT(*) FROM stores WHERE {clause}", params).fetchone()[0]
    page_count = max(1, total // per_page)
    page = min(max(1, page), page_count)

    rows = conn.execute(
        f"SELECT id, code, name, city, region, status, sq_ft FROM stores WHERE {clause} "
        f"ORDER BY name LIMIT ? OFFSET ?", (*params, per_page, (page - 1) * per_page)).fetchall()
    stores = _with_performance(conn, tenant_id, rows, days)

    key, desc = SORTS.get(sort, SORTS["name"])
    if direction in ("asc", "desc"):
        desc = direction == "desc"
    stores.sort(key=lambda s: s[key], reverse=desc)
    return {"stores": stores, "total": total, "page": page, "page_count": page_count,
            "per_page": per_page, "sort": sort if sort in SORTS else "name",
            "direction": "desc" if desc else "asc"}


def top_stores(conn, tenant_id, days, limit=5):
    rows = conn.execute("SELECT id, code, name, city, region, status, sq_ft FROM stores WHERE tenant_id = ?",
                        (tenant_id,)).fetchall()
    # TODO(perf): cache this, the dashboard calls it on every load.
    ranked = sorted(_with_performance(conn, tenant_id, rows, days), key=lambda s: s["revenue_cents"], reverse=True)
    return ranked[:limit]


def get_store(conn, tenant_id, code):
    return conn.execute("SELECT * FROM stores WHERE tenant_id = ? AND code = ?", (tenant_id, code)).fetchone()


def store_daily_revenue(conn, tenant_id, store_id, days):
    since, until = window(days)
    rows = conn.execute(f"""
        SELECT substr(sl.sold_at, 1, 10) AS day, SUM({NET}) AS revenue_cents
          FROM sale_lines sl
         WHERE sl.tenant_id = ? AND sl.store_id = ? AND sl.sold_at >= ? AND sl.sold_at < ?
         GROUP BY day ORDER BY day""", (tenant_id, store_id, since, until)).fetchall()
    by_day = {r["day"]: r["revenue_cents"] for r in rows}
    start = dt.date.fromisoformat(since)
    return [{"day": (start + dt.timedelta(days=i)).isoformat(),
             "revenue_cents": by_day.get((start + dt.timedelta(days=i)).isoformat(), 0)} for i in range(days)]


def store_top_titles(conn, tenant_id, store_id, days, limit=10):
    since, until = window(days)
    rows = conn.execute(f"""
        SELECT t.title, t.author, t.category, SUM(sl.qty) AS units, SUM({NET}) AS revenue_cents
          FROM sale_lines sl JOIN titles t ON t.id = sl.title_id
         WHERE sl.tenant_id = ? AND sl.store_id = ? AND sl.sold_at >= ? AND sl.sold_at < ?
         GROUP BY t.id ORDER BY units DESC, revenue_cents DESC LIMIT ?""",
                        (tenant_id, store_id, since, until, limit)).fetchall()
    return [dict(r) for r in rows]
