# -*- coding: utf-8 -*-
"""
Bilimsel Kolaj Olusturucu (Collage Builder)
============================================
Q1 dergi standardinda figur kolaji uretir.
Multi-format export: PNG, PDF, SVG (PNG-embed), TIFF.

Etiket pozisyon stratejileri:
- Inside: gorsel uzerinde, kontrastli banner
- Outside: SEM tarzi gorsel disinda beyaz alan (alt/ust/sol/sag)
- None: sadece gorsel

Standartlar:
- Elsevier tek-sutun: 8.5 cm width @ 300/600 DPI
- Springer: 8.4 cm / 17.4 cm
- ACS: 8.25 cm / 17.78 cm
"""
import io
import os
import base64
from datetime import datetime
import numpy as np
from PIL import Image, ImageDraw, ImageFont


# ============================================================
# FONT HELPER
# ============================================================

def _get_font(size, bold=False):
    """En iyi cross-platform font'u bul."""
    candidates_bold = [
        '/System/Library/Fonts/Helvetica.ttc',  # macOS
        '/System/Library/Fonts/Supplemental/Arial Bold.ttf',  # macOS
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',  # Linux
        'C:/Windows/Fonts/arialbd.ttf',  # Windows
    ]
    candidates_regular = [
        '/System/Library/Fonts/Helvetica.ttc',
        '/System/Library/Fonts/Supplemental/Arial.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        'C:/Windows/Fonts/arial.ttf',
    ]
    candidates = candidates_bold if bold else candidates_regular
    for path in candidates:
        try:
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _text_size(draw, text, font):
    """Pillow >=10 ile uyumlu metin boyut olcumu."""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


# ============================================================
# IMAGE LOADING
# ============================================================

def _load_image(source):
    """Path / BytesIO / PIL.Image kabul eder, RGB PIL.Image doner."""
    if isinstance(source, Image.Image):
        return source.convert('RGB')
    if hasattr(source, 'read'):
        source.seek(0)
        return Image.open(source).convert('RGB')
    if isinstance(source, (str, bytes, os.PathLike)):
        return Image.open(source).convert('RGB')
    raise ValueError(f'Unknown image source type: {type(source)}')


