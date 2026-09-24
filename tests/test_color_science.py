"""sRGB -> CIELAB (D65, 2 deg) conversion and helper functions."""
import math

import pytest

from modules import color_science as cs


@pytest.mark.parametrize("rgb,lab", [
    # Reference values: CIE 15:2004 / IEC 61966-2-1 sRGB, D65 white.
    ((255, 255, 255), (100.000, 0.000, 0.000)),
    ((0, 0, 0), (0.000, 0.000, 0.000)),
    ((255, 0, 0), (53.241, 80.092, 67.203)),
    ((0, 255, 0), (87.735, -86.183, 83.179)),
    ((0, 0, 255), (32.297, 79.188, -107.860)),
    ((128, 128, 128), (53.585, 0.000, 0.000)),
])
def test_rgb_to_lab_reference_values(rgb, lab):
    L, a, b = cs.rgb_to_lab(rgb)
    assert L == pytest.approx(lab[0], abs=0.02)
    assert a == pytest.approx(lab[1], abs=0.02)
    assert b == pytest.approx(lab[2], abs=0.02)


def test_lab_to_lch_quadrants():
    _, C, h = cs.lab_to_lch(50, 0, 10)
    assert C == pytest.approx(10) and h == pytest.approx(90)
    _, C, h = cs.lab_to_lch(50, -10, 0)
    assert h == pytest.approx(180)
    _, C, h = cs.lab_to_lch(50, 0, -10)
    assert h == pytest.approx(270)          # never negative
    _, C, h = cs.lab_to_lch(50, 3, 4)
    assert C == pytest.approx(5) and h == pytest.approx(math.degrees(math.atan2(4, 3)))


def test_rgb_wrappers_agree_with_lab_function():
    rgb1, rgb2 = (200, 170, 140), (190, 165, 138)
    lab1, lab2 = cs.rgb_to_lab(rgb1), cs.rgb_to_lab(rgb2)
    assert cs.delta_e_2000(rgb1, rgb2) == pytest.approx(cs.delta_e_lab(lab1, lab2, "2000"), abs=1e-9)
    assert cs.delta_e_76(rgb1, rgb2) == pytest.approx(cs.delta_e_lab(lab1, lab2, "76"), abs=1e-9)
    assert cs.delta_e_94(rgb1, rgb2) == pytest.approx(cs.delta_e_lab(lab1, lab2, "94"), abs=1e-9)


def test_uniform_image_statistics():
    import numpy as np
    img = np.full((50, 60, 3), (200, 170, 140), dtype=np.uint8)
    u = cs.compute_uniformity(img, sample_size=1000)
    L, a, b = cs.rgb_to_lab((200, 170, 140))
    assert u["mean_L"] == pytest.approx(L, abs=0.01)
    assert u["mean_a"] == pytest.approx(a, abs=0.01)
    assert u["mean_b"] == pytest.approx(b, abs=0.01)
    assert u["std_L"] == pytest.approx(0.0, abs=1e-6)
    assert u["delta_e_avg_from_mean"] == pytest.approx(0.0, abs=0.01)
    assert u["homogeneity_score_0_10"] == pytest.approx(10.0)


# ----------------------------------------------------------------------------
# v1.3.0 metric-specific perceptual classes
# ----------------------------------------------------------------------------
@pytest.mark.parametrize("de,idx", [(0.0, 0), (0.79, 0), (0.8, 1), (1.79, 1), (1.8, 2), (7.0, 2)])
def test_ciede2000_uses_paravina_pt_at(de, idx):
    """PT = 0.8, AT = 1.8 dE00 (Paravina et al. 2015, abstract)."""
    assert cs.interpret_delta_e(de, method="2000") == cs.DE2000_CLASSES[idx]


@pytest.mark.parametrize("de,idx", [(0.5, 0), (1.5, 1), (2.3, 2), (4.0, 3), (5.0, 4), (12.0, 4)])
def test_cie76_uses_mokrzycki_tatol_classes(de, idx):
    assert cs.interpret_delta_e(de, method="76") == cs.MT_CLASSES_76[idx][1]


def test_mokrzycki_tatol_has_exactly_five_classes():
    # M&T (2011, sec. 6.2) define five classes; the >5 class is open-ended.
    assert len(cs.MT_CLASSES_76) == 5 and cs.MT_CLASSES_76[-1][0] == float("inf")


def test_cie94_gets_no_perceptual_class():
    assert cs.interpret_delta_e(1.0, method="94") == cs.NO_CLASS_94


def test_custom_thresholds_override_defaults():
    assert cs.interpret_delta_e(1.0, "2000", pt=1.2, at=2.2) == cs.DE2000_CLASSES[0]
