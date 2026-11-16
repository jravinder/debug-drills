# Wayfold

- Setup + run: `make up` (creates `.venv`, seeds `wayfold.db` if missing, serves http://127.0.0.1:8775)
- Test: `make test` (pytest, uses its own temp database)
- Bench (app must be running): `make bench`
- Nightly job by hand: `.venv/bin/python jobs/manifest_export.py <tenant-slug> [--date YYYY-MM-DD]`
- Reseed: `make seed`. Reset to the starting state: `make reset`
- Tenants: `brookhollow-cartage` (small), `ironvale-freight` (large)
