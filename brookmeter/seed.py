"""Build brookmeter.db with two demo tenants. Deterministic: fixed RNG seed.

    python seed.py                    # demo data (Pinecrest small, Halvard big)
    python seed.py --profile test     # smaller dataset used by the test suite
    python seed.py --db /tmp/x.db
"""
import argparse
import datetime as dt
import os
import random
import re
import sqlite3
import sys
import time

from faker import Faker

import settings
from migrations.migrate import migrate

SEED = 7319
USAGE_DAYS = 35

COUNTRIES = [("US", 40), ("GB", 10), ("DE", 9), ("CA", 7), ("FR", 6), ("NL", 5), ("AU", 5), ("IN", 5),
             ("SE", 3), ("JP", 3), ("BR", 3), ("ES", 2), ("SG", 2)]

# (code, name, interval, amount_cents, meter, unit_price_cents, weight, max_seats)
SMALL_PLANS = [
    ("starter", "Starter", "month", 2900, None, None, 40, 1),
    ("team", "Team", "month", 7900, None, None, 30, 8),
    ("business", "Business", "month", 19900, None, None, 10, 3),
    ("team_builds", "Team + Build minutes", "month", 4900, "build_minutes", 2.0, 20, 4),
]
BIG_PLANS = [
    ("developer", "Developer", "month", 0, "api_calls", 0.04, 5, 1),
    ("pro", "Pro", "month", 4900, "api_calls", 0.03, 7, 3),
    ("growth", "Growth", "month", 29900, None, None, 48, 4),
    ("team_annual", "Team (annual)", "year", 58800, None, None, 28, 12),
    ("scale_annual", "Scale (annual)", "year", 499000, None, None, 10, 2),
    ("enterprise_annual", "Enterprise (annual)", "year", 2400000, None, None, 2, 1),
]

PROFILES = {
    "demo": {
        "pinecrest-labs": dict(name="Pinecrest Labs", plan="starter", prefix="PCL", plans=SMALL_PLANS,
                               customers=170, subscriptions=200, usage=4000),
        "halvard": dict(name="Halvard Cloud", plan="enterprise", prefix="HVD", plans=BIG_PLANS,
                        customers=45000, subscriptions=60000, usage=1070000),
    },
    "test": {
        "pinecrest-labs": dict(name="Pinecrest Labs", plan="starter", prefix="PCL", plans=SMALL_PLANS,
                               customers=170, subscriptions=200, usage=4000),
        "halvard": dict(name="Halvard Cloud", plan="enterprise", prefix="HVD", plans=BIG_PLANS,
                        customers=4500, subscriptions=6000, usage=100000),
    },
}


