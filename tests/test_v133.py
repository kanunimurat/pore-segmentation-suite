"""
v1.3.3 changes:
  * specimen masking and all-pixel mean colour in the aging workflow
  * direction of a significant threshold test read from the test's own
    location estimate (Hodges-Lehmann for Wilcoxon)
  * stone palettes stored in sRGB (converted from the scanner encoding)
  * trivial 'Dark-q%' baselines and the pooled accuracy summary script
"""
import csv
import io
import json
import os
import subprocess
import sys

import numpy as np
import pytest
from PIL import Image, ImageCms

from modules import aging_analysis as aa
from modules import color_science as cs
from modules import palettes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENERIC_RGB = [
    "/System/Library/ColorSync/Profiles/Generic RGB Profile.icc",
    "/Library/ColorSync/Profiles/Generic RGB Profile.icc",
]


# ----------------------------------------------------------------------------
# specimen mask
# ----------------------------------------------------------------------------
def _specimen_on_black(rgb=(200, 170, 140), frame=10, shape=(80, 100)):
    img = np.full(shape + (3,), 18, np.uint8)            # black cloth / scanner lid
    img[frame:-frame, frame:-frame] = rgb
    return img


def test_mask_removes_border_connected_background():
    img = _specimen_on_black()
    m = cs.specimen_mask(img, dilate=0)
    assert m[0, 0] == False and m[40, 50] == True
    assert m.sum() == (80 - 20) * (100 - 20)


def test_dark_pores_inside_the_specimen_are_kept():
    img = _specimen_on_black()
    img[40:44, 50:54] = 10                                # a dark pore, not touching the border
    m = cs.specimen_mask(img, dilate=0)
    assert m[41, 51] == True


def test_mean_colour_ignores_background():
    img = _specimen_on_black()
    L, a, b = cs.rgb_to_lab((200, 170, 140))
    u = cs.compute_uniformity(img)
    assert u["mean_L"] == pytest.approx(L, abs=0.01)
    assert u["background_fraction"] > 0.3
    u0 = cs.compute_uniformity(img, mask_background=False)
    assert u0["mean_L"] < L - 10                          # v1.3.2 behaviour: background drags L* down
    assert u0["background_fraction"] == 0.0


def test_all_dark_image_falls_back_to_all_pixels():
    img = np.full((30, 30, 3), 12, np.uint8)
    u = cs.compute_uniformity(img)
    assert np.isfinite(u["mean_L"])


def test_pair_change_uses_all_pixels_by_default_and_reports_background():
    pre, post = _specimen_on_black((200, 170, 140)), _specimen_on_black((196, 168, 139))
    r = aa.compute_pair_color_change(pre, post, "2000")
    ref = aa.compute_pair_color_change(np.full((60, 80, 3), (200, 170, 140), np.uint8),
                                       np.full((60, 80, 3), (196, 168, 139), np.uint8), "2000")
    assert r["delta_e"] == ref["delta_e"] and r["pre_L"] == ref["pre_L"]
    r0 = aa.compute_pair_color_change(pre, post, "2000", mask_background=False)
    assert r0["pre_L"] < ref["pre_L"] - 10
    assert r["pre_background_fraction"] > 0.3 and r["post_background_fraction"] > 0.3


def test_sampling_is_still_available_and_seeded():
    rng = np.random.default_rng(3)
    img = rng.integers(60, 250, size=(120, 120, 3), dtype=np.uint8)
    a = cs.compute_uniformity(img, sample_size=2000)
    b = cs.compute_uniformity(img, sample_size=2000)
    assert a["mean_L"] == b["mean_L"]


# ----------------------------------------------------------------------------
# K14: direction of a significant threshold test
# ----------------------------------------------------------------------------
def test_hodges_lehmann_location_is_returned():
    vals = [0.2, 0.25, 0.3, 0.3, 0.35, 0.4, 0.45, 5.0]    # skewed, not normal
    test, stat, p, loc = aa._one_sample_vs(vals, float(np.mean(vals)), float(np.std(vals, ddof=1)), len(vals), 0.8)
    assert test == "Wilcoxon signed-rank test"
    d = np.asarray(vals) - 0.8
    i, j = np.triu_indices(len(d))
    assert loc == pytest.approx(np.median((d[i] + d[j]) / 2) + 0.8)


def test_direction_follows_the_test_not_the_mean():
    """Mean above PT (pulled up by one outlier), but most values and the
    Wilcoxon location are below it: a significant result must read 'below'."""
    vals = [0.10, 0.12, 0.15, 0.2, 0.22, 0.25, 0.3, 0.33, 0.35, 0.4, 0.42, 0.45, 9.0]
    assert np.mean(vals) > 0.8
    agg = dict(n=len(vals), delta_e_method="2000", delta_e_values=vals,
               delta_e=dict(mean=float(np.mean(vals)), std=float(np.std(vals, ddof=1)),
                            min=min(vals), max=max(vals), median=float(np.median(vals))))
    res = aa.auto_interpret(agg)
    pt = next(t for t in res["threshold_tests"] if t["threshold"] == "PT")
    assert pt["test"] == "Wilcoxon signed-rank test" and pt["p_two_sided"] < 0.05
    assert pt["location"] < 0.8
    assert "below the perceptibility threshold" in res["paper_ready_en"]


