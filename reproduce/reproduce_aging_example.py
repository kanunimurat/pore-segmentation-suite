#!/usr/bin/env python3
"""
Regenerates the aging example (Table 3, Supplementary Note S1 / Fig. S3)
from the raw pre/post surface images.

For every specimen it reports the colour change computed by
  * the v1.2.x pipeline (dE from an 8-bit sRGB round-trip; 'dE00_legacy'), and
  * the v1.3.0 pipeline (dE directly from the mean CIELAB; 'dE00'),
then the paired statistics on L* and one-sample tests of the mean dE00
against user-supplied perceptibility / acceptability thresholds.

Usage:
    python reproduce/reproduce_aging_example.py PRE_DIR POST_DIR --prefix NT-D \
        --thresholds 0.8 1.8 --out results/
Images are paired alphabetically, exactly as in the interface.
"""
import argparse
import csv
import glob
import json
import os
import sys

import numpy as np
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from modules import aging_analysis as aa, color_science as cs, utils  # noqa: E402


def legacy_delta_e(r):
    """v1.2.x: mean Lab -> sRGB -> int() truncation -> Lab -> dE00."""
    from skimage import color as skc

    def roundtrip(L, a, b):
        rgb = skc.lab2rgb(np.array([[[L, a, b]]], dtype=np.float64)).reshape(3)
        return [int(np.clip(c * 255, 0, 255)) for c in rgb]
    return cs.delta_e_2000(roundtrip(r["pre_L"], r["pre_a"], r["pre_b"]),
                           roundtrip(r["post_L"], r["post_a"], r["post_b"]))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pre_dir")
    ap.add_argument("post_dir")
    ap.add_argument("--prefix", default="", help="file-name prefix filter, e.g. NT-D")
    ap.add_argument("--thresholds", type=float, nargs="*", default=[0.8, 1.8])
    ap.add_argument("--out", default="results")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    exts = ("*.jpg", "*.jpeg", "*.png", "*.tif", "*.tiff")
    pick = lambda d: sorted(p for e in exts for p in glob.glob(os.path.join(d, args.prefix + e)))
    pre, post = pick(args.pre_dir), pick(args.post_dir)
    if len(pre) != len(post) or not pre:
        sys.exit(f"pre/post count mismatch or empty: {len(pre)} vs {len(post)}")

    pairs = aa.pair_alphabetic(pre, post, key_fn=lambda p: os.path.basename(p).split("_")[0])
    rows = []
    for p_pre, p_post in pairs:
        name = os.path.basename(p_pre).split("_")[0]
        r = aa.compute_pair_color_change(utils.load_image(p_pre), utils.load_image(p_post),
                                         "2000", sample_name=name)
        r["dE00_legacy"] = round(legacy_delta_e(r), 2)
        r["dEab"] = round(cs.delta_e_lab((r["pre_L"], r["pre_a"], r["pre_b"]),
                                         (r["post_L"], r["post_a"], r["post_b"]), "76"), 2)
        rows.append(r)
        print(f"{name:8s} dL*={r['delta_L']:+6.2f} da*={r['delta_a']:+6.2f} db*={r['delta_b']:+6.2f} "
              f"dE00={r['delta_e']:5.2f} (legacy {r['dE00_legacy']:5.2f})  dE*ab={r['dEab']:5.2f}")

    de = np.array([r["delta_e"] for r in rows])
    n = len(de)
    ci = stats.t.interval(0.95, n - 1, loc=de.mean(), scale=stats.sem(de))
    summary = dict(n=n, dE00_mean=round(float(de.mean()), 3), dE00_sd=round(float(de.std(ddof=1)), 3),
                   dE00_ci95=[round(float(ci[0]), 3), round(float(ci[1]), 3)],
                   dE00_legacy_mean=round(float(np.mean([r["dE00_legacy"] for r in rows])), 3),
                   paired_L=aa.statistical_test_paired(rows, "delta_L"),
                   threshold_tests=[])
    summary["dE00_median"] = round(float(np.median(de)), 3)
    summary["dE00_shapiro_p"] = round(float(stats.shapiro(de).pvalue), 4)
    for thr in args.thresholds:
        test, stat, p = aa._one_sample_vs(list(de), de.mean(), de.std(ddof=1), n, thr)
        summary["threshold_tests"].append(dict(threshold=thr, test=test, statistic=stat,
                                               p_two_sided=round(float(p), 4),
                                               n_at_or_above=int((de >= thr).sum())))
    agg = aa.aggregate_pairs(rows)
    summary["auto_interpretation"] = aa.auto_interpret(agg, summary["paired_L"])["paper_ready_en"]
    print(json.dumps(summary, indent=2))

    keys = ["sample_name", "pre_L", "pre_a", "pre_b", "post_L", "post_a", "post_b",
            "delta_L", "delta_a", "delta_b", "delta_C", "delta_H", "delta_e", "dE00_legacy", "dEab"]
    tag = args.prefix or "aging"
    with open(os.path.join(args.out, f"{tag}_pairs.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(keys)
        for r in rows:
            w.writerow([r[k] for k in keys])
    with open(os.path.join(args.out, f"{tag}_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)


if __name__ == "__main__":
    main()
