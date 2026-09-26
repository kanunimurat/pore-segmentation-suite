#!/usr/bin/env python3
"""
Accuracy of the segmentation algorithms against manually annotated pore masks
(Section 3.3 of the SoftwareX paper).

Every algorithm is run on the FULL image with the interface defaults and the
interface post-filter (as in benchmark_algorithms.py); the mask is then cut to
the crop and compared with the manual mask of that crop. Optional extra masks
(e.g. SAM 2, Cellpose from run_foundation_models.py) are compared the same way.

    python reproduce/evaluate_ground_truth.py \
        --crops gt/crops/crops.csv --images DIR --annotations gt/annotations \
        [--extra-masks DIR ...] --out gt/results

Annotation files: <annotations>/<crop_id>_<annotator>.png, pores white (>127)
on black, same size as the crop. The first annotator in alphabetical order
(or --reference NAME) is the reference; any other annotator of the same crop
gives the inter-annotator agreement, i.e. the human ceiling.

Metrics per crop and method
  pixel     : precision, recall, Dice (= F1), IoU, porosity (%) and its error (pp)
  boundary  : Dice with a +-t px tolerance (default t = 1) for boundary ambiguity
  object    : components >= min_area px; a predicted and a reference pore match
              when IoU > 0.5 (a match is then unique); object precision, recall, F1
  size      : recall of reference pores by size class (>= 50 % of the pore covered)
Summary: mean and seeded bootstrap 95 % CI over crops, Friedman test across
methods (crops as blocks) with Kendall's W, and Holm-corrected Wilcoxon tests of
every method against the best one.
"""
import argparse
import csv
import glob
import json
import os
import sys
import warnings
from collections import defaultdict

import numpy as np
from PIL import Image
from scipy import ndimage, stats
from skimage import measure

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

warnings.filterwarnings("ignore", category=FutureWarning)

SIZE_BINS = ((8, 50, "small (8-49 px)"), (50, 500, "medium (50-499 px)"), (500, None, "large (>=500 px)"))


# ----------------------------------------------------------------- metrics
def _b(m):
    return np.asarray(m).astype(bool)


def pixel_metrics(pred, ref):
    pred, ref = _b(pred), _b(ref)
    tp = np.logical_and(pred, ref).sum()
    fp = np.logical_and(pred, ~ref).sum()
    fn = np.logical_and(~pred, ref).sum()
    prec = tp / (tp + fp) if tp + fp else (1.0 if fn == 0 else 0.0)
    rec = tp / (tp + fn) if tp + fn else 1.0
    dice = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 1.0
    iou = tp / (tp + fp + fn) if (tp + fp + fn) else 1.0
    por_p, por_r = 100.0 * pred.mean(), 100.0 * ref.mean()
    return dict(precision=float(prec), recall=float(rec), dice=float(dice), iou=float(iou),
                porosity_pred=float(por_p), porosity_ref=float(por_r), porosity_err=float(por_p - por_r))


def tolerant_dice(pred, ref, tol=1):
    """Boundary-tolerant F1: a predicted pixel counts as correct if it lies within
    tol px of the reference, and a reference pixel as found if it lies within tol
    px of the prediction."""
    pred, ref = _b(pred), _b(ref)
    if tol <= 0:
        return pixel_metrics(pred, ref)["dice"]
    st = ndimage.generate_binary_structure(2, 2)
    ref_d = ndimage.binary_dilation(ref, st, iterations=tol)
    pred_d = ndimage.binary_dilation(pred, st, iterations=tol)
    p = np.logical_and(pred, ref_d).sum() / pred.sum() if pred.sum() else (1.0 if not ref.any() else 0.0)
    r = np.logical_and(ref, pred_d).sum() / ref.sum() if ref.sum() else 1.0
    return float(2 * p * r / (p + r)) if p + r else 0.0


def _components(mask, min_area):
    lab = measure.label(_b(mask), connectivity=2)
    if min_area > 1 and lab.max():
        areas = np.bincount(lab.ravel())
        small = np.where(areas < min_area)[0]
        small = small[small > 0]
        if small.size:
            lab[np.isin(lab, small)] = 0
            lab = measure.label(lab > 0, connectivity=2)
    return lab


