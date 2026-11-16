"""Dashboard KPIs: MRR, subscription counts, invoicing totals."""
import datetime as dt

MRR = "(s.quantity * p.amount_cents)"
LIVE = "s.status IN ('active', 'past_due')"


def window(days, today=None):
    today = today or dt.date.today()
    return (today - dt.timedelta(days=days)).isoformat(), today.isoformat()


def kpis(conn, tenant_id, days, today=None):
    since, until = window(days, today)
    subs = conn.execute(f"""
        SELECT COALESCE(SUM(CASE WHEN {LIVE} THEN {MRR} END), 0) AS mrr_cents,
               COALESCE(SUM({LIVE}), 0) AS live,
               COALESCE(SUM(s.status = 'trialing'), 0) AS trialing,
               COALESCE(SUM(s.status = 'past_due'), 0) AS past_due,
               COALESCE(SUM(s.status = 'canceled' AND s.canceled_on >= ?), 0) AS churned
          FROM subscriptions s JOIN plans p ON p.id = s.plan_id
         WHERE s.tenant_id = ?""", (since, tenant_id)).fetchone()
    inv = conn.execute("""
        SELECT COUNT(*) AS invoices, COALESCE(SUM(total_cents), 0) AS invoiced_cents
          FROM invoices WHERE tenant_id = ? AND issued_on >= ? AND issued_on < ? AND status != 'void'""",
                       (tenant_id, since, until)).fetchone()
    mrr = round(subs["mrr_cents"])
    return {"mrr_cents": mrr, "arr_cents": mrr * 12, "live": subs["live"], "trialing": subs["trialing"],
            "past_due": subs["past_due"], "churned": subs["churned"],
            "invoices": inv["invoices"], "invoiced_cents": inv["invoiced_cents"]}


def mrr_by_plan(conn, tenant_id):
    rows = conn.execute(f"""
        SELECT p.code, p.name, p.interval, COUNT(*) AS subscriptions, SUM({MRR}) AS mrr_cents
          FROM subscriptions s JOIN plans p ON p.id = s.plan_id
         WHERE s.tenant_id = ? AND {LIVE}
         GROUP BY p.id ORDER BY mrr_cents DESC""", (tenant_id,)).fetchall()
    return [{**dict(r), "mrr_cents": round(r["mrr_cents"])} for r in rows]


def top_customers(conn, tenant_id, limit=6):
    rows = conn.execute(f"""
        SELECT c.id, c.name, c.country, COUNT(*) AS subscriptions, SUM({MRR}) AS mrr_cents
          FROM subscriptions s JOIN plans p ON p.id = s.plan_id JOIN customers c ON c.id = s.customer_id
         WHERE s.tenant_id = ? AND {LIVE}
         GROUP BY c.id ORDER BY mrr_cents DESC LIMIT ?""", (tenant_id, limit)).fetchall()
    return [{**dict(r), "mrr_cents": round(r["mrr_cents"])} for r in rows]


def invoiced_by_month(conn, tenant_id, months, today=None):
    today = today or dt.date.today()
    first = today.replace(day=1)
    starts = []
    for _ in range(months):
        starts.append(first)
        first = (first - dt.timedelta(days=1)).replace(day=1)
    starts.reverse()
    rows = conn.execute("""
        SELECT substr(issued_on, 1, 7) AS month, SUM(total_cents) AS cents
          FROM invoices WHERE tenant_id = ? AND issued_on >= ? AND status != 'void'
         GROUP BY month""", (tenant_id, starts[0].isoformat())).fetchall()
    by_month = {r["month"]: r["cents"] for r in rows}
    return [{"month": s.strftime("%Y-%m"), "label": s.strftime("%b"), "cents": by_month.get(s.strftime("%Y-%m"), 0)}
            for s in starts]
