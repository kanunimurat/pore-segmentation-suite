"""
Aging-analysis workflow: per-pair colour change, aggregation, and the
automatic paired statistics (Shapiro-Wilk -> paired t / Wilcoxon, 95% CI,
Cohen's d_z). Every statistic is checked against an independent SciPy call.
"""
import numpy as np
import pytest
from scipy import stats

from modules import aging_analysis as aa
from modules import color_science as cs


def _uniform(rgb, shape=(40, 40)):
    return np.full(shape + (3,), rgb, dtype=np.uint8)


# ----------------------------------------------------------------------------
# per-pair colour change
# ----------------------------------------------------------------------------
@pytest.mark.parametrize("pre,post", [
    ((200, 170, 140), (197, 168, 139)),     # small change, dE00 ~ 1
    ((120, 110, 100), (118, 111, 104)),
    ((230, 205, 170), (210, 190, 160)),     # larger change
])
def test_delta_e_equals_ciede2000_of_mean_lab(pre, post):
    """
    Regression test for the v1.2.x sRGB round-trip: dE must be computed from the
    reported mean L*a*b* coordinates, so dE, dL*, da* and db* stay consistent.
    """
    r = aa.compute_pair_color_change(_uniform(pre), _uniform(post), "2000", sample_size=500)
    expected = cs.delta_e_lab((r["pre_L"], r["pre_a"], r["pre_b"]),
                              (r["post_L"], r["post_a"], r["post_b"]), "2000")
    assert r["delta_e"] == pytest.approx(expected, abs=0.006)   # rounding to 2 dp


def test_delta_components_are_post_minus_pre():
    r = aa.compute_pair_color_change(_uniform((200, 170, 140)), _uniform((180, 160, 140)), sample_size=500)
    assert r["delta_L"] == pytest.approx(r["post_L"] - r["pre_L"], abs=0.011)
    assert r["delta_a"] == pytest.approx(r["post_a"] - r["pre_a"], abs=0.011)
    assert r["delta_b"] == pytest.approx(r["post_b"] - r["pre_b"], abs=0.011)
    assert r["delta_L"] < 0            # post is darker


def test_delta_H_closes_the_colour_difference_budget():
    """dE*ab^2 = dL*^2 + dC*^2 + dH*^2 (CIE 1976 decomposition)."""
    r = aa.compute_pair_color_change(_uniform((200, 170, 140)), _uniform((190, 172, 120)), "76", sample_size=500)
    lhs = r["delta_e"] ** 2
    rhs = r["delta_L"] ** 2 + r["delta_C"] ** 2 + r["delta_H"] ** 2
    assert lhs == pytest.approx(rhs, rel=0.02)


def test_no_change_gives_zero():
    r = aa.compute_pair_color_change(_uniform((150, 140, 120)), _uniform((150, 140, 120)), sample_size=500)
    assert r["delta_e"] == pytest.approx(0.0, abs=1e-9)


# ----------------------------------------------------------------------------
# pairing
# ----------------------------------------------------------------------------
def test_alphabetic_pairing_is_order_independent():
    pre = ["NT-D3", "NT-D1", "NT-D2"]
    post = ["NT-D2", "NT-D3", "NT-D1"]
    pairs = aa.pair_alphabetic(pre, post, key_fn=str)
    assert pairs == [("NT-D1", "NT-D1"), ("NT-D2", "NT-D2"), ("NT-D3", "NT-D3")]


# ----------------------------------------------------------------------------
# aggregation and statistics
# ----------------------------------------------------------------------------
def _fake_pairs(pre_L, post_L, de):
    return [dict(pre_L=p, post_L=q, pre_a=0, post_a=0, pre_b=0, post_b=0,
                 delta_L=q - p, delta_a=0, delta_b=0, delta_C=0, delta_H=0, delta_e=e,
                 delta_e_method="2000")
            for p, q, e in zip(pre_L, post_L, de)]


PRE = [60.1, 58.4, 61.0, 59.7, 60.5, 58.9]
POST = [60.9, 55.9, 60.4, 59.4, 59.4, 58.7]
DE = [0.72, 2.61, 0.62, 0.50, 1.16, 0.44]


def test_aggregate_matches_numpy():
    agg = aa.aggregate_pairs(_fake_pairs(PRE, POST, DE))
    assert agg["n"] == 6
    assert agg["delta_e"]["mean"] == pytest.approx(np.mean(DE), abs=1e-3)
    assert agg["delta_e"]["std"] == pytest.approx(np.std(DE, ddof=1), abs=1e-3)
    assert agg["delta_e"]["median"] == pytest.approx(np.median(DE), abs=1e-3)


