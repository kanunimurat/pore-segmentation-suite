# -*- coding: utf-8 -*-
"""
CIE Renk Bilimi Modülü
=======================
RGB ↔ CIE L*a*b* ↔ CIE LCh dönüşümleri,
Munsell hue family yaklaşık tahmini,
ΔE-76, ΔE-94, ΔE-2000 renk farkı metrikleri.

Standartlar:
  - D65 illuminant (gün ışığı, 6504K)
  - CIE 1931 2° standard observer
  - skimage.color bağımlılığı (zaten requirements.txt'te)

Referanslar:
  - Sharma, G., Wu, W., Dalal, E.N. (2005). The CIEDE2000 color-difference 
    formula. Color Research & Application, 30(1), 21-30.
  - Wyszecki, G., Stiles, W.S. (2000). Color Science: Concepts and Methods.
"""
import math
import numpy as np
from skimage import color as skcolor


# ============================================================
# RGB ↔ Lab ↔ LCh DÖNÜŞÜMLERİ
# ============================================================

def rgb_to_lab(rgb):
    """
    sRGB [0-255] tuple/list → CIE L*a*b* (D65, 2°)
    Returns: (L*, a*, b*) — L*∈[0,100], a*∈[-128,127], b*∈[-128,127]
    """
    rgb_norm = np.array(rgb, dtype=np.float64).reshape(1, 1, 3) / 255.0
    lab = skcolor.rgb2lab(rgb_norm).reshape(3)
    return float(lab[0]), float(lab[1]), float(lab[2])


def lab_to_lch(L, a, b):
    """
    CIE L*a*b* → CIE LCh
    Returns: (L*, C*, h) — C*≥0, h∈[0,360°)
    """
    C = math.sqrt(a*a + b*b)
    h = math.degrees(math.atan2(b, a))
    if h < 0:
        h += 360
    return float(L), float(C), float(h)


def rgb_to_lch(rgb):
    """sRGB → LCh (kısa yol)."""
    L, a, b = rgb_to_lab(rgb)
    return lab_to_lch(L, a, b)


# ============================================================
# MUNSELL YAKLAŞIK TAHMİNİ
# ============================================================

# Munsell 10-hue family — taş endüstrisinde standart
MUNSELL_FAMILIES = ['R', 'YR', 'Y', 'GY', 'G', 'BG', 'B', 'PB', 'P', 'RP']
# Her family için merkez hue açısı (CIE LCh, derece)
MUNSELL_HUE_CENTERS = [0, 36, 72, 108, 144, 180, 216, 252, 288, 324]


def lab_to_munsell_approx(L, a, b):
    """
    CIE Lab → Munsell yaklaşık notation (örn. "7.5YR 6/4").
    
    NOT: Bu kesin Munsell renormalization değil — Munsell 10-hue family'lere
    LCh hue açısı eşlenmesi tabanlı bir yaklaşımdır. Tam doğruluk için
    `colour-science` paketi (Munsell lookup tables) kullanılmalıdır.
    
    Returns: string "HueNumber HueFamily Value/Chroma"
    """
    # Value ≈ L* / 10 (Munsell value 0-10)
    V = L / 10
    
    # Chroma in LCh
    C_lab = math.sqrt(a*a + b*b)
    # Munsell chroma ≈ C_lab / 5 (yaklaşık skala)
    munsell_C = C_lab / 5
    
    # Hue açısı [0,360)
    h = math.degrees(math.atan2(b, a))
    if h < 0:
        h += 360
    
    # Family bul — h_shifted = -18°'den 18°'ye kadar R, 18-54° YR, ...
    h_shifted = (h + 18) % 360
    family_idx = int(h_shifted / 36) % 10
    family_name = MUNSELL_FAMILIES[family_idx]
    
    # Family içindeki numara: 1-10 (3.6°'lik aralıklara böl)
    h_in_family = h_shifted - family_idx * 36
    family_num = int(h_in_family / 3.6) + 1
    family_num = max(1, min(10, family_num))
    
    # Value ve chroma yuvarla
    V_round = round(V * 2) / 2  # 0.5 hassasiyet
    C_round = round(munsell_C)
    
    if C_round < 1:
        # Çok düşük chroma → nötr (N)
        return f"N {V_round:.1f}/"
    
    return f"{family_num}{family_name} {V_round:.1f}/{C_round}"


