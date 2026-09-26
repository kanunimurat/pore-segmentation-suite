#!/usr/bin/env python3
"""
Cut the specimen out of a flatbed scan without altering its pixels.

The specimen is found as the largest bright region against the dark
background (scanner lid open, specimen covered with black cloth). The crop is
the largest axis-aligned rectangle that lies entirely on the specimen, shrunk
by an optional inset (default 1 mm) so that chipped edges and the shadow line
are excluded. Pixels are copied bit-for-bit (no rotation, no resampling) and
written as lossless PNG.

Optionally (--pixel-mm) a second, resampled copy is written at a target pixel
size, e.g. 0.1277 mm to match the travertine images of the paper (300 dpi scan
reduced by 1.508); area-averaging (cv2.INTER_AREA) is used.

    python reproduce/crop_specimen.py SCAN [SCAN ...] --dpi 300 --inset-mm 1 \
        --pixel-mm 0.1277 --out cropped/

Writes <out>/<stem>.png (native), <out>/<stem>_0.128mm.png (optional) and
<out>/crop_log.csv (source SHA-256, crop box, specimen size, skew, pixel size).
"""
import argparse
import csv
import hashlib
import os

import cv2
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def specimen_mask(rgb, dark=60, white=250):
    g = rgb.astype(np.float32).mean(axis=2)
    m = ((g > dark) & (g < white)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    if n < 2:
        raise ValueError("no specimen found")
    k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    spec = lab == k
    # fill holes (dark pores inside the specimen belong to it)
    filled = spec.astype(np.uint8)
    cnts, _ = cv2.findContours(filled, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(filled, cnts, -1, 1, thickness=cv2.FILLED)
    return filled.astype(bool), max(cnts, key=cv2.contourArea)


def inner_rect(mask, frac=0.999):
    """Shrink the bounding box side by side until every border row/column is
    (almost) entirely specimen: the largest axis-aligned rectangle inside it."""
    ys, xs = np.where(mask)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    for _ in range(10000):
        top, bot = mask[y0, x0:x1 + 1].mean(), mask[y1, x0:x1 + 1].mean()
        lef, rig = mask[y0:y1 + 1, x0].mean(), mask[y0:y1 + 1, x1].mean()
        worst = min(top, bot, lef, rig)
        if worst >= frac:
            return y0, y1, x0, x1
        if worst == top: y0 += 1
        elif worst == bot: y1 -= 1
        elif worst == lef: x0 += 1
        else: x1 -= 1
    raise RuntimeError("inner rectangle did not converge")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scans", nargs="+")
    ap.add_argument("--dpi", type=float, default=None, help="scan resolution (default: read from file)")
    ap.add_argument("--inset-mm", type=float, default=1.0)
    ap.add_argument("--pixel-mm", type=float, default=None, help="also write a copy resampled to this pixel size")
    ap.add_argument("--out", default="cropped")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rows = []
    for path in a.scans:
        im = Image.open(path)
        dpi = a.dpi or float((im.info.get("dpi") or (0, 0))[0]) or None
        if not dpi:
            raise ValueError(f"{path}: resolution unknown, pass --dpi")
        rgb = np.asarray(im.convert("RGB"))
        mask, cnt = specimen_mask(rgb)
        (cx, cy), (w, h), ang = cv2.minAreaRect(cnt)
        skew = ang if abs(ang) < 45 else ang - 90 * np.sign(ang)
        y0, y1, x0, x1 = inner_rect(mask)
        ins = int(round(a.inset_mm / 25.4 * dpi))
        y0, y1, x0, x1 = y0 + ins, y1 - ins, x0 + ins, x1 - ins
        crop = rgb[y0:y1 + 1, x0:x1 + 1]
        stem = os.path.splitext(os.path.basename(path))[0]
        Image.fromarray(crop).save(os.path.join(a.out, f"{stem}.png"), dpi=(dpi, dpi))
        px = 25.4 / dpi
        row = dict(file=os.path.basename(path), sha256=sha256(path), dpi=dpi, pixel_mm=round(px, 5),
                   x0=int(x0), y0=int(y0), x1=int(x1), y1=int(y1), crop_w_px=crop.shape[1], crop_h_px=crop.shape[0],
                   crop_w_mm=round(crop.shape[1] * px, 1), crop_h_mm=round(crop.shape[0] * px, 1),
                   specimen_w_mm=round(max(w, h) * px, 1), specimen_h_mm=round(min(w, h) * px, 1),
                   skew_deg=round(float(skew), 2), inset_mm=a.inset_mm, resampled_pixel_mm="")
        if a.pixel_mm:
            f = px / a.pixel_mm
            small = cv2.resize(crop, (int(round(crop.shape[1] * f)), int(round(crop.shape[0] * f))),
                               interpolation=cv2.INTER_AREA)
            tag = f"{a.pixel_mm:.3f}mm"
            Image.fromarray(small).save(os.path.join(a.out, f"{stem}_{tag}.png"),
                                        dpi=(25.4 / a.pixel_mm, 25.4 / a.pixel_mm))
            row["resampled_pixel_mm"] = a.pixel_mm
        rows.append(row)
        print(f"{stem}: crop {crop.shape[1]}x{crop.shape[0]} px = {row['crop_w_mm']} x {row['crop_h_mm']} mm, "
              f"specimen {row['specimen_w_mm']} x {row['specimen_h_mm']} mm, skew {row['skew_deg']} deg")
        if abs(skew) > 1.0:
            print(f"  WARNING: specimen rotated {skew:.1f} deg; straighten it on the glass and rescan "
                  f"(the crop loses corners but pixels are not rotated)")
    with open(os.path.join(a.out, "crop_log.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)


if __name__ == "__main__":
    main()
