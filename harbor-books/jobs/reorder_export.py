"""Nightly reorder export (cron: 02:15 local, one run per tenant).

For every SKU a store carries, project sell-through over the cover window and suggest a
reorder quantity rounded up to the supplier's case pack. Writes
out/reorder/<tenant>-<date>.csv, which buyers import into the supplier portal each morning.

    python jobs/reorder_export.py <tenant-slug> [--out DIR]
"""
import argparse
import collections
import csv
import datetime as dt
import logging
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import settings  # noqa: E402
from harbor import db  # noqa: E402
from harbor.logging_setup import configure, kv  # noqa: E402

log = logging.getLogger("harbor.jobs.reorder")

COLUMNS = ["store_code", "isbn", "title", "supplier", "on_hand", "reorder_point",
           "daily_velocity", "suggested_qty", "cases"]


def round_up_to_case(qty, case_pack):
    """Suppliers only ship full cases."""
    cases = -(-qty // case_pack)
    return cases * case_pack, cases


def load_sales(conn, tenant_id):
    # Pull the tenant's sale lines; we bucket by (store, title) below.
    # TODO(perf): fine for Tidewater-sized accounts, revisit when an account gets big.
    rows = conn.execute("SELECT * FROM sale_lines WHERE tenant_id = ?", (tenant_id,)).fetchall()
    return [dict(r) for r in rows]


def build_rows(conn, tenant, today=None):
    today = today or dt.date.today()
    since = (today - dt.timedelta(days=settings.REORDER_LOOKBACK_DAYS)).isoformat()

    sales = load_sales(conn, tenant["id"])
    log.info(kv(event="loaded_sales", tenant=tenant["slug"], lines=len(sales)))
    sold = collections.Counter()
    for s in sales:
        if s["sold_at"] >= since:
            sold[(s["store_id"], s["title_id"])] += s["qty"]

    stock = conn.execute("""
        SELECT i.store_id, i.title_id, i.on_hand, i.reorder_point, s.code AS store_code,
               t.isbn, t.title, t.supplier, t.case_pack
          FROM inventory i
          JOIN stores s ON s.id = i.store_id
          JOIN titles t ON t.id = i.title_id
         WHERE s.tenant_id = ? AND s.status = 'open'
         ORDER BY s.code, t.isbn""", (tenant["id"],)).fetchall()

    out = []
    for r in stock:
        velocity = sold[(r["store_id"], r["title_id"])] / settings.REORDER_LOOKBACK_DAYS
        target = max(r["reorder_point"], round(velocity * settings.REORDER_COVER_DAYS))
        need = max(0, target - r["on_hand"])
        qty, cases = round_up_to_case(need, r["case_pack"])
        if qty == 0:
            continue
        out.append({"store_code": r["store_code"], "isbn": r["isbn"], "title": r["title"],
                    "supplier": r["supplier"], "on_hand": r["on_hand"], "reorder_point": r["reorder_point"],
                    "daily_velocity": f"{velocity:.2f}", "suggested_qty": qty, "cases": cases})
    return out


def run(slug, out_dir=None, conn=None, today=None):
    configure()
    t0 = time.perf_counter()
    own = conn is None
    conn = conn or db.connect()
    try:
        tenant = db.tenant_by_slug(conn, slug)
        if tenant is None:
            raise SystemExit(f"unknown tenant: {slug}")
        rows = build_rows(conn, tenant, today=today)
    finally:
        if own:
            conn.close()
    out_dir = os.path.join(out_dir or settings.EXPORT_DIR, "reorder")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{slug}-{(today or dt.date.today()).isoformat()}.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    log.info(kv(event="reorder_export_done", tenant=slug, rows=len(rows), path=os.path.relpath(path, settings.BASE_DIR),
                ms=f"{(time.perf_counter() - t0) * 1000:.0f}"))
    return path, len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tenant")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    path, n = run(a.tenant, a.out)
    print(f"{n} reorder lines -> {path}")


if __name__ == "__main__":
    main()
