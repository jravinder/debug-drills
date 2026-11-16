"""Metered usage reporting."""
import datetime as dt


def window(days, today=None):
    today = today or dt.date.today()
    return (today - dt.timedelta(days=days)).isoformat(), today.isoformat()


def meter_totals(conn, tenant_id, days):
    since, until = window(days)
    rows = conn.execute("""
        SELECT p.meter, p.name AS plan, p.unit_price_cents, COUNT(DISTINCT u.subscription_id) AS subscriptions,
               SUM(u.quantity) AS quantity
          FROM usage_records u
          JOIN subscriptions s ON s.id = u.subscription_id
          JOIN plans p ON p.id = s.plan_id
         WHERE u.tenant_id = ? AND u.recorded_at >= ? AND u.recorded_at < ?
         GROUP BY p.id ORDER BY quantity DESC""", (tenant_id, since, until)).fetchall()
    return [{**dict(r), "charges_cents": round(r["quantity"] * r["unit_price_cents"])} for r in rows]


def daily(conn, tenant_id, days):
    since, until = window(days)
    rows = conn.execute("""
        SELECT substr(recorded_at, 1, 10) AS day, SUM(quantity) AS quantity
          FROM usage_records
         WHERE tenant_id = ? AND recorded_at >= ? AND recorded_at < ?
         GROUP BY day ORDER BY day""", (tenant_id, since, until)).fetchall()
    by_day = {r["day"]: r["quantity"] for r in rows}
    start = dt.date.fromisoformat(since)
    days_list = [(start + dt.timedelta(days=i)).isoformat() for i in range(days)]
    return [{"day": d, "quantity": by_day.get(d, 0)} for d in days_list]
