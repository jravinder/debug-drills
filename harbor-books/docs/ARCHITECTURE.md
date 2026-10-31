# Architecture

One FastAPI process, server-rendered with Jinja2, SQLite on local disk. Two chart endpoints return JSON. A cron job writes the reorder CSV per tenant every night.

```mermaid
flowchart LR
  B[Browser] -->|HTML| P[routes/pages.py]
  B -->|fetch JSON| A[routes/api.py]
  P --> S[services/*]
  A --> S
  S --> D[(SQLite harbor.db)]
  C[cron 02:15 / 02:20] --> J[jobs/reorder_export.py]
  J --> D
  J --> O[out/reorder/*.csv]
  O -->|buyers upload| SP[Supplier portal]
```

## Request path

```mermaid
sequenceDiagram
  participant U as Browser
  participant M as timing middleware
  participant R as route
  participant Q as services
  participant DB as SQLite
  U->>M: GET /t/{tenant}/dashboard
  M->>R: start query counter
  R->>Q: kpis, categories, top stores, low stock
  Q->>DB: SQL (each statement counted)
  R-->>M: rendered HTML
  M-->>U: X-Query-Count, X-Response-Time-Ms, log line
  U->>R: GET /api/t/{tenant}/revenue-series
```

## Data model

```mermaid
erDiagram
  tenants ||--o{ stores : has
  tenants ||--o{ titles : catalogs
  stores ||--o{ sale_lines : records
  titles ||--o{ sale_lines : sold_as
  stores ||--o{ inventory : stocks
  titles ||--o{ inventory : stocked_as
```

- Money is integer cents. Net = `qty * unit_price_cents - discount_cents`.
- `sold_at` is local time text, `YYYY-MM-DD HH:MM:SS`; range filters are string comparisons.
- Every query is scoped by `tenant_id` (stores, titles, sale_lines) or through `stores` (inventory).
- `titles.case_pack` arrived with supplier feed v2 (migration 002). Older tenants default to 1.

## Conventions

- One SQLite connection per request (`harbor.db.get_conn`), foreign keys on.
- Schema changes are new numbered files in `migrations/`; never edit an applied one.
- Logs: `logs/app.log`, key=value, millisecond timestamps.
- Config: `settings.py`, env overrides `HARBOR_*`.

## Tech debt

- No caching layer anywhere.
- Charts load Chart.js from a CDN; no offline fallback.
- No auth in this build (fronted by the SSO proxy in production).
- `seed.py` is the only fixture source; tests use its `test` profile.
