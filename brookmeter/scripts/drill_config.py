"""The ONLY file with app-specific values. Everything else in the drill kit reads from here.

Shell use: python3 scripts/drill_config.py <key>   (prints the value)
"""
import datetime as _dt
import sys

NAME = "brookmeter"
SCHEMA_VERSION = 3
START_TAG = "drill-start"
HOST = "127.0.0.1"
PORT = 8767
VENV_PY = ".venv/bin/python"
SETUP_CMD = f"[ -x {VENV_PY} ] || (python3 -m venv .venv && {VENV_PY} -m pip install -q --disable-pip-version-check -r requirements.txt)"
SEED_CMD = f"{VENV_PY} seed.py"
START_CMD = f"{VENV_PY} -m uvicorn brookmeter.app:app --host {HOST} --port {PORT} --no-access-log"
TESTS_DIR = "tests"
DB_FILE = "brookmeter.db"

TENANTS = ["pinecrest-labs", "halvard"]

# (label, path template, requests) hit against the running app by bench.py
BENCH_ENDPOINTS = [
    ("dashboard", "/t/{tenant}/dashboard", 3),
    ("subscriptions", "/t/{tenant}/subscriptions?status=active", 3),
    ("usage api", "/api/t/{tenant}/usage-daily", 3),
]
# The invoice run bills subscriptions whose anchor day matches the run date.
# Pin it to the most recent 15th so every bench run bills a full day's batch;
# on the 29th to 31st few or no subscriptions are due and the timing shows nothing.
_today = _dt.date.today()
_run = _today.replace(day=15)
if _run > _today:
    _run = (_today.replace(day=1) - _dt.timedelta(days=1)).replace(day=15)
BENCH_RUN_DATE = _run.isoformat()

# (label, argv template) run once per tenant by bench.py
BENCH_JOBS = [
    ("invoice run", ["{python}", "jobs/invoice_run.py", "{tenant}", "--date", BENCH_RUN_DATE]),
]

BASE_URL = f"http://{HOST}:{PORT}"

if __name__ == "__main__":
    print(globals()[sys.argv[1].upper()])