def shift_months(d, months):
    m = d.month - 1 + months
    return d.replace(year=d.year + m // 12, month=m % 12 + 1)


def past_period_ends(anchor_day, anchor_month, interval, started, until, today, lookback_days):
    """Anchor dates in (started, until) within the lookback window, oldest first."""
    out = []
    if interval == "month":
        d = today.replace(day=anchor_day)
        if d >= today:
            d = shift_months(d, -1)
        step = -1
    else:
        d = dt.date(today.year, anchor_month, anchor_day)
        if d >= today:
            d = d.replace(year=d.year - 1)
        step = -12
    while d > started and d > today - dt.timedelta(days=lookback_days):
        if d < until:
            out.append(d)
        d = shift_months(d, step)
    return out[::-1]


def seed_tenant(conn, rng, fake, slug, p, today):
    cur = conn.execute("INSERT INTO tenants (slug, name, plan, invoice_prefix, created_at) VALUES (?, ?, ?, ?, ?)",
                       (slug, p["name"], p["plan"], p["prefix"], "2022-03-01 09:00:00"))
    tid = cur.lastrowid

    plans = []
    for code, name, interval, amount, meter, unit, weight, seats in p["plans"]:
        cur = conn.execute("INSERT INTO plans (tenant_id, code, name, interval, amount_cents, meter, unit_price_cents)"
                           " VALUES (?,?,?,?,?,?,?)", (tid, code, name, interval, amount, meter, unit))
        plans.append(dict(id=cur.lastrowid, interval=interval, amount=amount, meter=meter, unit=unit,
                          weight=weight, seats=seats))

    codes, code_w = zip(*COUNTRIES)
    customers = []
    for _ in range(p["customers"]):
        name = fake.company()
        email = "billing@" + re.sub(r"[^a-z0-9]+", "", name.lower())[:18] + ".example"
        joined = today - dt.timedelta(days=rng.randint(20, 1400))
        customers.append((tid, name, email, rng.choices(codes, weights=code_w)[0], joined.isoformat()))
    conn.executemany("INSERT INTO customers (tenant_id, name, email, country, created_at) VALUES (?,?,?,?,?)",
                     customers)
    customer_ids = [r[0] for r in conn.execute("SELECT id FROM customers WHERE tenant_id = ? ORDER BY id", (tid,))]

    subs = []
    plan_w = [pl["weight"] for pl in plans]
    for i in range(p["subscriptions"]):
        cid = customer_ids[i] if i < len(customer_ids) else rng.choice(customer_ids)
        pl = rng.choices(plans, weights=plan_w)[0]
        r = rng.random()
        status = "active" if r < 0.86 else "past_due" if r < 0.89 else "canceled" if r < 0.97 else "trialing"
        if status == "trialing":
            started = today - dt.timedelta(days=rng.randint(1, 13))
        else:
            started = today - dt.timedelta(days=rng.randint(40, 1400))
        if started.day > 28:
            started -= dt.timedelta(days=3)
        canceled = None
        if status == "canceled":
            canceled = today - dt.timedelta(days=rng.randint(1, min(120, (today - started).days - 1)))
        seats = rng.randint(1, pl["seats"])
        subs.append(dict(tid=tid, cid=cid, plan=pl, status=status, seats=seats, anchor_day=started.day,
                         anchor_month=started.month, started=started, canceled=canceled))
    conn.executemany(
        "INSERT INTO subscriptions (tenant_id, customer_id, plan_id, status, quantity, anchor_day, anchor_month,"
        " started_on, canceled_on) VALUES (?,?,?,?,?,?,?,?,?)",
        [(s["tid"], s["cid"], s["plan"]["id"], s["status"], s["seats"], s["anchor_day"], s["anchor_month"],
          s["started"].isoformat(), s["canceled"].isoformat() if s["canceled"] else None) for s in subs])
    for s, (sid,) in zip(subs, conn.execute("SELECT id FROM subscriptions WHERE tenant_id = ? ORDER BY id", (tid,))):
        s["id"] = sid

    # usage: metered subscriptions report batches of calls/minutes throughout the day
    metered = [s for s in subs if s["plan"]["meter"] and s["status"] != "trialing"]
    usage = []
    if metered:
        intensity = [rng.paretovariate(1.5) for _ in metered]
        picks = rng.choices(metered, weights=intensity, k=p["usage"])
        start = dt.datetime.combine(today - dt.timedelta(days=USAGE_DAYS), dt.time())
        span = USAGE_DAYS * 86400
        for s in picks:
            at = start + dt.timedelta(seconds=int(rng.random() * span))
            if s["canceled"] and at.date() >= s["canceled"]:
                continue
            q = rng.randint(1, 40) if rng.random() < 0.94 else rng.randint(200, 5000)
            usage.append((tid, s["id"], s["plan"]["meter"], q, at.strftime("%Y-%m-%d %H:%M:%S")))
        conn.executemany("INSERT INTO usage_records (tenant_id, subscription_id, meter, quantity, recorded_at)"
                         " VALUES (?,?,?,?,?)", usage)

    # invoice history for the last few periods (issued before migration 004, so no fingerprint)
    history = []
    for s in subs:
        if s["status"] == "trialing":
            continue
        pl = s["plan"]
        until = s["canceled"] or today
        lookback = 400 if pl["interval"] == "year" else 190
        for end in past_period_ends(s["anchor_day"], s["anchor_month"], pl["interval"], s["started"], until,
                                    today, lookback):
            start = shift_months(end, -12 if pl["interval"] == "year" else -1)
            lines = [("plan", f"{'Annual' if pl['interval'] == 'year' else 'Monthly'} plan ({start} to {end})",
                      s["seats"], pl["amount"], s["seats"] * pl["amount"])]
            if pl["meter"]:
                q = int(rng.paretovariate(1.6) * 300)
                lines.append(("usage", f"{pl['meter']} ({start} to {end})", q, pl["unit"], round(q * pl["unit"])))
            age = (today - end).days
            status = "void" if rng.random() < 0.01 else ("paid" if age > 20 or rng.random() < 0.6 else "open")
            history.append((end, s["id"], start, lines, status))
    history.sort(key=lambda h: (h[0], h[1]))
    for n, (end, sid, start, lines, status) in enumerate(history, 1):
        cur = conn.execute(
            "INSERT INTO invoices (tenant_id, subscription_id, number, period_start, period_end, issued_on, status,"
            " total_cents) VALUES (?,?,?,?,?,?,?,?)",
            (tid, sid, f"{p['prefix']}-{n:07d}", start.isoformat(), end.isoformat(), end.isoformat(), status,
             sum(l[4] for l in lines)))
        conn.executemany("INSERT INTO invoice_lines (invoice_id, kind, description, quantity, unit_amount_cents,"
                         " amount_cents) VALUES (?,?,?,?,?,?)", [(cur.lastrowid, *l) for l in lines])
    conn.commit()
    return len(customers), len(subs), len(usage), len(history)


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
    for slug, (c, s, u, i) in build(a.db, a.profile).items():
        print(f"  {slug:<16} customers={c:<6} subscriptions={s:<6} usage_records={u:<8} invoices={i}")
    print(f"seeded {a.db} in {time.time() - t:.1f}s")


if __name__ == "__main__":
    sys.exit(main())
