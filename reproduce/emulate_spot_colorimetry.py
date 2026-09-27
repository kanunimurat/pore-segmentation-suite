#!/usr/bin/env python3
"""
Emulates a contact-colorimeter protocol on the scanned pre/post images
(Supplementary Note S1 of the SoftwareX paper, v1.3.3).

A contact colorimeter reads small spots (e.g. 8 mm, on a 3 x 3 grid) and the
colour change of a specimen is then usually reported as the MEAN OF THE LOCAL
dE00 values. The Aging mode of the software instead reports the dE00 BETWEEN
THE MEAN COLOURS of the whole specimen faces. The two estimands differ (the
mean of local differences is never smaller than the difference of the means),
so this script computes, for every specimen pair,

  grid_dE00_mean      mean of the nine spot dE00 values (colorimeter-like)
  grid_dE00_of_means  dE00 between the mean spot colours
  (the whole-surface value is given by reproduce_dataset_matrix.py)

Spots are placed at the centres of a 3 x 3 grid over the bounding box of the
specimen (dark border-connected background removed); the pixel size follows
from the known face width (default 150 mm).

    python reproduce/emulate_spot_colorimetry.py ROOT --out results/
Layout of ROOT as for reproduce_dataset_matrix.py.
"""
import argparse
import csv
import glob
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "reproduce"))

from modules import color_science as cs, utils  # noqa: E402
from reproduce_dataset_matrix import SALTS, STONES, find_dir  # noqa: E402


def spot_labs(img, face_mm=150.0, spot_mm=8.0, grid=3):
    """Mean CIELAB of circular spots on a grid x grid layout; returns (labs, pixel size in mm)."""
    from skimage.color import rgb2lab
    m = cs.specimen_mask(img)
    ys, xs = np.nonzero(m)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    px = face_mm / (x1 - x0 + 1)
    r = spot_mm / 2.0 / px
    yy, xx = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    labs = []
    for i in range(grid):
        for j in range(grid):
            cy = y0 + (i + 0.5) * (y1 - y0) / grid
            cx = x0 + (j + 0.5) * (x1 - x0) / grid
            disc = (yy - cy) ** 2 + (xx - cx) ** 2 <= r * r
            labs.append(rgb2lab(np.asarray(img)[disc][None, :, :3] / 255.0)[0].mean(axis=0))
    return labs, px


def pair_metrics(img_pre, img_post, face_mm=150.0, spot_mm=8.0, grid=3):
    a, pa = spot_labs(img_pre, face_mm, spot_mm, grid)
    b, pb = spot_labs(img_post, face_mm, spot_mm, grid)
    local = [cs.delta_e_lab(tuple(x), tuple(y), "2000") for x, y in zip(a, b)]
    return dict(grid_dE00_mean=float(np.mean(local)),
                grid_dE00_of_means=float(cs.delta_e_lab(tuple(np.mean(a, 0)), tuple(np.mean(b, 0)), "2000")),
                px_pre_mm=pa, px_post_mm=pb)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root")
    ap.add_argument("--face-mm", type=float, default=150.0)
    ap.add_argument("--spot-mm", type=float, default=8.0)
    ap.add_argument("--grid", type=int, default=3)
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
                    print("missing", sid)
                    continue
                m = pair_metrics(utils.load_image(p[0]), utils.load_image(q[0]), a.face_mm, a.spot_mm, a.grid)
                rows.append(dict(stone=sc, salt=salt, specimen=sid, **{k: round(v, 4) for k, v in m.items()}))
                print(sid, round(m["grid_dE00_mean"], 2), round(m["grid_dE00_of_means"], 2))
    with open(os.path.join(a.out, "spot_colorimetry_pairs.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
