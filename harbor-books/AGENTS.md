# Harbor Books

- Setup + run: `make up` (creates `.venv`, seeds `harbor.db` if missing, serves http://127.0.0.1:8765)
- Test: `make test` (pytest, uses its own temp database)
- Bench (app must be running): `make bench`
- Nightly job by hand: `.venv/bin/python jobs/reorder_export.py <tenant-slug>`
- Reseed: `make seed`. Reset to the starting state: `make reset`
- Tenants: `tidewater-books` (small), `lanternfield` (large)
