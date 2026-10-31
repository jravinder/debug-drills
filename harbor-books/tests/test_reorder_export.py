import csv

import pytest

from jobs import reorder_export
from tests.conftest import BIG, SMALL


def test_round_up_to_case():
    assert reorder_export.round_up_to_case(7, 6) == (12, 2)
    assert reorder_export.round_up_to_case(0, 12) == (0, 0)


def test_export_small_tenant(tmp_path):
    path, n = reorder_export.run(SMALL, out_dir=str(tmp_path))
    with open(path) as f:
        rows = list(csv.DictReader(f))
    assert n == len(rows) > 0
    assert all(int(r["suggested_qty"]) > 0 for r in rows)


@pytest.mark.parametrize("slug", [SMALL, BIG])
def test_nightly_export_completes_for_every_tenant(tmp_path, slug):
    path, n = reorder_export.run(slug, out_dir=str(tmp_path))
    assert n > 0
