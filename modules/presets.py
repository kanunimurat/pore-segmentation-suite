"""
Kullanıcı parametre preset'leri — taş+algoritma bazlı kaydet/yükle.
"""
import os
import json
from datetime import datetime


PRESETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'presets')
os.makedirs(PRESETS_DIR, exist_ok=True)


def save_preset(name, stone_code, algorithm, params, metrics=None, notes=''):
    """Bir parametre seti'ni isimlendirerek kaydet."""
    preset = {
        'name': name,
        'stone_code': stone_code,
        'algorithm': algorithm,
        'params': params,
        'metrics': metrics,
        'notes': notes,
        'saved_at': datetime.now().isoformat(),
    }
    safe_name = name.replace(' ', '_').replace('/', '_')
    path = os.path.join(PRESETS_DIR, f'{stone_code}_{algorithm}_{safe_name}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(preset, f, ensure_ascii=False, indent=2)
    return path


def list_presets(stone_code=None):
    """Tüm preset'leri (veya belirli taşa ait olanları) listele."""
    if not os.path.exists(PRESETS_DIR):
        return []
    out = []
    for fn in sorted(os.listdir(PRESETS_DIR)):
        if not fn.endswith('.json'): continue
        if stone_code and not fn.startswith(stone_code + '_'): continue
        path = os.path.join(PRESETS_DIR, fn)
        try:
            with open(path, encoding='utf-8') as f:
                out.append(json.load(f))
        except: pass
    return out


def load_preset_by_name(stone_code, algorithm, name):
    safe_name = name.replace(' ', '_').replace('/', '_')
    path = os.path.join(PRESETS_DIR, f'{stone_code}_{algorithm}_{safe_name}.json')
    if not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as f:
        return json.load(f)