# ----------------------------------------------------------------------------
# palettes in sRGB
# ----------------------------------------------------------------------------
@pytest.mark.parametrize("code", ["KT", "GT", "NT", "PT"])
def test_palettes_are_srgb_and_keep_scanner_values(code):
    d = json.load(open(os.path.join(ROOT, "palettes", f"{code}.json"), encoding="utf-8"))
    assert d["color_space"] == "sRGB"
    for c in d["colors"]:
        assert len(c["rgb_scanner"]) == 3 and c["hex"] == "#%02x%02x%02x" % tuple(c["rgb"])
    # Generic RGB (gamma 1.8) -> sRGB lightens the mid-tones
    mid = [(c["rgb"], c["rgb_scanner"]) for c in d["colors"] if 40 < np.mean(c["rgb_scanner"]) < 200]
    assert all(np.mean(a) > np.mean(b) for a, b in mid)
    # the loaded palette (used by the colour-based methods) carries the sRGB values
    pal = palettes.load_palette(code)
    assert [c["rgb"] for c in pal["colors"]] == [c["rgb"] for c in d["colors"]]


@pytest.mark.parametrize("code", ["KT", "GT", "NT", "PT"])
def test_palette_conversion_matches_image_loading(code):
    icc = next((open(f, "rb").read() for f in GENERIC_RGB if os.path.exists(f)), None)
    if icc is None:
        pytest.skip("Generic RGB profile only available on macOS")
    d = json.load(open(os.path.join(ROOT, "palettes", f"{code}.json"), encoding="utf-8"))
    raw = np.array([c["rgb_scanner"] for c in d["colors"]], np.uint8)[None]
    buf = io.BytesIO()
    Image.fromarray(raw).save(buf, format="PNG", icc_profile=icc)
    buf.seek(0)
    from modules import utils
    out = utils.load_image(buf)[0].astype(int)
    # the Generic RGB profile shipped with macOS differs slightly between releases
    # from the one embedded in the scans: allow 3 levels per channel
    assert np.abs(out - np.array([c["rgb"] for c in d["colors"]])).max() <= 3


# ----------------------------------------------------------------------------
# dark baselines + pooled summary
# ----------------------------------------------------------------------------
def test_dark_baseline_marks_exactly_q_percent(tmp_path):
    sys.path.insert(0, os.path.join(ROOT, "reproduce"))
    import evaluate_ground_truth as ev
    rng = np.random.default_rng(0)
    img = rng.integers(0, 256, size=(50, 40, 3), dtype=np.uint8)
    p = tmp_path / "x.png"
    Image.fromarray(img).save(p)
    out = ev.dark_baselines(str(p), [1, 2.5])
    assert out["Dark-1%"].sum() == 20 and out["Dark-2.5%"].sum() == 50


def test_summarize_accuracy_constant_predictor_and_ceiling(tmp_path):
    rows = []
    ref = {"A": 1.0, "B": 2.0, "C": 3.0, "D": 6.0}
    for c, por in ref.items():
        for m, dice, pred in (("M1", 0.5, por + 0.5), ("M2", 0.3, por * 2), ("Dark-2%", 0.4, 2.0)):
            rows.append(dict(crop_id=c, group=c, method=m, reference="R", precision=0.5, recall=0.5,
                             dice=dice + 0.01 * len(rows), iou=0.3, porosity_pred=pred, porosity_ref=por,
                             porosity_err=pred - por, dice_tol=dice, n_pred=1, n_ref=1, n_matched=1,
                             obj_precision=0.5, obj_recall=0.5, obj_f1=0.2))
    rows.append(dict(rows[0], method="Annotator X", dice=0.6, reference="-"))
    rows.append(dict(rows[3], method="Annotator X", dice=0.7, reference="-"))
    f = tmp_path / "pc.csv"
    with open(f, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    subprocess.run([sys.executable, os.path.join(ROOT, "reproduce", "summarize_accuracy.py"),
                    "--per-crop", str(f), "--out", str(tmp_path / "s"), "--methods", "M1", "M2"],
                   check=True, capture_output=True)
    s = json.load(open(tmp_path / "s" / "accuracy_summary.json", encoding="utf-8"))
    loo = [np.mean([v for k, v in ref.items() if k != c]) for c in ref]
    assert s["constant_predictor"]["porosity_mae"][0] == pytest.approx(np.mean(np.abs(np.array(loo) - list(ref.values()))))
    assert s["summary"]["M1"]["porosity_mae"][0] == pytest.approx(0.5)
    assert s["baselines"] == ["Dark-2%"]
    assert set(s["human_ceiling"]["crops"]) == {"A", "B"}
    assert len(s["comparison"]["all_pairs_holm"]) == 1


# ----------------------------------------------------------------------------
# colorimeter-like spot protocol (Supplementary Note S1)
# ----------------------------------------------------------------------------
def test_spot_protocol_uniform_and_heterogeneous():
    sys.path.insert(0, os.path.join(ROOT, "reproduce"))
    import emulate_spot_colorimetry as esc
    pre, post = _specimen_on_black((200, 170, 140), shape=(160, 160)), _specimen_on_black((190, 165, 138), shape=(160, 160))
    m = esc.pair_metrics(pre, post, face_mm=140.0)
    whole = aa.compute_pair_color_change(pre, post, "2000")["delta_e"]
    assert m["grid_dE00_mean"] == pytest.approx(m["grid_dE00_of_means"], abs=1e-6)
    assert m["grid_dE00_mean"] == pytest.approx(whole, abs=0.015)   # whole value rounded to 2 dp
    # opposite local changes cancel in the mean colour but not in the mean of local differences
    post2 = pre.copy()
    post2[10:80, 10:150] = (215, 180, 145)
    post2[80:150, 10:150] = (185, 160, 135)
    m2 = esc.pair_metrics(pre, post2, face_mm=140.0)
    assert m2["grid_dE00_mean"] > m2["grid_dE00_of_means"] + 1.0
