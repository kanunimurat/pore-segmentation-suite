"""
Yanlış-pozitif filtreler — shape, texture, intensity tabanlı eleme.
"""
import numpy as np
from skimage import measure, morphology


def post_morphology(mask, opening_radius=1, closing_radius=1):
    """Küçük gürültüyü temizle, deliklere doldur."""
    if opening_radius > 0:
        mask = morphology.binary_opening(mask, morphology.disk(opening_radius))
    if closing_radius > 0:
        mask = morphology.binary_closing(mask, morphology.disk(closing_radius))
    return mask


def filter_components(mask, gray, 
                      min_area=8, max_area=None,
                      max_eccentricity=None, min_solidity=None,
                      max_interior_std=None,
                      must_be_dark=True, dark_thresh_factor=0.95):
    """
    Bağlı bileşen üzerinde shape/texture/intensity filtreleri uygula.
    
    Parametreler:
      min_area, max_area      : Alan eşikleri (piksel)
      max_eccentricity        : 0=daire, 1=çizgi. Bantları reddetmek için <0.95
      min_solidity            : 1=konveks, 0=düzensiz. Yüksek = düzgün şekiller
      max_interior_std        : Pore içi std. Yüksek = dokulu (mineral). Düşük tut.
      must_be_dark            : Pore mean intensity < median * dark_thresh_factor olmalı
      dark_thresh_factor      : Karanlık eşik çarpanı (0.95 default)
    
    Returns: filtered_mask, list of kept properties
    """
    labeled = measure.label(mask)
    props = measure.regionprops(labeled, intensity_image=gray)
    
    median = float(np.median(gray))
    final = np.zeros_like(mask, dtype=bool)
    kept = []
    
    for p in props:
        if p.area < min_area:
            continue
        if max_area is not None and p.area > max_area:
            continue
        if must_be_dark and p.mean_intensity > median * dark_thresh_factor:
            continue
        if max_eccentricity is not None and p.eccentricity > max_eccentricity:
            continue
        if min_solidity is not None and p.solidity < min_solidity:
            continue
        if max_interior_std is not None:
            ys, xs = np.where(labeled == p.label)
            if gray[ys, xs].std() > max_interior_std:
                continue
        
        final[labeled == p.label] = True
        kept.append(p)
    
    return final, kept


def compute_metrics(mask, kept_props, pixel_scale_mm=0.091):
    """Pore istatistiklerini hesapla — sayı, alan, dairesellik vb."""
    total_area_px = mask.size
    pore_area_px = int(mask.sum())
    porosity_pct = pore_area_px / total_area_px * 100
    
    n_pores = len(kept_props)
    if n_pores == 0:
        return {
            'porosity_pct': porosity_pct,
            'n_pores': 0,
            'mean_area_mm2': 0,
            'median_area_mm2': 0,
            'mean_circularity': 0,
            'mean_eccentricity': 0,
        }
    
    scale_area_mm2 = pixel_scale_mm ** 2
    areas_mm2 = [p.area * scale_area_mm2 for p in kept_props]
    
    circularities = []
    for p in kept_props:
        if p.perimeter > 0:
            c = 4 * np.pi * p.area / (p.perimeter ** 2)
            circularities.append(min(c, 1.0))
        else:
            circularities.append(0)
    
    eccentricities = [p.eccentricity for p in kept_props]
    
    return {
        'porosity_pct': float(porosity_pct),
        'n_pores': n_pores,
        'mean_area_mm2': float(np.mean(areas_mm2)),
        'median_area_mm2': float(np.median(areas_mm2)),
        'mean_circularity': float(np.mean(circularities)),
        'mean_eccentricity': float(np.mean(eccentricities)),
        'pore_area_px': pore_area_px,
        'total_area_px': total_area_px,
    }
