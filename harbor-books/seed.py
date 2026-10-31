"""Build harbor.db with two demo tenants. Deterministic: fixed RNG seed.

    python seed.py                    # demo data (Tidewater small, Lanternfield big)
    python seed.py --profile test     # smaller dataset used by the test suite
    python seed.py --db /tmp/x.db
"""
import argparse
import datetime as dt
import os
import random
import sqlite3
import sys
import time

from faker import Faker

import settings
from migrations.migrate import migrate

SEED = 4242

CATEGORIES = [
    ("Fiction", 18), ("Mystery & Thriller", 12), ("Science Fiction & Fantasy", 9), ("Romance", 8),
    ("Biography", 6), ("History", 6), ("Children's", 11), ("Young Adult", 7), ("Cookbooks", 5),
    ("Travel", 3), ("Science", 4), ("Poetry", 2), ("Graphic Novels", 5), ("Self-Help", 4),
]
FORMATS = [("Paperback", 55, (1299, 1999), [6, 12, 24]), ("Hardcover", 30, (2499, 3499), [6, 12]),
           ("Mass market", 10, (799, 999), [24, 30]), ("Board book", 5, (699, 1099), [12])]
SUPPLIERS = ["Meridian Book Distribution", "Northgate Wholesale", "Bluewater Publishers Group", "Cedar & Quill Supply"]
POD_SUPPLIER = "PageForge Print-on-Demand"

BIG_REGIONS = ["Northeast", "Mid-Atlantic", "Southeast", "Great Lakes", "Plains",
               "Mountain", "Pacific Northwest", "California", "Southwest", "Gulf Coast"]

PROFILES = {
    "demo": {
        "tidewater-books": dict(name="Tidewater Books", plan="starter", stores=3, titles=3000, lines=8000,
                                stocked=1200, pod=0, feed_v2=False, regions=["Coastal"], prefix="TW"),
        "lanternfield": dict(name="Lanternfield Booksellers", plan="enterprise", stores=140, titles=40000,
                             lines=600000, stocked=1500, pod=36, feed_v2=True, regions=BIG_REGIONS, prefix="LF"),
    },
    "test": {
        "tidewater-books": dict(name="Tidewater Books", plan="starter", stores=3, titles=400, lines=2000,
                                stocked=200, pod=0, feed_v2=False, regions=["Coastal"], prefix="TW"),
        "lanternfield": dict(name="Lanternfield Booksellers", plan="enterprise", stores=140, titles=2500,
                             lines=30000, stocked=120, pod=8, feed_v2=True, regions=BIG_REGIONS, prefix="LF"),
    },
}


def isbn13(rng):
    body = "978" + "".join(str(rng.randint(0, 9)) for _ in range(9))
    s = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(body))
    return body + str((10 - s % 10) % 10)


