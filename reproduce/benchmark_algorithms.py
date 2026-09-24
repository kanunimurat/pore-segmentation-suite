#!/usr/bin/env python3
"""
Reproducible multi-algorithm benchmark (Table 2 / Figure 5 of the SoftwareX paper).

Runs the twelve setup-free algorithms on one image with the SAME default
parameters the graphical interface uses, applies the default post-filter
(min_area = 8 px, must_be_dark = True, dark_thresh_factor = 0.95) and writes

    <out>/<stem>_benchmark.csv   one row per algorithm
    <out>/<stem>_benchmark.json  parameters, library versions, image SHA-256

so every number in the paper can be regenerated from the raw image.

Usage:
    python reproduce/benchmark_algorithms.py IMAGE --palette KT --out results/
"""
import argparse
import hashlib
import json
import os
import platform
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from modules import filters, palettes, segmentation as seg, utils  # noqa: E402

GUI_FILTER_DEFAULTS = dict(min_area=8, must_be_dark=True, dark_thresh_factor=0.95)
COLOR_DEFAULTS = dict(max_distance=25, color_space="lab")


def build_methods(pore_colors):
    def color_distance(img):
        return seg.segment_ColorDistance(img, pore_colors, **COLOR_DEFAULTS)

    def hybrid(base):
        def run(img):
            mask, gray = base(img)
            cmask, _ = seg.segment_ColorDistance(img, pore_colors, **COLOR_DEFAULTS)
            return mask & cmask, gray
        return run

    return [
        ("Sauvola", "Classical", seg.segment_Sauvola, dict(window_size=51, k=0.2)),
        ("Multi-Otsu", "Classical", seg.segment_MultiOtsu, dict(n_classes=3, dark_class_count=1)),
        ("Auto-Threshold", "Classical", seg.segment_AutoThreshold, dict(method="triangle")),
        ("DoG", "Blob/region", seg.segment_DoG, dict(sigma1=3, sigma2=15, percentile=95)),
        ("MSER", "Blob/region", seg.segment_MSER, dict(delta=4, min_area=10, max_area=3000)),
        ("Bottom-Hat", "Blob/region", seg.segment_BottomHat, dict(kernel_size=21, percentile=90)),
        ("Frangi", "Blob/region", seg.segment_Frangi, dict(sigma_min=1, sigma_max=8, step=2, percentile=90)),
        ("Watershed", "Blob/region", seg.segment_Watershed, dict(min_distance=10, base_threshold="otsu")),
        ("Color-Distance", "Color", color_distance, dict(COLOR_DEFAULTS)),
        ("GMM", "Color", seg.segment_GMM, dict(n_components=3, dark_component_count=1)),
        ("DoG+Color", "Hybrid", hybrid(seg.segment_DoG), dict(COLOR_DEFAULTS)),
        ("MSER+Color", "Hybrid", hybrid(seg.segment_MSER), dict(COLOR_DEFAULTS)),
    ]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image")
    ap.add_argument("--palette", default="KT", help="stone palette code in palettes/ (KT, GT, NT, PT)")
    ap.add_argument("--repeats", type=int, default=3, help="timing repeats (median reported)")
    ap.add_argument("--out", default="results")
    ap.add_argument("--save-masks", action="store_true")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    img = utils.load_image(args.image)
    pal = palettes.load_palette(args.palette)
    pore_colors = palettes.palette_to_dict(pal)
    stem = os.path.splitext(os.path.basename(args.image))[0]

    rows = []
    for name, family, fn, params in build_methods(pore_colors):
        times, final, kept = [], None, None
        for _ in range(max(1, args.repeats)):
            t0 = time.perf_counter()
            mask, gray = fn(img)
            final, kept = filters.filter_components(mask, gray, **GUI_FILTER_DEFAULTS)
            times.append((time.perf_counter() - t0) * 1000.0)
        m = filters.compute_metrics(final, kept)
        rows.append(dict(algorithm=name, family=family,
                         porosity_pct=round(m["porosity_pct"], 2),
                         pore_count=int(m["n_pores"]),
                         time_ms=round(float(np.median(times)), 1),
                         params=params))
        if args.save_masks:
            from PIL import Image
            Image.fromarray((final * 255).astype(np.uint8)).save(
                os.path.join(args.out, f"{stem}_{name}_mask.png"))
        print(f"{name:15s} {family:12s} {rows[-1]['porosity_pct']:7.2f} % "
              f"{rows[-1]['pore_count']:6d} pores {rows[-1]['time_ms']:8.1f} ms")

    import csv
    with open(os.path.join(args.out, f"{stem}_benchmark.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["algorithm", "family", "porosity_pct", "pore_count", "time_ms"])
        for r in rows:
            w.writerow([r["algorithm"], r["family"], r["porosity_pct"], r["pore_count"], r["time_ms"]])

    import cv2
    import scipy
    import skimage
    import sklearn
    meta = dict(image=os.path.basename(args.image), image_sha256=sha256(args.image),
                image_shape=list(img.shape), palette=args.palette, pore_colors=pore_colors,
                post_filter=GUI_FILTER_DEFAULTS, repeats=args.repeats,
                environment=dict(python=platform.python_version(), platform=platform.platform(),
                                 numpy=np.__version__, scipy=scipy.__version__,
                                 scikit_image=skimage.__version__, scikit_learn=sklearn.__version__,
                                 opencv=cv2.__version__),
                results=rows)
    with open(os.path.join(args.out, f"{stem}_benchmark.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
