"""Runtime configuration. Everything can be overridden with HARBOR_* environment variables."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _env(name, default):
    return os.environ.get(f"HARBOR_{name}", default)


DB_PATH = _env("DB_PATH", os.path.join(BASE_DIR, "harbor.db"))
LOG_DIR = _env("LOG_DIR", os.path.join(BASE_DIR, "logs"))
LOG_LEVEL = _env("LOG_LEVEL", "INFO")
EXPORT_DIR = _env("EXPORT_DIR", os.path.join(BASE_DIR, "out"))

# Dashboard windows (days)
KPI_WINDOW_DAYS = int(_env("KPI_WINDOW_DAYS", "30"))
CHART_WINDOW_DAYS = int(_env("CHART_WINDOW_DAYS", "90"))

# Stores table
STORES_PER_PAGE = int(_env("STORES_PER_PAGE", "25"))
SALES_PER_PAGE = int(_env("SALES_PER_PAGE", "50"))

# Reorder export: how many days of sell-through to project from, and cover target
REORDER_LOOKBACK_DAYS = int(_env("REORDER_LOOKBACK_DAYS", "28"))
REORDER_COVER_DAYS = int(_env("REORDER_COVER_DAYS", "21"))

# TODO(ops): move to a real secret store once we have more than one environment.
APP_ENV = _env("ENV", "dev")
