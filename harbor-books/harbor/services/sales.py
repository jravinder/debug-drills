"""Sales ledger queries."""
from harbor.services.metrics import NET, window


def sale_lines_page(conn, tenant_id, page, per_page, store_code="", days=30):
    since, until = window(days)
    where = ["sl.tenant_id = ?", "sl.sold_at >= ?", "sl.sold_at < ?"]
    params = [tenant_id, since, until]
    if store_code:
        where.append("s.code = ?")
        params.append(store_code)
    clause = " AND ".join(where)
    totals = conn.execute(f"""
        SELECT COUNT(*) AS lines, COALESCE(SUM(sl.qty), 0) AS units, COALESCE(SUM({NET}), 0) AS revenue_cents
          FROM sale_lines sl JOIN stores s ON s.id = sl.store_id WHERE {clause}""", params).fetchone()
    page_count = max(1, -(-totals["lines"] // per_page))
    page = min(max(1, page), page_count)
    rows = conn.execute(f"""
        SELECT sl.sold_at, sl.receipt_no, s.code AS store_code, t.title, t.isbn, sl.qty,
               sl.unit_price_cents, sl.discount_cents, {NET} AS net_cents
          FROM sale_lines sl
          JOIN stores s ON s.id = sl.store_id
          JOIN titles t ON t.id = sl.title_id
         WHERE {clause}
         ORDER BY sl.sold_at DESC, sl.id DESC
         LIMIT ? OFFSET ?""", (*params, per_page, (page - 1) * per_page)).fetchall()
    return {"rows": [dict(r) for r in rows], "page": page, "page_count": page_count, **dict(totals)}


def revenue_lines(conn, tenant_id, days):
    """Line-level sales for the dashboard revenue chart (the chart buckets them client-side)."""
    since, _ = window(days)
    rows = conn.execute("""
        SELECT sl.id, sl.sold_at, sl.store_id, s.code AS store_code, s.name AS store_name, sl.title_id,
               t.category, sl.qty, sl.unit_price_cents, sl.discount_cents
          FROM sale_lines sl
          JOIN stores s ON s.id = sl.store_id
          JOIN titles t ON t.id = sl.title_id
         WHERE sl.tenant_id = ? AND sl.sold_at >= ?
         ORDER BY sl.sold_at""", (tenant_id, since)).fetchall()
    return [dict(r) for r in rows]
