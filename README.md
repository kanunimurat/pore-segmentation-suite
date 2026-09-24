# 🪨 Pore Segmentation Suite

**An interactive pore-segmentation tool for travertines (and similar natural stones).**
Version: 1.3.0 — 2026  
License: MIT  |  Developer: Murat SERT, AKU

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20416896.svg)](https://doi.org/10.5281/zenodo.20416896)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![cite](https://img.shields.io/badge/cite-CITATION.cff-blue)](CITATION.cff)

---

## 🌐 Try it online (no installation)

Use the app directly in your browser — no Python required:

**https://pore-and-color-segmentation-suite.streamlit.app**

> Hosted on Streamlit Community Cloud (free tier). Very large images (>3000 px) may be slow online — for heavy use, run locally (below).

---

## ✨ What's new (v1.3.0 — validation & reproducibility)

- **Automated tests**: 120 pytest tests run on every push (GitHub Actions, Linux/Windows/macOS). CIEDE2000 is checked against the 34 reference pairs of Sharma, Wu & Dalal (2005).
- **Correct ΔE**: computed directly from the mean CIELAB (the 8-bit sRGB round-trip of v1.2 shifted ΔE-2000 by up to 0.24).
- **Metric-specific perceptual thresholds**: ΔE-2000 → PT = 0.8 / AT = 1.8 (Paravina et al., 2015); ΔE-76 → Mokrzycki & Tatol (2011) classes. ΔE is tested against the perceptibility threshold, not against zero.
- **SAM 2 prompted mode**: Sauvola candidates → SAM 2 pore outlines. **Cellpose 4** (Cellpose-SAM) supported.
- **Fixed-percentile warning** for DoG, Bottom-Hat and Frangi (they mark a nearly constant area fraction whatever the stone).
- **`reproduce/`** scripts regenerate every table and figure of the SoftwareX paper from the raw images.

> Previous: **v1.2.1** — web release, sample gallery; **v1.2.0** — pore-size distribution, reliability badge.

---

## 🧪 Tests and reproducibility

```bash
pip install -r requirements.txt -r requirements-test.txt
python -m pytest            # 120 tests
```

| Script | Regenerates |
|---|---|
| `reproduce/benchmark_algorithms.py IMAGE --palette KT` | Table 2 / Figure 6 data (12 setup-free algorithms, interface defaults; logs SHA-256, parameters, library versions) |
| `reproduce/make_figures.py fig5 / fig6 / figS3` | Figures 5, 6 and S3 |
| `reproduce/reproduce_aging_example.py PRE POST --prefix NT-D` | Table 3 and Supplementary Note S1 |
| `reproduce/reproduce_dataset_matrix.py ROOT` | Supplementary Table S1 (96 specimen pairs) |
| `reproduce/run_foundation_models.py IMAGES --sam-weights sam2_b.pt` | SAM 2 / Cellpose runs (porosity, pore count, time) |

Library versions matter: MSER output differs between OpenCV 4.x and 5.x, so `requirements.txt` pins OpenCV < 5.

---

## 🚀 Quick Start (3 steps)

### 1️⃣ First-time setup (only once)

**macOS:** double-click `İlk Kurulum.command`.  
(Use right-click → Open if needed — macOS may show a security warning.)

**Windows:** skip this step — `Baslat.bat` installs everything automatically on first run.

This installs the required Python libraries automatically (~2-3 minutes).

### 2️⃣ Run the app

**macOS:** double-click `Başlat.command` (or the `Gözenek Tespit.app` application).  
**Windows:** double-click `Baslat.bat`.

Your browser opens automatically at `http://localhost:8501`.

### 3️⃣ Use it

- Upload an image from the left panel (jpg/png/tif)
- Pick a stone type (KT/GT/NT/PT)
- Choose an algorithm (14 methods available)
- Move the sliders — the overlay updates in real time
- Save a good parameter set with "💾 Save these parameters"

---

## ⚠️ macOS Security Warning on First Run

macOS may block downloaded software. If you get a "cannot be opened" error:

**Option 1 (easy):** Open the file via **right-click → Open**. After the first launch, normal double-click works.

**Option 2 (permanent):** In Terminal:
```bash
cd pore-segmentation-suite
xattr -dr com.apple.quarantine Başlat.command
xattr -dr com.apple.quarantine "İlk Kurulum.command"
xattr -dr com.apple.quarantine "Gözenek Tespit.app"
```

---

## 🎨 14 Algorithms — 5 Categories

### 🔵 Classical Thresholding
- **Sauvola** — Local adaptive threshold
- **Multi-Otsu** — Automatic multi-level
- **Auto Threshold** — Triangle / Yen / IsoData / Otsu / Mean / Minimum

### 🟢 Blob & Region Detection
- **DoG** — Difference of Gaussians (multi-scale option available)
- **MSER** — Maximally Stable Extremal Regions
- **Bottom-Hat Morphology** — Isolates small dark details
- **Frangi Vesselness** — Elongated/connected structures
- **Watershed (Marker-Controlled)** — Separates touching pores

### 🟣 Color & Clustering Based
- **Color Distance** — Color-palette based
- **GMM** — Gaussian Mixture Model (probabilistic)

### 🤝 Hybrid
- **DoG + Color Filter**
- **MSER + Color Filter**

### 🚀 Modern Deep Learning (optional)
- **SAM 2** (Segment Anything Model 2, Meta 2024) — default *prompted* mode: classical candidates → SAM 2 outlines
- **Cellpose** (v3 `cyto3` or v4 Cellpose-SAM)

**Extra setup for DL:**
```bash
pip3 install -r requirements-modern.txt
```
(İlk Kurulum.command will also offer this.)

---

## 🎨 Color Palette System

**7 dominant colors** per stone (K-means clustering):
- Auto-load: `palettes/{KT,GT,NT,PT}.json`
- Compute a new K-means palette from the image (one click)
- Pixel-click color picker ("Add the color at this point to the pore list")
- Mark each color as pore/matrix (checkbox)

## 🚫 False-Positive Filters

- **Min pore area** (px)
- **Eccentricity** — Reject bands
- **Solidity** — Reject irregular shapes
- **Texture std** — Reject fossils/minerals (critical for NT)
- **Must be dark** — Below median

## 🎯 Overlay Customization

- **2 styles**: Fill (transparent) / Boundaries only
- **12 color presets** + Auto + Custom (hex picker)
- **Alpha slider** (0.1 — 0.95)
- **Boundary thickness slider** (1 — 8 px)

---

## 📁 Folder Structure

```
pore-segmentation-suite/
├── 🚀 Başlat.command            ← DOUBLE-CLICK TO LAUNCH (macOS)
├── 🚀 Baslat.bat                 ← DOUBLE-CLICK TO LAUNCH (Windows)
├── 🛠️ İlk Kurulum.command       ← First-time setup
├── 📱 Gözenek Tespit.app/        ← .app bundle (with icon)
├── 📄 pore_tuner_v2.py           ← Main Streamlit application
├── 📁 modules/                   ← Backend modules
│   ├── segmentation.py           (14 algorithms)
│   ├── filters.py                (false-positive removal)
│   ├── palettes.py               (palette I/O)
│   ├── presets.py                (save/load parameters)
│   ├── color_science.py          (Lab / ΔE color metrics)
│   ├── aging_analysis.py         (pre/post ΔE analysis)
│   ├── comparison.py             (multi-method comparison)
│   ├── collage_builder.py        (comparison collage)
│   ├── pore_size.py              (pore-size distribution)
│   ├── i18n.py                   (TR/EN localization)
│   └── utils.py                  (helpers)
├── 📁 palettes/                  ← Per-stone color palette JSONs
│   ├── KT.json   (Karaman Light)
│   ├── GT.json   (Emirdağ Silver)
│   ├── NT.json   (Antalya Noche)
│   └── PT.json   (Kütahya Pembe)
├── 📁 sample_images/             ← Demo travertine image
├── 📁 presets/                   ← User parameter presets
├── 📁 assets/                    ← Icon files (PNG, ICNS)
│
├── 📄 README.md                  ← This file
├── 📄 LICENSE                    ← MIT
├── 📄 CITATION.cff               ← Modern citation format
├── 📄 CHANGELOG.md               ← Version history
├── 📄 ZENODO_SETUP.md            ← Citation infrastructure guide
├── 📄 requirements.txt           ← Required Python deps
└── 📄 requirements-modern.txt    ← Optional DL deps (SAM 2, CellPose)
```

---

## 🆘 Troubleshooting

**"streamlit: command not found"**
→ In Terminal: `python3 -m pip install -r requirements.txt`

**"Permission denied" (when double-clicking a .command file)**
→ In Terminal: `chmod +x "Başlat.command"`

**App opened but is slow**
→ Processing is slow on very large images (>3000 px). Downscale first: around 1500 px is ideal.

**SAM 2 / CellPose selected but "not installed" error**
→ `pip3 install -r requirements-modern.txt` (downloads ~500MB-2GB)

**Browser did not open automatically**
→ Manually: http://localhost:8501

---

## 📚 Citation

If you use this tool, please cite the software (the concept DOI always resolves to the latest version):

Sert, M. (2026). Pore Segmentation Suite: an open-source, interactive, multi-method tool
for pore segmentation and colour characterization (v1.3.0) [Computer software]. Zenodo.
https://doi.org/10.5281/zenodo.20416896

Software paper: Sert, M. Pore Segmentation Suite: an open-source, interactive, multi-method tool
for pore segmentation and colour characterization. SoftwareX (under review).

The `CITATION.cff` file is automatically recognized by GitHub.

---

## 📞 Contact

**Assist. Prof. Dr. Murat SERT**  
Afyon Kocatepe University  
Marble and Natural Stone Technologies Application and Research Center  
Department of Mining Engineering  
📧 msert@aku.edu.tr  
🔬 Project: 24.MÜH.03 — AKÜ BAP (Scientific Research Projects)

---

## 🤝 Contributing

If you have a new algorithm, a new filter, or a new feature in mind, open a GitHub issue or email directly.  
This software was built for the scientific community — your use cases are valuable.
