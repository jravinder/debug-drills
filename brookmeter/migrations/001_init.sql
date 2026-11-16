-- 001: initial schema (2022-02)
CREATE TABLE tenants (
    id              INTEGER PRIMARY KEY,
    slug            TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    plan            TEXT NOT NULL DEFAULT 'standard',
    invoice_prefix  TEXT NOT NULL,
    created_at      TEXT NOT NULL
);

CREATE TABLE customers (
    id          INTEGER PRIMARY KEY,
    tenant_id   INTEGER NOT NULL REFERENCES tenants(id),
    name        TEXT NOT NULL,
    email       TEXT NOT NULL,
    country     TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE TABLE plans (
    id            INTEGER PRIMARY KEY,
    tenant_id     INTEGER NOT NULL REFERENCES tenants(id),
    code          TEXT NOT NULL,
    name          TEXT NOT NULL,
    interval      TEXT NOT NULL CHECK (interval IN ('month', 'year')),
    amount_cents  INTEGER NOT NULL,           -- per seat, per billing interval
    UNIQUE (tenant_id, code)
);

CREATE TABLE subscriptions (
    id            INTEGER PRIMARY KEY,
    tenant_id     INTEGER NOT NULL REFERENCES tenants(id),
    customer_id   INTEGER NOT NULL REFERENCES customers(id),
    plan_id       INTEGER NOT NULL REFERENCES plans(id),
    status        TEXT NOT NULL CHECK (status IN ('trialing', 'active', 'past_due', 'canceled')),
    quantity      INTEGER NOT NULL DEFAULT 1,
    anchor_day    INTEGER NOT NULL CHECK (anchor_day BETWEEN 1 AND 28),
    anchor_month  INTEGER NOT NULL CHECK (anchor_month BETWEEN 1 AND 12),
    started_on    TEXT NOT NULL,
    canceled_on   TEXT
);

CREATE TABLE invoices (
    id               INTEGER PRIMARY KEY,
    tenant_id        INTEGER NOT NULL REFERENCES tenants(id),
    subscription_id  INTEGER NOT NULL REFERENCES subscriptions(id),
    number           TEXT NOT NULL,
    period_start     TEXT NOT NULL,          -- 'YYYY-MM-DD', inclusive
    period_end       TEXT NOT NULL,          -- 'YYYY-MM-DD', exclusive
    issued_on        TEXT NOT NULL,
    status           TEXT NOT NULL CHECK (status IN ('open', 'paid', 'void')),
    total_cents      INTEGER NOT NULL
);

CREATE TABLE invoice_lines (
    id                 INTEGER PRIMARY KEY,
    invoice_id         INTEGER NOT NULL REFERENCES invoices(id),
    kind               TEXT NOT NULL,        -- 'plan' | 'usage'
    description        TEXT NOT NULL,
    quantity           INTEGER NOT NULL,
    unit_amount_cents  REAL NOT NULL,
    amount_cents       INTEGER NOT NULL
);

CREATE INDEX idx_customers_tenant ON customers (tenant_id);
CREATE INDEX idx_subscriptions_tenant ON subscriptions (tenant_id, status);
CREATE INDEX idx_invoices_tenant_issued ON invoices (tenant_id, issued_on);
CREATE INDEX idx_invoice_lines_invoice ON invoice_lines (invoice_id);