def seed_tenant(conn, rng, fake, slug, p, today):
    cur = conn.execute("INSERT INTO tenants (slug, name, plan, created_at) VALUES (?, ?, ?, ?)",
                       (slug, p["name"], p["plan"], "2021-04-01 09:00:00"))
    tid = cur.lastrowid

    # stores
    stores = []
    used_cities = set()
    for i in range(p["stores"]):
        city = fake.city()
        while city in used_cities:
            city = fake.city()
        used_cities.add(city)
        code = f"{p['prefix']}-{i + 1:03d}"
        sq_ft = rng.choice([1800, 2400, 3200, 4500, 6000, 8500])
        opened = dt.date(2004, 1, 1) + dt.timedelta(days=rng.randint(0, 7000))
        status = "open" if rng.random() > 0.03 else "renovating"
        cur = conn.execute(
            "INSERT INTO stores (tenant_id, code, name, city, region, opened_on, sq_ft, status) VALUES (?,?,?,?,?,?,?,?)",
            (tid, code, f"{p['name'].split()[0]} {city}", city, rng.choice(p["regions"]), opened.isoformat(), sq_ft, status))
        stores.append((cur.lastrowid, code, sq_ft))

    # titles
    cats, cat_w = zip(*CATEGORIES)
    titles = []
    isbns = set()
    for i in range(p["titles"]):
        pod = i < p["pod"]
        isbn = isbn13(rng)
        while isbn in isbns:
            isbn = isbn13(rng)
        isbns.add(isbn)
        if pod:
            fmt, price, supplier, case_pack = "Print on demand", rng.randint(1499, 2899), POD_SUPPLIER, 0
        else:
            f = rng.choices(FORMATS, weights=[x[1] for x in FORMATS])[0]
            fmt, price, supplier = f[0], rng.randint(*f[2]), rng.choice(SUPPLIERS)
            case_pack = rng.choice(f[3]) if p["feed_v2"] else 1
        name = fake.sentence(nb_words=rng.randint(2, 5)).rstrip(".").title()
        titles.append((tid, isbn, name, fake.name(), rng.choices(cats, weights=cat_w)[0], fmt, price, supplier, case_pack))
    conn.executemany(
        "INSERT INTO titles (tenant_id, isbn, title, author, category, format, list_price_cents, supplier, case_pack)"
        " VALUES (?,?,?,?,?,?,?,?,?)", titles)
    rows = conn.execute("SELECT id, list_price_cents, case_pack FROM titles WHERE tenant_id=? ORDER BY id", (tid,)).fetchall()
    title_ids = [r[0] for r in rows]
    prices = {r[0]: r[1] for r in rows}
    pod_ids = [r[0] for r in rows if r[2] == 0]
    # long-tail popularity
    pop = [1.0 / (rank + 8) ** 0.9 for rank in range(len(title_ids))]
    shuffled = title_ids[:]
    rng.shuffle(shuffled)
    pop_cum, acc = [], 0.0
    for w in pop:
        acc += w
        pop_cum.append(acc)

    # sale lines over the last 365 days, weekend + December lift
    days = [today - dt.timedelta(days=d) for d in range(1, 366)]
    day_w = [(1.35 if d.weekday() >= 5 else 1.0) * (1.6 if d.month == 12 else 1.0) for d in days]
    store_w = [s[2] for s in stores]
    lines, receipt = [], 0
    while len(lines) < p["lines"]:
        receipt += 1
        sid, scode, _ = rng.choices(stores, weights=store_w)[0]
        day = rng.choices(days, weights=day_w)[0]
        ts = f"{day.isoformat()} {rng.randint(9, 20):02d}:{rng.randint(0, 59):02d}:{rng.randint(0, 59):02d}"
        rno = f"{scode}-{day.strftime('%y%m%d')}-{receipt:07d}"
        for _ in range(rng.choices([1, 2, 3, 4], weights=[50, 30, 15, 5])[0]):
            t = shuffled[rng.choices(range(len(shuffled)), cum_weights=pop_cum)[0]]
            qty = rng.choices([1, 2, 3], weights=[85, 12, 3])[0]
            price = prices[t]
            disc = int(price * qty * 0.1) if rng.random() < 0.12 else 0
            lines.append((tid, sid, t, rno, ts, qty, price, disc))
    conn.executemany(
        "INSERT INTO sale_lines (tenant_id, store_id, title_id, receipt_no, sold_at, qty, unit_price_cents, discount_cents)"
        " VALUES (?,?,?,?,?,?,?,?)", lines[: p["lines"]])

    # inventory: each store carries a subset, biased to popular titles; POD titles listed at 0 on hand
    stamp = f"{(today - dt.timedelta(days=1)).isoformat()} 23:30:00"
    inv = []
    for sid, _, _ in stores:
        carried = set()
        while len(carried) < min(p["stocked"], len(shuffled)):
            carried.add(shuffled[rng.choices(range(len(shuffled)), cum_weights=pop_cum)[0]])
        for t in pod_ids:
            if rng.random() < 0.5:
                carried.add(t)
        for t in carried:
            if t in pod_ids:
                inv.append((sid, t, 0, 1, stamp))
                continue
            rp = rng.randint(2, 6)
            on_hand = rng.randint(0, rp) if rng.random() < 0.08 else rng.randint(rp + 1, rp + 24)
            inv.append((sid, t, on_hand, rp, stamp))
    conn.executemany("INSERT INTO inventory (store_id, title_id, on_hand, reorder_point, updated_at) VALUES (?,?,?,?,?)", inv)
    conn.commit()
    return len(stores), len(title_ids), min(len(lines), p["lines"]), len(inv)


def build(db_path, profile="demo", today=None):
    today = today or dt.date.today()
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    migrate(conn)
    rng = random.Random(SEED)
    fake = Faker("en_US")
    fake.seed_instance(SEED)
    out = {}
    for slug, p in PROFILES[profile].items():
        out[slug] = seed_tenant(conn, rng, fake, slug, p, today)
    conn.execute("ANALYZE")
    conn.commit()
    conn.close()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="demo", choices=sorted(PROFILES))
    ap.add_argument("--db", default=settings.DB_PATH)
    a = ap.parse_args()
    t = time.time()
    for slug, (s, ti, li, inv) in build(a.db, a.profile).items():
        print(f"  {slug:<18} stores={s:<4} titles={ti:<6} sale_lines={li:<7} inventory={inv}")
    print(f"seeded {a.db} in {time.time() - t:.1f}s")


if __name__ == "__main__":
    sys.exit(main())
