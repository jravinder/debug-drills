-- 002: usage-based pricing. Plans may carry a meter with a per-unit price in cents (2023-05)
ALTER TABLE plans ADD COLUMN meter TEXT;
ALTER TABLE plans ADD COLUMN unit_price_cents REAL;

CREATE TABLE usage_records (
    id               INTEGER PRIMARY KEY,
    tenant_id        INTEGER NOT NULL REFERENCES tenants(id),
    subscription_id  INTEGER NOT NULL REFERENCES subscriptions(id),
    meter            TEXT NOT NULL,
    quantity         INTEGER NOT NULL,
    recorded_at      TEXT NOT NULL           -- UTC, 'YYYY-MM-DD HH:MM:SS'
);
CREATE INDEX idx_usage_tenant_recorded ON usage_records (tenant_id, recorded_at);
