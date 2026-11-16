"""Nightly invoice run (cron: 01:05 UTC, one run per tenant).

Every live subscription whose billing anchor falls on the run date gets an invoice for the
period that just ended: the plan fee plus any metered usage recorded
during the period. Safe to re-run for the same date.

    python jobs/invoice_run.py <tenant-slug> [--date YYYY-MM-DD]
"""
import argparse
import datetime as dt
import logging
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import settings  # noqa: E402
from brookmeter import db  # noqa: E402
from brookmeter.logging_setup import configure, kv  # noqa: E402
from brookmeter.services import invoicing, rating  # noqa: E402

log = logging.getLogger("brookmeter.jobs.invoice_run")


def shift_months(d, months):
    m = d.month - 1 + months
    return d.replace(year=d.year + m // 12, month=m % 12 + 1)


def period(run_date, interval):
    """[start, end) of the period that ends on run_date."""
    start = shift_months(run_date, -12 if interval == "year" else -1)
    return start.isoformat(), run_date.isoformat()


def due_subscriptions(conn, tenant_id, run_date):
    return conn.execute("""
        SELECT s.id, s.quantity, c.name AS customer, p.name AS plan_name, p.interval, p.amount_cents,
               p.meter, p.unit_price_cents
          FROM subscriptions s
          JOIN plans p ON p.id = s.plan_id
          JOIN customers c ON c.id = s.customer_id
         WHERE s.tenant_id = ? AND s.status IN ('active', 'past_due') AND s.anchor_day = ?
           AND (p.interval = 'month' OR s.anchor_month = ?)
         ORDER BY s.id""", (tenant_id, run_date.day, run_date.month)).fetchall()


def load_usage(conn, tenant_id, run_date):
    since, until = period(run_date, "month")
    return conn.execute("""
        SELECT subscription_id, quantity FROM usage_records
         WHERE tenant_id = ? AND recorded_at >= ? AND recorded_at < ?""", (tenant_id, since, until)).fetchall()


def usage_for(usage, subscription_id):
    return [u for u in usage if u["subscription_id"] == subscription_id]


def build_drafts(due, usage, run_date):
    drafts = []
    for sub in due:
        start, end = period(run_date, sub["interval"])
        lines = [{"kind": "plan", "description": f"{sub['plan_name']} ({start} to {end})",
                  "quantity": sub["quantity"], "unit_amount_cents": sub["amount_cents"],
                  "amount_cents": sub["quantity"] * sub["amount_cents"]}]
        records = usage_for(usage, sub["id"]) if sub["meter"] else []
        if records:
            quantity, amount = rating.rate_usage(records, sub["unit_price_cents"])
            lines.append({"kind": "usage", "description": f"{sub['meter']} ({start} to {end})",
                          "quantity": quantity, "unit_amount_cents": sub["unit_price_cents"],
                          "amount_cents": amount})
        drafts.append({"subscription_id": sub["id"], "period_start": start, "period_end": end,
                       "lines": lines, "total_cents": sum(l["amount_cents"] for l in lines)})
    return drafts


def run(slug, run_date=None, conn=None):
    configure()
    t0 = time.perf_counter()
    run_date = run_date or dt.date.today()
    own = conn is None
    conn = conn or db.connect()
    created = skipped = 0
    try:
        tenant = db.tenant_by_slug(conn, slug)
        if tenant is None:
            raise SystemExit(f"unknown tenant: {slug}")
        due = due_subscriptions(conn, tenant["id"], run_date)
        usage = load_usage(conn, tenant["id"], run_date)
        log.info(kv(event="invoice_run_start", tenant=slug, date=run_date, due=len(due), usage_records=len(usage)))
        drafts = build_drafts(due, usage, run_date)
        seq = invoicing.next_number(conn, tenant)
        for i, draft in enumerate(drafts, 1):
            if invoicing.write_invoice(conn, tenant, draft, seq, run_date.isoformat()):
                created += 1
                seq += 1
            else:
                skipped += 1
            if i % settings.INVOICE_BATCH_SIZE == 0:
                conn.commit()
        conn.commit()
    finally:
        if own:
            conn.close()
    log.info(kv(event="invoice_run_done", tenant=slug, date=run_date, created=created, skipped=skipped,
                ms=f"{(time.perf_counter() - t0) * 1000:.0f}"))
    return {"created": created, "skipped": skipped, "due": len(due)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tenant")
    ap.add_argument("--date", type=dt.date.fromisoformat, default=None)
    a = ap.parse_args()
    out = run(a.tenant, a.date)
    print(f"{out['created']} invoices created, {out['skipped']} already issued ({out['due']} due)")


if __name__ == "__main__":
    main()
