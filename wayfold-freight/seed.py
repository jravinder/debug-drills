"""Build wayfold.db with two demo tenants. Deterministic: fixed RNG seed.

    python seed.py                    # demo data (Brookhollow small, Ironvale big)
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

SEED = 7319
FMT = "%Y-%m-%d %H:%M:%S"

# region -> (UTC offset in minutes, weight)
BIG_REGIONS = {
    "Northeast": (-300, 10), "Mid-Atlantic": (-300, 9), "Southeast": (-300, 10), "Ohio Valley": (-300, 7),
    "Great Lakes": (-360, 9), "Plains": (-360, 8), "Gulf Coast": (-360, 8), "Texas": (-360, 10),
    "Mountain": (-420, 7), "Desert Southwest": (-420, 6), "Pacific Northwest": (-480, 8), "California": (-480, 10),
}
SMALL_REGIONS = {"Cascade": (-480, 1)}

PREFIX_WORDS = ["Alder", "Bramble", "Cobalt", "Dunmore", "Elmstead", "Fallow", "Gristle", "Hollin", "Kestrel",
                "Kettle", "Larch", "Marrow", "Nettle", "Oriel", "Pallet", "Quarry", "Rowan", "Saddle", "Thistle",
                "Umber", "Vellum", "Willet", "Yarrow", "Ashgrove", "Birchway", "Copperleaf", "Driftmoor", "Emberly"]
SUFFIX_WORDS = ["Provisions", "Ceramics", "Millworks", "Supply Co.", "Outfitters", "Fabrication", "Growers",
                "Hardware", "Textiles", "Paper Goods", "Cold Storage", "Brewing", "Tile & Stone", "Pet Supply"]

PROFILES = {
    "demo": {
        "brookhollow-cartage": dict(name="Brookhollow Cartage", plan="starter", offset=-480, depots=3, drivers=24,
                                    shipments=7000, customers=60, relay=False, regions=SMALL_REGIONS, prefix="BH",
                                    rates={"standard": (95.0, 0.0, 0.0), "express": (140.0, 0.0, 0.0)}),
        "ironvale-freight": dict(name="Ironvale Freight Lines", plan="enterprise", offset=-360, depots=120,
                                 drivers=1100, shipments=135000, customers=900, relay=True, regions=BIG_REGIONS,
                                 prefix="IV", rates={"standard": (38.0, 0.185, 11.5), "express": (52.0, 0.26, 11.5)}),
    },
    "test": {
        "brookhollow-cartage": dict(name="Brookhollow Cartage", plan="starter", offset=-480, depots=3, drivers=8,
                                    shipments=800, customers=20, relay=False, regions=SMALL_REGIONS, prefix="BH",
                                    rates={"standard": (95.0, 0.0, 0.0), "express": (140.0, 0.0, 0.0)}),
        "ironvale-freight": dict(name="Ironvale Freight Lines", plan="enterprise", offset=-360, depots=120,
                                 drivers=300, shipments=14000, customers=120, relay=True, regions=BIG_REGIONS,
                                 prefix="IV", rates={"standard": (38.0, 0.185, 11.5), "express": (52.0, 0.26, 11.5)}),
    },
}


class Ids:
    def __init__(self):
        self.n = {}

    def next(self, table):
        self.n[table] = self.n.get(table, 0) + 1
        return self.n[table]


def ceil_hour(t):
    return (t + dt.timedelta(minutes=59, seconds=59)).replace(minute=0, second=0, microsecond=0)


def seed_tenant(conn, rng, fake, ids, slug, p, now):
    cur = conn.execute("INSERT INTO tenants (slug, name, plan, utc_offset_min, created_at) VALUES (?,?,?,?,?)",
                       (slug, p["name"], p["plan"], p["offset"], "2022-03-01 09:00:00"))
    tid = cur.lastrowid
    for service, (base, per_kg, fuel) in p["rates"].items():
        conn.execute("INSERT INTO rate_cards VALUES (?,?,?,?,?)", (tid, service, base, per_kg, fuel))

    # depots
    regions = list(p["regions"])
    region_w = [p["regions"][r][1] for r in regions]
    depots, used = [], set()
    for i in range(p["depots"]):
        city = fake.city()
        while city in used:
            city = fake.city()
        used.add(city)
        region = regions[i % len(regions)] if i < len(regions) else rng.choices(regions, weights=region_w)[0]
        did = ids.next("depots")
        status = "active" if rng.random() > 0.02 else "seasonal"
        doors = rng.choice([8, 12, 16, 24, 36, 48])
        conn.execute("INSERT INTO depots (id, tenant_id, code, name, city, region, doors, status, utc_offset_min)"
                     " VALUES (?,?,?,?,?,?,?,?,?)",
                     (did, tid, f"{p['prefix']}-{i + 1:03d}", f"{city} Terminal", city, region, doors, status,
                      p["regions"][region][0]))
        depots.append({"id": did, "region": region, "offset": p["regions"][region][0], "doors": doors})
    hubs = {}
    for d in depots:
        hubs.setdefault(d["region"], d)

    # drivers
    drivers_by_depot = {d["id"]: [] for d in depots}
    rows = []
    for i in range(p["drivers"]):
        d = depots[i % len(depots)] if i < len(depots) else rng.choices(depots, weights=[x["doors"] for x in depots])[0]
        drv = ids.next("drivers")
        drivers_by_depot[d["id"]].append(drv)
        rows.append((drv, tid, d["id"], fake.name(), rng.choice(["CDL-A", "CDL-A", "CDL-B"]),
                     "active" if rng.random() > 0.04 else "leave"))
    conn.executemany("INSERT INTO drivers (id, tenant_id, depot_id, name, license, status) VALUES (?,?,?,?,?,?)", rows)

    customers = sorted({f"{rng.choice(PREFIX_WORDS)} {rng.choice(SUFFIX_WORDS)}" for _ in range(p["customers"] * 2)})
    customers = customers[: p["customers"]]

    # shipments, legs, stops over the last 365 days; volume grows toward today
    depot_w = [d["doors"] for d in depots]
    days_back = list(range(1, 366))
    day_w = [1.0 + (365 - b) / 365 for b in days_back]
    picked = sorted((rng.choices(days_back, weights=day_w)[0] for _ in range(p["shipments"])), reverse=True)
    ship_rows, leg_rows, stop_rows = [], [], []
    today = now.date()
    for n, back in enumerate(picked):
        sid = ids.next("shipments")
        origin = rng.choices(depots, weights=depot_w)[0]
        dest = rng.choices(depots, weights=depot_w)[0]
        service = "express" if rng.random() < 0.18 else "standard"
        weight = round(min(max(rng.lognormvariate(6.1, 0.9), 15.0), 12000.0), 1)
        day = today - dt.timedelta(days=back)

        path = [origin]
        if p["relay"] and origin["id"] != dest["id"]:
            for hub in (hubs[origin["region"]], hubs[dest["region"]]):
                if hub["id"] != path[-1]["id"]:
                    path.append(hub)
        if dest["id"] != path[-1]["id"] or len(path) == 1:
            path.append(dest)

        local_depart = dt.datetime.combine(day, dt.time(rng.randint(6, 13), rng.choice([0, 15, 30, 45])))
        t = local_depart - dt.timedelta(minutes=origin["offset"])
        schedule = []
        for a, b in zip(path, path[1:]):
            transit = dt.timedelta(minutes=rng.randint(90, 600) if a["id"] != b["id"] else rng.randint(45, 150))
            schedule.append((a, b, t, t + transit))
            t = t + transit + dt.timedelta(minutes=rng.randint(60, 240))
        planned = schedule[-1][3]
        promised_utc = ceil_hour(planned) + dt.timedelta(hours=2 if service == "express" else 4)
        if rng.random() < 0.91:
            delta = -rng.triangular(0, 200, 25)
        else:
            delta = rng.triangular(0, 300, 30)
        actual = promised_utc + dt.timedelta(minutes=delta)

        parent = None
        delivered = False
        for k, (a, b, dep, arr) in enumerate(schedule):
            last = k == len(schedule) - 1
            if last:
                arr = max(actual, dep + dt.timedelta(minutes=30))
            if dep > now:
                break
            lid = ids.next("legs")
            drv = rng.choice(drivers_by_depot[a["id"]] or drivers_by_depot[origin["id"]] or [1])
            leg_rows.append((lid, tid, sid, parent, a["id"], b["id"], drv, dep.strftime(FMT), arr.strftime(FMT)))
            if k == 0:
                stop_rows.append((ids.next("stops"), tid, sid, lid, a["id"], drv, "pickup",
                                  (dep + dt.timedelta(minutes=a["offset"] + 30)).strftime(FMT),
                                  (dep - dt.timedelta(minutes=rng.randint(5, 40))).strftime(FMT)))
            if arr <= now:
                if last:
                    window = promised_utc + dt.timedelta(minutes=b["offset"])
                    stop_rows.append((ids.next("stops"), tid, sid, lid, b["id"], drv, "delivery",
                                      window.strftime(FMT), arr.strftime(FMT)))
                    delivered = True
                else:
                    window = ceil_hour(arr) + dt.timedelta(minutes=b["offset"] + 60)
                    stop_rows.append((ids.next("stops"), tid, sid, lid, b["id"], drv, "transfer",
                                      window.strftime(FMT), arr.strftime(FMT)))
            parent = lid
        ship_rows.append((sid, tid, str(10000001 + n), rng.choice(customers), origin["id"], dest["id"], service,
                          weight, rng.randint(1, 26), day.isoformat(), "delivered" if delivered else "in_transit"))

    conn.executemany("INSERT INTO shipments (id, tenant_id, pro, customer, origin_depot_id, dest_depot_id, service,"
                     " weight_kg, pieces, tendered_on, status) VALUES (?,?,?,?,?,?,?,?,?,?,?)", ship_rows)
    conn.executemany("INSERT INTO legs (id, tenant_id, shipment_id, parent_leg_id, from_depot_id, to_depot_id,"
                     " driver_id, departed_at, arrived_at) VALUES (?,?,?,?,?,?,?,?,?)", leg_rows)
    conn.executemany("INSERT INTO stops (id, tenant_id, shipment_id, leg_id, depot_id, driver_id, kind, window_end,"
                     " arrived_at) VALUES (?,?,?,?,?,?,?,?,?)", stop_rows)
    conn.commit()
    return len(depots), len(ship_rows), len(leg_rows), len(stop_rows)


def build(db_path, profile="demo", now=None):
    now = now or dt.datetime.now(dt.timezone.utc).replace(tzinfo=None, microsecond=0)
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    migrate(conn)
    rng = random.Random(SEED)
    fake = Faker("en_US")
    fake.seed_instance(SEED)
    ids = Ids()
    out = {}
    for slug, p in PROFILES[profile].items():
        out[slug] = seed_tenant(conn, rng, fake, ids, slug, p, now)
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
    for slug, (d, s, legs, stops) in build(a.db, a.profile).items():
        print(f"  {slug:<20} depots={d:<4} shipments={s:<7} legs={legs:<7} stop_events={stops}")
    print(f"seeded {a.db} in {time.time() - t:.1f}s")


if __name__ == "__main__":
    sys.exit(main())
