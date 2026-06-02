# CHANGELOG

Sürüm geçmişi — [Semantic Versioning](https://semver.org/lang/tr/).

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
