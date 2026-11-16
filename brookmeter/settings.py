"""Runtime configuration. Everything can be overridden with BROOK_* environment variables."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _env(name, default):
    return os.environ.get(f"BROOK_{name}", default)


DB_PATH = _env("DB_PATH", os.path.join(BASE_DIR, "brookmeter.db"))
LOG_DIR = _env("LOG_DIR", os.path.join(BASE_DIR, "logs"))
LOG_LEVEL = _env("LOG_LEVEL", "INFO")

# Dashboard windows
KPI_WINDOW_DAYS = int(_env("KPI_WINDOW_DAYS", "30"))
CHART_MONTHS = int(_env("CHART_MONTHS", "6"))
USAGE_WINDOW_DAYS = int(_env("USAGE_WINDOW_DAYS", "30"))

# Tables
SUBSCRIPTIONS_PER_PAGE = int(_env("SUBSCRIPTIONS_PER_PAGE", "25"))
INVOICES_PER_PAGE = int(_env("INVOICES_PER_PAGE", "50"))

# Invoice run: invoices are committed in batches so a long run does not hold the write lock
INVOICE_BATCH_SIZE = int(_env("INVOICE_BATCH_SIZE", "500"))

APP_ENV = _env("ENV", "dev")
