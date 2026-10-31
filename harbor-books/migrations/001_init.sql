-- 001: initial schema (2021-03)
CREATE TABLE tenants (
    id          INTEGER PRIMARY KEY,
    slug        TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    plan        TEXT NOT NULL DEFAULT 'standard',
    created_at  TEXT NOT NULL
);

CREATE TABLE stores (
    id          INTEGER PRIMARY KEY,
    tenant_id   INTEGER NOT NULL REFERENCES tenants(id),
    code        TEXT NOT NULL,
    name        TEXT NOT NULL,
    city        TEXT NOT NULL,
    region      TEXT NOT NULL,
    opened_on   TEXT NOT NULL,
    sq_ft       INTEGER NOT NULL,
    status      TEXT NOT NULL DEFAULT 'open',
    UNIQUE (tenant_id, code)
);

CREATE TABLE titles (
    id                INTEGER PRIMARY KEY,
    tenant_id         INTEGER NOT NULL REFERENCES tenants(id),
    isbn              TEXT NOT NULL,
    title             TEXT NOT NULL,
    author            TEXT NOT NULL,
    category          TEXT NOT NULL,
    format            TEXT NOT NULL,
    list_price_cents  INTEGER NOT NULL,
    supplier          TEXT NOT NULL,
    UNIQUE (tenant_id, isbn)
);

CREATE TABLE sale_lines (
    id                INTEGER PRIMARY KEY,
    tenant_id         INTEGER NOT NULL REFERENCES tenants(id),
    store_id          INTEGER NOT NULL REFERENCES stores(id),
    title_id          INTEGER NOT NULL REFERENCES titles(id),
    receipt_no        TEXT NOT NULL,
    sold_at           TEXT NOT NULL,          -- ISO-8601 local time, 'YYYY-MM-DD HH:MM:SS'
    qty               INTEGER NOT NULL,
    unit_price_cents  INTEGER NOT NULL,
    discount_cents    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE inventory (
    store_id       INTEGER NOT NULL REFERENCES stores(id),
    title_id       INTEGER NOT NULL REFERENCES titles(id),
    on_hand        INTEGER NOT NULL,
    reorder_point  INTEGER NOT NULL,
    updated_at     TEXT NOT NULL,
    PRIMARY KEY (store_id, title_id)
);

CREATE INDEX idx_stores_tenant ON stores (tenant_id);
CREATE INDEX idx_titles_tenant ON titles (tenant_id);
