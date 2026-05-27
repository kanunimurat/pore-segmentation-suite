# 🪨 Pore Segmentation Suite

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20416896.svg)](https://doi.org/10.5281/zenodo.20416896)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![FAIR4RS](https://img.shields.io/badge/FAIR4RS-compliant-brightgreen.svg)](https://www.rd-alliance.org/group/fair-research-software-fair4rs-wg)

**An open-source interactive software for travertine surface characterization.**
Version: 1.0.0 — 2026
License: MIT  |  Author: Murat SERT, Afyon Kocatepe University

---

## 🚀 Quick Start (3 Steps)

### 1️⃣ First-time installation (only once)

Double-click `İlk Kurulum.command` (Initial Setup).
(If macOS shows a security warning: right-click → Open)

This automatically installs the required Python libraries (~2-3 minutes).

### 2️⃣ Launch the application

Double-click `Başlat.command` (Launch) or the `Pore Segmentation Suite.app` bundle.

Your browser opens automatically at `http://localhost:8501`.

### 3️⃣ Use

- Upload an image from the left panel (jpg/png/tif)
- Select the stone type (KT/GT/NT/PT)
- Select an algorithm (13 methods available)
- Adjust the sliders — the overlay updates in real time
- Save good parameter sets via "💾 Save these parameters"

---

## ⚠️ macOS Security Warning on First Launch

Mac may block downloaded executables. If you see a "cannot be opened" error:

**Solution 1 (easy):** Right-click the file → **Open**. After the first launch, normal double-click works.

**Solution 2 (permanent):** In Terminal:
```bash
cd pore-segmentation-suite
xattr -dr com.apple.quarantine Başlat.command
xattr -dr com.apple.quarantine "İlk Kurulum.command"
```

---

## 🎨 13 Algorithms — 5 Categories

### 🔵 Classical Thresholding
- **Sauvola** — Local adaptive thresholding
- **Multi-Otsu** — Automatic multi-level
- **Auto Threshold** — Triangle / Yen / IsoData / Otsu / Mean / Minimum

### 🟢 Blob & Region Detection
- **DoG** — Difference of Gaussians (with multi-scale option)
- **MSER** — Maximally Stable Extremal Regions
- **Bottom-Hat Morphology** — Isolates small dark details
- **Frangi Vesselness** — Elongated/connected structures
- **Watershed (Marker-Controlled)** — Separates touching pores

### 🟣 Color & Clustering-Based
- **Color Distance** — Color-palette based
- **GMM** — Gaussian Mixture Model (probabilistic)

### 🤝 Hybrid
- **DoG + Color Filter**
- **MSER + Color Filter**

### 🚀 Modern Deep Learning (optional)
- **SAM 2** (Segment Anything Model 2, Meta 2024)
- **CellPose 3** (Pretrained generalist)

**Additional installation for DL backends:**
```bash
pip3 install -r requirements-modern.txt
```

---

## 🎨 Color Palette System

For each stone type, **7 dominant colors** (K-means clustering):
- Automatic loading: `palettes/{KT,GT,NT,PT}.json`
- New K-means computation from image (one click)
- Pixel-click color picker ("Add this point's color to the pore list")
- Mark each color as pore/matrix (checkbox)

## 🚫 False-Positive Filters

- **Minimum pore area** (px)
- **Eccentricity** — Reject bands
- **Solidity** — Reject irregular shapes
- **Texture std** — Reject fossils/minerals (critical for NT)
- **Must be dark** — Below median

## 🎯 Overlay Customization

- **2 styles**: Fill (transparent) / Outline only
- **12 color presets** + Auto + Custom (hex picker)
- **Alpha slider** (0.1 — 0.95)
- **Outline thickness slider** (1 — 8 px)

---

## 📁 Folder Structure

```
pore-segmentation-suite/
├── 🚀 Başlat.command           ← DOUBLE-CLICK TO LAUNCH
├── 🛠️ İlk Kurulum.command      ← For first-time setup
├── 📄 pore_tuner.py             ← Main Streamlit application (v1)
├── 📄 pore_tuner_v2.py          ← Main Streamlit application (v2, mode selector)
├── 📁 modules/                  ← Backend modules
│   ├── segmentation.py          (13 algorithms)
│   ├── color_science.py         (CIE Lab, CIEDE2000)
│   ├── aging_analysis.py        (Pre/post pairing, statistics)
│   ├── collage_builder.py       (Q1 journal figure builder)
│   ├── filters.py               (False-positive filtering)
│   ├── palettes.py              (Palette I/O)
│   ├── presets.py               (Parameter save/load)
│   └── utils.py                 (Helper functions)
├── 📁 palettes/                 ← Per-stone color palette JSONs
│   ├── KT.json   (Karaman Light Travertine)
│   ├── GT.json   (Emirdağ Silver Travertine)
│   ├── NT.json   (Antalya Noche Travertine)
│   └── PT.json   (Kütahya Pink Travertine)
├── 📁 presets/                  ← User parameter presets
├── 📁 assets/                   ← Icon files (PNG, ICNS)
│
├── 📄 README.md                 ← This file
├── 📄 LICENSE                   ← MIT
├── 📄 CITATION.cff              ← Modern citation format
├── 📄 CHANGELOG.md              ← Version history
├── 📄 ZENODO_SETUP.md           ← Citation infrastructure guide
├── 📄 requirements.txt          ← Core Python dependencies
└── 📄 requirements-modern.txt   ← Optional DL dependencies (SAM 2, CellPose)
```

---

## 🆘 Troubleshooting

**"streamlit: command not found"**
→ In Terminal: `python3 -m pip install -r requirements.txt`

**"Permission denied" (when double-clicking .command files)**
→ In Terminal: `chmod +x "Başlat.command"`

**Application launched but slow**
→ Very large images (>3000 px) process slowly. Resize first: ~1500 px is ideal.

**SAM 2 / CellPose selected but "not installed" error**
→ `pip3 install -r requirements-modern.txt` (downloads approximately 500MB–2GB)

**Browser did not open automatically**
→ Manual: http://localhost:8501

---

## 📚 Citation

If you use this software, please cite it as follows:

> Sert, M. (2026). *Pore Segmentation Suite v1.0.0:*
> *An open-source interactive software for travertine surface characterization.*
> Zenodo. https://doi.org/10.5281/zenodo.20416896

And the companion software paper:

> Sert, M. (2026). *Pore Segmentation Suite: An open-source multi-mode*
> *software for travertine characterization.*
> SoftwareX. [in preparation]

And the companion methodology paper:

> Sert, M. (2026). *Per-stone adaptive pore segmentation of travertines:*
> *A comparative benchmark of classical thresholding, extremal regions,*
> *and modern foundation models.*
> Construction and Building Materials. [in preparation]

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

If you have suggestions for new algorithms, new filters, or new features, please open a GitHub issue or contact me directly via email.
This software is designed for the scientific community — your use cases are valuable.
