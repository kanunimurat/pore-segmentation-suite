"""
Segmentation algoritmaları — pore tespiti için.
Tüm algoritmalar (H, W) shape'inde bool numpy mask döner.
"""
import numpy as np
import cv2
from skimage import filters, morphology, measure
from sklearn.cluster import KMeans


def _bilateral_denoise(gray, d=7, sigma_color=50, sigma_space=50):
    """Standart kenar-koruyucu yumuşatma."""
    return cv2.bilateralFilter(gray, d, sigma_color, sigma_space)


def segment_DoG(img_rgb, sigma1=3, sigma2=15, percentile=95, multiscale=False):
    """
    Difference of Gaussians blob detection.
    multiscale=True ise [(1,7),(3,15),(5,25)] ölçeklerinde union alır.
    """
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    denoised = _bilateral_denoise(gray)
    
    if multiscale:
        scales = [(1,7), (3,15), (5,25)]
    else:
        scales = [(sigma1, sigma2)]
    
    union = np.zeros_like(gray, dtype=bool)
    for s1, s2 in scales:
        g1 = cv2.GaussianBlur(denoised, (0,0), s1)
        g2 = cv2.GaussianBlur(denoised, (0,0), s2)
        dog = g2.astype(np.float32) - g1.astype(np.float32)
        union |= (dog > np.percentile(dog, percentile))
    
    return union, gray


def segment_MSER(img_rgb, delta=4, min_area=10, max_area=3000):
    """
    Maximally Stable Extremal Regions — koyu lekeleri yakalar.
    """
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    denoised = _bilateral_denoise(gray, d=5, sigma_color=40, sigma_space=40)
    mser = cv2.MSER_create(delta=delta, min_area=min_area, max_area=max_area)
    regions, _ = mser.detectRegions(denoised)
    mask = np.zeros_like(gray, dtype=bool)
    for region in regions:
        for (x,y) in region:
            mask[y,x] = True
    return mask, denoised


def segment_Sauvola(img_rgb, window_size=51, k=0.2, R=128):
    """
    Sauvola adaptive thresholding — yerel pencere bazlı.
    """
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    denoised = _bilateral_denoise(gray)
    if window_size % 2 == 0: window_size += 1
    thresh = filters.threshold_sauvola(denoised, window_size=window_size, k=k, r=R)
    mask = denoised < thresh
    return mask, denoised


def segment_ColorDistance(img_rgb, pore_colors_rgb, max_distance=25, color_space='lab'):
    """
    Renk-paleti tabanlı segmentasyon.
    pore_colors_rgb: list of [R,G,B] — pore olarak işaretlenmiş renkler
    max_distance: Euclidean distance threshold in chosen color space
    color_space: 'rgb' | 'lab' | 'hsv'
    """
    if not pore_colors_rgb:
        return np.zeros(img_rgb.shape[:2], dtype=bool), cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    
    # Convert image and reference colors to chosen space
    if color_space == 'lab':
        img_conv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
        ref = np.array(pore_colors_rgb, dtype=np.uint8).reshape(-1,1,3)
        ref_conv = cv2.cvtColor(ref, cv2.COLOR_RGB2LAB).astype(np.float32).reshape(-1,3)
    elif color_space == 'hsv':
        img_conv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV).astype(np.float32)
        ref = np.array(pore_colors_rgb, dtype=np.uint8).reshape(-1,1,3)
        ref_conv = cv2.cvtColor(ref, cv2.COLOR_RGB2HSV).astype(np.float32).reshape(-1,3)
    else:  # rgb
        img_conv = img_rgb.astype(np.float32)
        ref_conv = np.array(pore_colors_rgb, dtype=np.float32)
    
    # Per-pixel min distance to any reference color
    H, W = img_rgb.shape[:2]
    pixels = img_conv.reshape(-1, 3)
    # Vectorized distance: (N, 1, 3) - (1, K, 3) -> (N, K, 3) -> norm over axis 2
    diffs = pixels[:, None, :] - ref_conv[None, :, :]
    dists = np.linalg.norm(diffs, axis=2)
    min_dist = dists.min(axis=1).reshape(H, W)
    
    mask = min_dist < max_distance
    
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    return mask, gray


