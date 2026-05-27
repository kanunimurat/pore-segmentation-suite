# 🪨 Pore Segmentation Suite

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![FAIR4RS](https://img.shields.io/badge/FAIR4RS-compliant-brightgreen.svg)](https://www.rd-alliance.org/group/fair-research-software-fair4rs-wg)


*(Türkçe adıyla "Gözenek ve Renk Tespit Yazılımı")*

**Travertenler (ve benzer doğal taşlar) için interaktif gözenek segmentasyon aracı.**
Sürüm: 1.0 — 2026  
Lisans: MIT  |  Geliştirici: Murat SERT, AKÜ

---

## 🚀 Hızlı Başlangıç (3 Adım)

### 1️⃣ İlk kurulum (sadece bir defa)

`İlk Kurulum.command` dosyasına **çift tıkla**.  
(Sağ tık → Aç gerekirse — macOS güvenlik uyarısı çıkabilir)

Bu, gerekli Python kütüphanelerini otomatik kurar (~2-3 dakika).

### 2️⃣ Uygulamayı çalıştır

`Başlat.command` dosyasına **çift tıkla**.  
Veya `Gözenek Tespit.app` uygulamasına çift tıkla.

Tarayıcın otomatik olarak `http://localhost:8501` adresinde açılır.

### 3️⃣ Kullan

- Sol panelden bir görüntü yükle (jpg/png/tif)
- Taş tipini seç (KT/GT/NT/PT)
- Algoritma seç (13 farklı yöntem mevcut)
- Sliderları oyna, overlay anlık güncellenir
- İyi parametre setini "💾 Bu parametreleri kaydet" ile sakla

---

## ⚠️ İlk Çalıştırmada macOS Güvenlik Uyarısı

Mac'in indirilmiş yazılımları otomatik bloke edebilir. Eğer "açılamaz" hatası çıkarsa:

**Çözüm 1 (kolay):** Dosyaya **sağ tık → Aç** seçeneği ile aç. İlk açılıştan sonra normal çift tık çalışır.

**Çözüm 2 (kalıcı):** Terminal'de:
```bash
cd pore-segmentation-suite
xattr -dr com.apple.quarantine Başlat.command
xattr -dr com.apple.quarantine "İlk Kurulum.command"
xattr -dr com.apple.quarantine "Gözenek Tespit.app"
```

---

## 🎨 13 Algoritma — 5 Kategori

### 🔵 Klasik Eşikleme
- **Sauvola** — Yerel adaptif eşik
- **Multi-Otsu** — Otomatik multi-level
- **Auto Threshold** — Triangle / Yen / IsoData / Otsu / Mean / Minimum

### 🟢 Blob & Region Detection
- **DoG** — Difference of Gaussians (multi-scale opsiyonu var)
- **MSER** — Maximally Stable Extremal Regions
- **Bottom-Hat Morphology** — Küçük koyu detayları izole eder
- **Frangi Vesselness** — Uzamış/bağlantılı yapılar
- **Watershed Marker-Controlled** — Yapışık pore'ları ayırır

### 🟣 Renk & Clustering Tabanlı
- **Color Distance** — Renk paleti tabanlı
- **GMM** — Gaussian Mixture Model (probabilistik)

### 🤝 Hibrit
- **DoG + Color Filter**
- **MSER + Color Filter**

### 🚀 Modern Deep Learning (opsiyonel)
- **SAM 2** (Segment Anything Model 2, Meta 2024)
- **CellPose 3** (Pretrained generalist)

**DL için ek kurulum:**
```bash
pip3 install -r requirements-modern.txt
```
(İlk Kurulum.command bunu da soracak.)

---

## 🎨 Renk Paleti Sistemi

Her taş için **7 dominant renk** (K-means kümeleme):
- Otomatik yükleme: `palettes/{KT,GT,NT,PT}.json`
- Görüntüden yeni K-means hesaplama (tek tık)
- Pixel-tıklama renk seçici ("Bu noktadaki rengi pore listesine ekle")
- Her rengin pore/matriks olarak işaretlenmesi (checkbox)

## 🚫 Yanlış-Pozitif Filtreleri

- **Min pore alanı** (px)
- **Eccentricity** — Bantları reddet
- **Solidity** — Düzensiz şekilleri reddet
- **Doku std** — Fosil/mineralleri reddet (NT için kritik)
- **Karanlık olmalı** — Median altı

## 🎯 Overlay Özelleştirme

- **2 stil**: Dolgu (saydam) / Sadece sınırlar
- **12 renk preseti** + Auto + Custom (hex picker)
- **Alpha slider** (0.1 — 0.95)
- **Sınır kalınlığı slider** (1 — 8 px)

---

## 📁 Klasör Yapısı

```
pore-segmentation-suite/
├── 🚀 Başlat.command           ← ÇİFT TIKLA UYGULAMAYI BAŞLAT
├── 🛠️ İlk Kurulum.command      ← İlk kez için
├── 📱 Gözenek Tespit.app/       ← .app bundle (icon ile)
├── 📄 pore_tuner.py             ← Ana Streamlit uygulaması
├── 📁 modules/                  ← Backend modülleri
│   ├── segmentation.py          (13 algoritma)
│   ├── filters.py               (yanlış-pozitif eleme)
│   ├── palettes.py              (palet I/O)
│   ├── presets.py               (parametre kaydet/yükle)
│   └── utils.py                 (yardımcı)
├── 📁 palettes/                 ← Per-stone renk palet JSON'ları
│   ├── KT.json   (Karaman Light)
│   ├── GT.json   (Emirdağ Silver)
│   ├── NT.json   (Antalya Noche)
│   └── PT.json   (Kütahya Pembe)
├── 📁 presets/                  ← Kullanıcı parametre presetleri
├── 📁 outputs/                  ← Batch işlem çıktıları
├── 📁 assets/                   ← İkon dosyaları (PNG, ICNS)
│
├── 📄 README.md                 ← Bu dosya
├── 📄 LICENSE                   ← MIT
├── 📄 CITATION.cff              ← Modern citation format
├── 📄 CHANGELOG.md              ← Sürüm geçmişi
├── 📄 ZENODO_SETUP.md           ← Atıf altyapısı kılavuzu
├── 📄 requirements.txt          ← Zorunlu Python deps
└── 📄 requirements-modern.txt   ← Opsiyonel DL deps (SAM 2, CellPose)
```

---

## 🆘 Sorun Giderme

**"streamlit: command not found"**
→ Terminal'de: `python3 -m pip install -r requirements.txt`

**"Permission denied" (.command dosyasına çift tıklayınca)**
→ Terminal'de: `chmod +x "Başlat.command"`

**Uygulama açıldı ama yavaş**
→ Çok büyük görüntülerde (>3000 px) işleme yavaş. Önce küçült: 1500 px civarı ideal.

**SAM 2 / CellPose seçildi ama "yüklü değil" hatası**
→ `pip3 install -r requirements-modern.txt` (yaklaşık 500MB-2GB indirir)

**Tarayıcı otomatik açılmadı**
→ Manuel: http://localhost:8501

---

## 📚 Atıf

Bu aracı kullanırsanız lütfen şu şekilde atıf yapın:

> Sert, M. (2026). *Pore Segmentation Suite v1.0.0:*  
> *An open-source interactive software for travertine surface characterization.*  
> Zenodo. https://doi.org/10.5281/zenodo.XXXXXXX

Ve eşlik eden yazılım makalesi:

> Sert, M. (2026). *Pore Segmentation Suite: An open-source multi-mode*  
> *software for travertine characterization.*  
> SoftwareX. [in preparation]

Ve eşlik eden metodoloji makalesi:

> Sert, M. (2026). *Per-stone adaptive pore segmentation of travertines:*  
> *A comparative benchmark of classical thresholding, extremal regions,*  
> *and modern foundation models.*  
> Construction and Building Materials. [in preparation]

`CITATION.cff` dosyası GitHub tarafından otomatik tanınır.

---

## 📞 İletişim

**Dr. Öğr. Üyesi Murat SERT**  
Afyon Kocatepe Üniversitesi  
Mermer ve Doğaltaş Teknolojileri Uygulama ve Araştırma Merkezi  
📧 msert@aku.edu.tr  
🔬 Proje: 24.MÜH.03 — AKÜ BAP

---

## 🤝 Katkı

Yeni algoritma, yeni filtre veya yeni özellik önerin varsa GitHub issue aç veya doğrudan e-posta gönder.  
Bu yazılım bilim insanları topluluğu için tasarlandı — kullanım örneklerin değerlidir.
