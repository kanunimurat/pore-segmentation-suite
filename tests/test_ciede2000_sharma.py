"""
CIEDE2000 numerical accuracy against the reference data set of

    Sharma, G., Wu, W., & Dalal, E. N. (2005). The CIEDE2000 color-difference
    formula: Implementation notes, supplementary test data, and mathematical
    observations. Color Research & Application, 30(1), 21-30.
    https://doi.org/10.1002/col.20070

The 34 colour pairs (tests/data/ciede2000_test_data.txt) include the
discontinuities of the hue-angle computation that naive implementations
get wrong. Sharma et al. report the expected dE00 to four decimals, so the
tolerance is 1e-4.
"""
import os

import numpy as np
import pytest

from conftest import DATA_DIR
from modules import color_science as cs


def _load_pairs():
    path = os.path.join(DATA_DIR, "ciede2000_test_data.txt")
    pairs = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip() or line.startswith("#"):
                continue
            tok = line.split()
            # columns: pair, 1, L1, a1, b1, ap1, cp1, hp1, hbar1, G, T, SL, SC,
            #          SH, RT, dE, 2, L2, a2, b2, ap2, cp2, hp2
            lab1 = tuple(float(v) for v in tok[2:5])
            de = float(tok[15])
            lab2 = tuple(float(v) for v in tok[17:20])
            pairs.append((int(tok[0]), lab1, lab2, de))
    return pairs


PAIRS = _load_pairs()


def test_reference_file_complete():
    assert len(PAIRS) == 34


@pytest.mark.parametrize("pair_id,lab1,lab2,expected", PAIRS,
                         ids=[f"pair{p[0]:02d}" for p in PAIRS])
def test_ciede2000_matches_sharma_2005(pair_id, lab1, lab2, expected):
    assert cs.delta_e_lab(lab1, lab2, method="2000") == pytest.approx(expected, abs=1e-4)


@pytest.mark.parametrize("pair_id,lab1,lab2,expected", PAIRS[:10],
                         ids=[f"pair{p[0]:02d}" for p in PAIRS[:10]])
def test_ciede2000_is_symmetric(pair_id, lab1, lab2, expected):
    assert cs.delta_e_lab(lab1, lab2) == pytest.approx(cs.delta_e_lab(lab2, lab1), abs=1e-9)


def test_identical_colours_give_zero():
    for method in ("76", "94", "2000"):
        assert cs.delta_e_lab((55.0, 3.0, 12.0), (55.0, 3.0, 12.0), method) == pytest.approx(0.0, abs=1e-12)


def test_cie76_is_euclidean():
    assert cs.delta_e_lab((50, 0, 0), (53, 4, 0), "76") == pytest.approx(5.0, abs=1e-12)
