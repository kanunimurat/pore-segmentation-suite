"""
Yardımcı fonksiyonlar — görüntü I/O, overlay, color utility.
"""
import numpy as np
import cv2
from PIL import Image


SRGB_PROFILE = None
LAST_LOAD_INFO = {}


def _srgb_profile():
    global SRGB_PROFILE
    if SRGB_PROFILE is None:
        from PIL import ImageCms
        SRGB_PROFILE = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB'))
    return SRGB_PROFILE


def load_image(path_or_buffer, to_srgb=True):
    """Load an image as an 8-bit RGB numpy array.

    v1.3.1: colour-managed. If the file embeds an ICC profile that is not sRGB
    (e.g. macOS 'Generic RGB', Display P3, Adobe RGB), the pixels are converted
    to sRGB with the relative-colorimetric intent before any analysis, because
    every colour computation in the suite (CIELAB, CIEDE2000) assumes sRGB.
    Files without a profile are taken as sRGB, as before. EXIF orientation is
    applied. Details of the last call are kept in utils.LAST_LOAD_INFO.
    """
    import io
    from PIL import ImageCms, ImageOps
    try:
        img = Image.open(path_or_buffer)
    except Exception as exc:
        raise IOError(f'Görüntü okunamadı / cannot read image: {path_or_buffer}') from exc
    img = ImageOps.exif_transpose(img)
    icc = img.info.get('icc_profile')
    desc, converted = None, False
    if icc:
        try:
            src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
            desc = ImageCms.getProfileDescription(src).strip()
        except Exception:
            src, desc = None, 'unreadable ICC profile'
    rgb = img.convert('RGB')
    if to_srgb and icc and src is not None and 'srgb' not in (desc or '').lower():
        rgb = ImageCms.profileToProfile(rgb, src, _srgb_profile(),
                                        renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC,
                                        outputMode='RGB')
        converted = True
    LAST_LOAD_INFO.clear()
    LAST_LOAD_INFO.update(icc_profile=desc, converted_to_srgb=converted, dpi=img.info.get('dpi'),
                          size=rgb.size)
    return np.array(rgb)


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
