# -*- coding: utf-8 -*-
'''
Yaslandirma (Aging) Analizi Modulu
Standart: TS EN 15886, Sharma et al. 2005, Mokrzycki & Tatol 2011
'''
import math
import numpy as np
from . import color_science as _cs


# ============================================================
# PAIRING
# ============================================================
def pair_alphabetic(pre_items, post_items, key_fn=None):
    if key_fn is None:
        key_fn = lambda x: getattr(x, 'name', str(x))
    return list(zip(sorted(pre_items, key=key_fn), sorted(post_items, key=key_fn)))


def pair_upload_order(pre_items, post_items):
    return list(zip(pre_items, post_items))


def pair_manual(pre_items, post_items, manual_map):
    pairs = []
    for pi, qi in manual_map:
        if 0 <= pi < len(pre_items) and 0 <= qi < len(post_items):
            pairs.append((pre_items[pi], post_items[qi]))
    return pairs


# ============================================================
# PAIR-WISE COLOR CHANGE
# ============================================================
def compute_pair_color_change(img_pre, img_post, delta_e_method='2000',
                                sample_size=20000, sample_name=''):
    u_pre = _cs.compute_uniformity(img_pre, sample_size=sample_size)
    u_post = _cs.compute_uniformity(img_post, sample_size=sample_size)
    
    delta_L = u_post['mean_L'] - u_pre['mean_L']
    delta_a = u_post['mean_a'] - u_pre['mean_a']
    delta_b = u_post['mean_b'] - u_pre['mean_b']
    
    C1 = math.sqrt(u_pre['mean_a']**2 + u_pre['mean_b']**2)
    C2 = math.sqrt(u_post['mean_a']**2 + u_post['mean_b']**2)
    delta_C = C2 - C1
    
    h1 = math.degrees(math.atan2(u_pre['mean_b'], u_pre['mean_a'])) % 360
    h2 = math.degrees(math.atan2(u_post['mean_b'], u_post['mean_a'])) % 360
    delta_h = ((h2 - h1 + 180) % 360) - 180
    
    delta_E_ab_sq = delta_L**2 + delta_a**2 + delta_b**2
    delta_H_sq = delta_E_ab_sq - delta_L**2 - delta_C**2
    delta_H = math.sqrt(max(0.0, delta_H_sq)) * (1 if delta_h > 0 else -1)
    
    # v1.3.0 fix: the colour difference is computed directly from the mean
    # CIELAB coordinates. Up to v1.2.x the mean Lab colour was converted back
    # to 8-bit sRGB (truncated with int()) and then re-converted to Lab before
    # the formula was applied; that round-trip introduced a quantisation error
    # of up to ~0.25 dE00 units and made dE inconsistent with the reported
    # dL*, da*, db* (see tests/test_aging_analysis.py).
    delta_e_value = _cs.delta_e_lab(
        (u_pre['mean_L'], u_pre['mean_a'], u_pre['mean_b']),
        (u_post['mean_L'], u_post['mean_a'], u_post['mean_b']),
        method=delta_e_method)
    
    return {
        'sample_name': sample_name,
        'pre_color_hex': u_pre['mean_color_hex'],
        'post_color_hex': u_post['mean_color_hex'],
        'pre_L': round(u_pre['mean_L'], 2),
        'pre_a': round(u_pre['mean_a'], 2),
        'pre_b': round(u_pre['mean_b'], 2),
        'post_L': round(u_post['mean_L'], 2),
        'post_a': round(u_post['mean_a'], 2),
        'post_b': round(u_post['mean_b'], 2),
        'delta_L': round(delta_L, 2),
        'delta_a': round(delta_a, 2),
        'delta_b': round(delta_b, 2),
        'delta_C': round(delta_C, 2),
        'delta_h_deg': round(delta_h, 2),
        'delta_H': round(delta_H, 2),
        'delta_e': round(delta_e_value, 2),
        'delta_e_method': delta_e_method,
        'classification': _cs.interpret_delta_e(delta_e_value, method=delta_e_method),
        'pre_uniformity': u_pre['homogeneity_score_0_10'],
        'post_uniformity': u_post['homogeneity_score_0_10'],
        'delta_uniformity': round(u_post['homogeneity_score_0_10'] - u_pre['homogeneity_score_0_10'], 2),
    }


