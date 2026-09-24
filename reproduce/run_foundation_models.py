#!/usr/bin/env python3
"""
Runs the foundation-model family (SAM 2, optionally Cellpose) on a set of
surface images with the same post-filter as the interface, and records
image porosity, pore count, prompts/masks and wall-clock time.

    python reproduce/run_foundation_models.py IMG [IMG ...] --sam-weights sam2_b.pt \
        [--sam-auto] [--cellpose] --out results/

Outputs <out>/foundation_models.csv and one mask PNG per image and method.
The seed detector for prompted SAM 2 is Sauvola with the interface defaults,
so 'SAM 2 (prompted)' can be read directly as 'Sauvola detections with
SAM 2 outlines'.
"""
import argparse
import csv
import os
import platform
import sys
import time

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from modules import filters, segmentation as seg, utils  # noqa: E402

GUI = dict(min_area=8, must_be_dark=True, dark_thresh_factor=0.95)


def post(mask, gray):
    final, kept = filters.filter_components(mask, gray, **GUI)
    m = filters.compute_metrics(final, kept)
    return final, round(m['porosity_pct'], 2), int(m['n_pores'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('images', nargs='+')
    ap.add_argument('--sam-weights', default='sam2_b.pt')
    ap.add_argument('--sam-auto', action='store_true', help='also run segment-everything mode')
    ap.add_argument('--cellpose', action='store_true')
    ap.add_argument('--skip-sam', action='store_true', help='run only Sauvola (+ Cellpose if requested)')
    ap.add_argument('--out', default='results')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rows = []
    for path in a.images:
        name = os.path.splitext(os.path.basename(path))[0]
        img = utils.load_image(path)
        runs = [('Sauvola (seed)', lambda: seg.segment_Sauvola(img) + (None, {}))]
        if not a.skip_sam:
            runs.append(('SAM 2 (prompted)', lambda: seg.segment_SAM2(img, a.sam_weights, mode='prompted', return_info=True)))
        if a.sam_auto:
            runs.append(('SAM 2 (auto)', lambda: seg.segment_SAM2(img, a.sam_weights, mode='auto', return_info=True)))
        if a.cellpose:
            runs.append(('Cellpose', lambda: seg.segment_CellPose(img) + ({},)))
        for method, fn in runs:
            t0 = time.perf_counter()
            out = fn()
            dt = time.perf_counter() - t0
            mask, gray, err = out[0], out[1], out[2]
            info = out[3] if len(out) > 3 and out[3] else {}
            if err or mask is None:
                rows.append(dict(image=name, method=method, porosity_pct='', pore_count='', time_s=round(dt, 1),
                                 n_prompts='', n_masks='', n_kept='', note=err))
                print(name, method, 'ERROR', err)
                continue
            final, por, n = post(mask, gray)
            Image.fromarray((final * 255).astype(np.uint8)).save(
                os.path.join(a.out, f"{name}_{method.split(' ')[0]}{'_auto' if 'auto' in method else ''}_mask.png"))
            rows.append(dict(image=name, method=method, porosity_pct=por, pore_count=n, time_s=round(dt, 1),
                             n_prompts=info.get('n_prompts', ''), n_masks=info.get('n_masks', ''),
                             n_kept=info.get('n_kept', ''), note=''))
            print(f"{name:8s} {method:18s} {por:7.2f} % {n:5d} pores {dt:7.1f} s {info}", flush=True)
    with open(os.path.join(a.out, 'foundation_models.csv'), 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    with open(os.path.join(a.out, 'foundation_models_env.txt'), 'w') as fh:
        import torch
        try:
            import ultralytics
        except ImportError:
            ultralytics = type('x', (), {'__version__': 'n/a'})
        fh.write(f"python {platform.python_version()} | {platform.platform()} | torch {torch.__version__} | "
                 f"ultralytics {ultralytics.__version__} | CPU only | weights {os.path.basename(a.sam_weights)}\n")


if __name__ == '__main__':
    main()
