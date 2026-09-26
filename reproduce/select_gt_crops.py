#!/usr/bin/env python3
"""
Pre-registered, seeded selection of the crops to be annotated manually
(ground truth for the segmentation accuracy study, Section 3.3).

For every stone group the script picks images and crop positions with a fixed
random seed, BEFORE any annotation and without looking at algorithm output, so
that the crops cannot be chosen to favour a method. Positions are uniform over
the image with a margin from the edge; crops taken from the same image never
overlap. Crops are written losslessly (PNG).

    python reproduce/select_gt_crops.py IMG [IMG ...] --group-by-prefix \
        --crops-per-group 2 --size 512 --seed 20260926 --out gt/crops

Writes <out>/<crop_id>.png and <out>/crops.csv
(crop_id, group, image, image_sha256, x0, y0, size, priority, seed).
Priority 1 = first crop of each group (mandatory); 2 = optional.
--distinct-images draws the crops of a group from different images (used for the
tuffs, whose ~1050 px images cannot hold two non-overlapping 512 px crops).
"""
import argparse
import csv
import hashlib
import os
import sys
from collections import OrderedDict

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from modules import utils  # noqa: E402


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def group_of(path, by_prefix):
    stem = os.path.splitext(os.path.basename(path))[0]
    return stem.split("-")[0] if by_prefix else stem


def select(images, crops_per_group, size, margin, seed, by_prefix, distinct_images=False):
    rng = np.random.default_rng(seed)
    groups = OrderedDict()
    for p in sorted(images):
        groups.setdefault(group_of(p, by_prefix), []).append(p)
    plan = []
    for g, paths in groups.items():
        if distinct_images and crops_per_group > len(paths):
            raise ValueError(f"group {g}: {crops_per_group} crops requested but only {len(paths)} images")
        unused = list(paths)
        for k in range(crops_per_group):
            if distinct_images:          # each crop from a different specimen (drawn without replacement)
                p = unused.pop(int(rng.integers(len(unused))))
            else:
                p = paths[int(rng.integers(len(paths)))]
            h, w = np.asarray(Image.open(p)).shape[:2]
            if h < size + 2 * margin or w < size + 2 * margin:
                raise ValueError(f"{p} is smaller than crop + margins")
            # redraw until the crop does not overlap an earlier crop of the same image
            for _ in range(1000):
                x0 = int(rng.integers(margin, w - size - margin + 1))
                y0 = int(rng.integers(margin, h - size - margin + 1))
                if all(c["path"] != p or abs(c["x0"] - x0) >= size or abs(c["y0"] - y0) >= size
                       for c in plan):
                    break
            else:
                raise RuntimeError(f"no non-overlapping crop position found in {p}")
            plan.append(dict(crop_id=f"{g}_c{k + 1}", group=g, image=os.path.basename(p), path=p,
                             x0=x0, y0=y0, size=size, priority=1 if k == 0 else 2, seed=seed))
    return plan


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("images", nargs="+")
    ap.add_argument("--group-by-prefix", action="store_true",
                    help="group images by the part of the file name before the first '-' (e.g. KT-A1 -> KT)")
    ap.add_argument("--crops-per-group", type=int, default=2)
    ap.add_argument("--size", type=int, default=512)
    ap.add_argument("--margin", type=int, default=32)
    ap.add_argument("--seed", type=int, default=20260926)
    ap.add_argument("--distinct-images", action="store_true",
                    help="draw each crop of a group from a different image (without replacement); needed when "
                         "images are too small for two non-overlapping crops")
    ap.add_argument("--out", default="gt/crops")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    plan = select(a.images, a.crops_per_group, a.size, a.margin, a.seed, a.group_by_prefix, a.distinct_images)
    with open(os.path.join(a.out, "crops.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["crop_id", "group", "image", "image_sha256", "x0", "y0",
                                           "size", "priority", "seed"])
        w.writeheader()
        for c in plan:
            arr = utils.load_image(c["path"])        # colour-managed (v1.3.1): sRGB
            Image.fromarray(arr[c["y0"]:c["y0"] + c["size"], c["x0"]:c["x0"] + c["size"]]).save(
                os.path.join(a.out, f"{c['crop_id']}.png"))
            row = {k: c[k] for k in w.fieldnames if k in c}
            row["image_sha256"] = sha256(c["path"])
            w.writerow(row)
            print(f"{c['crop_id']:8s} {c['image']:10s} x0={c['x0']:4d} y0={c['y0']:4d} priority {c['priority']}")


if __name__ == "__main__":
    main()