def extract_palette_kmeans(img_rgb, n_clusters=7, sample_size=50000, random_state=42):
    """
    Görüntüden K-means ile dominant renkleri çıkar.
    Returns: list of dicts [{'rgb': [r,g,b], 'hex': '#xxxxxx', 'fraction_pct': float, 'brightness': float}]
    """
    pixels = img_rgb.reshape(-1, 3)
    n = min(sample_size, len(pixels))
    idx = np.random.RandomState(random_state).choice(len(pixels), size=n, replace=False)
    sample = pixels[idx]
    
    km = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=5).fit(sample)
    labels = km.predict(pixels)
    
    centers = km.cluster_centers_.astype(np.uint8)
    counts = np.bincount(labels, minlength=n_clusters)
    fractions = counts / counts.sum() * 100
    
    colors = []
    for i in range(n_clusters):
        rgb = centers[i].tolist()
        hex_str = '#{:02x}{:02x}{:02x}'.format(*rgb)
        colors.append({
            'rgb': rgb,
            'hex': hex_str,
            'fraction_pct': float(fractions[i]),
            'brightness': float(sum(rgb))/3
        })
    
    colors.sort(key=lambda c: c['brightness'])
    return colors



# ============================================================
# FAZ 1 — Klasik Yöntemler (ek)
# ============================================================

def segment_MultiOtsu(img_rgb, n_classes=3, dark_class_count=1):
    """
    Multi-level Otsu thresholding. Otomatik, parametresiz.
    dark_class_count: en koyu kaç sınıfı pore say (1, 2, ...)
    """
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    denoised = _bilateral_denoise(gray)
    try:
        thresholds = filters.threshold_multiotsu(denoised, classes=n_classes)
    except Exception:
        # Çok az dinamik aralık varsa basit Otsu'ya düş
        return segment_Sauvola(img_rgb, window_size=51, k=0.2)
    
    # En koyu dark_class_count sınıfı pore say
    if dark_class_count >= n_classes:
        dark_class_count = n_classes - 1
    cutoff = thresholds[dark_class_count - 1] if dark_class_count <= len(thresholds) else thresholds[-1]
    mask = denoised < cutoff
    return mask, gray


def segment_BottomHat(img_rgb, kernel_size=21, percentile=90):
    """
    Bottom-hat (a.k.a. black-hat) morfoloji — küçük koyu detayları izole eder.
    Hızlı, yorumlanabilir; DoG alternatifi.
    """
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    denoised = _bilateral_denoise(gray)
    if kernel_size % 2 == 0: kernel_size += 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    bh = cv2.morphologyEx(denoised, cv2.MORPH_BLACKHAT, kernel)
    # Yüksek bh değeri = koyu detay
    t = np.percentile(bh, percentile)
    mask = bh > t
    return mask, gray


def segment_AutoThreshold(img_rgb, method='triangle'):
    """
    Otomatik global eşik: triangle | yen | isodata | otsu.
    Sıfır parametre, histogram tabanlı.
    """
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    denoised = _bilateral_denoise(gray)
    try:
        if method == 'triangle':
            t = filters.threshold_triangle(denoised)
        elif method == 'yen':
            t = filters.threshold_yen(denoised)
        elif method == 'isodata':
            t = filters.threshold_isodata(denoised)
        elif method == 'otsu':
            t = filters.threshold_otsu(denoised)
        elif method == 'mean':
            t = filters.threshold_mean(denoised)
        elif method == 'minimum':
            t = filters.threshold_minimum(denoised)
        else:
            t = filters.threshold_otsu(denoised)
    except Exception:
        t = float(np.median(denoised)) * 0.85
    mask = denoised < t
    return mask, gray


