"""Dashboard KPIs and breakdowns."""
import datetime as dt

NET = "(sl.qty * sl.unit_price_cents - sl.discount_cents)"


def window(days, today=None):
    today = today or dt.date.today()
    return (today - dt.timedelta(days=days)).isoformat(), today.isoformat()


def kpis(conn, tenant_id, days):
    since, until = window(days)
    prev_since, _ = window(days * 2)
    cur = conn.execute(f"""
        SELECT COALESCE(SUM({NET}), 0) AS revenue_cents,
               COALESCE(SUM(sl.qty), 0) AS units,
               COUNT(DISTINCT sl.receipt_no) AS transactions
          FROM sale_lines sl
         WHERE sl.tenant_id = ? AND sl.sold_at >= ? AND sl.sold_at < ?""", (tenant_id, since, until)).fetchone()
    prev = conn.execute(f"""
        SELECT COALESCE(SUM({NET}), 0) FROM sale_lines sl
         WHERE sl.tenant_id = ? AND sl.sold_at >= ? AND sl.sold_at < ?""", (tenant_id, prev_since, since)).fetchone()[0]
    low = conn.execute("""
        SELECT COUNT(*) FROM inventory i JOIN stores s ON s.id = i.store_id
         WHERE s.tenant_id = ? AND i.on_hand <= i.reorder_point""", (tenant_id,)).fetchone()[0]
    rev = cur["revenue_cents"]
    return {
        "revenue_cents": rev,
        "revenue_delta_pct": round((rev - prev) / prev * 100, 1) if prev else None,
        "units": cur["units"],
        "transactions": cur["transactions"],
        "avg_basket_cents": rev // cur["transactions"] if cur["transactions"] else 0,
        "low_stock": low,
    }


def revenue_by_category(conn, tenant_id, days):
    since, until = window(days)
    rows = conn.execute(f"""
        SELECT t.category, SUM({NET}) AS revenue_cents
          FROM sale_lines sl JOIN titles t ON t.id = sl.title_id
         WHERE sl.tenant_id = ? AND sl.sold_at >= ? AND sl.sold_at < ?
         GROUP BY t.category ORDER BY revenue_cents DESC""", (tenant_id, since, until)).fetchall()
    return [dict(r) for r in rows]


def low_stock(conn, tenant_id, limit=8, offset=0, store_id=None):
    params = [tenant_id]
    extra = ""
    if store_id is not None:
        extra = " AND s.id = ?"
        params.append(store_id)
    rows = conn.execute(f"""
        SELECT s.code AS store_code, s.name AS store_name, t.isbn, t.title, t.format,
               i.on_hand, i.reorder_point, (i.reorder_point - i.on_hand) AS short_by
          FROM inventory i
          JOIN stores s ON s.id = i.store_id
          JOIN titles t ON t.id = i.title_id
         WHERE s.tenant_id = ? AND i.on_hand <= i.reorder_point{extra}
         ORDER BY short_by DESC, t.title
         LIMIT ? OFFSET ?""", (*params, limit, offset)).fetchall()
    return [dict(r) for r in rows]
