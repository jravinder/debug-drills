"""Writes invoices produced by the invoice run."""
import hashlib


def fingerprint(draft):
    raw = f"{draft['subscription_id']}|{draft['period_start']}|{draft['total_cents']}"
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def next_number(conn, tenant):
    n = conn.execute("SELECT COUNT(*) FROM invoices WHERE tenant_id = ?", (tenant["id"],)).fetchone()[0]
    return n + 1


def write_invoice(conn, tenant, draft, seq, issued_on):
    """Insert one invoice and its lines. Returns False if this invoice already exists."""
    cur = conn.execute("""
        INSERT OR IGNORE INTO invoices (tenant_id, subscription_id, number, period_start, period_end, issued_on,
                                        status, total_cents, fingerprint)
        VALUES (?, ?, ?, ?, ?, ?, 'open', ?, ?)""",
                       (tenant["id"], draft["subscription_id"], f"{tenant['invoice_prefix']}-{seq:07d}",
                        draft["period_start"], draft["period_end"], issued_on, draft["total_cents"],
                        fingerprint(draft)))
    if cur.rowcount == 0:
        return False
    conn.executemany("""
        INSERT INTO invoice_lines (invoice_id, kind, description, quantity, unit_amount_cents, amount_cents)
        VALUES (?, ?, ?, ?, ?, ?)""",
                     [(cur.lastrowid, l["kind"], l["description"], l["quantity"], l["unit_amount_cents"],
                       l["amount_cents"]) for l in draft["lines"]])
    return True