def object_metrics(pred, ref, min_area=8, iou_thr=0.5):
    lp, lr = _components(pred, min_area), _components(ref, min_area)
    n_p, n_r = int(lp.max()), int(lr.max())
    size_rec = {name: [0, 0] for *_, name in SIZE_BINS}
    if n_r:
        area_r = np.bincount(lr.ravel(), minlength=n_r + 1)
        covered = np.bincount(lr[_b(pred)].ravel(), minlength=n_r + 1)
        for j in range(1, n_r + 1):
            for lo, hi, name in SIZE_BINS:
                if area_r[j] >= lo and (hi is None or area_r[j] < hi):
                    size_rec[name][1] += 1
                    size_rec[name][0] += int(covered[j] >= 0.5 * area_r[j])
    matched = 0
    if n_p and n_r:
        both = (lp > 0) & (lr > 0)
        pair, inter = np.unique(lp[both].astype(np.int64) * (n_r + 1) + lr[both], return_counts=True)
        ip, ir = pair // (n_r + 1), pair % (n_r + 1)
        ap = np.bincount(lp.ravel(), minlength=n_p + 1)
        ar = np.bincount(lr.ravel(), minlength=n_r + 1)
        iou = inter / (ap[ip] + ar[ir] - inter)
        matched = int((iou > iou_thr).sum())   # IoU > 0.5 makes the pairing one-to-one
    op = matched / n_p if n_p else (1.0 if n_r == 0 else 0.0)
    orc = matched / n_r if n_r else 1.0
    of1 = 2 * op * orc / (op + orc) if op + orc else 0.0
    out = dict(n_pred=n_p, n_ref=n_r, n_matched=matched, obj_precision=float(op),
               obj_recall=float(orc), obj_f1=float(of1))
    for *_, name in SIZE_BINS:
        hit, tot = size_rec[name]
        key = "recall_" + name.split(" ")[0]
        out[key] = float(hit / tot) if tot else float("nan")
        out["n_ref_" + name.split(" ")[0]] = tot
    return out


def all_metrics(pred, ref, tol=1, min_area=8):
    m = pixel_metrics(pred, ref)
    m["dice_tol"] = tolerant_dice(pred, ref, tol)
    m.update(object_metrics(pred, ref, min_area))
    return m


# ------------------------------------------------------------- statistics
def bootstrap_ci(x, n=10000, seed=0, alpha=0.05):
    x = np.asarray([v for v in x if np.isfinite(v)], float)
    if x.size == 0:
        return (float("nan"), float("nan"))
    if x.size == 1:
        return (float(x[0]), float(x[0]))
    rng = np.random.default_rng(seed)
    means = x[rng.integers(0, x.size, size=(n, x.size))].mean(axis=1)
    return (float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2)))


def holm(pvals):
    p = np.asarray(pvals, float)
    order = np.argsort(p)
    adj = np.empty_like(p)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(p) - rank) * p[i]))
        adj[i] = running
    return adj


def compare_methods(table, metric="dice"):
    """table: {method: {crop: value}} -> Friedman + Kendall's W + Holm-Wilcoxon vs best."""
    methods = sorted(table)
    crops = sorted(set.intersection(*[set(table[m]) for m in methods])) if methods else []
    res = dict(metric=metric, n_crops=len(crops), n_methods=len(methods))
    if len(crops) < 3 or len(methods) < 3:
        res["note"] = "too few crops or methods for the Friedman test"
        return res
    X = np.array([[table[m][c] for m in methods] for c in crops])
    chi2, p = stats.friedmanchisquare(*X.T)
    k, n = X.shape[1], X.shape[0]
    res.update(friedman_chi2=float(chi2), friedman_p=float(p), kendall_w=float(chi2 / (n * (k - 1))))
    best = methods[int(np.argmax(X.mean(axis=0)))]
    res["best"] = best
    pw = []
    for j, m in enumerate(methods):
        if m == best:
            continue
        d = X[:, methods.index(best)] - X[:, j]
        pval = 1.0 if np.allclose(d, 0) else float(stats.wilcoxon(d, zero_method="zsplit").pvalue)
        pw.append((m, float(d.mean()), pval))
    adj = holm([x[2] for x in pw]) if pw else []
    res["vs_best"] = [dict(method=m, mean_diff=md, p=pv, p_holm=float(a)) for (m, md, pv), a in zip(pw, adj)]
    return res


# ------------------------------------------------------------------- runs
def run_algorithms(image_path, palette_code):
    import importlib.util
    from modules import filters, palettes, utils
    spec = importlib.util.spec_from_file_location(
        "benchmark_algorithms", os.path.join(os.path.dirname(os.path.abspath(__file__)), "benchmark_algorithms.py"))
    bench = importlib.util.module_from_spec(spec); spec.loader.exec_module(bench)
    img = utils.load_image(image_path)
    try:
        pore_colors = palettes.palette_to_dict(palettes.load_palette(palette_code))
    except Exception as exc:      # no palette for this stone: colour-based methods are skipped
        print(f"  no palette '{palette_code}' ({exc}); colour-based methods skipped")
        pore_colors = None
    out = {}
    for name, family, fn, _params in bench.build_methods(pore_colors or {}):
        if pore_colors is None and family in ("Color", "Hybrid") and name != "GMM":
            continue
        mask, gray = fn(img)
        final, _ = filters.filter_components(mask, gray, **bench.GUI_FILTER_DEFAULTS)
        out[name] = _b(final)
    return out



