"""
Segmentation algorithms and post-filters on a synthetic surface with a known
ground-truth pore mask (see conftest.make_synthetic_stone: 40 dark discs,
about 5 % areal porosity, additive Gaussian noise).

These tests guard against regressions; they are not a claim of accuracy on
real stone, which is assessed separately against manually annotated masks.
"""
import cv2
import numpy as np
import pytest

from conftest import dice
from modules import filters
from modules import segmentation as seg

PORE_RGB = [[60, 50, 38]]

# (name, callable, minimum Dice, blur sigma applied to the synthetic image)
METHODS = [
    ("Sauvola", seg.segment_Sauvola, 0.95, 0),
    ("Multi-Otsu", seg.segment_MultiOtsu, 0.95, 0),
    ("Auto-Threshold", seg.segment_AutoThreshold, 0.95, 0),
    ("GMM", seg.segment_GMM, 0.95, 0),
    ("Watershed", seg.segment_Watershed, 0.95, 0),
    ("Color-Distance", lambda im: seg.segment_ColorDistance(im, PORE_RGB, max_distance=25), 0.95, 0),
    ("DoG", seg.segment_DoG, 0.90, 0),
    ("MSER", seg.segment_MSER, 0.75, 1),    # MSER needs graded pore edges
    ("Bottom-Hat", seg.segment_BottomHat, 0.65, 0),
    ("Frangi", seg.segment_Frangi, 0.65, 0),
]


def _run(fn, img):
    mask, gray = fn(img)
    final, kept = filters.filter_components(mask, gray, min_area=8)
    return mask, final, kept


@pytest.mark.parametrize("name,fn,min_dice,blur", METHODS, ids=[m[0] for m in METHODS])
def test_output_contract(name, fn, min_dice, blur, synthetic_stone):
    img, _ = synthetic_stone
    mask, gray = fn(img)
    assert mask.shape == img.shape[:2]
    assert mask.dtype == bool
    assert gray.shape == img.shape[:2]


@pytest.mark.parametrize("name,fn,min_dice,blur", METHODS, ids=[m[0] for m in METHODS])
def test_recovers_known_pores(name, fn, min_dice, blur, synthetic_stone):
    img, truth = synthetic_stone
    if blur:
        img = cv2.GaussianBlur(img, (0, 0), blur)
    _, final, _ = _run(fn, img)
    assert dice(final, truth) >= min_dice


@pytest.mark.parametrize("name,fn,min_dice,blur", METHODS, ids=[m[0] for m in METHODS])
def test_deterministic(name, fn, min_dice, blur, synthetic_stone):
    img, _ = synthetic_stone
    _, f1, _ = _run(fn, img)
    _, f2, _ = _run(fn, img)
    assert np.array_equal(f1, f2)


def test_blank_surface_gives_no_pores():
    rng = np.random.RandomState(1)
    img = np.clip(rng.normal(190, 3, (200, 200, 3)), 0, 255).astype(np.uint8)
    mask, gray = seg.segment_ColorDistance(img, PORE_RGB, max_distance=25)
    final, kept = filters.filter_components(mask, gray, min_area=8)
    assert final.sum() == 0 and len(kept) == 0


# ----------------------------------------------------------------------------
# post-filters and metrics
# ----------------------------------------------------------------------------
def test_compute_metrics_porosity_is_area_fraction():
    mask = np.zeros((100, 100), dtype=bool)
    mask[10:20, 10:20] = True          # 100 px
    mask[50:55, 50:70] = True          # 100 px
    final, kept = filters.filter_components(mask, np.full(mask.shape, 50, np.uint8),
                                            min_area=1, must_be_dark=False)
    m = filters.compute_metrics(final, kept, pixel_scale_mm=0.1)
    assert m["porosity_pct"] == pytest.approx(2.0)
    assert m["n_pores"] == 2
    assert m["mean_area_mm2"] == pytest.approx(1.0)      # 100 px x 0.01 mm2


def test_min_area_filter_removes_small_components():
    mask = np.zeros((60, 60), dtype=bool)
    mask[5:7, 5:7] = True              # 4 px -> removed
    mask[30:40, 30:40] = True          # 100 px -> kept
    final, kept = filters.filter_components(mask, np.zeros(mask.shape, np.uint8), min_area=8)
    assert len(kept) == 1 and final.sum() == 100


def test_dark_filter_rejects_bright_components():
    gray = np.full((60, 60), 150, np.uint8)
    gray[10:20, 10:20] = 40            # dark pore
    gray[40:50, 40:50] = 220           # bright inclusion
    mask = np.zeros_like(gray, dtype=bool)
    mask[10:20, 10:20] = True
    mask[40:50, 40:50] = True
    final, kept = filters.filter_components(mask, gray, min_area=1, must_be_dark=True)
    assert len(kept) == 1 and final[15, 15] and not final[45, 45]


def test_eccentricity_filter_rejects_elongated_features():
    mask = np.zeros((80, 80), dtype=bool)
    mask[10:20, 10:20] = True          # square
    mask[50:52, 5:75] = True           # thin band (vein / scratch)
    final, kept = filters.filter_components(mask, np.zeros(mask.shape, np.uint8),
                                            min_area=1, max_eccentricity=0.95)
    assert len(kept) == 1 and final[15, 15] and not final[51, 40]
