"""
Yardımcı fonksiyonlar — görüntü I/O, overlay, color utility.
"""
import numpy as np
import cv2
from PIL import Image


def load_image(path_or_buffer):
    """Path veya BytesIO'dan RGB numpy array yükle."""
    if hasattr(path_or_buffer, 'read'):
        img = Image.open(path_or_buffer).convert('RGB')
        return np.array(img)
    else:
        img = cv2.imread(str(path_or_buffer))
        if img is None:
            raise IOError(f'Görüntü okunamadı: {path_or_buffer}')
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def make_overlay(img_rgb, mask, color=(0,255,80), alpha=0.55):
    """Mask'in olduğu pikselleri verilen renkle blend et."""
    out = img_rgb.copy()
    if mask.sum() == 0:
        return out
    color_arr = np.array(color, dtype=np.uint8)
    out[mask] = (out[mask].astype(np.float32) * (1-alpha) + color_arr * alpha).astype(np.uint8)
    return out


def make_outline_overlay(img_rgb, mask, color=(0,255,80), thickness=2):
    """Mask sınırlarını çiz (içini doldurma yerine)."""
    out = img_rgb.copy()
    mask_u8 = (mask * 255).astype(np.uint8)
    contours, _ = cv2.findContours(mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(out, contours, -1, color, thickness)
    return out


def hex_to_rgb(hex_str):
    h = hex_str.lstrip('#')
    return [int(h[i:i+2], 16) for i in (0,2,4)]


def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(*[int(c) for c in rgb])


def resize_for_display(img, max_dim=900):
    h, w = img.shape[:2]
    scale = max_dim / max(h, w)
    if scale < 1:
        return cv2.resize(img, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_AREA)
    return img


def pick_color_at(img_rgb, x, y, neighborhood=3):
    """Bir noktadaki ortalama RGB rengi al (küçük komşuluk ile)."""
    h, w = img_rgb.shape[:2]
    x0 = max(0, x-neighborhood); x1 = min(w, x+neighborhood+1)
    y0 = max(0, y-neighborhood); y1 = min(h, y+neighborhood+1)
    patch = img_rgb[y0:y1, x0:x1]
    return [int(patch[...,0].mean()), int(patch[...,1].mean()), int(patch[...,2].mean())]
