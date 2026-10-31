"""key=value logs with millisecond timestamps, to stdout and logs/app.log."""
import logging
import os

import settings

FORMAT = "%(asctime)s.%(msecs)03d level=%(levelname)s logger=%(name)s %(message)s"
DATEFMT = "%Y-%m-%dT%H:%M:%S"
_configured = False


def configure():
    global _configured
    if _configured:
        return
    os.makedirs(settings.LOG_DIR, exist_ok=True)
    fmt = logging.Formatter(FORMAT, DATEFMT)
    root = logging.getLogger("harbor")
    root.setLevel(settings.LOG_LEVEL)
    for h in (logging.StreamHandler(), logging.FileHandler(os.path.join(settings.LOG_DIR, "app.log"))):
        h.setFormatter(fmt)
        root.addHandler(h)
    root.propagate = False
    _configured = True


def kv(**fields):
    return " ".join(f"{k}={v}" for k, v in fields.items())
