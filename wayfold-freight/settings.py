"""Runtime configuration. Everything can be overridden with WAYFOLD_* environment variables."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _env(name, default):
    return os.environ.get(f"WAYFOLD_{name}", default)


DB_PATH = _env("DB_PATH", os.path.join(BASE_DIR, "wayfold.db"))
LOG_DIR = _env("LOG_DIR", os.path.join(BASE_DIR, "logs"))
LOG_LEVEL = _env("LOG_LEVEL", "INFO")
EXPORT_DIR = _env("EXPORT_DIR", os.path.join(BASE_DIR, "out"))

# Dashboard windows (days)
KPI_WINDOW_DAYS = int(_env("KPI_WINDOW_DAYS", "30"))
CHART_WINDOW_DAYS = int(_env("CHART_WINDOW_DAYS", "90"))

# Lists
SHIPMENTS_PER_PAGE = int(_env("SHIPMENTS_PER_PAGE", "50"))
DRIVERS_PER_PAGE = int(_env("DRIVERS_PER_PAGE", "50"))

# Depot scorecard: accounts with many depots get the aggregate memoised in-process.
SCORECARD_CACHE_MIN_DEPOTS = int(_env("SCORECARD_CACHE_MIN_DEPOTS", "40"))
SCORECARD_CACHE_SECONDS = int(_env("SCORECARD_CACHE_SECONDS", "600"))

APP_ENV = _env("ENV", "dev")
