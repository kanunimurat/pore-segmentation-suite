# CHANGELOG

Sürüm geçmişi — [Semantic Versioning](https://semver.org/lang/tr/).

## [1.0.0] — 2026-05-26 — İlk halka açık sürüm

### Eklenen
- 4 traverten için önceden yüklü renk paletleri (KT, GT, NT, PT)
- 13 segmentasyon algoritması:
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

## [Planlanan v1.1]
- Dil seçimi (TR/EN/DE)
- Toplu işlem (192 görüntü → tek tıkla)
- IoU/Dice metrik (manuel ground truth ile)
- Ölçek çubuğu (scale bar) overlay
- Pixel-mm scale preset (kamera başına)

## [Planlanan v2.0]
- Custom U-Net transfer learning
- MicroSAM (SEM görüntüleri için)
- ImageJ macro export
- Web demo (Streamlit Cloud)