def segment_Frangi(img_rgb, sigma_min=1, sigma_max=8, step=2, 
                    alpha=0.5, beta=0.5, gamma=15, dark=True, percentile=90):
    """
    Frangi vesselness — uzamış/bağlantılı yapılar için.
    Travertende bağlı gözenek ağlarını yakalar.
    """
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    denoised = _bilateral_denoise(gray)
    sigmas = list(range(sigma_min, sigma_max+1, step))
    vesselness = filters.frangi(denoised, sigmas=sigmas, alpha=alpha, beta=beta, 
                                  gamma=gamma, black_ridges=dark)
    t = np.percentile(vesselness, percentile)
    mask = vesselness > t
    return mask, gray


def segment_GMM(img_rgb, n_components=3, dark_component_count=1, sample_size=20000):
    """
    Gaussian Mixture Model renk kümeleme — K-means'in probabilistik versiyonu.
    """
    from sklearn.mixture import GaussianMixture
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    pixels = img_rgb.reshape(-1, 3).astype(np.float32)
    n = min(sample_size, len(pixels))
    idx = np.random.RandomState(42).choice(len(pixels), size=n, replace=False)
    gmm = GaussianMixture(n_components=n_components, random_state=42, 
                          covariance_type='full', max_iter=100).fit(pixels[idx])
    labels = gmm.predict(pixels).reshape(img_rgb.shape[:2])
    # Means'i brightness'a göre sırala, en koyu N component pore
    means = gmm.means_
    brightness = means.sum(axis=1)
    order = np.argsort(brightness)
    dark_labels = order[:dark_component_count]
    mask = np.isin(labels, dark_labels)
    return mask, gray


def segment_Watershed(img_rgb, min_distance=10, base_threshold='otsu'):
    """
    Marker-controlled watershed — yapışık pore'ları ayırır.
    İlk aşama: kaba binary mask (otsu/triangle/multi-otsu).
    İkinci: distance transform → local maxima → marker.
    Üçüncü: watershed boundary.
    """
    from scipy import ndimage as ndi
    from skimage.feature import peak_local_max
    from skimage.segmentation import watershed as ws_func
    
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    denoised = _bilateral_denoise(gray)
    
    # Kaba mask
    if base_threshold == 'otsu':
        t = filters.threshold_otsu(denoised); base_mask = denoised < t
    elif base_threshold == 'multiotsu':
        thr = filters.threshold_multiotsu(denoised, classes=3)
        base_mask = denoised < thr[0]
    else:
        t = filters.threshold_triangle(denoised); base_mask = denoised < t
    
    # Distance transform
    distance = ndi.distance_transform_edt(base_mask)
    # Local maxima as markers
    coords = peak_local_max(distance, min_distance=min_distance, labels=base_mask)
    marker_mask = np.zeros(distance.shape, dtype=bool)
    if len(coords) > 0:
        marker_mask[tuple(coords.T)] = True
    markers, _ = ndi.label(marker_mask)
    # Watershed
    labels = ws_func(-distance, markers, mask=base_mask)
    mask = labels > 0
    return mask, gray


# ============================================================
# FAZ 2 — Modern Deep Learning (optional imports)
# ============================================================

# SAM2 — Segment Anything Model 2 (Meta, 2024)
_SAM2_AVAILABLE = None  # lazy check

def _check_sam2():
    global _SAM2_AVAILABLE
    if _SAM2_AVAILABLE is not None:
        return _SAM2_AVAILABLE
    try:
        from ultralytics import SAM  # noqa: F401
        _SAM2_AVAILABLE = True
    except ImportError:
        _SAM2_AVAILABLE = False
    return _SAM2_AVAILABLE


