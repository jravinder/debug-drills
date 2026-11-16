"""Dashboard KPIs: volume and on-time delivery."""
import datetime as dt

DEADLINE_UTC = "datetime(st.window_end, (-t.utc_offset_min) || ' minutes')"
ON_TIME = f"(st.arrived_at <= {DEADLINE_UTC})"


def window(days, today=None):
    today = today or dt.datetime.now(dt.timezone.utc).date()
    return (today - dt.timedelta(days=days)).isoformat(), today.isoformat()


def kpis(conn, tenant_id, days):
    since, until = window(days)
    deliveries = conn.execute(f"""
        SELECT COUNT(*) AS deliveries, COALESCE(SUM({ON_TIME}), 0) AS on_time
          FROM stops st JOIN tenants t ON t.id = st.tenant_id
         WHERE st.tenant_id = ? AND st.kind = 'delivery' AND st.arrived_at >= ? AND st.arrived_at < ?""",
                              (tenant_id, since, until)).fetchone()
    shipments = conn.execute("""
        SELECT COUNT(*) FROM shipments WHERE tenant_id = ? AND tendered_on >= ? AND tendered_on < ?""",
                             (tenant_id, since, until)).fetchone()[0]
    stop_events = conn.execute("""
        SELECT COUNT(*) FROM stops WHERE tenant_id = ? AND arrived_at >= ? AND arrived_at < ?""",
                               (tenant_id, since, until)).fetchone()[0]
    drivers = conn.execute("""
        SELECT COUNT(DISTINCT driver_id) FROM stops WHERE tenant_id = ? AND arrived_at >= ? AND arrived_at < ?""",
                           (tenant_id, since, until)).fetchone()[0]
    n = deliveries["deliveries"]
    return {
        "shipments": shipments,
        "stop_events": stop_events,
        "deliveries": n,
        "on_time": deliveries["on_time"],
        "on_time_pct": round(deliveries["on_time"] / n * 100, 1) if n else None,
        "active_drivers": drivers,
    }


def on_time_series(conn, tenant_id, days):
    since, until = window(days)
    rows = conn.execute(f"""
        SELECT substr(st.arrived_at, 1, 10) AS day, COUNT(*) AS deliveries, SUM({ON_TIME}) AS on_time
          FROM stops st JOIN tenants t ON t.id = st.tenant_id
         WHERE st.tenant_id = ? AND st.kind = 'delivery' AND st.arrived_at >= ? AND st.arrived_at < ?
         GROUP BY day ORDER BY day""", (tenant_id, since, until)).fetchall()
    return [{"day": r["day"], "deliveries": r["deliveries"],
             "on_time_pct": round(r["on_time"] / r["deliveries"] * 100, 1)} for r in rows]


def stops_by_region(conn, tenant_id, days):
    since, until = window(days)
    rows = conn.execute("""
        SELECT d.region, COUNT(*) AS stops
          FROM stops st JOIN depots d ON d.id = st.depot_id
         WHERE st.tenant_id = ? AND st.arrived_at >= ? AND st.arrived_at < ?
         GROUP BY d.region ORDER BY stops DESC""", (tenant_id, since, until)).fetchall()
    return [dict(r) for r in rows]


def recent_late(conn, tenant_id, limit=8):
    since, until = window(7)
    rows = conn.execute(f"""
        SELECT s.pro, s.customer, d.code AS depot_code, st.window_end, st.arrived_at,
               CAST(ROUND((julianday(st.arrived_at) - julianday({DEADLINE_UTC})) * 1440) AS INTEGER) AS late_min
          FROM stops st
          JOIN tenants t ON t.id = st.tenant_id
          JOIN shipments s ON s.id = st.shipment_id
          JOIN depots d ON d.id = st.depot_id
         WHERE st.tenant_id = ? AND st.kind = 'delivery' AND st.arrived_at >= ? AND st.arrived_at < ?
           AND NOT {ON_TIME}
         ORDER BY st.arrived_at DESC LIMIT ?""", (tenant_id, since, until, limit)).fetchall()
    return [dict(r) for r in rows]
