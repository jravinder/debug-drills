"""Subscription listing."""
import settings
from brookmeter.services.metrics import MRR

STATUSES = ["active", "trialing", "past_due", "canceled"]


def list_subscriptions(conn, tenant_id, q="", status="", page=1, per_page=None):
    per_page = per_page or settings.SUBSCRIPTIONS_PER_PAGE
    where, params = ["s.tenant_id = ?"], [tenant_id]
    if q:
        where.append("(c.name LIKE ? OR c.email LIKE ?)")
        params += [f"%{q}%"] * 2
    if status in STATUSES:
        where.append("s.status = ?")
        params.append(status)
    clause = " AND ".join(where)
    total = conn.execute(f"""
        SELECT COUNT(*) FROM subscriptions s JOIN customers c ON c.id = s.customer_id WHERE {clause}""",
                         params).fetchone()[0]
    page_count = max(1, -(-total // per_page))
    page = min(max(1, page), page_count)
    rows = conn.execute(f"""
        SELECT s.id, s.status, s.quantity, s.anchor_day, s.started_on, c.name AS customer, c.email,
               p.name AS plan, p.interval, {MRR} AS mrr_cents
          FROM subscriptions s
          JOIN customers c ON c.id = s.customer_id
          JOIN plans p ON p.id = s.plan_id
         WHERE {clause}
         ORDER BY s.started_on DESC, s.id DESC
         LIMIT ? OFFSET ?""", (*params, per_page, (page - 1) * per_page)).fetchall()
    return {"rows": [dict(r) for r in rows], "total": total, "page": page, "page_count": page_count,
            "per_page": per_page}
