"""The ONLY file with app-specific values. Everything else in the drill kit reads from here.

Shell use: python3 scripts/drill_config.py <key>   (prints the value)
"""
import sys

NAME = "harbor-books"
SCHEMA_VERSION = 3
START_TAG = "drill-start"
HOST = "127.0.0.1"
PORT = 8765
VENV_PY = ".venv/bin/python"
SETUP_CMD = f"[ -x {VENV_PY} ] || (python3 -m venv .venv && {VENV_PY} -m pip install -q --disable-pip-version-check -r requirements.txt)"
SEED_CMD = f"{VENV_PY} seed.py"
START_CMD = f"{VENV_PY} -m uvicorn harbor.app:app --host {HOST} --port {PORT} --no-access-log"
TESTS_DIR = "tests"
DB_FILE = "harbor.db"

TENANTS = ["tidewater-books", "lanternfield"]

# (label, path template, requests) hit against the running app by bench.py
BENCH_ENDPOINTS = [
    ("dashboard", "/t/{tenant}/dashboard", 3),
    ("stores", "/t/{tenant}/stores?sort=revenue", 3),
    ("revenue api", "/api/t/{tenant}/revenue-series", 3),
]
# (label, argv template) run once per tenant by bench.py
BENCH_JOBS = [
    ("reorder job", ["{python}", "jobs/reorder_export.py", "{tenant}"]),
]

BASE_URL = f"http://{HOST}:{PORT}"

if __name__ == "__main__":
    print(globals()[sys.argv[1].upper()])