# ============================================================
# ΔE RENK FARKI METRİKLERİ
# ============================================================

def delta_e_76(rgb1, rgb2):
    """
    ΔE-76 (CIE 1976) — basit Euclidean Lab mesafesi.
    Tarihsel öneme sahip, en eski formül.
    """
    L1, a1, b1 = rgb_to_lab(rgb1)
    L2, a2, b2 = rgb_to_lab(rgb2)
    return math.sqrt((L1-L2)**2 + (a1-a2)**2 + (b1-b2)**2)


def delta_e_94(rgb1, rgb2):
    """
    ΔE-94 (CIE 1994) — chroma ve hue ağırlıklı düzeltme.
    """
    lab1 = np.array(rgb_to_lab(rgb1), dtype=np.float64).reshape(1, 3)
    lab2 = np.array(rgb_to_lab(rgb2), dtype=np.float64).reshape(1, 3)
    return float(skcolor.deltaE_ciede94(lab1, lab2)[0])


def delta_e_2000(rgb1, rgb2):
    """
    ΔE-2000 (CIEDE2000) — modern standart, en doğru perceptual metrik.
    Q1 dergilerde önerilen formül (Sharma et al. 2005).
    """
    lab1 = np.array(rgb_to_lab(rgb1), dtype=np.float64).reshape(1, 1, 3)
    lab2 = np.array(rgb_to_lab(rgb2), dtype=np.float64).reshape(1, 1, 3)
    return float(skcolor.deltaE_ciede2000(lab1, lab2)[0, 0])


def delta_e_lab(lab1, lab2, method='2000'):
    """
    Colour difference between two CIELAB triplets (no sRGB round-trip).
    method: '76' (Euclidean dE*ab), '94' (CIE94, graphic arts) or '2000'
    (CIEDE2000, kL = kC = kH = 1). Validated against the 34 reference pairs
    of Sharma, Wu & Dalal (2005) in tests/test_ciede2000_sharma.py.
    """
    a = np.asarray(lab1, dtype=np.float64).reshape(1, 1, 3)
    b = np.asarray(lab2, dtype=np.float64).reshape(1, 1, 3)
    if str(method) == '76':
        return float(np.sqrt(((a - b) ** 2).sum()))
    if str(method) == '94':
        return float(skcolor.deltaE_ciede94(a, b)[0, 0])
    return float(skcolor.deltaE_ciede2000(a, b)[0, 0])


# ------------------------------------------------------------------
# Perceptual interpretation (v1.3.0)
# ------------------------------------------------------------------
# Each metric is interpreted only with thresholds that were defined FOR
# THAT METRIC:
#   * CIEDE2000: 50:50% perceptibility (PT) and acceptability (AT)
#     thresholds, dE00 = 0.8 and 1.8 (Paravina et al., 2015, J Esthet
#     Restor Dent 27:S1-S9, doi:10.1111/jerd.12149; 175 observers, 7 sites).
#   * CIE76 dE*ab: the five observer classes of Mokrzycki & Tatol (2011,
#     Machine Graphics & Vision 20(4):383-411, section 6.2), which are
#     defined for the Euclidean CIELAB difference.
#   * CIE94: no widely validated perceptual thresholds -> no class.
# Up to v1.2.x the Mokrzycki & Tatol classes (plus two extra, unsourced
# classes 5-10 and >=10) were applied to dE00, which mixes metrics.
DE2000_THRESHOLDS = {'PT': 0.8, 'AT': 1.8}

DE2000_CLASSES = (
    "Algılanamaz (below perceptibility threshold)",
    "Algılanabilir, kabul edilebilir (perceptible, acceptable)",
    "Kabul edilebilirlik eşiğinin üzerinde (beyond acceptability threshold)",
)
MT_CLASSES_76 = (
    (1.0, "Fark edilmez (not noticed)"),
    (2.0, "Sadece deneyimli gözlemci fark eder (experienced observer only)"),
    (3.5, "Deneyimsiz gözlemci de fark eder (unexperienced observer notices)"),
    (5.0, "Açık fark (clear difference)"),
    (float('inf'), "İki farklı renk (two different colours)"),
)
NO_CLASS_94 = "Doğrulanmış eşik yok (no validated threshold for CIE94)"


