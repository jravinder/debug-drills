"""Nightly line-haul manifest (cron: 01:30 carrier time, one run per tenant).

Lists every shipment tendered on the manifest day, grouped by origin depot, with the rated
charge from the tenant's rate card. Each depot block ends with a SUBTOTAL row and the file
ends with a TOTAL row. The partner gateway rejects files whose totals do not foot, so the
file is checked before it is handed over. Writes out/manifests/<tenant>-<date>.csv.

    python jobs/manifest_export.py <tenant-slug> [--date YYYY-MM-DD] [--out DIR]
"""
import argparse
import csv
import datetime as dt
import decimal
import logging
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import settings  # noqa: E402
from wayfold import db  # noqa: E402
from wayfold.logging_setup import configure, kv  # noqa: E402

log = logging.getLogger("wayfold.jobs.manifest")

COLUMNS = ["depot_code", "pro", "customer", "dest_code", "service", "pieces", "weight_kg", "charge"]


class ManifestError(Exception):
    pass


def rate(card, weight_kg):
    linehaul = card["base"] + weight_kg * card["per_kg"]
    return linehaul * (1 + card["fuel_pct"] / 100)


def build_rows(conn, tenant, day):
    cards = {r["service"]: r for r in conn.execute("SELECT * FROM rate_cards WHERE tenant_id = ?", (tenant["id"],))}
    ships = conn.execute("""
        SELECT s.pro, s.customer, s.service, s.pieces, s.weight_kg, o.code AS depot_code, d.code AS dest_code
          FROM shipments s
          JOIN depots o ON o.id = s.origin_depot_id
          JOIN depots d ON d.id = s.dest_depot_id
         WHERE s.tenant_id = ? AND s.tendered_on = ?
         ORDER BY o.code, s.pro""", (tenant["id"], day)).fetchall()
    rows, total, depot, subtotal = [], 0.0, None, 0.0
    for s in ships:
        if depot is not None and s["depot_code"] != depot:
            rows.append({"depot_code": depot, "pro": "SUBTOTAL", "charge": f"{subtotal:.2f}"})
            subtotal = 0.0
        depot = s["depot_code"]
        charge = rate(cards[s["service"]], s["weight_kg"])
        subtotal += charge
        total += charge
        rows.append({"depot_code": depot, "pro": s["pro"], "customer": s["customer"], "dest_code": s["dest_code"],
                     "service": s["service"], "pieces": s["pieces"], "weight_kg": f"{s['weight_kg']:.1f}",
                     "charge": f"{charge:.2f}"})
    if depot is not None:
        rows.append({"depot_code": depot, "pro": "SUBTOTAL", "charge": f"{subtotal:.2f}"})
    rows.append({"depot_code": "", "pro": "TOTAL", "charge": f"{total:.2f}"})
    return rows


def verify(path):
    """Re-read the file the way the partner gateway does and check that every total foots."""
    D = decimal.Decimal
    block, grand = D(0), D(0)
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            amount = D(r["charge"])
            if r["pro"] == "SUBTOTAL":
                if amount != block:
                    raise ManifestError(f"depot {r['depot_code']}: lines sum to {block}, subtotal says {amount}")
                block = D(0)
            elif r["pro"] == "TOTAL":
                if amount != grand:
                    raise ManifestError(f"lines sum to {grand}, total says {amount}")
            else:
                block += amount
                grand += amount


def run(slug, out_dir=None, conn=None, day=None):
    configure()
    t0 = time.perf_counter()
    day = day or (dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=1)).isoformat()
    own = conn is None
    conn = conn or db.connect()
    try:
        tenant = db.tenant_by_slug(conn, slug)
        if tenant is None:
            raise SystemExit(f"unknown tenant: {slug}")
        rows = build_rows(conn, tenant, day)
    finally:
        if own:
            conn.close()
    out_dir = os.path.join(out_dir or settings.EXPORT_DIR, "manifests")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{slug}-{day}.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    lines = sum(1 for r in rows if r["pro"] not in ("SUBTOTAL", "TOTAL"))
    try:
        verify(path)
    except ManifestError as e:
        log.error(kv(event="manifest_rejected", tenant=slug, day=day, error=f'"{e}"'))
        raise
    log.info(kv(event="manifest_done", tenant=slug, day=day, lines=lines,
                path=os.path.relpath(path, settings.BASE_DIR), ms=f"{(time.perf_counter() - t0) * 1000:.0f}"))
    return path, lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tenant")
    ap.add_argument("--date", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    path, n = run(a.tenant, a.out, day=a.date)
    print(f"{n} manifest lines -> {path}")


if __name__ == "__main__":
    main()