def _resize_to_cell(img, target_size, mode='cover'):
    """
    Hucre boyutuna sigdirma.
    mode='cover': aspect koruyarak kirpilarak doldur (default)
    mode='contain': aspect koruyarak icine sigdir (kenar bosluk olur)
    mode='stretch': dogrudan resize (aspect bozulur)
    """
    target_w, target_h = target_size
    if mode == 'stretch':
        return img.resize(target_size, Image.LANCZOS)
    
    src_w, src_h = img.size
    src_ratio = src_w / src_h
    target_ratio = target_w / target_h
    
    if mode == 'cover':
        if src_ratio > target_ratio:
            # source genis -> source yuksekligi target_h olacak sekilde resize, sonra kirp
            new_h = target_h
            new_w = int(src_w * target_h / src_h)
            resized = img.resize((new_w, new_h), Image.LANCZOS)
            left = (new_w - target_w) // 2
            return resized.crop((left, 0, left + target_w, target_h))
        else:
            new_w = target_w
            new_h = int(src_h * target_w / src_w)
            resized = img.resize((new_w, new_h), Image.LANCZOS)
            top = (new_h - target_h) // 2
            return resized.crop((0, top, target_w, top + target_h))
    else:  # contain
        ratio = min(target_w / src_w, target_h / src_h)
        new_w = int(src_w * ratio)
        new_h = int(src_h * ratio)
        resized = img.resize((new_w, new_h), Image.LANCZOS)
        canvas = Image.new('RGB', target_size, (255, 255, 255))
        offset = ((target_w - new_w) // 2, (target_h - new_h) // 2)
        canvas.paste(resized, offset)
        return canvas


# ============================================================
# LABEL RENDERING
# ============================================================

def _render_inside_label(cell_img, label_text, position='bottom_center',
                          bg_color=(220, 30, 30), text_color=(255, 255, 255),
                          font_size=14, padding=8, alpha=200):
    """
    Gorsel uzerine yarı-saydam banner etiket yerlestir.
    position: 'bottom_center' | 'bottom_left' | 'bottom_right' | 'top_center' | etc.
    """
    if not label_text:
        return cell_img
    
    img = cell_img.copy()
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = _get_font(font_size, bold=True)
    
    text_w, text_h = _text_size(draw, label_text, font)
    box_w = text_w + 2 * padding
    box_h = text_h + 2 * padding
    
    W, H = img.size
    if 'bottom' in position:
        y0 = H - box_h - 8
    elif 'top' in position:
        y0 = 8
    else:
        y0 = (H - box_h) // 2
    
    if 'left' in position:
        x0 = 8
    elif 'right' in position:
        x0 = W - box_w - 8
    else:  # center
        x0 = (W - box_w) // 2
    
    # Yari saydam arka plan
    draw.rounded_rectangle([x0, y0, x0 + box_w, y0 + box_h],
                            radius=4, fill=(*bg_color, alpha))
    draw.text((x0 + padding, y0 + padding), label_text, fill=text_color, font=font)
    
    img_rgba = img.convert('RGBA')
    composite = Image.alpha_composite(img_rgba, overlay)
    return composite.convert('RGB')


def _build_outside_cell(cell_img, label_text, position='bottom',
                         bg_color=(255, 255, 255), text_color=(0, 0, 0),
                         font_size=12, padding=10, strip_height=None):
    """
    Hucre dısında beyaz şerit + etiket (SEM tarzı).
    position: 'bottom' | 'top' | 'left' | 'right'
    """
    if not label_text:
        return cell_img
    
    W, H = cell_img.size
    font = _get_font(font_size, bold=False)
    
    # Olcum icin gecici draw
    dummy = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    text_w, text_h = _text_size(dummy, label_text, font)
    
    if position in ('bottom', 'top'):
        sh = strip_height or (text_h + 2 * padding)
        new_w, new_h = W, H + sh
        canvas = Image.new('RGB', (new_w, new_h), bg_color)
        draw = ImageDraw.Draw(canvas)
        if position == 'bottom':
            canvas.paste(cell_img, (0, 0))
            text_x = (W - text_w) // 2
            text_y = H + (sh - text_h) // 2
        else:  # top
            canvas.paste(cell_img, (0, sh))
            text_x = (W - text_w) // 2
            text_y = (sh - text_h) // 2
        draw.text((text_x, text_y), label_text, fill=text_color, font=font)
        return canvas
    
    else:  # left / right
        sw = strip_height or (text_w + 2 * padding)
        new_w, new_h = W + sw, H
        canvas = Image.new('RGB', (new_w, new_h), bg_color)
        draw = ImageDraw.Draw(canvas)
        if position == 'right':
            canvas.paste(cell_img, (0, 0))
            text_x = W + (sw - text_w) // 2
            text_y = (H - text_h) // 2
        else:  # left
            canvas.paste(cell_img, (sw, 0))
            text_x = (sw - text_w) // 2
            text_y = (H - text_h) // 2
        draw.text((text_x, text_y), label_text, fill=text_color, font=font)
        return canvas


# ============================================================
# MAIN COLLAGE BUILDER
# ============================================================

def build_collage(
    cells_2d,                       # 2D list: [[{image, label, ...}, ...], ...]
    cell_size=(400, 400),          # her hucre gorsel boyutu (px)
    resize_mode='cover',           # cover | contain | stretch
    label_position='inside_bottom_center',
    label_bg_color=(220, 30, 30),
    label_text_color=(255, 255, 255),
    label_font_size=14,
    label_padding=8,
    label_alpha=200,
    col_headers=None,              # list of strings or None
    row_labels=None,
    header_font_size=18,
    header_color=(0, 0, 0),
    header_height=None,            # auto if None
    row_label_width=None,
    cell_spacing=4,
    background_color=(255, 255, 255),
    footer_text=None,
    footer_font_size=10,
    footer_color=(120, 120, 120),
    footer_height=None,
):
    """
    Ana kolaj uretici.
    
    cells_2d: 2D list, [row][col] dict with keys:
              'image' (required): path / BytesIO / PIL.Image
              'label' (optional): str
    
    label_position: 'none' | 
                    'inside_bottom_center/left/right' | 'inside_top_center/left/right' |
                    'outside_bottom' | 'outside_top' | 'outside_left' | 'outside_right'
    
    Returns: PIL.Image (RGB)
    """
    if not cells_2d:
        raise ValueError('cells_2d empty')
    
    n_rows = len(cells_2d)
    n_cols = max(len(row) for row in cells_2d)
    
    cw, ch = cell_size
    
    # --- Hucreleri hazirla (resize + label) ---
    prepared_cells = []
    for r in range(n_rows):
        row_cells = []
        for c in range(n_cols):
            if c >= len(cells_2d[r]) or cells_2d[r][c] is None:
                # Bos hucre — beyaz placeholder
                empty = Image.new('RGB', (cw, ch), background_color)
                row_cells.append(empty)
                continue
            
            cell_dict = cells_2d[r][c]
            img = _load_image(cell_dict['image'])
            resized = _resize_to_cell(img, (cw, ch), mode=resize_mode)
            
            label = cell_dict.get('label', '')
            
            # Label rendering
            if label and label_position != 'none':
                if label_position.startswith('inside_'):
                    pos = label_position.replace('inside_', '')
                    resized = _render_inside_label(
                        resized, label, position=pos,
                        bg_color=label_bg_color,
                        text_color=label_text_color,
                        font_size=label_font_size,
                        padding=label_padding,
                        alpha=label_alpha,
                    )
                elif label_position.startswith('outside_'):
                    pos = label_position.replace('outside_', '')
                    resized = _build_outside_cell(
                        resized, label, position=pos,
                        bg_color=background_color,
                        text_color=header_color,
                        font_size=label_font_size,
                        padding=label_padding,
                    )
            
            row_cells.append(resized)
        prepared_cells.append(row_cells)
    
    # Tum hucreler ayni boyutta olmali (etiket sonrasi label outside ise farklilasir)
    # Her hucreyi en buyuk olcuye genislet
    max_cell_w = max(c.width for row in prepared_cells for c in row)
    max_cell_h = max(c.height for row in prepared_cells for c in row)
    
    normalized = []
    for row in prepared_cells:
        norm_row = []
        for c in row:
            if c.size != (max_cell_w, max_cell_h):
                canvas = Image.new('RGB', (max_cell_w, max_cell_h), background_color)
                offset = ((max_cell_w - c.width) // 2, (max_cell_h - c.height) // 2)
                canvas.paste(c, offset)
                norm_row.append(canvas)
            else:
                norm_row.append(c)
        normalized.append(norm_row)
    
    # --- Toplam boyut hesabi ---
    # Header satiri
    show_col_headers = col_headers is not None and any(col_headers)
    show_row_labels = row_labels is not None and any(row_labels)
    
    if show_col_headers and header_height is None:
        header_height = header_font_size * 2 + 20
    elif not show_col_headers:
        header_height = 0
    
    if show_row_labels and row_label_width is None:
        # En genis row label'a gore
        dummy = ImageDraw.Draw(Image.new('RGB', (1, 1)))
        font = _get_font(header_font_size, bold=True)
        max_w = max(_text_size(dummy, str(rl), font)[0] for rl in row_labels)
        row_label_width = max_w + 24
    elif not show_row_labels:
        row_label_width = 0
    
    if footer_text and footer_height is None:
        footer_height = footer_font_size * 2 + 16
    elif not footer_text:
        footer_height = 0
    
    total_w = row_label_width + n_cols * max_cell_w + (n_cols - 1) * cell_spacing
    total_h = header_height + n_rows * max_cell_h + (n_rows - 1) * cell_spacing + footer_height
    
    # --- Canvas olustur ---
    canvas = Image.new('RGB', (total_w, total_h), background_color)
    draw = ImageDraw.Draw(canvas)
    
    # Col headers
    if show_col_headers:
        font_h = _get_font(header_font_size, bold=True)
        for c in range(n_cols):
            if c >= len(col_headers) or not col_headers[c]:
                continue
            header_txt = str(col_headers[c])
            text_w, text_h = _text_size(draw, header_txt, font_h)
            x = row_label_width + c * (max_cell_w + cell_spacing) + (max_cell_w - text_w) // 2
            y = (header_height - text_h) // 2
            draw.text((x, y), header_txt, fill=header_color, font=font_h)
    
    # Row labels + cells
    font_r = _get_font(header_font_size, bold=True)
    for r in range(n_rows):
        y_top = header_height + r * (max_cell_h + cell_spacing)
        
        if show_row_labels and r < len(row_labels) and row_labels[r]:
            row_txt = str(row_labels[r])
            text_w, text_h = _text_size(draw, row_txt, font_r)
            tx = (row_label_width - text_w) // 2
            ty = y_top + (max_cell_h - text_h) // 2
            draw.text((tx, ty), row_txt, fill=header_color, font=font_r)
        
        for c in range(n_cols):
            x_left = row_label_width + c * (max_cell_w + cell_spacing)
            canvas.paste(normalized[r][c], (x_left, y_top))
    
    # Footer
    if footer_text:
        font_f = _get_font(footer_font_size, bold=False)
        text_w, text_h = _text_size(draw, footer_text, font_f)
        fx = (total_w - text_w) // 2
        fy = total_h - footer_height + (footer_height - text_h) // 2
        draw.text((fx, fy), footer_text, fill=footer_color, font=font_f)
    
    return canvas


# ============================================================
# EXPORT
# ============================================================

def export_collage(collage_img, format='PNG', dpi=300, target_width_cm=None):
    """
    Kolaj export.
    
    format: 'PNG' | 'PDF' | 'TIFF' | 'SVG'
    dpi: 72 | 300 | 600
    target_width_cm: Hedef genislik cm. None ise dogal pikseller.
    
    Returns: bytes
    """
    img = collage_img
    
    # Hedef DPI'ye gore resize
    if target_width_cm:
        target_px = int(target_width_cm / 2.54 * dpi)
        if img.width != target_px:
            ratio = target_px / img.width
            new_size = (target_px, int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
    
    buf = io.BytesIO()
    
    if format == 'PNG':
        img.save(buf, format='PNG', dpi=(dpi, dpi), optimize=True)
    elif format == 'TIFF':
        img.save(buf, format='TIFF', dpi=(dpi, dpi), compression='tiff_lzw')
    elif format == 'PDF':
        img.save(buf, format='PDF', dpi=(dpi, dpi), resolution=dpi)
    elif format == 'SVG':
        # PNG'yi base64'e cevirip SVG'ye gom
        png_buf = io.BytesIO()
        img.save(png_buf, format='PNG', dpi=(dpi, dpi), optimize=True)
        b64 = base64.b64encode(png_buf.getvalue()).decode('ascii')
        # SVG width/height inch cinsinden
        w_in = img.width / dpi
        h_in = img.height / dpi
        svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{w_in:.3f}in" height="{h_in:.3f}in" viewBox="0 0 {img.width} {img.height}">
<image href="data:image/png;base64,{b64}" width="{img.width}" height="{img.height}"/>
</svg>"""
        buf.write(svg.encode('utf-8'))
    else:
        raise ValueError(f'Unsupported format: {format}')
    
    return buf.getvalue()


# ============================================================
# AUTO CAPTION GENERATOR
# ============================================================

def auto_caption(n_rows, n_cols, col_headers=None, row_labels=None,
                  context='general', n_samples=None, stone=None, salt=None):
    """
    Otomatik figur captionu uretir (TR + EN).
    context: 'general' | 'pore_segmentation' | 'aging' | 'palette' | 'algorithm_comparison'
    """
    if context == 'aging':
        en = (f"Figure X. Pre- and post-aging surface comparison of {n_samples or n_rows} "
              f"{stone or 'travertine'} specimens"
              f"{f' subjected to {salt} crystallization' if salt else ''}. "
              f"Each row represents one specimen; columns show pre-treatment and "
              f"post-treatment images with overlay segmentation. "
              f"Numerical labels indicate ΔE-2000 color difference values "
              f"(Sharma et al. 2005) and algorithmic porosity (%).")
    elif context == 'algorithm_comparison':
        algos = ', '.join(col_headers[1:]) if col_headers and len(col_headers) > 1 else 'multiple algorithms'
        en = (f"Figure X. Comparative visualization of pore segmentation results across "
              f"{n_rows} {stone or 'travertine'} specimens using {algos}. "
              f"Each row represents one specimen; columns show the original surface "
              f"photograph followed by algorithm overlay outputs. "
              f"Numerical labels indicate algorithmic porosity (%) versus "
              f"experimental TS EN 1936 open porosity (Exp%).")
    elif context == 'pore_segmentation':
        en = (f"Figure X. Pore segmentation outputs for {n_rows} specimens. "
              f"Overlay color encodes detected pore regions. "
              f"Numerical labels indicate computed porosity (%).")
    elif context == 'palette':
        en = (f"Figure X. Color palette comparison across {n_rows*n_cols} samples. "
              f"Each cell shows dominant color extraction from surface imagery.")
    else:
        en = f"Figure X. Multi-panel image collage ({n_rows}×{n_cols} grid)."
    
    return {
        'en': en,
        'tr': en,  # TR translation can be added later
        'generated_at': datetime.now().isoformat(),
    }
