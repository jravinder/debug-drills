-- 003: per-tenant rate cards for the line-haul manifest; enterprise lanes rate by weight (2026-08)
CREATE TABLE rate_cards (
    tenant_id   INTEGER NOT NULL REFERENCES tenants(id),
    service     TEXT NOT NULL,
    base        REAL NOT NULL,      -- dollars per shipment
    per_kg      REAL NOT NULL,      -- dollars per kg
    fuel_pct    REAL NOT NULL,      -- surcharge, percent of linehaul
    PRIMARY KEY (tenant_id, service)
);
