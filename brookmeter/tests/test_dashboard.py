import pytest

from brookmeter.services import metrics
from tests.conftest import BIG, SMALL, tenant_id

MONTHS_PER_INTERVAL = {"month": 1, "year": 12}


def ledger_mrr_cents(conn, tid):
    """MRR straight from the subscription ledger: every live subscription's price, per month."""
    rows = conn.execute("""
        SELECT s.quantity, p.amount_cents, p.interval FROM subscriptions s JOIN plans p ON p.id = s.plan_id
         WHERE s.tenant_id = ? AND s.status IN ('active', 'past_due')""", (tid,)).fetchall()
    return sum(r["quantity"] * r["amount_cents"] / MONTHS_PER_INTERVAL[r["interval"]] for r in rows)


@pytest.mark.parametrize("slug", [SMALL, BIG])
def test_mrr_matches_subscription_ledger(conn, slug):
    tid = tenant_id(conn, slug)
    assert abs(metrics.kpis(conn, tid, 30)["mrr_cents"] - ledger_mrr_cents(conn, tid)) <= 1


@pytest.mark.parametrize("slug", [SMALL, BIG])
def test_mrr_by_plan_sums_to_mrr(conn, slug):
    tid = tenant_id(conn, slug)
    total = sum(p["mrr_cents"] for p in metrics.mrr_by_plan(conn, tid))
    assert abs(total - metrics.kpis(conn, tid, 30)["mrr_cents"]) <= len(metrics.mrr_by_plan(conn, tid))


@pytest.mark.parametrize("slug", [SMALL, BIG])
def test_live_count_matches_ledger(conn, slug):
    tid = tenant_id(conn, slug)
    raw = conn.execute("SELECT COUNT(*) FROM subscriptions WHERE tenant_id = ? AND status IN ('active', 'past_due')",
                       (tid,)).fetchone()[0]
    assert metrics.kpis(conn, tid, 30)["live"] == raw


def test_invoiced_by_month_covers_window(conn):
    months = metrics.invoiced_by_month(conn, tenant_id(conn, SMALL), 6)
    assert len(months) == 6 and months[-1]["cents"] >= 0


@pytest.mark.parametrize("slug", [SMALL, BIG])
def test_dashboard_query_budget(client, slug):
    r = client.get(f"/t/{slug}/dashboard")
    assert int(r.headers["X-Query-Count"]) <= 12
