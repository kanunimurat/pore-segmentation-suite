# -*- coding: utf-8 -*-
"""
comparison.py — Comparison-collage engine (samples x methods x conditions).
================================================================================
Reproduces, *natively inside the software*, the kind of result-oriented
comparison collage used in the manuscript (e.g. before/after x [Original +
method overlays], with per-panel "Method: img% | Exp: ref%" banners in
method-specific colours).

Reuses the existing pipeline: segmentation.* -> filters.filter_components ->
filters.compute_metrics -> utils.make_overlay, then collage_builder.build_collage.
"""
import numpy as np
from PIL import Image

try:
    from . import segmentation as seg, filters, utils, collage_builder as cb
except ImportError:  # allow direct execution / sys.path import
    import segmentation as seg, filters, utils, collage_builder as cb


# ----------------------------------------------------------------------------
# Method registry: name -> segment fn + default kwargs + default banner colour
# (colours chosen to be distinct; user can override per call)
# ----------------------------------------------------------------------------
METHOD_REGISTRY = {
    'DoG':         dict(fn=seg.segment_DoG,        kwargs={},                       color=(40, 120, 255)),
    'MSER':        dict(fn=seg.segment_MSER,       kwargs={},                       color=(200, 40, 190)),
    'Sauvola':     dict(fn=seg.segment_Sauvola,    kwargs={},                       color=(0, 170, 90)),
    'Multi-Otsu':  dict(fn=seg.segment_MultiOtsu,  kwargs={},                       color=(150, 80, 200)),
    'Bottom-Hat':  dict(fn=seg.segment_BottomHat,  kwargs={},                       color=(230, 140, 0)),
    'Frangi':      dict(fn=seg.segment_Frangi,     kwargs={},                       color=(0, 150, 200)),
    'GMM':         dict(fn=seg.segment_GMM,        kwargs={},                       color=(200, 40, 150)),
}

def available_methods():
    """Method names usable without extra setup (no palette / no DL weights)."""
    return list(METHOD_REGISTRY.keys())

def method_color(name):
    return METHOD_REGISTRY.get(name, {}).get('color', (220, 30, 30))


# ----------------------------------------------------------------------------
def _as_rgb_array(src):
    """Accept path / BytesIO / PIL / ndarray -> uint8 RGB ndarray."""
    if isinstance(src, np.ndarray):
        return src
    if isinstance(src, Image.Image):
        return np.array(src.convert('RGB'))
    return utils.load_image(src)


def run_method(img_rgb, method_name, min_area=8, color=None, alpha=0.55,
               filter_params=None):
    """
    Run one segmentation method on an RGB image.
    Returns (overlay_pil, porosity_pct).
    """
    entry = METHOD_REGISTRY[method_name]
    mask, gray = entry['fn'](img_rgb, **entry.get('kwargs', {}))
    fp = dict(min_area=min_area)
    if filter_params:
        fp.update(filter_params)
    final_mask, kept = filters.filter_components(mask, gray, **fp)
    metrics = filters.compute_metrics(final_mask, kept)
    col = color if color is not None else entry['color']
    overlay = utils.make_overlay(img_rgb, final_mask, color=tuple(col), alpha=alpha)
    return Image.fromarray(np.asarray(overlay, dtype=np.uint8)), float(metrics['porosity_pct'])


# ----------------------------------------------------------------------------
def build_comparison_collage(
    samples,                       # list of dicts (see below)
    methods,                       # list of method names
    condition_keys=('before', 'after'),
    condition_labels=None,         # dict cond_key -> display label (e.g. {'before':'Before'})
    include_original=True,
    method_colors=None,            # dict method -> (r,g,b)  (overrides registry)
    cell_size=(440, 440),
    label_fmt='{m}: {img:.1f}% | Exp: {exp:.1f}%',
    label_fmt_noexp='{m}: {img:.1f}%',
    label_text_color=(255, 255, 255),
    label_font_size=15,
    label_position='inside_bottom_center',
    show_row_labels=True,
    row_label_vertical=True,
    header_font_size=18,
    cell_spacing=6,
    min_area=8,
    filter_params=None,
    progress_cb=None,              # optional callable(done, total)
):
    """
    samples: list of dicts, each:
        {
          'id': 'KT-A1',
          'conditions': {
              'before': {'image': <path/PIL/ndarray>, 'exp': 3.5},   # exp optional
              'after':  {'image': ..., 'exp': 3.7},
          }
        }
    methods: e.g. ['MSER', 'Multi-Otsu'] (each gets its own banner colour)
    Returns: PIL.Image collage.
    """
    if condition_labels is None:
        condition_labels = {k: k.capitalize() for k in condition_keys}
    if method_colors is None:
        method_colors = {}

    # column headers (flat): for each condition -> [Original] + methods
    col_headers = []
    for ck in condition_keys:
        clab = condition_labels.get(ck, ck.capitalize())
        if include_original:
            col_headers.append(f'{clab} (Original)')
        for m in methods:
            col_headers.append(f'{clab} ({m})')

    total = len(samples) * len(condition_keys) * len(methods)
    done = 0
    cells_2d = []
    row_labels = []
    for s in samples:
        row_labels.append(str(s.get('id', '')))
        row = []
        for ck in condition_keys:
            cond = s['conditions'][ck]
            img_rgb = _as_rgb_array(cond['image'])
            exp = cond.get('exp', None)
            if include_original:
                row.append({'image': Image.fromarray(np.asarray(img_rgb, np.uint8))})
            for m in methods:
                col = method_colors.get(m, method_color(m))
                overlay, por = run_method(img_rgb, m, min_area=min_area,
                                          color=col, filter_params=filter_params)
                if exp is not None:
                    lab = label_fmt.format(m=m, img=por, exp=float(exp))
                else:
                    lab = label_fmt_noexp.format(m=m, img=por)
                row.append({'image': overlay, 'label': lab,
                            'label_bg': tuple(col), 'label_tc': tuple(label_text_color),
                            'label_fs': label_font_size})
                done += 1
                if progress_cb:
                    progress_cb(done, total)
        cells_2d.append(row)

    collage = cb.build_collage(
        cells_2d,
        cell_size=cell_size,
        label_position=label_position,
        label_text_color=label_text_color,
        label_font_size=label_font_size,
        col_headers=col_headers,
        row_labels=row_labels if show_row_labels else None,
        row_label_vertical=row_label_vertical,
        header_font_size=header_font_size,
        cell_spacing=cell_spacing,
    )
    return collage
