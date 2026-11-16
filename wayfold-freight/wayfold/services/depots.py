"""Depot list and the per-depot on-time scorecard."""
import time

import settings
from wayfold.services.metrics import ON_TIME, window

_scorecards = {}


def regions(conn, tenant_id):
    return [r[0] for r in conn.execute(
        "SELECT DISTINCT region FROM depots WHERE tenant_id = ? ORDER BY region", (tenant_id,))]


def depot_count(conn, tenant_id):
    return conn.execute("SELECT COUNT(*) FROM depots WHERE tenant_id = ?", (tenant_id,)).fetchone()[0]


def _compute_scorecard(conn, tenant_id, days):
    since, until = window(days)
    rows = conn.execute(f"""
        SELECT d.id, d.code, d.name, d.city, d.region, d.status, d.utc_offset_min,
               COUNT(st.id) AS deliveries, COALESCE(SUM({ON_TIME}), 0) AS on_time
          FROM depots d
          JOIN tenants t ON t.id = d.tenant_id
          LEFT JOIN stops st ON st.depot_id = d.id AND st.kind = 'delivery'
                            AND st.arrived_at >= ? AND st.arrived_at < ?
         WHERE d.tenant_id = ?
         GROUP BY d.id ORDER BY d.code""", (since, until, tenant_id)).fetchall()
    drivers = dict(conn.execute("SELECT depot_id, COUNT(*) FROM drivers WHERE tenant_id = ? AND status = 'active'"
                                " GROUP BY depot_id", (tenant_id,)).fetchall())
    out = []
    for r in rows:
        d = dict(r)
        d["late"] = d["deliveries"] - d["on_time"]
        d["on_time_pct"] = round(d["on_time"] / d["deliveries"] * 100, 1) if d["deliveries"] else None
        d["drivers"] = drivers.get(d["id"], 0)
        out.append(d)
    return out


def scorecard(conn, tenant_id, days):
    if depot_count(conn, tenant_id) < settings.SCORECARD_CACHE_MIN_DEPOTS:
        return _compute_scorecard(conn, tenant_id, days)
    hit = _scorecards.get(tenant_id)
    if hit and time.monotonic() - hit[0] < settings.SCORECARD_CACHE_SECONDS:
        return hit[1]
    rows = _compute_scorecard(conn, tenant_id, days)
    _scorecards[tenant_id] = (time.monotonic(), rows)
    return rows


def list_depots(conn, tenant_id, days, region=""):
    rows = scorecard(conn, tenant_id, days)
    if region:
        rows = [r for r in rows if r["region"] == region]
    return rows


def worst_depots(conn, tenant_id, days, limit=6):
    rows = [r for r in scorecard(conn, tenant_id, days) if r["deliveries"] >= 5]
    return sorted(rows, key=lambda r: (r["on_time_pct"], -r["deliveries"]))[:limit]
