"""Tests of the ground-truth evaluation metrics (reproduce/evaluate_ground_truth.py)."""
import importlib.util
import os

import numpy as np
import pytest

_P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reproduce", "evaluate_ground_truth.py")
_spec = importlib.util.spec_from_file_location("evaluate_ground_truth", _P)
ev = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ev)


def disk(shape, centre, r):
    yy, xx = np.ogrid[:shape[0], :shape[1]]
    return (yy - centre[0]) ** 2 + (xx - centre[1]) ** 2 <= r * r


@pytest.fixture
def ref():
    m = np.zeros((100, 100), bool)
    m |= disk(m.shape, (25, 25), 8)      # large-ish pore
    m |= disk(m.shape, (70, 70), 5)
    m[10:13, 80:83] = True               # 9 px pore (small class)
    return m


def test_identical_masks_are_perfect(ref):
    m = ev.all_metrics(ref, ref)
    for k in ("precision", "recall", "dice", "iou", "dice_tol", "obj_precision", "obj_recall", "obj_f1"):
        assert m[k] == pytest.approx(1.0)
    assert m["porosity_err"] == pytest.approx(0.0)
    assert m["n_ref"] == 3 and m["n_matched"] == 3


def test_dice_iou_by_hand():
    ref = np.zeros((10, 10), bool); ref[0:4, 0:4] = True          # 16 px
    pred = np.zeros((10, 10), bool); pred[0:4, 2:6] = True        # 16 px, 8 overlap
    m = ev.pixel_metrics(pred, ref)
    assert m["dice"] == pytest.approx(2 * 8 / 32)
    assert m["iou"] == pytest.approx(8 / 24)
    assert m["precision"] == pytest.approx(0.5) and m["recall"] == pytest.approx(0.5)
    assert m["porosity_err"] == pytest.approx(0.0)


def test_empty_masks():
    z = np.zeros((20, 20), bool)
    m = ev.all_metrics(z, z)
    assert m["dice"] == 1.0 and m["obj_f1"] == 1.0
    one = z.copy(); one[5:9, 5:9] = True
    assert ev.pixel_metrics(z, one)["dice"] == 0.0
    assert ev.pixel_metrics(one, z)["dice"] == 0.0


def test_one_pixel_shift_is_forgiven_by_tolerance(ref):
    shifted = np.roll(ref, 1, axis=1)
    strict = ev.pixel_metrics(shifted, ref)["dice"]
    assert strict < 0.95
    assert ev.tolerant_dice(shifted, ref, tol=1) == pytest.approx(1.0)
    assert ev.tolerant_dice(shifted, ref, tol=0) == pytest.approx(strict)


def test_dilation_lowers_precision_not_recall(ref):
    from scipy import ndimage
    fat = ndimage.binary_dilation(ref, iterations=2)
    m = ev.pixel_metrics(fat, ref)
    assert m["recall"] == pytest.approx(1.0)
    assert m["precision"] < 0.8
    assert m["porosity_err"] > 0


def test_object_matching_missing_and_false_pores(ref):
    pred = ref.copy()
    pred[10:13, 80:83] = False                       # small pore missed
    pred |= disk(ref.shape, (80, 20), 6)              # false pore
    m = ev.object_metrics(pred, ref)
    assert m["n_ref"] == 3 and m["n_pred"] == 3 and m["n_matched"] == 2
    assert m["obj_recall"] == pytest.approx(2 / 3)
    assert m["obj_precision"] == pytest.approx(2 / 3)
    assert m["recall_small"] == 0.0
    assert m["recall_medium"] == 1.0


def test_merged_pores_are_not_matched():
    ref = np.zeros((40, 40), bool); ref[10:20, 5:15] = True; ref[10:20, 17:27] = True
    pred = np.zeros_like(ref); pred[10:20, 5:27] = True    # one blob bridging both pores
    m = ev.object_metrics(pred, ref)
    assert m["n_pred"] == 1 and m["n_ref"] == 2
    assert m["n_matched"] == 0                              # each IoU = 100/220 < 0.5


def test_min_area_excludes_specks(ref):
    pred = ref.copy(); pred[90, 5] = True                   # 1-px speck
    m = ev.object_metrics(pred, ref, min_area=8)
    assert m["n_pred"] == 3 and m["obj_precision"] == 1.0


def test_bootstrap_and_holm():
    lo, hi = ev.bootstrap_ci([0.5, 0.6, 0.7, 0.8], seed=1)
    assert 0.5 <= lo < 0.65 < hi <= 0.8
    assert ev.bootstrap_ci([0.4]) == (0.4, 0.4)
    adj = ev.holm([0.01, 0.04, 0.03])
    assert list(np.round(adj, 3)) == [0.03, 0.06, 0.06]


def test_friedman_detects_consistent_ranking():
    rng = np.random.default_rng(0)
    table = {m: {} for m in "ABC"}
    for c in range(8):
        base = rng.uniform(0.3, 0.6)
        table["A"][c] = base + 0.2; table["B"][c] = base + 0.1; table["C"][c] = base
    res = ev.compare_methods(table)
    assert res["best"] == "A"
    assert res["friedman_p"] < 0.01 and res["kendall_w"] == pytest.approx(1.0)
    assert all(r["mean_diff"] > 0 for r in res["vs_best"])


# ---------------------------------------------------------------- crop selection
def _sel_module():
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reproduce", "select_gt_crops.py")
    spec = importlib.util.spec_from_file_location("select_gt_crops", p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def test_distinct_images_draws_each_crop_from_another_image(tmp_path):
    from PIL import Image
    sel = _sel_module()
    paths = []
    for i in range(1, 7):                      # 1050 px images: two 512 px crops cannot avoid overlap
        p = tmp_path / f"TF-{i}.png"
        Image.fromarray(np.zeros((1050, 1050, 3), np.uint8)).save(p)
        paths.append(str(p))
    plan = sel.select(paths, 3, 512, 32, 20260926, True, distinct_images=True)
    assert len({c["image"] for c in plan}) == 3
    assert [c["priority"] for c in plan] == [1, 2, 2]
    with pytest.raises(ValueError):
        sel.select(paths, 7, 512, 32, 20260926, True, distinct_images=True)
