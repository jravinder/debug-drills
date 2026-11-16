"""The ONLY file with app-specific values. Everything else in the drill kit reads from here.

Shell use: python3 scripts/drill_config.py <key>   (prints the value)
"""
import sys

NAME = "wayfold-freight"
SCHEMA_VERSION = 3
START_TAG = "drill-start"
HOST = "127.0.0.1"
PORT = 8775
VENV_PY = ".venv/bin/python"
SETUP_CMD = f"[ -x {VENV_PY} ] || (python3 -m venv .venv && {VENV_PY} -m pip install -q --disable-pip-version-check -r requirements.txt)"
SEED_CMD = f"{VENV_PY} seed.py"
START_CMD = f"{VENV_PY} -m uvicorn wayfold.app:app --host {HOST} --port {PORT} --no-access-log"
TESTS_DIR = "tests"
DB_FILE = "wayfold.db"

TENANTS = ["brookhollow-cartage", "ironvale-freight"]

# (label, path template, requests) hit against the running app by bench.py
BENCH_ENDPOINTS = [
    ("dashboard", "/t/{tenant}/dashboard", 3),
    ("depots 7d", "/t/{tenant}/depots?days=7", 3),
    ("route api", "/api/t/{tenant}/shipments/10000500/route", 3),
    ("on-time api", "/api/t/{tenant}/on-time-series", 3),
]
# (label, argv template) run once per tenant by bench.py
BENCH_JOBS = [
    ("manifest job", ["{python}", "jobs/manifest_export.py", "{tenant}"]),
]

BASE_URL = f"http://{HOST}:{PORT}"

if __name__ == "__main__":
    print(globals()[sys.argv[1].upper()])
