#!/usr/bin/env python3
"""
Regenerates the full aging matrix (Supplementary Table S1: 4 travertines x
4 salts x n = 6) from the raw pre/post images, with both the v1.3.0 dE00
(from mean CIELAB) and the legacy v1.2.x value.

Expected layout (as in the project archive):
    ROOT/<Stone folder>/JPEG/Tuz Öncesi/<ID>_*.jpg
    ROOT/<Stone folder>/JPEG/Tuz Sonrası/<ID>_*.jpg
with IDs such as KT-A1 ... PT-D6 (A = Na2SO4, B = MgSO4, C = NaCl, D = KCl).

Usage:
    python reproduce/reproduce_dataset_matrix.py ROOT --out results/
"""
import argparse
import csv
import glob
import os
import sys
import unicodedata

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "reproduce"))

from modules import aging_analysis as aa, color_science as cs, utils  # noqa: E402
from reproduce_aging_example import legacy_delta_e  # noqa: E402

STONES = {"KT": "Karaman Traverten", "GT": "Gri Traverten",
          "NT": "Noçe Traverten", "PT": "Pembe Traverten"}
SALTS = {"A": "Na2SO4", "B": "MgSO4", "C": "NaCl", "D": "KCl"}


def find_dir(root, name):
    target = unicodedata.normalize("NFC", name)
    for d in os.listdir(root):
        if unicodedata.normalize("NFC", d) == target:
            return os.path.join(root, d)
    raise FileNotFoundError(name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--out", default="results")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rows = []
    for sc, folder in STONES.items():
        jpeg = os.path.join(find_dir(a.root, folder), "JPEG")
        pre_dir, post_dir = find_dir(jpeg, "Tuz Öncesi"), find_dir(jpeg, "Tuz Sonrası")
        for salt_code, salt in SALTS.items():
            for i in range(1, 7):
                sid = f"{sc}-{salt_code}{i}"
                p = glob.glob(os.path.join(pre_dir, sid + "_*.jpg"))
                q = glob.glob(os.path.join(post_dir, sid + "_*.jpg"))
                if len(p) != 1 or len(q) != 1:
                    print("missing", sid, p, q)
                    continue
                r = aa.compute_pair_color_change(utils.load_image(p[0]), utils.load_image(q[0]), "2000", sample_name=sid)
                rows.append(dict(stone=sc, salt=salt, specimen=sid,
                                 pre_file=os.path.basename(p[0]), post_file=os.path.basename(q[0]),
                                 pre_L=r["pre_L"], pre_a=r["pre_a"], pre_b=r["pre_b"],
                                 post_L=r["post_L"], post_a=r["post_a"], post_b=r["post_b"],
                                 dL=r["delta_L"], da=r["delta_a"], db=r["delta_b"],
                                 dE00=r["delta_e"], dE00_legacy=round(legacy_delta_e(r), 2),
                                 dEab=round(cs.delta_e_lab((r["pre_L"], r["pre_a"], r["pre_b"]),
                                                           (r["post_L"], r["post_a"], r["post_b"]), "76"), 2)))
                print(sid, rows[-1]["dE00"], rows[-1]["dE00_legacy"])
    with open(os.path.join(a.out, "S1_pairs_all.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(a.out, "S1_matrix.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["stone", "salt", "n", "dE00_mean", "dE00_sd", "dE00_legacy_mean", "dE00_legacy_sd",
                    "dL_mean", "cv_dE00", "dEab_mean"])
        for sc in STONES:
            for salt in SALTS.values():
                sel = [r for r in rows if r["stone"] == sc and r["salt"] == salt]
                de = np.array([r["dE00"] for r in sel]); lg = np.array([r["dE00_legacy"] for r in sel])
                w.writerow([sc, salt, len(sel), round(de.mean(), 2), round(de.std(ddof=1), 2),
                            round(lg.mean(), 2), round(lg.std(ddof=1), 2),
                            round(np.mean([r["dL"] for r in sel]), 2), round(de.std(ddof=1) / de.mean(), 2),
                            round(np.mean([r["dEab"] for r in sel]), 2)])


if __name__ == "__main__":
    main()