def segment_SAM2(img_rgb, model_name='sam2_b.pt', mode='auto', points=None, point_labels=None):
    """
    Segment Anything Model 2 (Meta, 2024).
    mode='auto'  → tüm görüntüde otomatik tüm nesneleri segmente eder
    mode='point' → verilen noktalardan başlayarak segment çıkarır
    
    Gerektiren: pip install ultralytics
    Model boyutları: sam2_t.pt (39MB), sam2_s.pt (46MB), sam2_b.pt (80MB), sam2_l.pt (224MB)
    """
    if not _check_sam2():
        return None, None, 'SAM2 yüklü değil. Kur: pip install ultralytics'
    
    from ultralytics import SAM
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    
    try:
        sam = SAM(model_name)  # Model otomatik indirilir (ilk kullanımda)
        if mode == 'point' and points is not None:
            results = sam(img_rgb, points=points, labels=point_labels or [1]*len(points))
        else:
            results = sam(img_rgb)  # otomatik mode
        
        # Tüm mask'leri birleştir
        if results and len(results) > 0 and hasattr(results[0], 'masks') and results[0].masks is not None:
            masks_data = results[0].masks.data.cpu().numpy()  # (N, H, W)
            mask = np.any(masks_data > 0.5, axis=0)
            return mask.astype(bool), gray, None
        else:
            return np.zeros(gray.shape, dtype=bool), gray, 'SAM2 hiç maske üretmedi'
    except Exception as e:
        return None, None, f'SAM2 hatası: {e}'


# CellPose — Stringer & Pachitariu 2021-2024
_CELLPOSE_AVAILABLE = None

def _check_cellpose():
    global _CELLPOSE_AVAILABLE
    if _CELLPOSE_AVAILABLE is not None:
        return _CELLPOSE_AVAILABLE
    try:
        from cellpose import models  # noqa: F401
        _CELLPOSE_AVAILABLE = True
    except ImportError:
        _CELLPOSE_AVAILABLE = False
    return _CELLPOSE_AVAILABLE


def segment_CellPose(img_rgb, model_type='cyto3', diameter=None, flow_threshold=0.4, 
                       cellprob_threshold=0.0):
    """
    CellPose 3 generalist segmenter (Stringer & Pachitariu).
    model_type: 'cyto3' (önerilen) | 'nuclei' | 'cyto2'
    diameter: ortalama nesne çapı (None = otomatik tahmin)
    
    Gerektiren: pip install cellpose
    """
    if not _check_cellpose():
        return None, None, 'CellPose yüklü değil. Kur: pip install cellpose'
    
    from cellpose import models
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    
    try:
        # Cellpose koyu nesneler bekler — gerekirse invert et
        model = models.CellposeModel(model_type=model_type, gpu=False)
        # Inverted gray verirsek koyu pore'lar parlak nesne gibi davranır
        masks, flows, styles = model.eval(255-gray, diameter=diameter, 
                                            flow_threshold=flow_threshold,
                                            cellprob_threshold=cellprob_threshold,
                                            channels=[0,0])
        mask = masks > 0
        return mask, gray, None
    except Exception as e:
        return None, None, f'CellPose hatası: {e}'



# ============================================================
# GELİŞMİŞ RENK YELPAZESİ ÇIKARMA — Standalone Engine
# ============================================================

