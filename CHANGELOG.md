# CHANGELOG

Version history — [Semantic Versioning](https://semver.org/).

## [1.1.0] — 2026-05-31

### Added
- **Multi-method comparison engine** (`modules/comparison.py`): batch-segments a
  single image with all setup-free algorithms and produces a side-by-side
  comparison collage together with the resulting **porosity spread**, making the
  method-dependence of the porosity measurement explicit and auditable. This
  feature underlies the illustrative examples (inter-method porosity spread) in
  the companion software paper.
- **Comparison template** in the Collage Builder, wired to the new engine.
- **Bilingual user interface (English / Turkish)** via `modules/i18n.py`,
  switchable from the sidebar at run time.

### Changed
- Collage engine refinements: per-cell label colours, single-line / auto-height
  headers, vertical row labels, MSER overlay set to magenta, and pass-through
  styling options.
- Documentation harmonized: 14 algorithms stated consistently, standard names
  given as EN 15886 / EN 12370 / EN 1936, colour space written as CIE L*a*b*.

### Notes
- Public name standardized to **Pore Segmentation Suite**.
- This release is the version described in the SoftwareX software paper and is
  archived on Zenodo under the concept DOI 10.5281/zenodo.20416896.

## [1.0.0] — 2026-05-26 — Initial public release

### Added
- Pre-loaded colour palettes for four travertines (KT, GT, NT, PT)
- Segmentation algorithms across five families:
  - **Classical thresholding**: Sauvola, Multi-Otsu, Auto-Threshold (Triangle/Yen/Otsu/IsoData/Mean/Minimum)
  - **Blob & region**: DoG, MSER, Bottom-Hat, Frangi vesselness, Watershed
  - **Colour / clustering**: Color Distance, GMM (Gaussian Mixture Model)
  - **Hybrid**: DoG + Color Filter, MSER + Color Filter
  - **Modern DL (optional)**: SAM 2 (Meta 2024), Cellpose
- Five false-positive filters (area, eccentricity, solidity, texture std, dark-only)
- 12 fill colour presets + auto-detect + custom hex
- Transparent fill / outline-only overlay modes
- Preset save/load system
- K-means palette computation from an image
- Pixel-click colour picker
- Detailed pore statistics table (area, circularity, eccentricity, etc.)
- CSV and PNG output download

### Architecture
- Streamlit web interface
- Modular code: segmentation, colour science, aging analysis, filters, palettes, presets, utils
- All configuration JSON-based

## [Planned v2.0]
- Custom U-Net transfer learning
- MicroSAM (for SEM micrographs)
- ImageJ macro export
- Hosted web demo (Streamlit Cloud)
