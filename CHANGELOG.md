# CHANGELOG

Sürüm geçmişi — [Semantic Versioning](https://semver.org/lang/tr/).

## [1.3.0] — 2026-09-24 — Validation and reproducibility (SoftwareX revision)

### Fixed
- **ΔE computation** (`aging_analysis.compute_pair_color_change`): the colour difference is now computed directly from the mean CIELAB coordinates. Up to v1.2.x the mean colour was converted to 8-bit sRGB (truncated) and back, which shifted ΔE-2000 by up to 0.24 units and made ΔE inconsistent with the reported ΔL*, Δa*, Δb*.
- **GMM segmentation** failed with scikit-learn ≥ 1.8 ("ill-defined empirical covariance"); now uses float64.
- **SAM 2**: the automatic mode returned the union of all masks (≈100 % of a stone surface), which the dark-component filter then removed entirely. New default `mode='prompted'`: Sauvola candidates are given to SAM 2 as point prompts and SAM 2 delineates each pore; masks larger than 1 % of the image are discarded in every mode.
- **Cellpose**: updated for the Cellpose 4 API (Cellpose-SAM, `cpsam`); Cellpose 3 still supported.

### Changed
- **Perceptual interpretation** is now metric-specific: ΔE-2000 → CIEDE2000 50:50 % perceptibility/acceptability thresholds PT = 0.8, AT = 1.8 (Paravina et al., 2015); ΔE-76 → the five observer classes of Mokrzycki & Tatol (2011); ΔE-94 → no class. The unsourced 5–10 and ≥10 classes were removed. The previous "2.3 perceptibility threshold" (a CIE76 JND) is no longer used for ΔE-2000.
- ΔE is tested against the perceptibility threshold of the metric (not against 0), with a Shapiro–Wilk-dependent choice between the one-sample t-test and the Wilcoxon signed-rank test.
- `opencv-python-headless` pinned to `< 5`: the MSER output changes in OpenCV 5.x.
- Warning in the interface for fixed-percentile detectors (DoG, Bottom-Hat, Frangi), which return a nearly constant area fraction regardless of the stone.

### Added
- **Automated test suite** (`tests/`, 120 tests, pytest; GitHub Actions on Linux/Windows/macOS): CIEDE2000 vs. the 34 reference pairs of Sharma et al. (2005), sRGB→CIELAB reference values, aging statistics vs. SciPy, perceptual classes, segmentation vs. a synthetic ground truth.
- **`reproduce/` scripts** that regenerate every table and figure of the SoftwareX paper from the raw images and log the image SHA-256, all parameters and library versions.

## [1.2.1] — 2026-06-07

### Added
- **Windows launcher** (`Baslat.bat`): one double-click installs dependencies on first run and starts the app.
- **Streamlit Community Cloud compatibility**: switched to `opencv-python-headless` so the app can be hosted online (Try-it-online link in README).

## [1.2.0] — 2026-06-02 — Görsel yenileme + gözenek boyut dağılımı

### Eklenen
- **Gözenek boyut dağılımı grafiği** (MIP benzeri): KDE diferansiyel eğri, logaritmik çap ekseni, gözenek-sınıf bandı (sub-/capillary/super-capillary), görüntü çözünürlüğü sınırı gölgesi ve D50 işareti. Saf inline-SVG, matplotlib bağımlılığı yok.
- **Güvenilirlik rozeti**: gözeneklilik rejimine göre renkli uyarı (<%2 / %2–8 / >%8) ve kalibrasyon MAE bağlamı.
- **"Örnek görüntü dene" demo butonu**: yüklemeden test için sentetik traverten yüzeyi + boş-durum rehberi.
- **Toplu indirme**: tüm çıktıları tek ZIP olarak indir (overlay + binary mask + metrik JSON).

### Değişen
- Oğuz Ergin "Tantuni Endeksi" esinli **sıcak turuncu görsel kimlik**: turuncu vurgulu başlıklar, butonlar, kart panelleri ve ışıldayan marka yazısı.
- Inline-SVG grafikler artık **tema-duyarlı** (açık/koyu) — eksen, ızgara, metin, dolgu ve bantlar temaya göre.
- **"Çalışma Modu" seçici**: büyütülmüş ve ortalanmış başlık, tema-özel pastel (açık) / derin (koyu) arka planlar.
- Mod bilgilendirme metinleri ve buton yazıları okunabilirlik için büyütüldü; buton yazıları siyah.

## [1.1.0] — 2026-05-31 — Çok dillilik + karşılaştırma

### Eklenen
- TR/EN dil seçimi (i18n altyapısı).
- **Çoklu-yöntem porozite yayılımı (P2)**: aynı görüntüde algoritma-bağımlılığını şeffaf raporlama.
- **Karşılaştırma-kolaj oluşturucu**: pre/post görüntüler + yöntem overlay paneli.

## [1.0.0] — 2026-05-26 — İlk halka açık sürüm

### Eklenen
- 4 traverten için önceden yüklü renk paletleri (KT, GT, NT, PT)
- 14 segmentasyon algoritması:
  - **Klasik eşikleme**: Sauvola, Multi-Otsu, Auto-Threshold (Triangle/Yen/Otsu/IsoData/Mean/Minimum)
  - **Blob detection**: DoG, MSER, Bottom-Hat, Frangi vesselness, Watershed
  - **Renk/clustering**: Color Distance, GMM (Gaussian Mixture Model)
  - **Hibrit**: DoG+Color Filter, MSER+Color Filter
  - **Modern DL**: SAM 2 (Meta 2024), CellPose 3
- 5 yanlış-pozitif filtresi (alan, eccentricity, solidity, doku std, karanlık)
- 12 dolgu renk preseti + auto-detect + custom hex
- Saydam dolgu / sadece sınırlar overlay modu
- Preset kaydet/yükle sistemi
- Görüntüden K-means palet hesaplama
- Pixel-tıklama renk seçici
- Detaylı pore istatistikleri tablosu (alan, dairesellik, eksantriklik vb.)
- CSV ve PNG çıktı indirme

### Mimari
- Streamlit web arayüzü
- Modüler kod: segmentation, filters, palettes, presets, utils
- Tüm konfigürasyon JSON tabanlı

## [Planlanan v2.0]
- Custom U-Net transfer learning
- MicroSAM (SEM görüntüleri için)
- ImageJ macro export
- Web demo (Streamlit Cloud)