def load_mask(path):
    return np.asarray(Image.open(path).convert("L")) > 127


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--crops", required=True, help="crops.csv from select_gt_crops.py")
    ap.add_argument("--images", required=True, help="folder with the full images")
    ap.add_argument("--annotations", required=True)
    ap.add_argument("--extra-masks", nargs="*", default=[],
                    help="folders with full-image masks named <image stem>_<Method>_mask.png")
    ap.add_argument("--palette-from-prefix", action="store_true", default=True)
    ap.add_argument("--reference", default=None, help="annotator used as reference (default: first alphabetically)")
    ap.add_argument("--tolerance", type=int, default=1)
    ap.add_argument("--min-area", type=int, default=8)
    ap.add_argument("--save-crop-masks", action="store_true")
    ap.add_argument("--out", default="gt/results")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    crops = list(csv.DictReader(open(a.crops, encoding="utf-8")))
    cache, rows, human = {}, [], []
    for c in crops:
        cid = c["crop_id"]
        ann = sorted(glob.glob(os.path.join(a.annotations, f"{cid}_*.png")))
        if not ann:
            print(f"{cid}: no annotation yet, skipped")
            continue
        names = [os.path.splitext(os.path.basename(p))[0][len(cid) + 1:] for p in ann]
        ref_name = a.reference if a.reference in names else names[0]
        ref = load_mask(ann[names.index(ref_name)])
        x0, y0, s = int(c["x0"]), int(c["y0"]), int(c["size"])
        if ref.shape != (s, s):
            raise ValueError(f"{ann[names.index(ref_name)]}: shape {ref.shape}, expected {(s, s)}")
        for nm, p in zip(names, ann):
            if nm != ref_name:
                m = all_metrics(load_mask(p), ref, a.tolerance, a.min_area)
                human.append(dict(crop_id=cid, group=c["group"], method=f"Annotator {nm}", **m))
        img_path = os.path.join(a.images, c["image"])
        stem = os.path.splitext(c["image"])[0]
        if stem not in cache:
            cache[stem] = run_algorithms(img_path, c["group"])
            for d in a.extra_masks:
                for p in sorted(glob.glob(os.path.join(d, f"{stem}_*_mask.png"))):
                    meth = os.path.basename(p)[len(stem) + 1:-len("_mask.png")]
                    if meth.lower().startswith("sauvola"):
                        continue          # Sauvola is already in the algorithm set
                    cache[stem][meth] = load_mask(p)
        for meth, full in cache[stem].items():
            pred = full[y0:y0 + s, x0:x0 + s]
            m = all_metrics(pred, ref, a.tolerance, a.min_area)
            rows.append(dict(crop_id=cid, group=c["group"], method=meth, reference=ref_name, **m))
            if a.save_crop_masks:
                Image.fromarray(pred.astype(np.uint8) * 255).save(os.path.join(a.out, f"{cid}_{meth}.png"))
        print(f"{cid}: reference {ref_name}, {len(cache[stem])} methods, {len(names) - 1} extra annotator(s)")

    if not rows:
        print("no annotated crops found")
        return
    keys = list(rows[0].keys())
    with open(os.path.join(a.out, "gt_per_crop.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
        for h in human:
            w.writerow({**h, "reference": "-"})

    summary = defaultdict(dict)
    metrics = ["dice", "dice_tol", "iou", "precision", "recall", "obj_f1", "porosity_err",
               "recall_small", "recall_medium", "recall_large"]
    for meth in sorted({r["method"] for r in rows + human}):
        rr = [r for r in rows + human if r["method"] == meth]
        for k in metrics:
            v = [r[k] for r in rr if np.isfinite(r[k])]
            lo, hi = bootstrap_ci(v)
            summary[meth][k] = dict(mean=float(np.mean(v)) if v else float("nan"), ci95=[lo, hi], n=len(v))
        summary[meth]["abs_porosity_err_mean"] = float(np.mean([abs(r["porosity_err"]) for r in rr]))
    table = defaultdict(dict)
    for r in rows:
        table[r["method"]][r["crop_id"]] = r["dice"]
    result = dict(n_crops=len({r["crop_id"] for r in rows}), tolerance_px=a.tolerance, min_area_px=a.min_area,
                  summary=summary, comparison_dice=compare_methods(table, "dice"))
    table_t = defaultdict(dict)
    for r in rows:
        table_t[r["method"]][r["crop_id"]] = r["dice_tol"]
    result["comparison_dice_tol"] = compare_methods(table_t, "dice_tol")
    with open(os.path.join(a.out, "gt_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)

    print(f"\n{'method':22s} {'Dice':>6s} {'Dice±t':>7s} {'objF1':>6s} {'|dPor|':>7s}")
    for meth, s in sorted(summary.items(), key=lambda kv: -kv[1]["dice"]["mean"]):
        print(f"{meth:22s} {s['dice']['mean']:6.3f} {s['dice_tol']['mean']:7.3f} "
              f"{s['obj_f1']['mean']:6.3f} {s['abs_porosity_err_mean']:7.2f}")


if __name__ == "__main__":
    main()