def test_paired_t_test_matches_scipy():
    res = aa.statistical_test_paired(_fake_pairs(PRE, POST, DE), "delta_L")
    diffs = np.subtract(POST, PRE)
    assert res["normality_shapiro_p"] == pytest.approx(stats.shapiro(diffs).pvalue, abs=1e-4)
    assert res["is_normal_distribution"]
    t, p = stats.ttest_rel(PRE, POST)
    assert res["test_name"].startswith("Paired t-test")
    assert res["test_statistic"] == pytest.approx(t, abs=1e-4)
    assert res["p_value"] == pytest.approx(p, abs=1e-4)
    lo, hi = stats.t.interval(0.95, len(diffs) - 1, loc=diffs.mean(), scale=stats.sem(diffs))
    assert res["ci_95_low"] == pytest.approx(lo, abs=1e-3)
    assert res["ci_95_high"] == pytest.approx(hi, abs=1e-3)
    assert res["cohen_d"] == pytest.approx(diffs.mean() / diffs.std(ddof=1), abs=1e-3)


def test_non_normal_differences_switch_to_wilcoxon():
    pre = [50.0] * 8
    post = [50.1, 50.1, 50.1, 50.1, 50.1, 50.1, 50.1, 58.0]   # one gross outlier
    res = aa.statistical_test_paired(_fake_pairs(pre, post, [0.1] * 8), "delta_L")
    assert not res["is_normal_distribution"]
    assert res["test_name"].startswith("Wilcoxon")
    assert res["p_value"] == pytest.approx(stats.wilcoxon(pre, post).pvalue, abs=1e-4)


def test_too_few_pairs_is_reported_not_crashed():
    assert "error" in aa.statistical_test_paired(_fake_pairs([50], [51], [1.0]), "delta_L")


# ----------------------------------------------------------------------------
# v1.3.0: dE tested against the perceptibility threshold, not against 0
# ----------------------------------------------------------------------------
def test_delta_e_one_sample_test_uses_pt_by_default():
    res = aa.statistical_test_paired(_fake_pairs(PRE, POST, DE), "delta_e")
    d = np.array(DE) - 0.8
    assert res["reference"] == pytest.approx(0.8)
    if stats.shapiro(d).pvalue > 0.05:
        ref = stats.ttest_1samp(d, 0)
        assert res["test_name"].startswith("One-sample t-test (vs 0.8)")
    else:                                   # right-skewed dE -> signed-rank test
        ref = stats.wilcoxon(d)
        assert res["test_name"].startswith("Wilcoxon signed-rank (vs 0.8)")
    assert res["test_statistic"] == pytest.approx(ref.statistic, abs=1e-4)
    assert res["p_value"] == pytest.approx(ref.pvalue, abs=1e-4)
    assert res["mean_diff"] == pytest.approx(np.mean(DE), abs=1e-3)   # mean of dE itself
    lo, hi = stats.t.interval(0.95, 5, loc=np.mean(DE), scale=stats.sem(DE))
    assert res["ci_95_low"] == pytest.approx(lo, abs=1e-3)
    assert res["ci_95_high"] == pytest.approx(hi, abs=1e-3)


def test_auto_interpret_locates_mean_against_pt_and_at():
    agg = aa.aggregate_pairs(_fake_pairs(PRE, POST, DE))
    out = aa.auto_interpret(agg, aa.statistical_test_paired(_fake_pairs(PRE, POST, DE), "delta_L"))
    assert out["delta_e_method"] == "2000"
    assert out["damage_class"] == cs.DE2000_CLASSES[1]          # mean 1.01: PT <= mean < AT
    assert "indistinguishable from the perceptibility threshold" in out["paper_ready_en"]
    assert "indistinguishable from the acceptability threshold" in out["paper_ready_en"]  # CI 0.14-1.87
    assert "1 of 6 specimens reaches" in out["paper_ready_en"]
    at = [t for t in out["threshold_tests"] if t["threshold"] == "AT"][0]
    # dE is right-skewed here (Shapiro p = 0.017) -> Wilcoxon, not t
    assert at["test"] == "Wilcoxon signed-rank test"
    assert at["p_two_sided"] == pytest.approx(stats.wilcoxon(np.array(DE) - 1.8).pvalue, abs=1e-4)
    assert "2.3" not in out["paper_ready_en"]


def test_auto_interpret_cie76_uses_mokrzycki_tatol():
    pairs = _fake_pairs(PRE, POST, [2.5] * 6)
    for p in pairs:
        p["delta_e_method"] = "76"
    out = aa.auto_interpret(aa.aggregate_pairs(pairs))
    assert out["damage_class"] == cs.MT_CLASSES_76[2][1]
    assert "Mokrzycki" in out["paper_ready_en"]
