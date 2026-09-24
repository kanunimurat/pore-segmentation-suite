#!/usr/bin/env python3
"""
Regenerates Figure 5 (algorithm panels on one image) and Figure 6
(inter-method spread across specimens) of the SoftwareX paper from
scripted, archived runs - no manual step between software output and figure.

    python reproduce/make_figures.py fig5 IMAGE --palette KT --out figures/
    python reproduce/make_figures.py fig6 LONG_CSV --out figures/
    python reproduce/make_figures.py figS3 PAIRS_CSV --out figures/   (S1_pairs_all.csv; NT/KCl)

fig5 runs the twelve setup-free algorithms itself (same code and defaults
as reproduce/benchmark_algorithms.py) and writes the numbers it plotted to
<out>/Figure5_values.csv, so Table 2 and Figure 5 come from one run.
fig6 reads the long table produced by benchmark_algorithms.py over several
specimens (columns: specimen, algorithm, family, porosity_pct).
"""
import argparse
import csv
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "reproduce"))

FAMILY_COLOURS = {  # Okabe-Ito, colour-blind safe
    "Classical": "#0072B2",
    "Blob/region": "#D55E00",
    "Color": "#009E73",
    "Hybrid": "#CC79A7",
}
FAMILY_ORDER = ["Classical", "Blob/region", "Color", "Hybrid"]


