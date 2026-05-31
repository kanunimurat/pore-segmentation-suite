# 🪨 Pore Segmentation Suite

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20416896.svg)](https://doi.org/10.5281/zenodo.20416896)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![FAIR4RS](https://img.shields.io/badge/FAIR4RS-compliant-brightgreen.svg)](https://www.rd-alliance.org/group/fair-research-software-fair4rs-wg)

**An open-source, interactive, multi-method tool for pore segmentation and colour characterization of travertines and similar natural stones.**
Version: 1.1.0 — 2026
License: MIT | Author: Murat SERT, Afyon Kocatepe University

---

## 🚀 Quick Start (3 Steps)

### 1️⃣ First-time installation (only once)

Double-click `İlk Kurulum.command` (Initial Setup).
(If macOS shows a security warning: right-click → Open)

This automatically installs the required Python libraries (~2–3 minutes).

### 2️⃣ Launch the application

Double-click `Başlat.command` (Launch) or the `Pore Segmentation Suite.app` bundle.

Your browser opens automatically at `http://localhost:8501`.

### 3️⃣ Use

- Upload an image from the left panel (jpg/png/tif)
- Select the stone type (KT/GT/NT/PT)
- Select an algorithm (**14 methods available**)
- Adjust the sliders — the overlay updates in real time
- Save good parameter sets via "💾 Save these parameters"
- Switch the interface language (English / Turkish) from the sidebar

---

## ✨ Four Work Modes

1. **Pore Segmentation** — single-image pore detection with 14 algorithms across five families.
2. **Colour Palette** — dominant-colour extraction (5 clustering algorithms × 3 colour spaces).
3. **Aging Analysis** — pre/post colour-change statistics compliant with EN 15886 and CIEDE2000, with a Mokrzycki–Tatol perceptual interpretation.
4. **Collage Builder** — journal-ready figure collages (Elsevier/Springer/ACS presets, up to 600 DPI).

The modes are unified in a single Streamlit interface with no manual data transfer between separate tools.

---

## 🎨 14 Algorithms — 5 Families

### 🔵 Classical Thresholding
- **Sauvola** — Local adaptive thresholding
- **Multi-Otsu** — Automatic multi-level
- **Auto Threshold** — Triangle / Yen / IsoData / Otsu / Mean / Minimum

### 🟢 Blob & Region Detection
- **DoG** — Difference of Gaussians (with multi-scale option)
- **MSER** — Maximally Stable Extremal Regions
- **Bottom-Hat Morphology** — Isolates small dark details
- **Frangi Vesselness** — Elongated / connected structures
- **Watershed (Marker-Controlled)** — Separates touching pores

### 🟣 Colour & Clustering-Based
- **Color Distance** — Colour-palette based
- **GMM** — Gaussian Mixture Model (probabilistic)

### 🤝 Hybrid
- **DoG + Color Filter**
- **MSER + Color Filter**

### 🚀 Modern Deep Learning (optional)
- **SAM 2** (Segment Anything Model 2, Meta 2024)
- **Cellpose** (pretrained generalist)

**Additional installation for DL backends:**
```bash
pip3 install -r requirements-modern.txt
```

---

## 🔬 Multi-Method Comparison (porosity spread)

A distinctive feature of the suite: the same image can be processed by all
setup-free algorithms at once, and the results are presented side by side as a
comparison collage together with the resulting **porosity spread**. This makes
the dependence of the porosity measurement on method choice — and the
associated uncertainty — explicit and auditable rather than hidden behind a
single number. The engine lives in `modules/comparison.py` and is also exposed
as a "Comparison" template in the Collage Builder.

---

## 🌐 Bilingual Interface

The full user interface is available in **English and Turkish** (`modules/i18n.py`),
switchable from the sidebar at run time.

---

## 🎨 Colour Palette System

For each stone type, **7 dominant colours** (K-means clustering):
- Automatic loading: `palettes/{KT,GT,NT,PT}.json`
- New K-means computation from an image (one click)
- Pixel-click colour picker ("Add this point's colour to the pore list")
- Mark each colour as pore/matrix (checkbox)

## 🚫 False-Positive Filters
- **Minimum pore area** (px)
- **Eccentricity** — Reject bands
- **Solidity** — Reject irregular shapes
- **Texture std** — Reject fossils/minerals (critical for NT)
- **Must be dark** — Below median

## 🎯 Overlay Customization
- **2 styles**: Fill (transparent) / Outline only
- **12 colour presets** + Auto + Custom (hex picker)
- **Alpha slider** (0.1 — 0.95)
- **Outline thickness slider** (1 — 8 px)

---

## 📁 Folder Structure

```
pore-segmentation-suite/
├── 🚀 Başlat.command            ← DOUBLE-CLICK TO LAUNCH
├── 🛠️ İlk Kurulum.command       ← For first-time setup
├── 📄 pore_tuner.py             ← Streamlit application (v1)
├── 📄 pore_tuner_v2.py          ← Streamlit application (v2, mode selector)
├── 📁 modules/                  ← Backend modules
│   ├── segmentation.py          (14 algorithms)
│   ├── color_science.py         (CIE L*a*b*, CIEDE2000)
│   ├── aging_analysis.py        (pre/post pairing, statistics)
│   ├── collage_builder.py       (journal figure builder)
│   ├── comparison.py            (multi-method batch + comparison collage)
│   ├── filters.py               (false-positive filtering)
│   ├── palettes.py              (palette I/O)
│   ├── presets.py               (parameter save/load)
│   ├── i18n.py                  (English / Turkish interface)
│   └── utils.py                 (helper functions)
├── 📁 palettes/                 ← Per-stone colour palette JSONs
│   ├── KT.json   (Karaman)
│   ├── GT.json   (Grey / Emirdağ)
│   ├── NT.json   (Antalya Noche)
│   └── PT.json   (Kütahya Pink)
├── 📁 presets/                  ← User parameter presets
├── 📁 assets/                   ← Icon files (PNG, ICNS)
│
├── 📄 README.md                 ← This file
├── 📄 LICENSE                   ← MIT
├── 📄 CITATION.cff              ← Citation metadata
├── 📄 CHANGELOG.md              ← Version history
├── 📄 requirements.txt          ← Core Python dependencies
└── 📄 requirements-modern.txt   ← Optional DL dependencies (SAM 2, Cellpose)
```

---

## 🆘 Troubleshooting

**"streamlit: command not found"** → In Terminal: `python3 -m pip install -r requirements.txt`

**"Permission denied" (when double-clicking .command files)** → In Terminal: `chmod +x "Başlat.command"`

**Application launched but slow** → Very large images (>3000 px) process slowly. Resize first: ~1500 px is ideal.

**SAM 2 / Cellpose selected but "not installed" error** → `pip3 install -r requirements-modern.txt` (downloads approximately 500 MB – 2 GB)

**Browser did not open automatically** → Manual: http://localhost:8501

---

## 📚 Citation

If you use this software, please cite it as follows:

> Sert, M. (2026). *Pore Segmentation Suite: an open-source, interactive, multi-method tool for pore segmentation and colour characterization.* Zenodo. https://doi.org/10.5281/zenodo.20416896

And the companion software paper:

> Sert, M. (2026). *Pore Segmentation Suite: an open-source, interactive, multi-method tool for pore segmentation and colour characterization.* SoftwareX. [under review]

The `CITATION.cff` file is automatically recognized by GitHub.

---

## 📞 Contact

**Dr. Murat SERT**
Afyon Kocatepe University
Marble and Natural Stone Technology Application and Research Center
📧 msert@aku.edu.tr
🔬 Project: 24.MÜH.03 — Afyon Kocatepe University, Scientific Research Projects Coordination Unit (BAP)

---

## 🤝 Contributing

If you have suggestions for new algorithms, filters, or features, please open a GitHub issue or contact me directly via email.
This software is designed for the scientific community — your use cases are valuable.
