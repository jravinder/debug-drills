"""Shipment list, detail and routing."""

CHAIN = """
WITH RECURSIVE chain(id, shipment_id, parent_leg_id, from_depot_id, to_depot_id, driver_id,
                     departed_at, arrived_at, hop) AS (
    SELECT id, shipment_id, parent_leg_id, from_depot_id, to_depot_id, driver_id, departed_at, arrived_at, 1
      FROM legs
     WHERE tenant_id = ? AND parent_leg_id IS NULL
    UNION ALL
    SELECT l.id, l.shipment_id, l.parent_leg_id, l.from_depot_id, l.to_depot_id, l.driver_id,
           l.departed_at, l.arrived_at, c.hop + 1
      FROM legs l JOIN chain c ON l.parent_leg_id = c.id
)
"""


def list_shipments(conn, tenant_id, page, per_page, q=""):
    where, params = ["s.tenant_id = ?"], [tenant_id]
    if q:
        where.append("(s.pro LIKE ? OR s.customer LIKE ?)")
        params += [f"{q}%", f"%{q}%"]
    clause = " AND ".join(where)
    total = conn.execute(f"SELECT COUNT(*) FROM shipments s WHERE {clause}", params).fetchone()[0]
    page_count = max(1, -(-total // per_page))
    page = min(max(1, page), page_count)
    rows = conn.execute(f"""
        SELECT s.pro, s.customer, s.service, s.weight_kg, s.pieces, s.tendered_on, s.status,
               o.code AS origin_code, d.code AS dest_code,
               (SELECT COUNT(*) FROM legs l WHERE l.shipment_id = s.id) AS legs
          FROM shipments s
          JOIN depots o ON o.id = s.origin_depot_id
          JOIN depots d ON d.id = s.dest_depot_id
         WHERE {clause}
         ORDER BY s.tendered_on DESC, s.id DESC
         LIMIT ? OFFSET ?""", (*params, per_page, (page - 1) * per_page)).fetchall()
    return {"rows": [dict(r) for r in rows], "total": total, "page": page, "page_count": page_count}


def get_shipment(conn, tenant_id, pro):
    return conn.execute("""
        SELECT s.*, o.code AS origin_code, o.name AS origin_name, d.code AS dest_code, d.name AS dest_name
          FROM shipments s
          JOIN depots o ON o.id = s.origin_depot_id
          JOIN depots d ON d.id = s.dest_depot_id
         WHERE s.tenant_id = ? AND s.pro = ?""", (tenant_id, pro)).fetchone()


def route(conn, tenant_id, shipment_id):
    rows = conn.execute(CHAIN + """
        SELECT c.hop, c.departed_at, c.arrived_at, f.code AS from_code, f.city AS from_city,
               t.code AS to_code, t.city AS to_city, dr.name AS driver
          FROM chain c
          JOIN depots f ON f.id = c.from_depot_id
          JOIN depots t ON t.id = c.to_depot_id
          JOIN drivers dr ON dr.id = c.driver_id
         WHERE c.shipment_id = ?
         ORDER BY c.hop""", (tenant_id, shipment_id)).fetchall()
    return [dict(r) for r in rows]


def stops(conn, shipment_id):
    rows = conn.execute("""
        SELECT st.kind, st.window_end, st.arrived_at, d.code AS depot_code, d.utc_offset_min
          FROM stops st JOIN depots d ON d.id = st.depot_id
         WHERE st.shipment_id = ? ORDER BY st.arrived_at""", (shipment_id,)).fetchall()
    return [dict(r) for r in rows]


def drivers_page(conn, tenant_id, page, per_page, since):
    total = conn.execute("SELECT COUNT(*) FROM drivers WHERE tenant_id = ?", (tenant_id,)).fetchone()[0]
    page_count = max(1, -(-total // per_page))
    page = min(max(1, page), page_count)
    rows = conn.execute("""
        SELECT dr.id, dr.name, dr.license, dr.status, d.code AS depot_code, d.city AS depot_city
          FROM drivers dr JOIN depots d ON d.id = dr.depot_id
         WHERE dr.tenant_id = ? ORDER BY d.code, dr.name LIMIT ? OFFSET ?""",
                        (tenant_id, per_page, (page - 1) * per_page)).fetchall()
    ids = [r["id"] for r in rows]
    counts = {}
    if ids:
        marks = ",".join("?" * len(ids))
        counts = dict(conn.execute(f"""
            SELECT driver_id, COUNT(*) FROM stops
             WHERE tenant_id = ? AND arrived_at >= ? AND driver_id IN ({marks}) GROUP BY driver_id""",
                                   (tenant_id, since, *ids)).fetchall())
    out = [dict(r, stops=counts.get(r["id"], 0)) for r in rows]
    return {"rows": out, "total": total, "page": page, "page_count": page_count}
