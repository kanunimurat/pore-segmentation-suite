"""v1.3.1: benchmark_algorithms.py --palette none runs the nine palette-free methods only."""
import csv
import os
import subprocess
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "reproduce", "benchmark_algorithms.py")


def _run(tmp_path, palette):
    rng = np.random.default_rng(1)
    img = np.full((160, 160, 3), 200, np.uint8)
    for _ in range(25):
        y, x = rng.integers(10, 150, 2)
        img[y - 3:y + 3, x - 3:x + 3] = 40
    p = tmp_path / "SYN-1.png"
    Image.fromarray(img).save(p)
    out = tmp_path / palette
    subprocess.run([sys.executable, SCRIPT, str(p), "--palette", palette, "--repeats", "1", "--out", str(out)],
                   check=True, capture_output=True)
    with open(out / "SYN-1_benchmark.csv", encoding="utf-8") as fh:
        return {r["algorithm"]: float(r["porosity_pct"]) for r in csv.DictReader(fh)}


def test_palette_none_skips_palette_methods_only(tmp_path):
    sys.path.insert(0, os.path.join(ROOT, "reproduce"))
    import benchmark_algorithms as bench
    with_pal = _run(tmp_path, "KT")
    without = _run(tmp_path, "none")
    assert len(with_pal) == 12 and len(without) == 9
    assert set(with_pal) - set(without) == set(bench.PALETTE_METHODS)
    for name, value in without.items():          # palette-free methods are unaffected
        assert value == with_pal[name]
