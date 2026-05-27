"""
Palet yükleme/kaydetme — JSON tabanlı.
"""
import os
import json


PALETTE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'palettes')


def load_palette(stone_code):
    """JSON'dan palet yükle. Bulunamazsa None döner."""
    path = os.path.join(PALETTE_DIR, f'{stone_code}.json')
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_palette(stone_code, palette_data):
    """Paleti JSON'a kaydet."""
    path = os.path.join(PALETTE_DIR, f'{stone_code}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(palette_data, f, ensure_ascii=False, indent=2)
    return path


def list_palettes():
    """Mevcut tüm taş kodlarını listele."""
    if not os.path.exists(PALETTE_DIR):
        return []
    return sorted([f[:-5] for f in os.listdir(PALETTE_DIR) if f.endswith('.json')])


def palette_to_dict(palette_data, selected_indices=None):
    """Selected pore color indices'ten RGB listesini çıkar."""
    if selected_indices is None:
        selected_indices = palette_data.get('pore_candidate_indices', [0])
    pore_colors = [palette_data['colors'][i]['rgb'] for i in selected_indices 
                   if i < len(palette_data['colors'])]
    return pore_colors