# ============================================================
# AGGREGATE STATISTICS
# ============================================================
def aggregate_pairs(pair_results, ddof=1):
    n = len(pair_results)
    if n == 0:
        return {'error': 'Pair sonuc yok'}
    
    delta_es = np.array([p['delta_e'] for p in pair_results])
    delta_Ls = np.array([p['delta_L'] for p in pair_results])
    delta_as = np.array([p['delta_a'] for p in pair_results])
    delta_bs = np.array([p['delta_b'] for p in pair_results])
    delta_Cs = np.array([p['delta_C'] for p in pair_results])
    delta_Hs = np.array([p['delta_H'] for p in pair_results])
    
    def stats_dict(arr):
        if n > 1:
            return {
                'mean': round(float(np.mean(arr)), 3),
                'std':  round(float(np.std(arr, ddof=ddof)), 3),
                'min':  round(float(np.min(arr)), 3),
                'max':  round(float(np.max(arr)), 3),
                'median': round(float(np.median(arr)), 3),
                'cv_pct': round(float(np.std(arr, ddof=ddof)/abs(np.mean(arr))*100) if abs(np.mean(arr))>1e-6 else 0, 1),
            }
        return {
            'mean': round(float(arr[0]), 3),
            'std': 0, 'min': round(float(arr[0]),3), 'max': round(float(arr[0]),3),
            'median': round(float(arr[0]),3), 'cv_pct': 0,
        }
    
    return {
        'n': n,
        'delta_e_method': str(pair_results[0].get('delta_e_method', '2000')),
        'delta_e_values': [float(v) for v in delta_es],
        'delta_e': stats_dict(delta_es),
        'delta_L': stats_dict(delta_Ls),
        'delta_a': stats_dict(delta_as),
        'delta_b': stats_dict(delta_bs),
        'delta_C': stats_dict(delta_Cs),
        'delta_H': stats_dict(delta_Hs),
    }