def extract_palette(img_rgb, algorithm='kmeans', n_clusters=7,
                     color_space='lab', sample_size=50000, random_state=42):
    """
    Görüntüden dominant renk paletini çıkarır.
    
    algorithm: 'kmeans' | 'minibatch_kmeans' | 'gmm' | 'meanshift' | 'median_cut'
    color_space: 'rgb' | 'hsv' | 'lab'
    n_clusters: Renk sayısı (MeanShift'te yok sayılır — otomatik bulur)
    sample_size: Hız için pixel sub-sampling (büyük görüntülerde önemli)
    
    Returns: list of dicts with keys: rgb, hex, fraction_pct, brightness
    """
    H, W = img_rgb.shape[:2]
    
    # Renk uzayı dönüşümü (Lab perceptual açıdan tercih edilir)
    if color_space == 'lab':
        img_conv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2LAB)
    elif color_space == 'hsv':
        img_conv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
    else:
        img_conv = img_rgb
    
    pixels = img_conv.reshape(-1, 3).astype(np.float32)
    n = min(sample_size, len(pixels))
    rng = np.random.RandomState(random_state)
    idx = rng.choice(len(pixels), size=n, replace=False)
    sample = pixels[idx]
    
    # ─── Median Cut özel yol (kendi renk uzayında çalışır) ───
    if algorithm == 'median_cut':
        from PIL import Image as PILImage
        pil_img = PILImage.fromarray(img_rgb)
        quant = pil_img.quantize(colors=n_clusters, method=PILImage.MEDIANCUT)
        palette = quant.getpalette()[:n_clusters*3]
        centers_rgb = np.array(palette).reshape(-1, 3).astype(np.uint8)
        labels = np.array(quant).flatten()
        counts = np.bincount(labels, minlength=n_clusters)
        fractions = counts / counts.sum() * 100
        return _format_palette(centers_rgb, fractions)
    
    # ─── sklearn tabanlı algoritmalar ───
    if algorithm == 'kmeans':
        from sklearn.cluster import KMeans
        model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=5).fit(sample)
        labels_full = model.predict(pixels)
        centers_in_space = model.cluster_centers_
    elif algorithm == 'minibatch_kmeans':
        from sklearn.cluster import MiniBatchKMeans
        model = MiniBatchKMeans(n_clusters=n_clusters, random_state=random_state, 
                                  batch_size=1024, n_init=5).fit(sample)
        labels_full = model.predict(pixels)
        centers_in_space = model.cluster_centers_
    elif algorithm == 'gmm':
        from sklearn.mixture import GaussianMixture
        # reg_covar ile singular kovaryans matrix'i önle; float64 sayısal kararlılık için
        model = GaussianMixture(n_components=n_clusters, random_state=random_state,
                                  covariance_type='full', max_iter=100, reg_covar=1e-3).fit(sample.astype(np.float64))
        labels_full = model.predict(pixels)
        centers_in_space = model.means_
    elif algorithm == 'meanshift':
        from sklearn.cluster import MeanShift, estimate_bandwidth
        bandwidth = estimate_bandwidth(sample, quantile=0.2, n_samples=min(500, len(sample)))
        if bandwidth <= 0:
            bandwidth = 25
        model = MeanShift(bandwidth=bandwidth, bin_seeding=True).fit(sample)
        labels_full = model.predict(pixels)
        centers_in_space = model.cluster_centers_
    else:
        raise ValueError(f'Bilinmeyen algoritma: {algorithm}')
    
    # Renk merkezlerini RGB'ye geri dönüştür
    n_centers = len(centers_in_space)
    if color_space != 'rgb':
        # Center'ları uint8 img formatına sok ve geri çevir
        centers_img = np.clip(centers_in_space, 0, 255).astype(np.uint8).reshape(-1, 1, 3)
        if color_space == 'lab':
            centers_rgb = cv2.cvtColor(centers_img, cv2.COLOR_LAB2RGB).reshape(-1, 3)
        elif color_space == 'hsv':
            centers_rgb = cv2.cvtColor(centers_img, cv2.COLOR_HSV2RGB).reshape(-1, 3)
    else:
        centers_rgb = np.clip(centers_in_space, 0, 255).astype(np.uint8)
    
    counts = np.bincount(labels_full, minlength=n_centers)
    fractions = counts / counts.sum() * 100
    
    return _format_palette(centers_rgb, fractions)


def _format_palette(centers_rgb, fractions):
    """Renk merkezlerini standart palet formatına çevir + Lab/LCh/Munsell ekle + brightness'a göre sırala."""
    # Lazy import — color_science modülü
    from . import color_science as _cs
    
    colors = []
    for i in range(len(centers_rgb)):
        rgb = [int(x) for x in centers_rgb[i]]
        hex_str = '#{:02x}{:02x}{:02x}'.format(*rgb)
        c = {
            'rgb': rgb,
            'hex': hex_str,
            'fraction_pct': float(fractions[i]),
            'brightness': float(sum(rgb))/3
        }
        # CIE Lab, LCh, Munsell ekle
        _cs.enrich_color_with_lab(c)
        colors.append(c)
    # L* (perceptual lightness)'a göre sırala — karanlıktan açığa
    colors.sort(key=lambda c: c['lab']['L'])
    return colors
