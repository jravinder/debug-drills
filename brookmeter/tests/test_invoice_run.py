import datetime as dt
import random
import time

import pytest

from jobs import invoice_run
from tests.conftest import BIG, SMALL, billing_days, tenant_id

# One run date per scenario so tests do not see each other's invoices.
RUN_DAY, RERUN_DAY, LATE_DAY = billing_days(3)


def invoices_for(conn, slug, day):
    return conn.execute("""
        SELECT i.* FROM invoices i JOIN tenants t ON t.id = i.tenant_id
         WHERE t.slug = ? AND i.issued_on = ?""", (slug, day.isoformat())).fetchall()


def test_period_monthly_and_annual():
    d = dt.date(2026, 3, 14)
    assert invoice_run.period(d, "month") == ("2026-02-14", "2026-03-14")
    assert invoice_run.period(d, "year") == ("2025-03-14", "2026-03-14")
    assert invoice_run.period(dt.date(2026, 1, 5), "month") == ("2025-12-05", "2026-01-05")


@pytest.mark.parametrize("slug", [SMALL, BIG])
def test_run_invoices_every_due_subscription_once(conn, slug):
    out = invoice_run.run(slug, RUN_DAY)
    rows = invoices_for(conn, slug, RUN_DAY)
    assert out["created"] == out["due"] == len(rows)
    assert len({r["subscription_id"] for r in rows}) == len(rows)


@pytest.mark.parametrize("slug", [SMALL, BIG])
def test_invoice_totals_equal_sum_of_lines(conn, slug):
    for inv in invoices_for(conn, slug, RUN_DAY):
        lines = conn.execute("SELECT SUM(amount_cents) FROM invoice_lines WHERE invoice_id = ?", (inv["id"],)).fetchone()
        assert inv["total_cents"] == lines[0]


@pytest.mark.parametrize("slug", [SMALL, BIG])
def test_usage_lines_charge_quantity_times_rate(conn, slug):
    lines = conn.execute("""
        SELECT l.* FROM invoice_lines l JOIN invoices i ON i.id = l.invoice_id JOIN tenants t ON t.id = i.tenant_id
         WHERE t.slug = ? AND i.issued_on = ? AND l.kind = 'usage'""", (slug, RUN_DAY.isoformat())).fetchall()
    if slug == BIG:
        assert lines, "expected metered subscriptions on the run date"
    for l in lines:
        assert l["amount_cents"] == round(l["quantity"] * l["unit_amount_cents"]), dict(l)


@pytest.mark.parametrize("slug", [SMALL, BIG])
def test_rerun_same_day_is_a_no_op(conn, slug):
    first = invoice_run.run(slug, RERUN_DAY)
    again = invoice_run.run(slug, RERUN_DAY)
    assert again["created"] == 0 and again["skipped"] == first["created"]
    assert len(invoices_for(conn, slug, RERUN_DAY)) == first["created"]


def test_retry_after_late_usage_does_not_issue_second_invoice(conn):
    # Halvard's usage pipeline delivers events up to a few hours late, so a retried run can see more usage.
    invoice_run.run(BIG, LATE_DAY)
    inv = conn.execute("""
        SELECT i.subscription_id, i.period_start FROM invoices i JOIN invoice_lines l ON l.invoice_id = i.id
         WHERE i.tenant_id = ? AND i.issued_on = ? AND l.kind = 'usage' LIMIT 1""",
                       (tenant_id(conn, BIG), LATE_DAY.isoformat())).fetchone()
    assert inv is not None
    conn.execute("INSERT INTO usage_records (tenant_id, subscription_id, meter, quantity, recorded_at) "
                 "VALUES (?, ?, 'api_calls', 250, ?)", (tenant_id(conn, BIG), inv["subscription_id"],
                                                         f"{inv['period_start']} 12:00:00"))
    conn.commit()
    invoice_run.run(BIG, LATE_DAY)
    n = conn.execute("SELECT COUNT(*) FROM invoices WHERE subscription_id = ? AND period_start = ?",
                     (inv["subscription_id"], inv["period_start"])).fetchone()[0]
    assert n == 1


def test_invoice_drafts_scale_to_large_accounts():
    # Sized like a busy Halvard billing day: ~1.2k due subscriptions against a month of usage.
    rng = random.Random(11)
    due = [{"id": i, "quantity": 1, "customer": "c", "plan_name": "Pro", "interval": "month", "amount_cents": 4900,
            "meter": "api_calls", "unit_price_cents": 0.03} for i in range(1200)]
    usage = [{"subscription_id": rng.randrange(8000), "quantity": rng.randint(1, 40)} for _ in range(120_000)]
    t = time.perf_counter()
    drafts = invoice_run.build_drafts(due, usage, dt.date(2026, 3, 14))
    elapsed = time.perf_counter() - t
    assert len(drafts) == 1200
    assert elapsed < 1.0, f"build_drafts took {elapsed:.1f}s"