def perceptual_reference(method='2000', pt=None):
    """Lower bound of the 'perceptible' range for a metric (None if undefined)."""
    m = str(method)
    if m == '2000':
        return float(pt) if pt is not None else DE2000_THRESHOLDS['PT']
    if m == '76':
        return MT_CLASSES_76[0][0]
    return None


def interpret_delta_e(delta_e, method='2000', pt=None, at=None):
    """
    Perceptual class of a colour difference, using thresholds defined for
    the chosen metric (see the block comment above). pt/at override the
    CIEDE2000 thresholds (e.g. for material-specific values).
    """
    m = str(method)
    if m == '2000':
        pt = DE2000_THRESHOLDS['PT'] if pt is None else float(pt)
        at = DE2000_THRESHOLDS['AT'] if at is None else float(at)
        if delta_e < pt:
            return DE2000_CLASSES[0]
        if delta_e < at:
            return DE2000_CLASSES[1]
        return DE2000_CLASSES[2]
    if m == '76':
        for upper, label in MT_CLASSES_76:
            if delta_e < upper:
                return label
    return NO_CLASS_94


# ============================================================
# YARDIMCI — Lab/LCh/Munsell'i bir renge ekle
# ============================================================

def enrich_color_with_lab(color_dict):
    """
    Palet renk dict'ine Lab/LCh/Munsell alanlarını ekle.
    Input: {'rgb':[r,g,b], 'hex':..., 'fraction_pct':..., 'brightness':...}
    """
    L, a, b = rgb_to_lab(color_dict['rgb'])
    _, C, h = lab_to_lch(L, a, b)
    munsell = lab_to_munsell_approx(L, a, b)
    
    color_dict['lab'] = {'L': round(L, 2), 'a': round(a, 2), 'b': round(b, 2)}
    color_dict['lch'] = {'L': round(L, 2), 'C': round(C, 2), 'h': round(h, 1)}
    color_dict['munsell'] = munsell
    return color_dict


def enrich_palette_with_lab(palette):
    """Tüm palet listesindeki renklere Lab/LCh/Munsell ekle."""
    return [enrich_color_with_lab(c) for c in palette]



# ============================================================
# COLOR UNIFORMITY ANALYSIS (Seviye 4)
# ============================================================

