#!/usr/bin/env python3
"""
Pooled accuracy statistics of Section 3.3 (v1.3.3), computed from the per-crop
tables written by evaluate_ground_truth.py (gt_per_crop.csv).

    python reproduce/summarize_accuracy.py \
        --per-crop gt/results_trav/gt_per_crop.csv gt/results_tuff/gt_per_crop.csv \
        [--alt-reference gt/results_trav_G/gt_per_crop.csv gt/results_tuff_G/gt_per_crop.csv] \
        --out gt/summary

Every number of Section 3.3 and Supplementary Note S3 is printed by this
script: nothing is computed by hand.

What it reports (all over crops as the unit of analysis)
  * per method: mean Dice, tolerant Dice, object F1, porosity MAE and signed
    bias, each with a seeded percentile-bootstrap 95 % CI (10 000 resamples)
  * Friedman test with Kendall's W over the compared methods (crops = blocks)
  * Holm-corrected Wilcoxon tests of every method against the best one, AND of
    all method pairs (the latter does not depend on which method came first)
  * leave-one-crop-out stability: best method and the Holm p of every
    method against it after dropping each crop in turn
  * trivial baselines ('Dark-q%': the darkest q % of the grey image, written by
    evaluate_ground_truth.py --dark-baselines) with paired bootstrap CIs of the
    difference method - baseline
  * porosity: a constant predictor that never looks at the image (the mean
    reference porosity of the OTHER crops, leave-one-out) gives the MAE that any
    method has to beat; Spearman rho of predicted vs reference porosity across
    crops shows whether a method tracks porosity at all
  * human ceiling: on the crops annotated twice, the inter-annotator Dice and
    each method's mean Dice as a fraction of it, with a paired bootstrap CI
  * optional: Spearman rho between the method rankings obtained with the two
    reference annotators (--alt-reference)
"""
import argparse
import csv
import json
import os
from collections import defaultdict

import numpy as np
from scipy import stats

SEED, NBOOT = 0, 10000


def read_rows(paths):
    rows = []
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                for k, v in list(r.items()):
                    try:
                        r[k] = float(v)
                    except (TypeError, ValueError):
                        pass
                rows.append(r)
    return rows


def boot_mean(x, seed=SEED, n=NBOOT):
    x = np.asarray([v for v in x if np.isfinite(v)], float)
    if x.size == 0:
        return float("nan"), [float("nan"), float("nan")]
    if x.size == 1:
        return float(x[0]), [float(x[0])] * 2
    rng = np.random.default_rng(seed)
    m = x[rng.integers(0, x.size, size=(n, x.size))].mean(axis=1)
    return float(x.mean()), [float(np.quantile(m, .025)), float(np.quantile(m, .975))]


def boot_ratio(num, den, seed=SEED, n=NBOOT):
    """mean(num)/mean(den) with crops resampled jointly (paired)."""
    num, den = np.asarray(num, float), np.asarray(den, float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, num.size, size=(n, num.size))
    r = num[idx].mean(axis=1) / den[idx].mean(axis=1)
    return float(num.mean() / den.mean()), [float(np.quantile(r, .025)), float(np.quantile(r, .975))]


def holm(p):
    p = np.asarray(p, float)
    order, adj, run = np.argsort(p), np.empty(len(p)), 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (len(p) - rank) * p[i]))
        adj[i] = run
    return adj


def wilcoxon_p(d):
    d = np.asarray(d, float)
    return 1.0 if np.allclose(d, 0) else float(stats.wilcoxon(d, zero_method="zsplit").pvalue)


def matrix(rows, methods, crops, key):
    t = {(r["method"], r["crop_id"]): r[key] for r in rows}
    return np.array([[t[(m, c)] for m in methods] for c in crops], float)