# ============================================================
# STATISTICAL TEST
# ============================================================
def statistical_test_paired(pair_results, variable='delta_L', alpha=0.05, reference=None):
    """
    Paired test on a signed channel (dL*, da*, db*), or - for variable='delta_e' -
    a one-sample test of dE against `reference`. dE is non-negative by
    definition, so testing it against 0 is uninformative; since v1.3.0 the
    default reference is the lower bound of the perceptible range of the metric
    (dE00: PT = 0.8, Paravina et al. 2015; dE*ab: 1.0, Mokrzycki & Tatol 2011).
    """
    try:
        from scipy import stats
    except ImportError:
        return {'error': 'scipy yuklu degil — pip install scipy'}
    
    n = len(pair_results)
    if n < 2:
        return {'error': 'En az 2 numune gerekli (n>=2)'}
    
    if variable == 'delta_L':
        pre_vals = np.array([p['pre_L'] for p in pair_results])
        post_vals = np.array([p['post_L'] for p in pair_results])
        diffs = post_vals - pre_vals
        var_label = 'L* (lightness)'
    elif variable == 'delta_a':
        pre_vals = np.array([p['pre_a'] for p in pair_results])
        post_vals = np.array([p['post_a'] for p in pair_results])
        diffs = post_vals - pre_vals
        var_label = 'a* (green-red)'
    elif variable == 'delta_b':
        pre_vals = np.array([p['pre_b'] for p in pair_results])
        post_vals = np.array([p['post_b'] for p in pair_results])
        diffs = post_vals - pre_vals
        var_label = 'b* (blue-yellow)'
    else:
        if reference is None:
            reference = _cs.perceptual_reference(pair_results[0].get('delta_e_method', '2000'))
        reference = 0.0 if reference is None else float(reference)
        diffs = np.array([p['delta_e'] for p in pair_results]) - reference
        pre_vals = np.zeros(n)
        post_vals = diffs
        var_label = f'Delta-E minus reference ({reference:g})'
    
    if n >= 3:
        shapiro_stat, shapiro_p = stats.shapiro(diffs)
        is_normal = bool(shapiro_p > alpha)  # numpy.bool_ -> python bool
    else:
        shapiro_p = None
        is_normal = False
    
    test_name = None
    test_stat = None
    p_value = None
    
    if variable == 'delta_e':
        if is_normal:
            test_stat, p_value = stats.ttest_1samp(diffs, 0)
            test_name = f'One-sample t-test (vs {reference:g})'
        else:
            try:
                test_stat, p_value = stats.wilcoxon(diffs)
                test_name = f'Wilcoxon signed-rank (vs {reference:g})'
            except ValueError:
                test_name = 'No test (all zeros)'
                p_value = 1.0
                test_stat = 0
    else:
        if is_normal and n >= 3:
            test_stat, p_value = stats.ttest_rel(pre_vals, post_vals)
            test_name = 'Paired t-test (Student)'
        else:
            try:
                test_stat, p_value = stats.wilcoxon(pre_vals, post_vals)
                test_name = 'Wilcoxon signed-rank'
            except ValueError:
                test_name = 'No test (all zero diffs)'
                p_value = 1.0
                test_stat = 0
    
    mean_diff = float(np.mean(diffs))
    if n >= 2:
        sem = stats.sem(diffs)
        ci = stats.t.interval(1 - alpha, n - 1, loc=mean_diff, scale=sem)
        ci_low, ci_high = float(ci[0]), float(ci[1])
    else:
        ci_low = ci_high = None
    
    std_diff = float(np.std(diffs, ddof=1)) if n > 1 else 0
    if std_diff > 1e-9:
        cohen_d = mean_diff / std_diff
        abs_d = abs(cohen_d)
        if abs_d < 0.2:
            d_interp = 'Negligible (cok kucuk)'
        elif abs_d < 0.5:
            d_interp = 'Small (kucuk etki)'
        elif abs_d < 0.8:
            d_interp = 'Medium (orta etki)'
        else:
            d_interp = 'Large (buyuk etki)'
    else:
        cohen_d = None
        d_interp = 'Hesaplanamaz (sapma sifir)'
    
    if variable == 'delta_e':
        # report the mean/CI of dE itself, not of dE - reference
        mean_diff += reference
        if ci_low is not None:
            ci_low += reference
            ci_high += reference
    return {
        'variable_tested': variable,
        'reference': reference if variable == 'delta_e' else None,
        'variable_label': var_label,
        'n': n,
        'test_name': test_name,
        'test_statistic': round(float(test_stat), 4) if test_stat is not None else None,
        'p_value': round(float(p_value), 4) if p_value is not None else None,
        'is_significant': bool(p_value < alpha) if p_value is not None else None,
        'alpha': alpha,
        'normality_shapiro_p': round(float(shapiro_p), 4) if shapiro_p is not None else None,
        'is_normal_distribution': is_normal,
        'mean_diff': round(mean_diff, 3),
        'std_diff': round(std_diff, 3),
        'ci_95_low': round(ci_low, 3) if ci_low is not None else None,
        'ci_95_high': round(ci_high, 3) if ci_high is not None else None,
        'cohen_d': round(cohen_d, 3) if cohen_d is not None else None,
        'cohen_d_interpretation': d_interp,
    }