def compute_uniformity(img_rgb, sample_size=20000, delta_e_sample=2000):
    """
    Görüntünün CIE Lab uzayındaki renk homojenliğini ölçer.
    
    Returns dict:
      mean_L/a/b      : Ortalama Lab değerleri
      std_L/a/b       : Per-channel standart sapma  
      delta_e_avg     : Ortalama renk farkı (mean color'dan ΔE-2000)
      delta_e_std     : ΔE-2000 standart sapması
      delta_e_p95     : ΔE-2000 95. percentile (outlier göstergesi)
      homogeneity_score : 0-10 (10 = mükemmel homojen)
      uniformity_class : kategorik etiket
      n_pixels_sampled : İstatistik için kullanılan piksel sayısı
    
    Bilimsel önem:
      - Taş kalite kontrolü için sayısal indeks
      - Pre/post salt karşılaştırması (ΔE değişimi = renk hasarı)
      - Cross-batch tutarlılık ölçütü
    """
    H, W = img_rgb.shape[:2]
    pixels = img_rgb.reshape(-1, 3)
    n = min(sample_size, len(pixels))
    rng = np.random.RandomState(42)
    idx = rng.choice(len(pixels), size=n, replace=False)
    sample = pixels[idx]
    
    # RGB → Lab (skimage, gerçek CIE)
    sample_norm = sample.astype(np.float64) / 255.0
    lab_pixels = skcolor.rgb2lab(sample_norm.reshape(-1, 1, 3)).reshape(-1, 3)
    
    L = lab_pixels[:, 0]
    a = lab_pixels[:, 1]
    b = lab_pixels[:, 2]
    
    mean_L, std_L = float(np.mean(L)), float(np.std(L))
    mean_a, std_a = float(np.mean(a)), float(np.std(a))
    mean_b, std_b = float(np.mean(b)), float(np.std(b))
    
    # Ortalama ΔE-2000 (mean color'dan sapma)
    mean_color = np.array([[[mean_L, mean_a, mean_b]]], dtype=np.float64)
    n_de = min(delta_e_sample, len(lab_pixels))
    de_idx = rng.choice(len(lab_pixels), size=n_de, replace=False)
    sampled_lab = lab_pixels[de_idx].reshape(-1, 1, 3)
    mean_color_tiled = np.tile(mean_color, (n_de, 1, 1))
    delta_es = skcolor.deltaE_ciede2000(mean_color_tiled, sampled_lab).flatten()
    
    delta_e_avg = float(np.mean(delta_es))
    delta_e_std = float(np.std(delta_es))
    delta_e_p95 = float(np.percentile(delta_es, 95))
    delta_e_max = float(np.max(delta_es))
    
    # Homojenlik skoru 0-10
    # Toplam Lab std (3 channel ortalaması) — düşük = homojen
    # Empirik ölçek: total_std 0 → 10 puan, total_std 25+ → 0 puan
    total_std = (std_L + std_a + std_b) / 3
    homogeneity_score = max(0.0, min(10.0, 10.0 - total_std / 2.5))
    
    # Sınıflandırma (ΔE-2000 ortalamasına göre)
    if delta_e_avg < 2:
        u_class = '🟢 Çok homojen'
    elif delta_e_avg < 5:
        u_class = '🔵 Homojen'
    elif delta_e_avg < 10:
        u_class = '🟡 Orta heterojen'
    elif delta_e_avg < 20:
        u_class = '🟠 Heterojen'
    else:
        u_class = '🔴 Çok heterojen'
    
    return {
        'mean_L': round(mean_L, 2), 'std_L': round(std_L, 2),
        'mean_a': round(mean_a, 2), 'std_a': round(std_a, 2),
        'mean_b': round(mean_b, 2), 'std_b': round(std_b, 2),
        'delta_e_avg_from_mean': round(delta_e_avg, 2),
        'delta_e_std': round(delta_e_std, 2),
        'delta_e_p95': round(delta_e_p95, 2),
        'delta_e_max': round(delta_e_max, 2),
        'homogeneity_score_0_10': round(homogeneity_score, 2),
        'uniformity_class': u_class,
        'n_pixels_sampled': n,
        'mean_color_rgb': skcolor.lab2rgb(mean_color).reshape(3).tolist(),
        'mean_color_hex': '#{:02x}{:02x}{:02x}'.format(
            *[int(np.clip(c*255, 0, 255)) for c in skcolor.lab2rgb(mean_color).reshape(3)]),
    }


def compare_uniformity(uniformity_pre, uniformity_post):
    """
    İki uniformity sonucu karşılaştır (örn. pre/post salt).
    Returns: dict with delta metrics.
    """
    # Mean Lab arası ΔE-2000
    mean_pre = np.array([[[uniformity_pre['mean_L'], uniformity_pre['mean_a'], uniformity_pre['mean_b']]]], dtype=np.float64)
    mean_post = np.array([[[uniformity_post['mean_L'], uniformity_post['mean_a'], uniformity_post['mean_b']]]], dtype=np.float64)
    mean_color_delta_e = float(skcolor.deltaE_ciede2000(mean_pre, mean_post)[0, 0])
    
    return {
        'delta_mean_L': round(uniformity_post['mean_L'] - uniformity_pre['mean_L'], 2),
        'delta_mean_a': round(uniformity_post['mean_a'] - uniformity_pre['mean_a'], 2),
        'delta_mean_b': round(uniformity_post['mean_b'] - uniformity_pre['mean_b'], 2),
        'mean_color_delta_e_2000': round(mean_color_delta_e, 2),
        'mean_color_interpretation': interpret_delta_e(mean_color_delta_e),
        'delta_homogeneity': round(uniformity_post['homogeneity_score_0_10'] - uniformity_pre['homogeneity_score_0_10'], 2),
        'delta_total_variance': round((uniformity_post['std_L'] + uniformity_post['std_a'] + uniformity_post['std_b']) - 
                                        (uniformity_pre['std_L'] + uniformity_pre['std_a'] + uniformity_pre['std_b']), 2),
    }
