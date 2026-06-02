# 🪨 Pore Segmentation Suite

**An interactive pore-segmentation tool for travertines (and similar natural stones).**
Version: 1.2 — 2026  
License: MIT  |  Developer: Murat SERT, AKU

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20416896.svg)](https://doi.org/10.5281/zenodo.20416896)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![cite](https://img.shields.io/badge/cite-CITATION.cff-blue)](CITATION.cff)

---

## ✨ What's new (v1.2)

- **Pore-size distribution chart** (MIP-like, logarithmic axis, D50, imaging-resolution limit)
- **Reliability badge** — warning by porosity regime (<2% / 2–8% / >8%)
- **"Try a sample image"** demo button + one-click **Download all outputs as ZIP**
- **Theme-aware** inline-SVG charts (light/dark)
- Warm orange visual identity, glowing brand title, larger and more readable interface

> **This release (v1.2.0) DOI:** https://doi.org/10.5281/zenodo.20514039

> Previous: **v1.1** — TR/EN language switch, multi-method porosity spread, comparison collage.

---


## 🚀 Quick Start (3 steps)

### 1️⃣ First-time setup (only once)

**Double-click** `İlk Kurulum.command`.  
(Use right-click → Open if needed — macOS may show a security warning.)

This installs the required Python libraries automatically (~2-3 minutes).

### 2️⃣ Run the app

**Double-click** `Başlat.command`.  
Or double-click the `Gözenek Tespit.app` application.

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
- **SAM 2** (Segment Anything Model 2, Meta 2024)
- **CellPose 3** (Pretrained generalist)

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
├── 🚀 Başlat.command            ← DOUBLE-CLICK TO LAUNCH THE APP
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

If you use this tool, please cite it as:

> Sert, M. (2026). *Pore Segmentation Suite v1.2:*  
> *An open-source interactive tool for travertine pore segmentation.*  
> Zenodo. https://doi.org/10.5281/zenodo.20514039

And the accompanying methodology paper:

> Sert, M. (2026). *Per-stone adaptive pore segmentation of travertines:*  
> *A comparative benchmark of classical thresholding, extremal regions,*  
> *and modern foundation models.* (in preparation)

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