def compare(X, methods):
    n, k = X.shape
    chi2, p = stats.friedmanchisquare(*X.T) if k >= 3 and n >= 2 else (float("nan"), float("nan"))
    best = methods[int(np.argmax(X.mean(axis=0)))]
    b = methods.index(best)
    vs = [(m, float((X[:, b] - X[:, j]).mean()), wilcoxon_p(X[:, b] - X[:, j]))
          for j, m in enumerate(methods) if m != best]
    adj = holm([v[2] for v in vs])
    pairs = [(methods[i], methods[j], wilcoxon_p(X[:, i] - X[:, j]))
             for i in range(k) for j in range(i + 1, k)]
    adj_all = holm([v[2] for v in pairs])
    ranks = np.apply_along_axis(stats.rankdata, 1, -X).mean(axis=0)
    return dict(n_crops=n, n_methods=k, friedman_chi2=float(chi2), friedman_p=float(p),
                kendall_w=float(chi2 / (n * (k - 1))), best_by_mean=best,
                best_by_friedman_rank=methods[int(np.argmin(ranks))],
                mean_rank={m: float(r) for m, r in zip(methods, ranks)},
                vs_best=[dict(method=m, mean_diff=md, p=pv, p_holm=float(a)) for (m, md, pv), a in zip(vs, adj)],
                all_pairs_holm=[dict(a=x, b=y, p=pv, p_holm=float(q)) for (x, y, pv), q in zip(pairs, adj_all)])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--per-crop", nargs="+", required=True)
    ap.add_argument("--alt-reference", nargs="*", default=[])
    ap.add_argument("--methods", nargs="*", default=None,
                    help="methods to compare (default: every method present on all crops, "
                         "without the Dark-q%% baselines)")
    ap.add_argument("--metric", default="dice")
    ap.add_argument("--out", default="gt/summary")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    rows = read_rows(a.per_crop)
    human = [r for r in rows if str(r["method"]).startswith("Annotator")]
    algo = [r for r in rows if not str(r["method"]).startswith("Annotator")]
    crops = sorted({r["crop_id"] for r in algo})
    present = defaultdict(set)
    for r in algo:
        present[r["method"]].add(r["crop_id"])
    full = sorted(m for m, c in present.items() if c == set(crops))
    baselines = [m for m in full if m.startswith("Dark-")]
    methods = a.methods or [m for m in full if m not in baselines]
    by = defaultdict(dict)
    for r in algo:
        by[r["method"]][r["crop_id"]] = r

    out = dict(n_crops=len(crops), crops=crops, methods=methods, baselines=baselines,
               bootstrap=dict(seed=SEED, resamples=NBOOT))

    # --- per-method summary (compared methods + baselines)
    summ = {}
    ref_por = np.array([by[methods[0]][c]["porosity_ref"] for c in crops])
    for m in methods + baselines:
        rr = [by[m][c] for c in crops]
        err = np.array([r["porosity_err"] for r in rr])
        pred = np.array([r["porosity_pred"] for r in rr])
        rho = stats.spearmanr(pred, ref_por)
        summ[m] = dict(
            dice=boot_mean([r["dice"] for r in rr]), dice_tol=boot_mean([r["dice_tol"] for r in rr]),
            obj_f1=boot_mean([r["obj_f1"] for r in rr]), precision=boot_mean([r["precision"] for r in rr]),
            recall=boot_mean([r["recall"] for r in rr]),
            porosity_mae=boot_mean(np.abs(err)), porosity_bias=boot_mean(err),
            porosity_spearman=dict(rho=float(rho.statistic), p=float(rho.pvalue)))
    loo_const = np.array([ref_por[np.arange(len(crops)) != i].mean() for i in range(len(crops))])
    const_err = loo_const - ref_por
    out["constant_predictor"] = dict(
        description="leave-one-crop-out mean of the reference porosity of the other crops",
        porosity_mae=boot_mean(np.abs(const_err)), porosity_bias=boot_mean(const_err))
    for m in methods + baselines:
        d = np.abs([by[m][c]["porosity_err"] for c in crops]) - np.abs(const_err)
        summ[m]["mae_minus_constant"] = boot_mean(d)
    out["summary"] = summ

    # --- rank tests
    X = matrix(algo, methods, crops, a.metric)
    out["comparison"] = compare(X, methods)
    Xt = matrix(algo, methods, crops, "dice_tol")
    out["comparison_dice_tol"] = compare(Xt, methods)

    # --- leave-one-crop-out stability
    loo = []
    for i, c in enumerate(crops):
        keep = [j for j in range(len(crops)) if j != i]
        r = compare(X[keep], methods)
        loo.append(dict(dropped=c, best=r["best_by_mean"],
                        p_holm_vs_best={v["method"]: v["p_holm"] for v in r["vs_best"]}))
    out["leave_one_crop_out"] = loo

    # --- baselines: paired difference method - baseline
    out["vs_baselines"] = {
        b: {m: boot_mean([by[m][c][a.metric] - by[b][c][a.metric] for c in crops]) for m in methods}
        for b in baselines}

    # --- human ceiling on the doubly annotated crops
    if human:
        hc = sorted({r["crop_id"] for r in human})
        hd = {r["crop_id"]: r[a.metric] for r in human}
        hvals = [hd[c] for c in hc]
        ceil = dict(crops=hc, human=boot_mean(hvals), fraction_of_human={})
        for m in methods + baselines:
            mv = [by[m][c][a.metric] for c in hc]
            ceil["fraction_of_human"][m] = dict(mean_method=float(np.mean(mv)), ratio=boot_ratio(mv, hvals))
        out["human_ceiling"] = ceil

    # --- ranking agreement between the two references
    if a.alt_reference:
        alt = [r for r in read_rows(a.alt_reference) if not str(r["method"]).startswith("Annotator")]
        ac = sorted({r["crop_id"] for r in alt})
        abm = defaultdict(dict)
        for r in alt:
            abm[r["method"]][r["crop_id"]] = r
        common = [m for m in methods if m in abm and all(c in abm[m] for c in ac)]
        res = {}
        for k in ("dice", "dice_tol", "obj_f1"):
            x = [np.mean([by[m][c][k] for c in ac]) for m in common]
            y = [np.mean([abm[m][c][k] for c in ac]) for m in common]
            res[k] = float(stats.spearmanr(x, y).statistic)
        out["reference_rank_agreement"] = dict(crops=ac, methods=common, spearman=res)

    with open(os.path.join(a.out, "accuracy_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)

    # --- console report
    f = lambda t: f"{t[0]:.3f} [{t[1][0]:.3f}, {t[1][1]:.3f}]"
    print(f"{len(crops)} crops, {len(methods)} methods, baselines: {', '.join(baselines) or '-'}")
    print(f"\n{'method':16s} {'Dice [95% CI]':>24s} {'MAE pp [95% CI]':>24s} {'rho(por)':>9s}")
    for m in sorted(methods + baselines, key=lambda m: -summ[m]["dice"][0]):
        s = summ[m]
        print(f"{m:16s} {f(s['dice']):>24s} {f(s['porosity_mae']):>24s} {s['porosity_spearman']['rho']:9.2f}")
    print(f"{'constant (LOO)':16s} {'':>24s} {f(out['constant_predictor']['porosity_mae']):>24s}")
    c = out["comparison"]
    print(f"\nFriedman chi2={c['friedman_chi2']:.2f} p={c['friedman_p']:.2g} W={c['kendall_w']:.2f}; "
          f"best by mean: {c['best_by_mean']}, by mean rank: {c['best_by_friedman_rank']}")
    print("vs best (Holm):", ", ".join(f"{v['method']} {v['p_holm']:.3f}" for v in c["vs_best"]))
    sig = [v for v in c["all_pairs_holm"] if v["p_holm"] < 0.05]
    print(f"all pairs (Holm, {len(c['all_pairs_holm'])} pairs): {len(sig)} with p < 0.05",
          "; ".join(f"{v['a']}-{v['b']} {v['p_holm']:.3f}" for v in sig))
    print("leave-one-crop-out best:", ", ".join(f"{d['dropped']}:{d['best']}" for d in loo))
    if "human_ceiling" in out:
        h = out["human_ceiling"]
        print(f"human Dice on {len(h['crops'])} crops: {f(h['human'])}")
        for m, v in sorted(h["fraction_of_human"].items(), key=lambda kv: -kv[1]["ratio"][0]):
            print(f"   {m:16s} {v['mean_method']:.3f} = {v['ratio'][0]*100:.0f}% "
                  f"[{v['ratio'][1][0]*100:.0f}, {v['ratio'][1][1]*100:.0f}]")
    if "reference_rank_agreement" in out:
        print("ranking agreement between references (Spearman):", out["reference_rank_agreement"]["spearman"])


if __name__ == "__main__":
    main()
