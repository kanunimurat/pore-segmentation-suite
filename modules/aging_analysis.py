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
    
    pre_rgb_norm = u_pre['mean_color_rgb']
    post_rgb_norm = u_post['mean_color_rgb']
    pre_rgb_255 = [int(np.clip(c * 255, 0, 255)) for c in pre_rgb_norm]
    post_rgb_255 = [int(np.clip(c * 255, 0, 255)) for c in post_rgb_norm]
    
    if delta_e_method == '76':
        delta_e_value = _cs.delta_e_76(pre_rgb_255, post_rgb_255)
    elif delta_e_method == '94':
        delta_e_value = _cs.delta_e_94(pre_rgb_255, post_rgb_255)
    else:
        delta_e_value = _cs.delta_e_2000(pre_rgb_255, post_rgb_255)
    
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
        'classification': _cs.interpret_delta_e(delta_e_value),
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
def statistical_test_paired(pair_results, variable='delta_L', alpha=0.05):
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
        diffs = np.array([p['delta_e'] for p in pair_results])
        pre_vals = np.zeros(n)
        post_vals = diffs
        var_label = 'Delta-E (vs no change)'
    
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
            test_name = 'One-sample t-test (vs 0)'
        else:
            try:
                test_stat, p_value = stats.wilcoxon(diffs)
                test_name = 'Wilcoxon signed-rank (vs 0)'
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
    
    return {
        'variable_tested': variable,
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
# AUTO INTERPRETATION
# ============================================================
def auto_interpret(aggregate, stat_test):
    n = aggregate['n']
    de_mean = aggregate['delta_e']['mean']
    de_std = aggregate['delta_e']['std']
    de_max = aggregate['delta_e']['max']
    de_min = aggregate['delta_e']['min']
    
    if de_mean < 1:
        damage_class = 'gorsel olarak fark edilmez (perceptually identical)'
        damage_severity = 'minimal'
    elif de_mean < 2:
        damage_class = 'sadece egitimli goz fark eder (just noticeable)'
        damage_severity = 'cok hafif'
    elif de_mean < 3.5:
        damage_class = 'egitimsiz goz zar zor gorur (barely visible)'
        damage_severity = 'hafif'
    elif de_mean < 5:
        damage_class = 'acik gorsel fark (clear difference)'
        damage_severity = 'orta'
    elif de_mean < 10:
        damage_class = 'belirgin gorsel hasar (marked damage)'
        damage_severity = 'belirgin'
    else:
        damage_class = 'siddetli renk hasari (severe damage)'
        damage_severity = 'siddetli'
    
    p_str = ''
    sig_str = ''
    if stat_test and 'p_value' in stat_test and stat_test['p_value'] is not None:
        p = stat_test['p_value']
        if p < 0.001:
            p_str = 'p<0.001'
        else:
            p_str = f'p={p:.3f}'
        sig_str = 'istatistiksel olarak anlamli' if stat_test['is_significant'] else 'istatistiksel olarak anlamsiz'
    
    summary_tr = (
        f"Yaslandirma deneyi sonrasi numuneler (n={n}) ortalama Delta-E-2000 = "
        f"{de_mean:.2f} +/- {de_std:.2f} (aralik: {de_min:.2f}-{de_max:.2f}) renk degisimi gosterdi. "
        f"Bu, Mokrzycki & Tatol (2011) kriterlerine gore **{damage_class}** kategorisindedir "
        f"({damage_severity} hasar). "
    )
    if stat_test and 'test_name' in stat_test:
        cohen_str = ''
        if stat_test.get('cohen_d') is not None:
            cohen_str = f" Etki buyuklugu Cohen's d = {stat_test['cohen_d']:.2f} ({stat_test['cohen_d_interpretation']})."
        summary_tr += f"{stat_test['test_name']} ile degisim {sig_str} bulundu ({p_str}).{cohen_str}"
    
    eng = (
        f"After aging treatment, the {n} specimens exhibited a mean total color difference "
        f"of Delta-E-2000 = {de_mean:.2f} +/- {de_std:.2f} (range: {de_min:.2f}-{de_max:.2f}), "
        f"corresponding to a {damage_severity} damage class according to "
        f"Mokrzycki & Tatol (2011) classification."
    )
    if stat_test and 'test_name' in stat_test:
        eng += (
            f" {stat_test['test_name']} confirmed the change was "
            f"{'statistically significant' if stat_test['is_significant'] else 'not statistically significant'} "
            f"({p_str})."
        )
        if stat_test.get('cohen_d') is not None:
            eng += f" Effect size (Cohen's d = {stat_test['cohen_d']:.2f}) indicates a {stat_test['cohen_d_interpretation'].split(' (')[0].lower()} effect."
    
    return {
        'damage_class': damage_class,
        'damage_severity': damage_severity,
        'summary_tr': summary_tr,
        'paper_ready_en': eng,
    }
