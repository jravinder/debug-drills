import csv
import decimal

import pytest

from jobs import manifest_export
from tests.conftest import BIG, SMALL


def test_rate_flat_card():
    card = {"base": 95.0, "per_kg": 0.0, "fuel_pct": 0.0}
    assert manifest_export.rate(card, 812.4) == 95.0


def test_manifest_small_tenant_totals(tmp_path):
    path, n = manifest_export.run(SMALL, out_dir=str(tmp_path))
    with open(path) as f:
        rows = list(csv.DictReader(f))
    assert n > 0
    lines = [r for r in rows if r["pro"] not in ("SUBTOTAL", "TOTAL")]
    assert sum(decimal.Decimal(r["charge"]) for r in lines) == decimal.Decimal(rows[-1]["charge"])


@pytest.mark.parametrize("slug", [SMALL, BIG])
def test_nightly_manifest_completes_for_every_tenant(tmp_path, slug):
    path, n = manifest_export.run(slug, out_dir=str(tmp_path))
    assert n > 0
