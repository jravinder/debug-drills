-- 001: initial schema (2022-02)
CREATE TABLE tenants (
    id              INTEGER PRIMARY KEY,
    slug            TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    plan            TEXT NOT NULL DEFAULT 'standard',
    utc_offset_min  INTEGER NOT NULL,          -- carrier's home clock, e.g. -480 for UTC-8
    created_at      TEXT NOT NULL
);

CREATE TABLE depots (
    id          INTEGER PRIMARY KEY,
    tenant_id   INTEGER NOT NULL REFERENCES tenants(id),
    code        TEXT NOT NULL,
    name        TEXT NOT NULL,
    city        TEXT NOT NULL,
    region      TEXT NOT NULL,
    doors       INTEGER NOT NULL,
    status      TEXT NOT NULL DEFAULT 'active',
    UNIQUE (tenant_id, code)
);

CREATE TABLE drivers (
    id          INTEGER PRIMARY KEY,
    tenant_id   INTEGER NOT NULL REFERENCES tenants(id),
    depot_id    INTEGER NOT NULL REFERENCES depots(id),
    name        TEXT NOT NULL,
    license     TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'active'
);

CREATE TABLE shipments (
    id              INTEGER PRIMARY KEY,
    tenant_id       INTEGER NOT NULL REFERENCES tenants(id),
    pro             TEXT NOT NULL,              -- carrier tracking number
    customer        TEXT NOT NULL,
    origin_depot_id INTEGER NOT NULL REFERENCES depots(id),
    dest_depot_id   INTEGER NOT NULL REFERENCES depots(id),
    service         TEXT NOT NULL,              -- standard | express
    weight_kg       REAL NOT NULL,
    pieces          INTEGER NOT NULL,
    tendered_on     TEXT NOT NULL,              -- 'YYYY-MM-DD', origin depot's day
    status          TEXT NOT NULL,
    UNIQUE (tenant_id, pro)
);

-- A shipment moves as one or more legs; relay legs point at the leg they continue.
CREATE TABLE legs (
    id              INTEGER PRIMARY KEY,
    tenant_id       INTEGER NOT NULL REFERENCES tenants(id),
    shipment_id     INTEGER NOT NULL REFERENCES shipments(id),
    parent_leg_id   INTEGER REFERENCES legs(id),
    from_depot_id   INTEGER NOT NULL REFERENCES depots(id),
    to_depot_id     INTEGER NOT NULL REFERENCES depots(id),
    driver_id       INTEGER NOT NULL REFERENCES drivers(id),
    departed_at     TEXT NOT NULL,              -- UTC
    arrived_at      TEXT NOT NULL               -- UTC
);

CREATE TABLE stops (
    id              INTEGER PRIMARY KEY,
    tenant_id       INTEGER NOT NULL REFERENCES tenants(id),
    shipment_id     INTEGER NOT NULL REFERENCES shipments(id),
    leg_id          INTEGER NOT NULL REFERENCES legs(id),
    depot_id        INTEGER NOT NULL REFERENCES depots(id),
    driver_id       INTEGER NOT NULL REFERENCES drivers(id),
    kind            TEXT NOT NULL,              -- pickup | transfer | delivery
    window_end      TEXT NOT NULL,              -- promised-by, depot local wall clock, 'YYYY-MM-DD HH:MM:SS'
    arrived_at      TEXT NOT NULL               -- driver app scan, UTC, 'YYYY-MM-DD HH:MM:SS'
);

CREATE INDEX idx_depots_tenant ON depots (tenant_id);
CREATE INDEX idx_drivers_tenant ON drivers (tenant_id, depot_id);
CREATE INDEX idx_shipments_tenant_day ON shipments (tenant_id, tendered_on);
CREATE INDEX idx_legs_tenant ON legs (tenant_id);
CREATE INDEX idx_legs_shipment ON legs (shipment_id);
CREATE INDEX idx_stops_shipment ON stops (shipment_id);
CREATE INDEX idx_stops_tenant_arrived ON stops (tenant_id, arrived_at);