# ============================================================
# AUTO INTERPRETATION (v1.3.0)
# ============================================================
def _one_sample_vs(values, mean, sd, n, ref, alpha=0.05):
    """
    One-sample location test of dE against a threshold. Uses the per-specimen
    values when available: Shapiro-Wilk decides between the t-test and the
    Wilcoxon signed-rank test (dE is bounded at 0 and often right-skewed).
    Falls back to a t-test from summary statistics.
    """
    from scipy import stats
    if values and len(values) >= 3:
        d = np.asarray(values, dtype=float) - ref
        normal = bool(stats.shapiro(d).pvalue > alpha) if np.ptp(d) > 0 else False
        if normal:
            r = stats.ttest_1samp(d, 0)
            return 'one-sample t-test', float(r.statistic), float(r.pvalue)
        try:
            r = stats.wilcoxon(d)
            return 'Wilcoxon signed-rank test', float(r.statistic), float(r.pvalue)
        except ValueError:
            return 'Wilcoxon signed-rank test', None, 1.0
    if n < 2 or sd <= 0:
        return None, None, None
    t = (mean - ref) / (sd / math.sqrt(n))
    return 'one-sample t-test', float(t), float(2 * stats.t.sf(abs(t), n - 1))


def auto_interpret(aggregate, stat_test=None, pt=None, at=None, alpha=0.05):
    """
    Paper-ready interpretation of an aging data set.

    The perceptual class is taken from the thresholds defined for the metric
    that was actually computed (see color_science.interpret_delta_e):
    dE00 -> PT/AT (Paravina et al. 2015); dE*ab -> Mokrzycki & Tatol (2011);
    CIE94 -> no class. For dE00 the mean is also located against PT and AT
    with its 95% CI and one-sample t-tests, so that 'below the threshold' is
    only claimed when the data support it.
    """
    from scipy import stats
    method = str(aggregate.get('delta_e_method', '2000'))
    n = aggregate['n']
    de = aggregate['delta_e']
    de_mean, de_std, de_min, de_max = de['mean'], de['std'], de['min'], de['max']
    values = aggregate.get('delta_e_values', [])
    label = {'2000': 'Delta-E-2000', '76': 'Delta-E*ab', '94': 'Delta-E-94'}.get(method, 'Delta-E')
    damage_class = _cs.interpret_delta_e(de_mean, method=method, pt=pt, at=at)

    if method == '2000':
        severity = {0: 'minimal', 1: 'hafif', 2: 'belirgin'}[
            list(_cs.DE2000_CLASSES).index(damage_class)]
    elif method == '76':
        severity = ['minimal', 'cok hafif', 'hafif', 'orta', 'belirgin'][
            [c[1] for c in _cs.MT_CLASSES_76].index(damage_class)]
    else:
        severity = 'hafif'

    ci = None
    if n >= 2 and de_std > 0:
        lo, hi = stats.t.interval(0.95, n - 1, loc=de_mean, scale=de_std / math.sqrt(n))
        ci = (float(lo), float(hi))
    ci_en = f", 95% CI [{ci[0]:.2f}, {ci[1]:.2f}]" if ci else ''
    ci_tr = f", %95 GA [{ci[0]:.2f}, {ci[1]:.2f}]" if ci else ''

    threshold_tests = []
    en_thr = tr_thr = ''
    if method == '2000':
        PT = _cs.DE2000_THRESHOLDS['PT'] if pt is None else float(pt)
        AT = _cs.DE2000_THRESHOLDS['AT'] if at is None else float(at)
        for name, ref in (('PT', PT), ('AT', AT)):
            test, stat, p = _one_sample_vs(values, de_mean, de_std, n, ref, alpha)
            n_above = int(sum(v >= ref for v in values)) if values else None
            threshold_tests.append({'threshold': name, 'value': ref, 'test': test, 'statistic': stat,
                                    'p_two_sided': p, 'n_at_or_above': n_above})

        def locate(tt, name_en, name_tr):
            ref, p = tt['value'], tt['p_two_sided']
            if p is None:
                return ('', '')
            tag = f" ({tt['test']}, p = {p:.3f})"
            if p < alpha and de_mean < ref:
                return (f"below the {name_en} ({ref:g}){tag}", f"{name_tr} ({ref:g}) altında{tag}")
            if p < alpha and de_mean > ref:
                return (f"above the {name_en} ({ref:g}){tag}", f"{name_tr} ({ref:g}) üzerinde{tag}")
            return (f"statistically indistinguishable from the {name_en} ({ref:g}){tag}",
                    f"{name_tr} ({ref:g}) ile istatistiksel olarak ayırt edilemez{tag}")
        pt_en, pt_tr = locate(threshold_tests[0], 'perceptibility threshold', 'algılanabilirlik eşiği')
        at_en, at_tr = locate(threshold_tests[1], 'acceptability threshold', 'kabul edilebilirlik eşiği')
        n_above_at = threshold_tests[1]['n_at_or_above']
        if pt_en:
            en_thr = (f" Relative to the CIEDE2000 50:50% thresholds of Paravina et al. (2015), the mean change is "
                      f"{pt_en} and {at_en}")
            tr_thr = (f" Paravina ve ark. (2015) CIEDE2000 %50:50 eşiklerine göre ortalama değişim "
                      f"{pt_tr}, {at_tr}")
            if n_above_at is not None:
                verb = 'reaches or exceeds' if n_above_at == 1 else 'reach or exceed'
                en_thr += f"; {n_above_at} of {n} specimens {verb} the acceptability threshold."
                tr_thr += f"; {n} numuneden {n_above_at} tanesi kabul edilebilirlik eşiğine ulaşıyor veya aşıyor."
            else:
                en_thr += '.'
                tr_thr += '.'
        scheme_en = 'CIEDE2000 perceptibility/acceptability thresholds (Paravina et al., 2015)'
        scheme_tr = 'CIEDE2000 algılanabilirlik/kabul edilebilirlik eşiklerine (Paravina ve ark., 2015)'
    elif method == '76':
        scheme_en = 'Mokrzycki & Tatol (2011) observer classes for Delta-E*ab'
        scheme_tr = 'Delta-E*ab için Mokrzycki & Tatol (2011) gözlemci sınıflarına'
    else:
        scheme_en = scheme_tr = ''

    cls_en = damage_class.split('(')[-1].rstrip(')') if '(' in damage_class else damage_class
    cls_tr = damage_class.split(' (')[0]

    summary_tr = (f"Yaşlandırma sonrası numuneler (n={n}) ortalama {label} = {de_mean:.2f} +/- {de_std:.2f}"
                  f"{ci_tr} (medyan {de['median']:.2f}, aralık: {de_min:.2f}-{de_max:.2f}) renk değişimi gösterdi.")
    eng = (f"After aging, the {n} specimens exhibited a mean total colour difference of {label} = "
           f"{de_mean:.2f} +/- {de_std:.2f}{ci_en} (median {de['median']:.2f}, range {de_min:.2f}-{de_max:.2f}).")
    if scheme_en:
        summary_tr += f" Bu değer {scheme_tr} göre '{cls_tr}' sınıfındadır."
        eng += f" According to the {scheme_en}, the mean falls in the class '{cls_en}'."
    else:
        summary_tr += " CIE94 için doğrulanmış algısal eşik bulunmadığından sınıf atanmamıştır."
        eng += " No perceptual class is assigned because no validated CIE94 thresholds exist."
    summary_tr += tr_thr
    eng += en_thr

    if stat_test and stat_test.get('test_name') and stat_test.get('variable_tested') != 'delta_e':
        p = stat_test.get('p_value')
        if p is not None:
            p_str = 'p<0.001' if p < 0.001 else f'p={p:.3f}'
            sig = stat_test.get('is_significant')
            eng += (f" {stat_test['test_name']} on {stat_test.get('variable_label', '')}: "
                    f"{'significant' if sig else 'not significant'} ({p_str}).")
            summary_tr += (f" {stat_test['test_name']} ({stat_test.get('variable_label', '')}): "
                           f"{'anlamlı' if sig else 'anlamlı değil'} ({p_str}).")

    return {
        'damage_class': damage_class,
        'damage_severity': severity,
        'delta_e_method': method,
        'ci_95': ci,
        'threshold_tests': threshold_tests,
        'summary_tr': summary_tr,
        'paper_ready_en': eng,
    }
