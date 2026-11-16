# Brookmeter

- Setup + run: `make up` (creates `.venv`, seeds `brookmeter.db` if missing, serves http://127.0.0.1:8767)
- Test: `make test` (pytest, uses its own temp database)
- Bench (app must be running): `make bench`
- Nightly invoice run by hand: `.venv/bin/python jobs/invoice_run.py <tenant-slug> [--date YYYY-MM-DD]`
- Reseed: `make seed`. Reset to the starting state: `make reset`
- Tenants: `pinecrest-labs` (small), `halvard` (large)
