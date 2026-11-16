"""Invoice ledger queries."""
import settings


def recent(conn, tenant_id, limit=8):
    rows = conn.execute("""
        SELECT i.number, i.issued_on, i.total_cents, i.status, c.name AS customer
          FROM invoices i
          JOIN subscriptions s ON s.id = i.subscription_id
          JOIN customers c ON c.id = s.customer_id
         WHERE i.tenant_id = ?
         ORDER BY i.issued_on DESC, i.id DESC LIMIT ?""", (tenant_id, limit)).fetchall()
    return [dict(r) for r in rows]


def invoices_page(conn, tenant_id, page=1, per_page=None, status=""):
    per_page = per_page or settings.INVOICES_PER_PAGE
    where, params = ["i.tenant_id = ?"], [tenant_id]
    if status in ("open", "paid", "void"):
        where.append("i.status = ?")
        params.append(status)
    clause = " AND ".join(where)
    totals = conn.execute(f"""
        SELECT COUNT(*) AS count, COALESCE(SUM(i.total_cents), 0) AS total_cents
          FROM invoices i WHERE {clause}""", params).fetchone()
    page_count = max(1, -(-totals["count"] // per_page))
    page = min(max(1, page), page_count)
    rows = conn.execute(f"""
        SELECT i.id, i.number, i.period_start, i.period_end, i.issued_on, i.status, i.total_cents,
               c.name AS customer, p.name AS plan
          FROM invoices i
          JOIN subscriptions s ON s.id = i.subscription_id
          JOIN customers c ON c.id = s.customer_id
          JOIN plans p ON p.id = s.plan_id
         WHERE {clause}
         ORDER BY i.issued_on DESC, i.id DESC
         LIMIT ? OFFSET ?""", (*params, per_page, (page - 1) * per_page)).fetchall()
    return {"rows": [dict(r) for r in rows], "page": page, "page_count": page_count, **dict(totals)}


def invoice_detail(conn, tenant_id, number):
    inv = conn.execute("""
        SELECT i.*, c.name AS customer, c.email, p.name AS plan
          FROM invoices i
          JOIN subscriptions s ON s.id = i.subscription_id
          JOIN customers c ON c.id = s.customer_id
          JOIN plans p ON p.id = s.plan_id
         WHERE i.tenant_id = ? AND i.number = ?""", (tenant_id, number)).fetchone()
    if inv is None:
        return None, []
    lines = conn.execute("SELECT * FROM invoice_lines WHERE invoice_id = ? ORDER BY id", (inv["id"],)).fetchall()
    return dict(inv), [dict(r) for r in lines]