def _hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def fig5(args):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from benchmark_algorithms import GUI_FILTER_DEFAULTS, build_methods
    from modules import filters, palettes, utils

    img = utils.load_image(args.input)
    pore_colors = palettes.palette_to_dict(palettes.load_palette(args.palette))
    methods = build_methods(pore_colors)
    methods.sort(key=lambda m: FAMILY_ORDER.index(m[1]))

    fig, axes = plt.subplots(3, 4, figsize=(7.48, 5.9), dpi=args.dpi)   # double column
    rows = []
    for ax, (name, family, fn, _params) in zip(axes.ravel(), methods):
        mask, gray = fn(img)
        final, kept = filters.filter_components(mask, gray, **GUI_FILTER_DEFAULTS)
        m = filters.compute_metrics(final, kept)
        rows.append((name, family, round(m["porosity_pct"], 2), int(m["n_pores"])))
        over = img.astype(np.float32).copy()
        col = np.array(_hex_rgb(FAMILY_COLOURS[family]), np.float32)
        over[final] = 0.35 * over[final] + 0.65 * col
        ax.imshow(over.astype(np.uint8), interpolation="nearest")
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)
        ax.text(0.5, 0.035, f"{name}  P = {m['porosity_pct']:.2f}%", transform=ax.transAxes,
                ha="center", va="bottom", fontsize=7, color="white", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.25", fc=FAMILY_COLOURS[family], ec="none", alpha=0.95))
    handles = [plt.Line2D([], [], marker="s", ls="", ms=7, color=FAMILY_COLOURS[f], label=f) for f in FAMILY_ORDER]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=8, bbox_to_anchor=(0.5, -0.005))
    fig.subplots_adjust(left=0.005, right=0.995, top=0.995, bottom=0.045, wspace=0.02, hspace=0.02)
    os.makedirs(args.out, exist_ok=True)
    for ext in ("png", "tiff"):
        fig.savefig(os.path.join(args.out, f"Figure5_algorithm_panels.{ext}"), dpi=args.dpi)
    with open(os.path.join(args.out, "Figure5_values.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["algorithm", "family", "porosity_pct", "pore_count"])
        w.writerows(rows)
    print("\n".join(f"{r[0]:15s} {r[2]:6.2f} %  {r[3]:5d}" for r in rows))


def variance_shares(wide):
    """Two-way additive decomposition of the algorithm x specimen table."""
    v = wide.values
    gm = v.mean()
    ss_t = ((v - gm) ** 2).sum()
    ss_m = v.shape[1] * ((v.mean(1) - gm) ** 2).sum()
    ss_s = v.shape[0] * ((v.mean(0) - gm) ** 2).sum()
    return ss_m / ss_t, ss_s / ss_t, 1 - (ss_m + ss_s) / ss_t


def fig6(args):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd

    d = pd.read_csv(args.input)
    specs = sorted(d.specimen.unique(), key=lambda s: (["KT", "GT", "NT", "PT"].index(s[:2]), s))
    wide = d.pivot(index="algorithm", columns="specimen", values="porosity_pct")[specs]
    fam = d.drop_duplicates("algorithm").set_index("algorithm").family

    lin = variance_shares(wide)
    log = variance_shares(np.log10(wide + 0.05))
    rng = wide.max() - wide.min()
    stone_rng = rng.groupby(rng.index.str[:2]).mean()
    # cross-specimen sensitivity of each algorithm
    cv = (wide.std(axis=1, ddof=1) / wide.mean(axis=1)).sort_values()

    fig, (a, b) = plt.subplots(1, 2, figsize=(7.48, 3.4), dpi=args.dpi,
                               gridspec_kw=dict(width_ratios=[2.35, 1]))
    x = np.arange(len(specs))
    for i, s in enumerate(specs):
        col = wide[s]
        a.vlines(i, col.min(), col.max(), color="0.75", lw=1, zorder=1)
        a.hlines(col.median(), i - 0.25, i + 0.25, color="k", lw=2, zorder=3)
        for alg, val in col.items():
            a.scatter(i, val, s=16, color=FAMILY_COLOURS[fam[alg]], ec="k", lw=0.3, zorder=2)
    a.set_ylim(-1.5, wide.values.max() * 1.22)
    a.set_xticks(x)
    a.set_xticklabels(specs, rotation=45, ha="right", fontsize=7)
    a.set_ylabel("Image porosity (%)", fontsize=8)
    a.tick_params(labelsize=7)
    a.grid(axis="y", color="0.92")
    a.set_axisbelow(True)
    txt = ("mean range: " + " · ".join(f"{k} {stone_rng[k]:.0f} pp" for k in ["KT", "GT", "NT", "PT"]) +
           f"\nvariance share (log): algorithm {log[0]*100:.0f}%, specimen {log[1]*100:.0f}%")
    a.text(0.01, 0.98, txt, transform=a.transAxes, va="top", fontsize=6.5,
           bbox=dict(fc="white", ec="0.8", boxstyle="round,pad=0.3"))
    a.text(-0.1, 1.0, "(a)", transform=a.transAxes, fontsize=9, fontweight="bold", va="top")
    handles = [plt.Line2D([], [], marker="o", ls="", ms=5, mec="k", mew=0.3, color=FAMILY_COLOURS[f], label=f)
               for f in FAMILY_ORDER] + [plt.Line2D([], [], color="k", lw=2, label="median")]
    a.legend(handles=handles, fontsize=6.5, loc="upper right", frameon=True)

    y = np.arange(len(cv))
    b.barh(y, cv.values, color=[FAMILY_COLOURS[fam[k]] for k in cv.index], ec="k", lw=0.3)
    b.set_yticks(y)
    b.set_yticklabels(cv.index, fontsize=6.5)
    b.set_xlabel("CV across specimens", fontsize=8)
    b.tick_params(axis="x", labelsize=7)
    b.axvline(0.1, color="0.4", ls="--", lw=0.8)
    b.text(0.12, -0.9, "CV = 0.1", fontsize=6, color="0.3", va="center")
    b.set_ylim(-1.4, len(cv) - 0.4)
    b.grid(axis="x", color="0.92")
    b.set_axisbelow(True)
    b.text(-0.62, 1.0, "(b)", transform=b.transAxes, fontsize=9, fontweight="bold", va="top")
    fig.tight_layout()
    os.makedirs(args.out, exist_ok=True)
    for ext in ("png", "tiff"):
        fig.savefig(os.path.join(args.out, f"Figure6_method_spread.{ext}"), dpi=args.dpi)
    with open(os.path.join(args.out, "Figure6_stats.txt"), "w", encoding="utf-8") as fh:
        fh.write(f"variance share linear: algorithm {lin[0]:.3f}, specimen {lin[1]:.3f}, residual {lin[2]:.3f}\n")
        fh.write(f"variance share log10:  algorithm {log[0]:.3f}, specimen {log[1]:.3f}, residual {log[2]:.3f}\n")
        fh.write("mean range by stone (pp): " + str(stone_rng.round(2).to_dict()) + "\n")
        fh.write("range by specimen (pp): " + str(rng.round(2).to_dict()) + "\n")
        fh.write("CV across specimens: " + str(cv.round(3).to_dict()) + "\n")
    print(open(os.path.join(args.out, "Figure6_stats.txt")).read())


def figS3(args):
    """Supplementary Fig. S3: NT-D (Noche, KCl) paired L* and dE00 against PT/AT."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd
    from scipy import stats

    d = pd.read_csv(args.input)
    d = d[(d.stone == "NT") & (d.salt == "KCl")].sort_values("specimen")
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.48, 3.0), dpi=args.dpi)
    for _, r in d.iterrows():
        a.plot([0, 1], [r.pre_L, r.post_L], "-o", color="0.55", ms=4, lw=1)
        a.text(1.04, r.post_L, r.specimen, fontsize=6, va="center")
    diffs = d.post_L - d.pre_L
    t = stats.ttest_rel(d.post_L, d.pre_L)
    ci = stats.t.interval(0.95, len(diffs) - 1, loc=diffs.mean(), scale=stats.sem(diffs))
    a.set_xticks([0, 1]); a.set_xticklabels(["pre", "post"], fontsize=8)
    a.set_xlim(-0.3, 1.35)
    a.set_ylabel("Surface lightness L*", fontsize=8); a.tick_params(labelsize=7)
    a.set_title(f"paired t = {t.statistic:.2f}, p = {t.pvalue:.2f}\nmean ΔL* = {diffs.mean():+.2f}, 95% CI [{ci[0]:.2f}, {ci[1]:.2f}]", fontsize=7)
    a.text(-0.2, 1.02, "(a)", transform=a.transAxes, fontsize=9, fontweight="bold")

    de = d.dE00.values
    x = np.arange(len(de))
    b.axhspan(0, 0.8, color="#009E73", alpha=0.10, lw=0)
    b.axhspan(0.8, 1.8, color="#E69F00", alpha=0.10, lw=0)
    b.axhspan(1.8, max(3.0, de.max() * 1.15), color="#D55E00", alpha=0.08, lw=0)
    b.axhline(0.8, color="#009E73", lw=1, label="PT = 0.8 (Paravina et al.)")
    b.axhline(1.8, color="#D55E00", lw=1, label="AT = 1.8 (Paravina et al.)")
    b.axhline(1.25, color="#009E73", lw=0.8, ls=":", label="PT = 1.25 (Ghinea et al.)")
    b.axhline(2.25, color="#D55E00", lw=0.8, ls=":", label="AT = 2.25 (Ghinea et al.)")
    b.scatter(x, de, color="k", s=18, zorder=3)
    b.axhline(np.median(de), color="k", lw=1.2, ls="--", label=f"median = {np.median(de):.2f}")
    b.set_xticks(x); b.set_xticklabels(d.specimen, fontsize=7, rotation=0)
    b.set_ylabel("ΔE-2000", fontsize=8); b.tick_params(labelsize=7)
    b.set_ylim(0, max(3.0, de.max() * 1.15))
    b.legend(fontsize=5.5, loc="upper right", frameon=True)
    b.text(-0.16, 1.02, "(b)", transform=b.transAxes, fontsize=9, fontweight="bold")
    fig.tight_layout()
    os.makedirs(args.out, exist_ok=True)
    for ext in ("png", "tiff"):
        fig.savefig(os.path.join(args.out, f"FigureS3_NTD_aging_statistics.{ext}"), dpi=args.dpi)
    print(d[["specimen", "pre_L", "post_L", "dE00"]].to_string(index=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("which", choices=["fig5", "fig6", "figS3"])
    ap.add_argument("input")
    ap.add_argument("--palette", default="KT")
    ap.add_argument("--out", default="figures")
    ap.add_argument("--dpi", type=int, default=600)
    args = ap.parse_args()
    {"fig5": fig5, "fig6": fig6, "figS3": figS3}[args.which](args)


if __name__ == "__main__":
    main()
