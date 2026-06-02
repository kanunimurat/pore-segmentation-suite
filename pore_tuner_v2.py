# -*- coding: utf-8 -*-
"""
Gözenek ve Renk Tespit Yazılımı
================================
Travertenler (ve benzer doğal taşlar) için interaktif gözenek tespiti.

Çalıştırma:
    streamlit run pore_tuner.py

Geliştirici notu: 
    Her algoritma (DoG, MSER, Sauvola, Color-Distance) için ayrı slider seti var.
    Yanlış-pozitif filtreler (shape + texture + intensity) tüm algoritmalara uygulanır.
    Per-stone renk paleti ile sınıflandırma destekli.
"""
import streamlit as st
import numpy as np
import cv2
import pandas as pd
import json
import os
from io import BytesIO
from PIL import Image
from datetime import datetime

from modules import segmentation, filters, utils, palettes, presets, color_science as cs, aging_analysis as aa, collage_builder as cb, comparison as comp, pore_size as psize
from modules.i18n import T, render_language_selector, init_language, translate_classification, translate_cs


# ============================================================
# TEMA-DUYARLI GRAFİK PALETİ
# Oğuz Ergin "Tantuni Endeksi" tasarım dili: sıcak turuncu ana vurgu,
# altın/kırmızı/yeşil anlamsal renkler, güçlü tipografi.
# Açık tema -> koyu metin + sıcak pastel; koyu tema -> açık metin + derin ton.
# ============================================================
def _detect_ui_theme():
    try:
        _t = st.context.theme.type
    except Exception:
        _t = None
    if _t not in ('light', 'dark'):
        try:
            _t = st.get_option('theme.base')
        except Exception:
            _t = None
    return _t if _t in ('light', 'dark') else 'light'


def _chart_pal(theme=None):
    theme = theme or _detect_ui_theme()
    if theme == 'dark':
        return dict(theme='dark', ink='#e8eef5', muted='#9aa7b4', grid='#2b3340',
                    axis='#c2ccd6', accent='#FF8C42', gold='#F4C04E', red='#FF6B6B',
                    green='#4FD17F', fill='#3a2f23', edge='#FF9F5A', dot_ring='#11161d',
                    res_shade='#5a6675', res_op='0.30',
                    fam={'Classical': '#5BA3F5', 'Blob/region': '#FF6B6B', 'Clustering': '#4FD17F'})
    return dict(theme='light', ink='#1f2d3a', muted='#5b6876', grid='#eceff3',
                axis='#334155', accent='#E8722C', gold='#C28A00', red='#D64545',
                green='#2E9E5B', fill='#FBE3CB', edge='#C25A18', dot_ring='#ffffff',
                res_shade='#b9c2cc', res_op='0.28',
                fam={'Classical': '#1f77b4', 'Blob/region': '#d62728', 'Clustering': '#2ca02c'})


def _inject_global_css():
    """Oğuz Ergin 'Tantuni Endeksi' görsel dili: turuncu vurgu, kart panelleri,
    güçlü tipografi. Tema (açık/koyu) otomatik algılanır."""
    pal = _chart_pal()
    acc = pal['accent']
    acc_d = '#C25A18' if pal['theme'] == 'light' else '#FF7A2B'
    soft = pal['fill']
    border = pal['grid']
    st.markdown(f"""
    <style>
    :root {{ --acc:{acc}; --acc-d:{acc_d}; }}
    html, body, .stApp, button, input, textarea, select {{
        font-family:'Inter','Segoe UI',system-ui,-apple-system,'Helvetica Neue',Arial,sans-serif; }}
    /* Başlıklar: turuncu sol vurgu (Oğuz tarzı bölüm başlığı) */
    .stApp h2, .stApp h3 {{
        border-left:4px solid var(--acc); padding-left:.6rem; letter-spacing:.2px; }}
    .stApp h1 {{ letter-spacing:.2px; }}
    /* Butonlar: sıcak turuncu dolgu */
    .stButton>button, .stDownloadButton>button, [data-testid="stFormSubmitButton"]>button {{
        background:var(--acc); color:#111 !important; border:0; border-radius:9px;
        font-weight:700; font-size:calc(1rem + 2pt) !important;
        box-shadow:0 1px 2px rgba(0,0,0,.10); transition:filter .15s ease; }}
    .stButton>button *, .stDownloadButton>button *, [data-testid="stFormSubmitButton"]>button * {{
        color:#111 !important; font-size:calc(1rem + 2pt) !important; }}
    .stButton>button:hover, .stDownloadButton>button:hover {{ filter:brightness(1.08); color:#111 !important; }}
    /* Mod bilgilendirme paneli metni +4pt (#3) */
    .st-key-mode_info_panel p, .st-key-mode_info_panel li,
    .st-key-mode_info_panel h2, .st-key-mode_info_panel h3,
    .st-key-mode_info_panel [data-testid="stMarkdownContainer"],
    .st-key-mode_info_panel [data-testid="stAlertContainer"],
    .st-key-mode_info_panel [data-testid="stAlert"] p {{
        font-size:calc(1rem + 4pt) !important; line-height:1.4 !important; }}
    .stButton>button:active {{ background:var(--acc-d); }}
    /* Metric değeri: turuncu vurgu */
    [data-testid="stMetricValue"] {{ color:var(--acc); font-weight:700; }}
    /* Expander: kart görünümü */
    [data-testid="stExpander"] details {{
        border:1px solid {border}; border-radius:12px; overflow:hidden; }}
    [data-testid="stExpander"] summary {{ font-weight:600; }}
    [data-testid="stExpander"] summary:hover {{ color:var(--acc); }}
    /* Sekmeler */
    .stTabs [aria-selected="true"] {{ color:var(--acc) !important; }}
    .stTabs [data-baseweb="tab-highlight"] {{ background:var(--acc) !important; }}
    /* Slider tutamacı */
    [data-testid="stSlider"] [role="slider"] {{ background:var(--acc) !important; }}
    /* Bağlantılar */
    .stApp a {{ color:var(--acc); }}
    /* Oğuz tarzı ışıldayan turuncu marka yazısı */
    @keyframes brandGlow {{
        0%, 100% {{ filter:drop-shadow(0 0 4px rgba(232,114,44,.45)) drop-shadow(0 0 9px rgba(232,114,44,.28)); }}
        50%      {{ filter:drop-shadow(0 0 9px rgba(255,140,66,.80)) drop-shadow(0 0 20px rgba(255,140,66,.50)); }}
    }}
    .brand-glow {{
        background:linear-gradient(180deg,#FFB36B 0%,#FF8C42 45%,#E8722C 100%);
        -webkit-background-clip:text; background-clip:text;
        -webkit-text-fill-color:transparent; color:#E8722C;
        font-weight:800 !important; letter-spacing:.4px;
        animation:brandGlow 2.6s ease-in-out infinite; }}
    @media (prefers-reduced-motion: reduce) {{
        .brand-glow {{ animation:none; filter:drop-shadow(0 0 7px rgba(232,114,44,.55)); }}
    }}
    </style>
    """, unsafe_allow_html=True)


# ============================================================
# SAYFA AYARLARI
# ============================================================
st.set_page_config(
    page_title='Pore Segmentation Suite | Gözenek Tespit',
    page_icon='🪨',
    layout='wide',
)

# Initialize language session state (must be before any T() call)
init_language()
_inject_global_css()  # Oğuz tarzı görsel kimlik (turuncu vurgu)

# Örnek (demo) görüntü yolu ve yükleyici (#3)
_SAMPLE_IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample_images', 'sample_travertine.png')

def _load_sample_image():
    if os.path.exists(_SAMPLE_IMG):
        st.session_state.image_rgb = utils.load_image(_SAMPLE_IMG)
        st.session_state.image_name = 'sample_travertine.png'
        return True
    return False



# JSON serialization helper for numpy types (Python 3.14 strict tip kontrolu)
class NumpyJSONEncoder(json.JSONEncoder):
    """numpy tiplerini Python native'lere dönüştürür."""
    def default(self, obj):
        import numpy as _np
        if isinstance(obj, _np.integer):
            return int(obj)
        if isinstance(obj, _np.floating):
            return float(obj)
        if isinstance(obj, _np.bool_):
            return bool(obj)
        if isinstance(obj, _np.ndarray):
            return obj.tolist()
        return super().default(obj)


def safe_json_dumps(obj, **kwargs):
    """numpy uyumlu json.dumps wrapper."""
    kwargs.setdefault('cls', NumpyJSONEncoder)
    kwargs.setdefault('ensure_ascii', False)
    return json.dumps(obj, **kwargs)

st.title(T('app_title'))
st.caption(T('app_caption'))


# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================
if 'image_rgb' not in st.session_state:
    st.session_state.image_rgb = None
if 'image_name' not in st.session_state:
    st.session_state.image_name = None
if 'palette_data' not in st.session_state:
    st.session_state.palette_data = None
if 'selected_pore_indices' not in st.session_state:
    st.session_state.selected_pore_indices = []
if 'custom_pore_colors' not in st.session_state:
    st.session_state.custom_pore_colors = []
if 'last_result' not in st.session_state:
    st.session_state.last_result = None


# ============================================================
# SIDEBAR — EXPANDER MİMARİSİ
# ============================================================
with st.sidebar:
    # ─── TOP BRANDING (üstte) ──────────────────────────────
    _brand_subtitle = 'v1.2'
    _brand_name = 'Pore Segmentation Suite' if st.session_state.get('lang', 'en') == 'en' else 'Gözenek & Renk Tespit'
    st.markdown(f"""
    <div style="text-align:center; padding:12px 4px; margin-bottom:8px;
                border-bottom:1px solid #444; border-radius:4px;">
        <div class="brand-glow" style="font-size:26px;">{_brand_name}</div>
        <div style="color:#888; font-size:20px; margin-top:4px;">{_brand_subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

    # ─── LANGUAGE SELECTOR (altta) (🇹🇷 / 🇬🇧) ───────────────
    render_language_selector()
    st.markdown('')  # spacer
    
    # =============================================================
    # 🎯 ÇALIŞMA MODU — Top-Level Mode Selector
    # =============================================================
    mode_options = {
        T('mode_pore'):    'pore',
        T('mode_palette'): 'palette',
        T('mode_aging'):   'aging',
        T('mode_collage'): 'collage',
    }
    # ─── Çalışma Modu görsel stili: +4pt yazı, 3 mm aralık, temaya özel renkler ───
    # Tema Streamlit'in kendi temasından algılanır (OS değil); açık=pastel, koyu=derin.
    try:
        _ui_theme = st.context.theme.type
    except Exception:
        _ui_theme = None
    if _ui_theme not in ('light', 'dark'):
        try:
            _ui_theme = st.get_option('theme.base')
        except Exception:
            _ui_theme = None
    _ui_theme = _ui_theme if _ui_theme in ('light', 'dark') else 'light'
    if _ui_theme == 'dark':
        _mc = ['#1e3a5f', '#1f3f2c', '#523a1c', '#3a2a52']
        _fg, _bd, _sh = '#eef2f8', 'rgba(255,255,255,0.14)', 'none'
    else:
        _mc = ['#dbe9fb', '#e2f3e1', '#fde9d3', '#ece1f6']
        _fg, _bd, _sh = '#1f2d3a', 'rgba(0,0,0,0.08)', '0 1px 2px rgba(0,0,0,0.06)'
    st.markdown(f"""
    <style>
    div.st-key-app_mode_selector div[role="radiogroup"]{{gap:0 !important;}}
    div.st-key-app_mode_selector div[role="radiogroup"] > label{{
        padding:11px 14px; margin-bottom:3mm; border-radius:11px;
        border:1px solid {_bd}; box-shadow:{_sh};}}
    div.st-key-app_mode_selector div[role="radiogroup"] > label:hover{{filter:brightness(0.97);}}
    div.st-key-app_mode_selector div[role="radiogroup"] > label p,
    div.st-key-app_mode_selector div[role="radiogroup"] > label div,
    div.st-key-app_mode_selector div[role="radiogroup"] > label{{
        font-size:calc(1rem + 4pt) !important; font-weight:600; line-height:1.25; color:{_fg} !important;}}
    div.st-key-app_mode_selector div[role="radiogroup"] > label:nth-of-type(1){{background:{_mc[0]};}}
    div.st-key-app_mode_selector div[role="radiogroup"] > label:nth-of-type(2){{background:{_mc[1]};}}
    div.st-key-app_mode_selector div[role="radiogroup"] > label:nth-of-type(3){{background:{_mc[2]};}}
    div.st-key-app_mode_selector div[role="radiogroup"] > label:nth-of-type(4){{background:{_mc[3]};}}
    div.st-key-app_mode_selector label[data-testid="stWidgetLabel"]{{
        width:100% !important; display:flex !important; justify-content:center !important;}}
    div.st-key-app_mode_selector label[data-testid="stWidgetLabel"] p,
    div.st-key-app_mode_selector label[data-testid="stWidgetLabel"] div{{
        font-size:calc(1rem + 5pt) !important; font-weight:700 !important;
        text-align:center !important; width:100% !important; color:{_fg} !important;}}
    </style>
    """, unsafe_allow_html=True)
    selected_mode = st.radio(
        '🎯 ' + T('select_mode'),
        list(mode_options.keys()),
        key='app_mode_selector',
        help=('Which analysis type? Switching mode opens the relevant sidebar and main panel. Data is preserved across modes.'
              if st.session_state.get('lang', 'en') == 'en'
              else 'Hangi tür analiz yapacaksın? Mod değiştirince ilgili sidebar ve ana panel açılır. Veriler tüm modlarda korunur.'))
    app_mode = mode_options[selected_mode]
    st.session_state['active_mode'] = app_mode
    
    st.markdown('---')
    
    # =============================================================
    # 📊 GÖZENEK ANALİZİ — sadece pore moduna aktif
    # =============================================================
    if app_mode == 'pore':
     with st.expander(T('analyze_start'), expanded=True):
        
        # ──────────── 1. GÖRÜNTÜ ────────────
        st.markdown(T('upload_image'))
        
        upload_mode = st.radio(T('source'), [T('src_upload_file'), T('src_from_folder')], 
                                 horizontal=True, label_visibility='collapsed')
        
        uploaded_file = None
        if upload_mode == T('src_upload_file'):
            uploaded_file = st.file_uploader(T('image_input_label'), 
                                              type=['jpg','jpeg','png','tif','tiff','bmp'],
                                              label_visibility='collapsed')
            if uploaded_file:
                st.session_state.image_rgb = utils.load_image(uploaded_file)
                st.session_state.image_name = uploaded_file.name
        else:
            folder = st.text_input(T('folder_path'), value=os.path.expanduser('~'))
            if folder and os.path.isdir(folder):
                imgs = sorted([f for f in os.listdir(folder) 
                              if f.lower().endswith(('.jpg','.jpeg','.png','.tif','.tiff','.bmp'))])
                if imgs:
                    pick = st.selectbox(T('pick_image'), imgs)
                    if pick:
                        full = os.path.join(folder, pick)
                        if st.button(T('load_btn'), use_container_width=True):
                            st.session_state.image_rgb = utils.load_image(full)
                            st.session_state.image_name = pick
                else:
                    st.warning(T('no_images_in_folder'))

        # Örnek (demo) görüntü — yüklemeden hızlı deneme (#3)
        if st.session_state.image_rgb is None:
            if st.button(T('demo_sample'), use_container_width=True, key='demo_btn_side'):
                if _load_sample_image():
                    st.rerun()
            st.caption(T('demo_caption'))

        st.markdown('---')
        
        # ──────────── 2. TAŞ & PALET ────────────
        st.markdown(T('stone_palette'))
        
        available_palettes = palettes.list_palettes()
        stone_options = available_palettes + [T('stone_custom_new')]
        selected_stone = st.selectbox(T('stone_code'), stone_options, key='stone_select',
                                       label_visibility='collapsed')
        
        if selected_stone != T('stone_custom_new') and (st.session_state.palette_data is None or 
                                                    st.session_state.palette_data.get('stone_code') != selected_stone):
            st.session_state.palette_data = palettes.load_palette(selected_stone)
            st.session_state.selected_pore_indices = list(st.session_state.palette_data.get('pore_candidate_indices', [0,1]))
        
        # Yeni palet hesaplama
        if st.session_state.image_rgb is not None:
            if st.button(T('compute_palette'), use_container_width=True):
                with st.spinner(T('computing')):
                    colors = segmentation.extract_palette_kmeans(st.session_state.image_rgb, n_clusters=7)
                    st.session_state.palette_data = {
                        'stone_code': selected_stone if selected_stone != T('stone_custom_new') else 'CUSTOM',
                        'stone_name': st.session_state.image_name or 'Custom',
                        'n_clusters': 7,
                        'colors': colors,
                        'source': 'K-means from current image',
                        'pore_candidate_indices': [0, 1],
                    }
                    st.session_state.selected_pore_indices = [0, 1]
                    st.success(T('palette_updated'))
        
        # Palet gösterimi + checkbox'lar
        if st.session_state.palette_data:
            st.caption(f'**{st.session_state.palette_data.get("stone_name", "")}** — {st.session_state.palette_data["n_clusters"]} ' + T('dominant_colors_label'))
            
            new_selected = []
            for i, c in enumerate(st.session_state.palette_data['colors']):
                cols = st.columns([0.5, 2, 3])
                with cols[0]:
                    checked = st.checkbox('', value=(i in st.session_state.selected_pore_indices), 
                                           key=f'pore_color_{i}', label_visibility='collapsed')
                    if checked: new_selected.append(i)
                with cols[1]:
                    st.markdown(f'<div style="background:{c["hex"]};width:40px;height:25px;border:1px solid #888;border-radius:4px"></div>', 
                                unsafe_allow_html=True)
                with cols[2]:
                    role = T('role_pore') if checked else (T('role_matrix') if c['brightness']>120 else '?')
                    st.caption(f'`{c["hex"]}` ({c["fraction_pct"]:.1f}%) {role}')
            st.session_state.selected_pore_indices = new_selected
        
        # Custom pore colors (görüntüden eklenmiş)
        if st.session_state.custom_pore_colors:
            st.caption(T('colors_from_image'))
            for i, rgb in enumerate(st.session_state.custom_pore_colors):
                hex_str = utils.rgb_to_hex(rgb)
                cols = st.columns([1,3,1])
                cols[0].markdown(f'<div style="background:{hex_str};width:30px;height:20px;border:1px solid #888"></div>', unsafe_allow_html=True)
                cols[1].caption(f'`{hex_str}` RGB={rgb}')
                if cols[2].button('❌', key=f'rm_custom_{i}'):
                    st.session_state.custom_pore_colors.pop(i)
                    st.rerun()
        
        st.markdown('---')
        
        # ──────────── 3. ALGORİTMA ────────────
        st.markdown(T('algorithm_section'))
        algo_categories = {
            T('family_classical_full'): [
                'Sauvola (Adaptive Threshold)',
                'Multi-Otsu (Auto Multi-level)',
                'Auto Threshold (Triangle/Yen/Otsu)',
            ],
            T('family_blob_full'): [
                'DoG (Difference of Gaussians)',
                'MSER (Extremal Regions)',
                'Bottom-Hat Morphology',
                'Frangi Vesselness',
                'Watershed (Marker-Controlled)',
            ],
            T('family_color_full'): [
                T('algo_color_distance'),
                'GMM (Gaussian Mixture)',
            ],
            T('family_hybrid_full'): [
                'DoG + Color Filter',
                'MSER + Color Filter',
            ],
            T('family_modern_full'): [
                'SAM 2 (Segment Anything, Meta 2024)',
                'CellPose 3 (Pretrained)',
            ],
        }
        category = st.selectbox(
            T('algorithm_method'),
            list(algo_categories.keys()),
            help=T('help_algo_family'))
        algo = st.selectbox(
            T('algorithm'),
            algo_categories[category],
            help=T('help_algo_specific'))
        
        params = {}
        
        # DoG
        if 'DoG' in algo and 'Color' not in algo or algo == 'DoG + Color Filter':
            st.caption(T('p_dog'))
            params['multiscale'] = st.checkbox(T('multiscale_3'), value=False)
            if not params['multiscale']:
                params['sigma1'] = st.slider(T('sigma_small'), 1, 10, 3)
                params['sigma2'] = st.slider(T('sigma_large'), 5, 30, 15)
            params['percentile'] = st.slider(T('percentile_low_more'), 80, 99, 95)
        
        # MSER
        if 'MSER' in algo:
            st.caption(T('p_mser'))
            params['delta'] = st.slider(T('delta_stability'), 1, 10, 4)
            params['min_area'] = st.slider('Min alan (px)', 4, 100, 10)
            params['max_area'] = st.slider('Max alan (px)', 500, 10000, 3000)
        
        # Sauvola
        if 'Sauvola' in algo:
            st.caption(T('p_sauvola'))
            params['window_size'] = st.slider(T('window_size'), 11, 151, 51, step=10)
            params['k'] = st.slider('k', 0.05, 0.5, 0.20, step=0.05)
        
        # Color Distance (& hibrit)
        if 'Color Distance' in algo or 'Color Filter' in algo:
            st.caption(T('p_color'))
            params['color_space'] = st.selectbox(T('color_space'), ['lab', 'rgb', 'hsv'])
            params['max_distance'] = st.slider(T('ps_max_color_dist'), 5, 80, 25)
        
        # Multi-Otsu
        if 'Multi-Otsu' in algo:
            st.caption(T('p_multiotsu'))
            params['n_classes'] = st.slider(T('n_classes'), 2, 6, 3, 
                                              help=T('ps_help_multiotsu'))
            params['dark_class_count'] = st.slider(T('darkest_classes_pore'), 1, 
                                                      params.get('n_classes',3)-1, 1)
        
        # Auto Threshold
        if 'Auto Threshold' in algo:
            st.caption(T('auto_thresh_caption'))
            params['method'] = st.selectbox(T('ps_method'), 
                                              ['triangle','yen','isodata','otsu','mean','minimum'],
                                              help=T('ps_help_autothresh'))
        
        # Bottom-Hat
        if 'Bottom-Hat' in algo:
            st.caption(T('p_bottomhat'))
            params['kernel_size'] = st.slider(T('ps_kernel_size'), 5, 81, 21, step=2)
            params['percentile'] = st.slider(T('percentile_high_less'), 80, 99, 90)
        
        # Frangi
        if 'Frangi' in algo:
            st.caption(T('frangi_caption'))
            params['sigma_min'] = st.slider('σ_min', 1, 5, 1)
            params['sigma_max'] = st.slider('σ_max', 4, 20, 8)
            params['step'] = st.slider(T('sigma_step'), 1, 4, 2)
            params['dark'] = st.checkbox(T('dark_ridges'), value=True)
            params['percentile'] = st.slider(T('ps_response_pct'), 80, 99, 90)
        
        # GMM
        if 'GMM' in algo:
            st.caption(T('ps_gmm_caption'))
            params['n_components'] = st.slider(T('ps_n_components'), 2, 7, 3)
            params['dark_component_count'] = st.slider(T('ps_dark_components'), 1, 
                                                          params.get('n_components',3)-1, 1)
        
        # Watershed
        if 'Watershed' in algo:
            st.caption(T('p_watershed'))
            params['min_distance'] = st.slider(T('ps_min_dist'), 5, 50, 10,
                                                  help=T('ps_help_mindist'))
            params['base_threshold'] = st.selectbox(T('ps_base_thresh'), ['otsu','triangle','multiotsu'])
        
        # SAM 2
        if 'SAM 2' in algo:
            sam_available = segmentation._check_sam2()
            if sam_available:
                st.caption('🚀 **SAM 2 (Meta 2024)** — zero-shot foundation model')
                params['model_name'] = st.selectbox(T('ps_model_size'), 
                                                      [T('ps_sam_t'), 
                                                       'sam2_s.pt (46MB)',
                                                       T('ps_sam_b'),
                                                       T('ps_sam_l')])
                params['model_name'] = params['model_name'].split(' ')[0]
                params['mode'] = st.selectbox(T('collage_mode'), ['auto','point'])
                st.info(T('ps_sam_download'))
            else:
                st.error(T('ps_sam_not_installed'))
                st.code('pip install ultralytics', language='bash')
                st.caption(T('ps_restart_after_install'))
        
        # CellPose
        if 'CellPose' in algo:
            cp_available = segmentation._check_cellpose()
            if cp_available:
                st.caption('🚀 **CellPose 3** — pretrained generalist segmenter')
                params['model_type'] = st.selectbox('Model', ['cyto3','cyto2','nuclei'])
                params['diameter'] = st.slider(T('ps_obj_diameter'), 0, 100, 0)
                if params['diameter'] == 0: params['diameter'] = None
                params['flow_threshold'] = st.slider('Flow threshold', 0.0, 1.0, 0.4, step=0.05)
                params['cellprob_threshold'] = st.slider('Cell probability threshold', -6.0, 6.0, 0.0, step=0.5)
            else:
                st.error(T('ps_cellpose_not_installed'))
                st.code('pip install cellpose', language='bash')
                st.caption(T('ps_restart_after_install'))
        
        st.markdown('---')
        
        # ──────────── 4. YANLIŞ-POZİTİF FİLTRELERİ ────────────
        st.markdown(T('filters_section'))
        f_params = {}
        f_params['min_area'] = st.slider(T('ps_min_pore_area'), 1, 200, 8)
        f_params['use_max_eccentricity'] = st.checkbox(T('ps_ecc_filter'), value=False)
        if f_params['use_max_eccentricity']:
            f_params['max_eccentricity'] = st.slider(T('ps_max_ecc'), 0.5, 1.0, 0.92, step=0.01)
        f_params['use_min_solidity'] = st.checkbox(T('ps_sol_filter'), value=False)
        if f_params['use_min_solidity']:
            f_params['min_solidity'] = st.slider(T('ps_min_sol'), 0.0, 1.0, 0.55, step=0.05)
        f_params['use_max_interior_std'] = st.checkbox(T('ps_texture_filter'), value=False)
        if f_params['use_max_interior_std']:
            f_params['max_interior_std'] = st.slider(T('ps_max_interior_std'), 5, 60, 25)
        f_params['must_be_dark'] = st.checkbox(T('must_be_dark'), value=True)
        if f_params['must_be_dark']:
            f_params['dark_thresh_factor'] = st.slider(T('ps_dark_thresh_factor'), 0.5, 1.0, 0.95, step=0.05)
        
        st.markdown('---')
        
        # ──────────── 5. PRESET ────────────
        st.markdown('##### ' + T('ps_preset_save_hdr'))
        preset_name = st.text_input(T('ps_preset_name'), value='preset_1')
        preset_notes = st.text_area(T('ps_notes'), value='', height=60)
        if st.button(T('save_params'), use_container_width=True):
            all_params = {'algorithm': algo, 'algo_params': params, 'filter_params': f_params,
                          'pore_color_indices': st.session_state.selected_pore_indices,
                          'custom_pore_colors': st.session_state.custom_pore_colors}
            metrics = st.session_state.last_result['metrics'] if st.session_state.last_result else None
            path = presets.save_preset(preset_name, selected_stone, algo.split(' ')[0], 
                                        all_params, metrics=metrics, notes=preset_notes)
            st.success(f'{T("ps_saved")}: {os.path.basename(path)}')
    
    # =============================================================
    # 🎨 RENK PALETİ — sadece palette moduna aktif
    # =============================================================
    if app_mode == 'palette':
     with st.expander(T('cp_expander_title'), expanded=True):
        st.caption(T('cp_intro'))
        
        # Görüntü Kaynağı
        st.markdown('##### ' + T('cp_source_img'))
        pal_source = st.radio(T('source'), 
                                [T('cp_use_loaded'), T('cp_upload_new')],
                                key='palette_source', horizontal=False)
        
        pal_image = None
        if pal_source == T('cp_use_loaded'):
            if st.session_state.image_rgb is not None:
                pal_image = st.session_state.image_rgb
                st.caption(f'✓ {T("cp_active_img")}: **{st.session_state.image_name}**')
            else:
                st.warning(T('cp_warn_load_first'))
        else:
            pal_upload = st.file_uploader(T('cp_image_file'), 
                                            type=['jpg','jpeg','png','tif','tiff','bmp'],
                                            key='palette_upload')
            if pal_upload:
                pal_image = utils.load_image(pal_upload)
                st.session_state.palette_source_name = pal_upload.name
        
        st.markdown('---')
        
        # Algoritma Ayarları
        st.markdown('##### ⚙️ Algoritma')
        pal_algo = st.selectbox(
            T('clustering_algo'),
            [T('cp_algo_kmeans'), 
             T('cp_algo_minibatch'), 
             T('cp_algo_gmm'),
             T('cp_algo_meanshift'),
             T('cp_algo_mediancut')],
            help=T('cp_help_algo'))
        algo_map = {
            T('cp_algo_kmeans'): 'kmeans',
            T('cp_algo_minibatch'): 'minibatch_kmeans',
            T('cp_algo_gmm'): 'gmm',
            T('cp_algo_meanshift'): 'meanshift',
            T('cp_algo_mediancut'): 'median_cut',
        }
        pal_algo_id = algo_map[pal_algo]
        
        if pal_algo_id != 'meanshift':
            pal_n = st.slider(T('n_colors'), 3, 15, 7, 
                                help=T('cp_help_ncolors'))
        else:
            pal_n = None
        
        pal_space = st.selectbox(
            T('color_space'),
            [T('cp_space_lab'), 'RGB', 'HSV'],
            help=T('cp_help_space'))
        space_map = {
            T('cp_space_lab'): 'lab',
            'RGB': 'rgb',
            'HSV': 'hsv',
        }
        pal_space_id = space_map[pal_space]
        
        pal_sample = st.select_slider(
            T('cp_sample_size'),
            options=[5000, 10000, 30000, 50000, 100000, T('cp_all')],
            value=30000,
            help=T('cp_help_sample'))
        pal_sample_n = pal_image.shape[0]*pal_image.shape[1] if pal_sample == T('cp_all') and pal_image is not None else (pal_sample if pal_sample != T('cp_all') else 50000)
        
        # Hesapla Butonu
        if pal_image is not None:
            if st.button(T('cp_compute_btn'), use_container_width=True, type='primary'):
                with st.spinner(T('computing')):
                    try:
                        result = segmentation.extract_palette(
                            pal_image,
                            algorithm=pal_algo_id,
                            n_clusters=pal_n or 7,
                            color_space=pal_space_id,
                            sample_size=pal_sample_n)
                        st.session_state.computed_palette = result
                        st.session_state.computed_palette_meta = {
                            'algorithm': pal_algo,
                            'color_space': pal_space,
                            'n_clusters': len(result),
                            'sample_size': pal_sample,
                            'source_image': getattr(st.session_state, 'palette_source_name', st.session_state.image_name or 'unknown'),
                        }
                        st.success(f'✓ {len(result)} ' + T('cp_colors_extracted'))
                    except Exception as e:
                        st.error(f'{T("err_generic")}: {e}')
        else:
            st.info(T('cp_info_load'))
        
        # Kompakt Sonuç
        if 'computed_palette' in st.session_state and st.session_state.get('computed_palette'):
            st.markdown('---')
            st.markdown('##### ' + T('cp_extracted_palette'))
            
            for i, c in enumerate(st.session_state.computed_palette):
                cols = st.columns([0.5, 1.5, 3, 1])
                cols[0].markdown(f'**{i+1}**')
                cols[1].markdown(f'<div style="background:{c["hex"]};width:50px;height:25px;border:1px solid #888;border-radius:4px"></div>', 
                                  unsafe_allow_html=True)
                cols[2].caption(f'`{c["hex"]}` (RGB {tuple(c["rgb"])})')
                cols[3].caption(f'{c["fraction_pct"]:.1f}%')
            
            st.caption(T('cp_detail_hint'))
            
            # Aksiyon Butonları
            st.markdown('---')
            ac1, ac2 = st.columns(2)
            with ac1:
                pal_save_code = st.text_input(T('cp_stone_code_opt'), value='CUSTOM', 
                                                 help=T('cp_help_save_code'))
                if st.button(T('cp_json_save'), use_container_width=True):
                    palette_data = {
                        'stone_code': pal_save_code,
                        'stone_name': st.session_state.computed_palette_meta.get('source_image', 'Custom'),
                        'n_clusters': len(st.session_state.computed_palette),
                        'colors': st.session_state.computed_palette,
                        'source': f"computed: {st.session_state.computed_palette_meta.get('algorithm','?')} in {st.session_state.computed_palette_meta.get('color_space','?')}",
                        'pore_candidate_indices': [0, 1] if len(st.session_state.computed_palette) >= 2 else [0],
                    }
                    saved_path = palettes.save_palette(pal_save_code, palette_data)
                    st.success(f'✓ {T("ps_saved")}: {os.path.basename(saved_path)}')
            with ac2:
                if st.button(T('cp_make_active'), use_container_width=True,
                              help=T('cp_help_make_active')):
                    st.session_state.palette_data = {
                        'stone_code': 'COMPUTED',
                        'stone_name': st.session_state.computed_palette_meta.get('source_image', 'Custom'),
                        'n_clusters': len(st.session_state.computed_palette),
                        'colors': st.session_state.computed_palette,
                        'source': 'live computed',
                        'pore_candidate_indices': [0, 1] if len(st.session_state.computed_palette) >= 2 else [0],
                    }
                    st.session_state.selected_pore_indices = [0, 1]
                    st.success(T('cp_activated'))
                    st.rerun()
    
        # =============================================================
    # 🔄 YAŞLANDIRMA ANALİZİ — sadece aging moduna aktif
    # =============================================================
    if app_mode == 'aging':
     with st.expander(T('aging_sidebar_title'), expanded=True):
        st.caption(T('ag_intro'))
        
        # ─── Mod Seçici ───
        aging_mode = st.radio(
            T('aging_compare_mode'),
            [T('aging_mode_single'), T('aging_mode_multi')],
            key='aging_mode', horizontal=False)
        
        st.markdown('---')
        st.markdown(T('pre_images_section'))
        pre_files = st.file_uploader(
            'Pre-test', accept_multiple_files=True,
            type=['jpg','jpeg','png','tif','tiff','bmp'],
            key='aging_pre_files', label_visibility='collapsed')
        if pre_files:
            st.caption(f'✓ {len(pre_files)} ' + T('ag_pretest_imgs'))
        
        st.markdown(T('post_images_section'))
        post_files = st.file_uploader(
            'Post-test', accept_multiple_files=True,
            type=['jpg','jpeg','png','tif','tiff','bmp'],
            key='aging_post_files', label_visibility='collapsed')
        if post_files:
            st.caption(f'✓ {len(post_files)} ' + T('ag_posttest_imgs'))
        
        # Eşitlik kontrolü
        n_pre = len(pre_files) if pre_files else 0
        n_post = len(post_files) if post_files else 0
        if n_pre and n_post:
            if n_pre != n_post:
                st.error(f'⚠️ ' + T('ag_equal_required') + f': {n_pre} pre vs {n_post} post')
            else:
                st.success(T('pairs_ready_template').format(npre=n_pre, npost=n_post, npairs=n_pre))
        
        # Mode tutarlılık
        if aging_mode.startswith('🪞') and (n_pre > 1 or n_post > 1):
            st.warning(T('single_mode_warn'))
        
        st.markdown('---')
        
        # ─── Eşleştirme Stratejisi ───
        st.markdown(T('pair_strategy_section'))
        pair_strategy = st.radio(
            T('pair_strategy_label'),
            [T('pair_opt_alpha'), T('pair_opt_order'), T('pair_opt_manual')],
            key='aging_pair_strategy', label_visibility='collapsed')
        
        # Manuel eşleştirme tablosu (eğer seçilmişse)
        manual_pairs = None
        if pair_strategy.startswith('✋') and n_pre and n_post and n_pre == n_post:
            st.caption(T('pair_manual_caption'))
            manual_pairs = []
            post_names = [p.name for p in post_files]
            for i, pre_f in enumerate(pre_files):
                selected = st.selectbox(
                    f'**{pre_f.name}** ' + T('pair_manual_match_prefix') + ':', post_names,
                    index=i if i < len(post_names) else 0,
                    key=f'aging_manual_{i}')
                post_idx = post_names.index(selected)
                manual_pairs.append((i, post_idx))
        
        st.markdown('---')
        
        # ─── Analiz Parametreleri ───
        st.markdown(T('analysis_params'))
        delta_e_method = st.selectbox(
            T('dE_metric_label'),
            [T('dE_2000_opt'), T('dE_94_opt'), T('dE_76_opt')],
            key='aging_de_method')
        de_method_id = '2000' if '2000' in delta_e_method else ('94' if '94' in delta_e_method else '76')
        
        analysis_depth = st.radio(
            T('analysis_depth_label'),
            [T('depth_standard'), T('depth_detailed')],
            key='aging_depth', label_visibility='collapsed')
        
        sample_px = st.select_slider(
            T('pixel_sample_size'),
            options=[5000, 10000, 20000, 50000, 100000],
            value=20000, key='aging_sample_size')
        
        # ─── Bilgilendirme ───
        if n_pre and n_post and n_pre == n_post:
            est_time = n_pre * 1.5  # ~1.5 sn/pair (CPU)
            st.info(T('estimated_time_template').format(secs=est_time, n=n_pre))
        
        # ─── Run Button ───
        if n_pre > 0 and n_post > 0 and n_pre == n_post:
            if st.button(T('ag_run_btn'), use_container_width=True, type='primary', key='aging_run'):
                with st.spinner(f'{n_pre} ' + T('ag_comparing')):
                    # Pairing
                    pre_buffers = list(pre_files)
                    post_buffers = list(post_files)
                    if pair_strategy.startswith('🔤'):
                        pairs = aa.pair_alphabetic(pre_buffers, post_buffers)
                    elif pair_strategy.startswith('✋'):
                        if manual_pairs is None:
                            pairs = aa.pair_upload_order(pre_buffers, post_buffers)
                        else:
                            pairs = aa.pair_manual(pre_buffers, post_buffers, manual_pairs)
                    else:
                        pairs = aa.pair_upload_order(pre_buffers, post_buffers)
                    
                    # Her çift için analiz
                    pair_results = []
                    progress = st.progress(0)
                    for i, (pre_f, post_f) in enumerate(pairs):
                        try:
                            pre_f.seek(0); post_f.seek(0)
                            img_pre = utils.load_image(pre_f)
                            img_post = utils.load_image(post_f)
                            sample_name = pre_f.name.rsplit('.',1)[0]
                            result = aa.compute_pair_color_change(
                                img_pre, img_post,
                                delta_e_method=de_method_id,
                                sample_size=sample_px,
                                sample_name=sample_name)
                            result['pre_file'] = pre_f.name
                            result['post_file'] = post_f.name
                            pair_results.append(result)
                        except Exception as e:
                            st.warning(f'{pre_f.name} ' + T('ag_processing_error') + f': {e}')
                        progress.progress((i+1)/len(pairs))
                    
                    # Aggregate + statistics
                    if pair_results:
                        st.session_state.aging_results = {
                            'pairs': pair_results,
                            'aggregate': aa.aggregate_pairs(pair_results),
                            'stat_test_dE': aa.statistical_test_paired(pair_results, variable='delta_e'),
                            'stat_test_L': aa.statistical_test_paired(pair_results, variable='delta_L'),
                            'stat_test_a': aa.statistical_test_paired(pair_results, variable='delta_a'),
                            'stat_test_b': aa.statistical_test_paired(pair_results, variable='delta_b'),
                            'depth': analysis_depth,
                            'method': delta_e_method,
                        }
                        st.success(f'✓ {len(pair_results)} ' + T('ag_analyzed'))
        else:
            st.info(T('ag_info_equal'))
    
        # =============================================================
    # 🖼️ KOLAJ OLUŞTURUCU — sadece collage moduna aktif
    # =============================================================
    if app_mode == 'collage':
     with st.expander(T('collage_mode_title'), expanded=True):
        st.caption(T('cb_intro'))
        
        # Mod seçimi
        st.markdown('##### 📋 Kolaj Modu')
        collage_mode = st.radio(T('collage_mode'), 
            [T('cb_mode_manual'), 
             T('cb_mode_quick'),
             T('cb_mode_template')],
            key='collage_mode', label_visibility='collapsed')
        
        st.markdown('---')
        
        # Grid boyutu
        st.markdown('##### ' + T('cb_grid_size'))
        gc1, gc2 = st.columns(2)
        n_rows = gc1.number_input(T('rows'), 1, 20, 3, key='collage_rows')
        n_cols = gc2.number_input(T('cols'), 1, 12, 2, key='collage_cols')
        
        # Görüntü yükleme
        st.markdown('---')
        st.markdown('##### ' + T('cb_images_hdr'))
        if collage_mode.startswith('🅰️'):
            bulk_imgs = st.file_uploader(
                T('cb_bulk_upload'),
                accept_multiple_files=True,
                type=['jpg','jpeg','png','tif','tiff','bmp'],
                key='collage_bulk_upload')
            if bulk_imgs:
                st.caption(f'✓ {len(bulk_imgs)} ' + T('cb_images_word') + f' ({n_rows*n_cols} ' + T('cb_cells_word') + ')')
                if len(bulk_imgs) != n_rows * n_cols:
                    st.warning(f'⚠️ {n_rows}×{n_cols}={n_rows*n_cols} ' + T('cb_cells_word') + f', {len(bulk_imgs)} ' + T('cb_uploaded_word'))
        elif collage_mode.startswith('🅱️'):
            if 'aging_results' in st.session_state and st.session_state.aging_results:
                ar = st.session_state.aging_results
                st.success(f'✓ ' + T('cb_aging_ready') + f': {len(ar["pairs"])} ' + T('cb_pairs_word'))
                st.caption(T('cb_grid_auto'))
            else:
                st.warning(T('cb_warn_run_aging'))
        else:  # Template
            template = st.selectbox(T('cb_template_label'),
                [T('cb_tpl_algo'),
                 T('cb_tpl_aging'),
                 T('cb_tpl_matrix'),
                 'Time series (cycle 0/5/10/15)'],
                key='collage_template')
            st.caption(T('cb_tpl_hint'))
            bulk_imgs = st.file_uploader(
                T('cb_images_label'),
                accept_multiple_files=True,
                type=['jpg','jpeg','png','tif','tiff','bmp'],
                key='collage_template_upload')
        
        st.markdown('---')
        
        # Etiket içeriği — multi-select (hepsi default seçili)
        st.markdown('##### ' + T('cb_label_content'))
        st.caption(T('cb_label_which'))
        label_opts = st.multiselect(T('cb_metrics'),
            ['Sample ID', T('cb_opt_algo_pct'), T('cb_opt_exp_pct'), 'ΔE-2000', T('cb_opt_pore_count'), 'Mean color hex', 'Custom text'],
            default=['Sample ID', T('cb_opt_algo_pct'), T('cb_opt_exp_pct')],
            key='collage_label_opts')
        
        label_format = st.text_input(
            T('cb_label_fmt'),
            value='Alg:{alg:.1f}% | Exp:{exp:.1f}%',
            key='collage_label_fmt',
            help='Python format: {alg}, {exp}, {de}, {pore_n}, {hex}, {sample_id}, {custom}')
        
        st.markdown('---')
        
        # Etiket pozisyonu
        st.markdown('##### ' + T('cb_label_pos_hdr'))
        label_pos = st.selectbox(T('cb_position'),
            ['inside_bottom_center',
             'inside_bottom_left', 'inside_bottom_right',
             'inside_top_center', 'inside_top_left', 'inside_top_right',
             T('cb_pos_outside_bottom'),
             T('cb_pos_outside_top'),
             T('cb_pos_outside_left'),
             T('cb_pos_outside_right'),
             T('cb_pos_none')],
            key='collage_label_pos',
            help=T('cb_help_pos'))
        # Position string clean
        label_pos_clean = label_pos.split(' ')[0]
        
        # Stil
        st.markdown('---')
        st.markdown(T('overlay_style'))
        sc1, sc2 = st.columns(2)
        label_bg = sc1.color_picker(T('cb_label_bg'), '#dc1e1e', key='collage_lbl_bg')
        label_tc = sc2.color_picker(T('cb_label_tc'), '#ffffff', key='collage_lbl_tc')
        # Yazı boyutu — auto-scale veya manuel preset
        font_mode = st.selectbox(
            T('cb_font_size_label'),
            [T('cb_font_auto'),
             T('cb_font_small'),
             T('cb_font_medium'),
             T('cb_font_large'),
             T('cb_font_custom')],
            key='collage_font_mode',
            help=T('cb_help_font'))
        if font_mode.startswith('⚙️'):
            font_sz = st.slider(T('cb_font_px'), 8, 96, 20, key='collage_font_sz_manual')
        else:
            font_sz = None  # auto hesap render zamani
        cell_spc = st.slider(T('cb_cell_spacing'), 0, 30, 6, key='collage_spc')
        
        # ─── HÜCRE BOYUTU (çözünürlük) ───
        st.markdown('---')
        st.markdown('##### ' + T('cb_cell_res_hdr'))
        auto_cell = st.checkbox(
            T('cb_autofit'), 
            value=True, key='collage_auto_cell',
            help=T('cb_help_autofit'))
        if not auto_cell:
            cell_size_px = st.slider(
                T('cb_cell_size'), 200, 1200, 600, step=50,
                key='collage_cell_size_manual',
                help=T('cb_help_cellsize'))
        else:
            cell_size_px = None  # auto
        
        # Sütun başlıkları
        st.markdown('---')
        st.markdown('##### ' + T('cb_headers_hdr'))
        col_headers_str = st.text_input(
            T('cb_col_headers').format(n=n_cols),
            value=','.join([f'Col{i+1}' for i in range(n_cols)]),
            key='collage_col_headers')
        row_labels_str = st.text_input(
            T('cb_row_labels').format(n=n_rows),
            value='',
            key='collage_row_labels')
        
        # Çıktı boyut + format
        st.markdown('---')
        st.markdown('##### ' + T('cb_output_size_hdr'))
        journal_preset = st.selectbox(T('cb_journal_preset'),
            ['Custom',
             T('jp_elsevier_single'),
             T('jp_elsevier_double'),
             T('jp_springer_single'),
             T('jp_springer_double'),
             T('jp_acs_single'),
             T('jp_acs_double')],
            key='collage_journal')
        
        width_cm_map = {
            'Custom': None,
            T('jp_elsevier_single'): 8.5,
            T('jp_elsevier_double'): 17.5,
            T('jp_springer_single'): 8.4,
            T('jp_springer_double'): 17.4,
            T('jp_acs_single'): 8.25,
            T('jp_acs_double'): 17.78,
        }
        target_w_cm = width_cm_map[journal_preset]
        if target_w_cm is None:
            target_w_cm = st.number_input(T('cb_custom_width'), 5.0, 30.0, 17.5, 0.5, key='collage_custom_w')
        
        dpi = st.selectbox('DPI', [72, 150, 300, 600], index=2, key='collage_dpi',
            help=T('cb_help_dpi'))
        
        # Footer (watermark) — opsiyonel
        st.markdown('---')
        show_footer = st.checkbox(T('cb_footer_add'), value=True, key='collage_footer_show')
        footer_text = ''
        if show_footer:
            footer_text = st.text_input(
                T('cb_footer_text'),
                value=T('cb_footer_default'),
                key='collage_footer_text')
        
        st.markdown('---')
        # Render butonu
        if st.button(T('cb_render_btn'), use_container_width=True, type='primary', key='collage_render'):
            with st.spinner(T('cb_rendering')):
                try:
                    # Cells oluştur
                    cells_2d = []
                    if collage_mode.startswith('🅰️') and bulk_imgs:
                        # Alfabetik sırala, grid'e dağıt
                        sorted_imgs = sorted(bulk_imgs, key=lambda f: f.name)
                        idx = 0
                        for r in range(n_rows):
                            row = []
                            for c in range(n_cols):
                                if idx < len(sorted_imgs):
                                    label_txt = sorted_imgs[idx].name.rsplit('.',1)[0][:30] if 'Sample ID' in label_opts else ''
                                    row.append({'image': sorted_imgs[idx], 'label': label_txt})
                                    idx += 1
                                else:
                                    row.append(None)
                            cells_2d.append(row)
                    elif collage_mode.startswith('🅱️') and 'aging_results' in st.session_state:
                        ar = st.session_state.aging_results
                        # Pre/Post 2-sütun
                        st.session_state.collage_grid_override = True
                        # TODO: file source for aging — pairs have BytesIO from session
                        # For now, prepare cells with placeholders
                        st.warning(T('cb_quick_warn'))
                        cells_2d = []
                    elif collage_mode.startswith('🅲️') and bulk_imgs:
                        sorted_imgs = sorted(bulk_imgs, key=lambda f: f.name)
                        idx = 0
                        for r in range(n_rows):
                            row = []
                            for c in range(n_cols):
                                if idx < len(sorted_imgs):
                                    label_txt = sorted_imgs[idx].name.rsplit('.',1)[0][:30] if 'Sample ID' in label_opts else ''
                                    row.append({'image': sorted_imgs[idx], 'label': label_txt})
                                    idx += 1
                                else:
                                    row.append(None)
                            cells_2d.append(row)
                    
                    if not cells_2d:
                        st.error(T('cb_no_image'))
                    else:
                        # Headers
                        col_h = [h.strip() for h in col_headers_str.split(',')] if col_headers_str.strip() else None
                        row_l = [r.strip() for r in row_labels_str.split(',')] if row_labels_str.strip() else None
                        
                        # RGB conversion
                        bg_rgb = tuple(int(label_bg[i:i+2], 16) for i in (1,3,5))
                        tc_rgb = tuple(int(label_tc[i:i+2], 16) for i in (1,3,5))
                        
                        # Cell size hesabi — supersampling ile yuksek kalite
                        MIN_QUALITY_PX = 500   # her hucre en az bu kadar olsun
                        SUPERSAMPLE = 2.0      # quality faktoru (render>downscale)
                        
                        if cell_size_px is None:  # auto-fit + supersample
                            target_px = int(target_w_cm / 2.54 * dpi)
                            avail_w = target_px - (n_cols - 1) * cell_spc
                            cells_at_target = avail_w / n_cols
                            # Supersample for sharpness; min quality bound
                            cw_calc = max(MIN_QUALITY_PX, int(cells_at_target * SUPERSAMPLE))
                            cell_size_final = (cw_calc, cw_calc)
                        else:
                            cell_size_final = (cell_size_px, cell_size_px)
                        
                        # FONT SIZE auto-scale (cell_size'e oranli)
                        cw_actual = cell_size_final[0]
                        if font_mode.startswith('🎯'):  # Auto
                            label_fs = max(14, int(cw_actual * 0.045))
                            header_fs = max(16, int(cw_actual * 0.055))
                            footer_fs = max(10, int(cw_actual * 0.022))
                        elif font_mode == T('cb_font_small'):
                            label_fs = max(12, int(cw_actual * 0.035))
                            header_fs = max(14, int(cw_actual * 0.045))
                            footer_fs = max(9, int(cw_actual * 0.018))
                        elif font_mode == T('cb_font_medium'):
                            label_fs = max(16, int(cw_actual * 0.055))
                            header_fs = max(20, int(cw_actual * 0.07))
                            footer_fs = max(11, int(cw_actual * 0.026))
                        elif font_mode == T('cb_font_large'):
                            label_fs = max(22, int(cw_actual * 0.075))
                            header_fs = max(28, int(cw_actual * 0.09))
                            footer_fs = max(14, int(cw_actual * 0.032))
                        else:  # Custom
                            label_fs = font_sz or 20
                            header_fs = int((font_sz or 20) * 1.3)
                            footer_fs = max(10, int((font_sz or 20) * 0.7))
                        
                        collage = cb.build_collage(
                            cells_2d,
                            cell_size=cell_size_final,
                            label_position=label_pos_clean,
                            label_bg_color=bg_rgb,
                            label_text_color=tc_rgb,
                            label_font_size=label_fs,
                            header_font_size=header_fs,
                            footer_font_size=footer_fs,
                            cell_spacing=cell_spc,
                            col_headers=col_h,
                            row_labels=row_l,
                            footer_text=footer_text if show_footer else None,
                        )
                        
                        st.session_state.collage_result = collage
                        st.session_state.collage_meta = {
                            'rows': len(cells_2d),
                            'cols': max(len(r) for r in cells_2d),
                            'col_headers': col_h,
                            'target_w_cm': target_w_cm,
                            'dpi': dpi,
                            'cell_size_px': cell_size_final[0],
                            'auto_fit': cell_size_px is None,
                            'context': 'algorithm_comparison',
                        }
                        st.success(f'✓ ' + T('cb_collage_built') + f': {collage.size}')
                
                except Exception as e:
                    st.error(f'{T("err_generic")}: {e}')
                    import traceback
                    st.code(traceback.format_exc())
    
        st.markdown('---')

    # =============================================================
    # 🆚 KARŞILAŞTIRMA KOLAJI — sadece collage modunda
    # =============================================================
    if app_mode == 'collage':
        with st.expander(T('cb_cmp_title'), expanded=False):
            st.caption(T('cb_cmp_caption'))
            _itypes = ['jpg','jpeg','png','tif','tiff','bmp']
            cmp_before = st.file_uploader(T('cb_cmp_before'), accept_multiple_files=True,
                                          type=_itypes, key='cmp_before')
            cmp_after = st.file_uploader(T('cb_cmp_after'), accept_multiple_files=True,
                                         type=_itypes, key='cmp_after')
            cmp_methods = st.multiselect(T('cb_cmp_methods'), comp.available_methods(),
                                         default=comp.available_methods()[:2], key='cmp_methods')
            cmp_cell = st.slider(T('cb_cmp_cell'), 200, 800, 420, step=20, key='cmp_cell')
            cmp_ref_on = st.checkbox(T('cb_cmp_use_ref'), value=False, key='cmp_ref_on')
            cmp_ref_text = ''
            if cmp_ref_on:
                cmp_ref_text = st.text_area(T('cb_cmp_ref'), value='', height=110, key='cmp_ref_text',
                                            help='KT-A1: 4.75, 4.58')
            _cs1, _cs2 = st.columns(2)
            cmp_hdrfs = _cs1.slider(T('cb_cmp_hdr_fs'), 12, 40, 23, key='cmp_hdrfs')
            cmp_lblfs = _cs2.slider(T('cb_cmp_lbl_fs'), 10, 36, 21, key='cmp_lblfs')
            cmp_vert = st.checkbox(T('cb_cmp_vertical'), value=True, key='cmp_vert')
            cmp_colors = {}
            if cmp_methods:
                st.caption(T('cb_cmp_colors'))
                _mcols = st.columns(min(len(cmp_methods), 4))
                for _i, _m in enumerate(cmp_methods):
                    _dflt = '#%02x%02x%02x' % comp.method_color(_m)
                    _hx = _mcols[_i % len(_mcols)].color_picker(_m, _dflt, key=f'cmp_color_{_m}')
                    cmp_colors[_m] = tuple(int(_hx[_j:_j+2], 16) for _j in (1, 3, 5))
            if st.button(T('cb_cmp_build'), use_container_width=True, type='primary', key='cmp_build'):
                if not cmp_before:
                    st.warning(T('cb_cmp_need_before'))
                elif not cmp_methods:
                    st.warning(T('cb_cmp_need_method'))
                else:
                    with st.spinner(T('cb_cmp_running')):
                        try:
                            bef = sorted(cmp_before, key=lambda f: f.name)
                            aft = sorted(cmp_after, key=lambda f: f.name) if cmp_after else []
                            refmap = {}
                            for line in cmp_ref_text.splitlines():
                                line = line.strip()
                                if not line or ':' not in line:
                                    continue
                                sid, rest = line.split(':', 1)
                                parts = [x.strip() for x in rest.replace(';', ',').split(',') if x.strip()]
                                rb = ra = None
                                try:
                                    if len(parts) >= 1: rb = float(parts[0])
                                    if len(parts) >= 2: ra = float(parts[1])
                                except ValueError:
                                    rb = ra = None
                                refmap[sid.strip()] = {'before': rb, 'after': ra}
                            conds = ['before', 'after'] if aft else ['before']
                            n = len(bef) if not aft else min(len(bef), len(aft))
                            samples = []
                            for i in range(n):
                                raw_id = bef[i].name.rsplit('.', 1)[0]
                                sid = raw_id.split('_')[0]
                                rec = refmap.get(sid) or refmap.get(raw_id) or {}
                                condd = {'before': {'image': bef[i], 'exp': rec.get('before')}}
                                if aft:
                                    condd['after'] = {'image': aft[i], 'exp': rec.get('after')}
                                samples.append({'id': sid[:18], 'conditions': condd})
                            prog = st.progress(0.0)
                            def _pcb(done, total):
                                prog.progress(min(1.0, done / max(1, total)))
                            collage = comp.build_comparison_collage(
                                samples, methods=cmp_methods, condition_keys=tuple(conds),
                                condition_labels={'before': 'Before', 'after': 'After'},
                                cell_size=(cmp_cell, cmp_cell),
                                label_font_size=cmp_lblfs, header_font_size=cmp_hdrfs,
                                row_label_vertical=cmp_vert, method_colors=cmp_colors,
                                progress_cb=_pcb)
                            st.session_state.collage_result = collage
                            st.session_state.collage_meta = {
                                'rows': len(samples),
                                'cols': len(conds) * (1 + len(cmp_methods)),
                                'cell_size_px': cmp_cell, 'auto_fit': False,
                                'target_w_cm': 17.5, 'dpi': 300,
                                'source_image': 'comparison', 'context': 'comparison',
                                'col_headers': None,
                            }
                            st.success('✓ ' + T('cb_collage_built') + f': {collage.size}')
                        except Exception as e:
                            st.error(f'{T("err_generic")}: {e}')
                            import traceback
                            st.code(traceback.format_exc())

    # =============================================================
    # ⚙️ AYARLAR ve HAKKINDA — her modda görünür
    # =============================================================
    with st.expander(T('set_title'), expanded=False):
        st.caption(T('set_wip'))
        if st.session_state.get('lang','en') == 'en':
            st.markdown("""
        **Planned features:**
        - 🌍 Language selection (TR / EN / DE)
        - 🎨 Appearance theme (Light / Dark)
        - 📏 Pixel scale (mm/px) — preset per camera/zoom
        - 💾 Default output folder
        - 📤 Batch processing (192 images → one click)
        - 🔄 Default algorithm & parameters
        - 📊 CSV separator preference (`,` vs `;`)
        - 🌐 Configuration sharing (.json export/import)
        - 🔬 Custom palette loading (your own colors.xlsx files)
        - 📐 Scale bar overlay
        - 🎯 IoU/Dice metric computation (with ground truth)
        """)
        else:
            st.markdown("""
        **Planlanan özellikler:**
        - 🌍 Dil seçimi (TR / EN / DE)
        - 🎨 Görünüm teması (Light / Dark)
        - 📏 Piksel ölçeği (mm/px) — kamera/zoom başına preset
        - 💾 Varsayılan çıktı klasörü
        - 📤 Toplu işlem (192 görüntü → tek tıkla)
        - 🔄 Varsayılan algoritma & parametreler
        - 📊 CSV ayraç tercihi (`,` vs `;`)
        - 🌐 Konfigürasyon paylaşımı (.json export/import)
        - 🔬 Custom palet yükleme (kendi colors.xlsx dosyalarınız)
        - 📐 Ölçek çubuğu (scale bar) overlay
        - 🎯 IoU/Dice metrik hesaplama (ground truth ile)
        """)
        st.markdown('---')
        st.caption(T('set_feedback'))
    
    # =============================================================
    # ℹ️ HAKKINDA — bilim insanları için yardımcı bilgiler
    # =============================================================
    with st.expander(T('about_title'), expanded=False):
        if st.session_state.get('lang','en') == 'en':
            st.markdown("""
        **Pore Segmentation Suite v1.2**

        An open-source tool that detects the surface porosity of travertines and
        similar natural building stones using image processing techniques.

        ---
        **Developer:** Assist. Prof. Dr. Murat SERT
        Afyon Kocatepe University
        Marble and Natural Stone Technologies Application and Research Center

        **Project:** 24.MÜH.03 — AKÜ BAP

        ---
        **Libraries used:**
        OpenCV · scikit-image · scikit-learn · Streamlit · NumPy

        **License:** MIT (recommended) — open for science.

        ---
        **If you use this tool, please cite:**
        > Sert, M. et al. (2026). *Pore Segmentation Suite v1.2.*
        > Afyon Kocatepe University. (In preparation)

        **Contact:** msert@aku.edu.tr
        """)
        else:
            st.markdown("""
        **Gözenek ve Renk Tespit Yazılımı v1.2**

        Travertenler ve benzer doğal yapı taşlarının yüzey gözenekliliğini
        görüntü işleme teknikleriyle tespit eden açık kaynak araç.

        ---
        **Geliştirici:** Dr. Öğr. Üyesi Murat SERT
        Afyon Kocatepe Üniversitesi
        Mermer ve Doğaltaş Teknolojileri Uygulama ve Araştırma Merkezi

        **Proje:** 24.MÜH.03 — AKÜ BAP

        ---
        **Kullanılan kütüphaneler:**
        OpenCV · scikit-image · scikit-learn · Streamlit · NumPy

        **Lisans:** MIT (önerilen) — bilim için açık.

        ---
        **Bu aracı kullanırsanız lütfen atıf yapın:**
        > Sert, M. ve diğ. (2026). *Gözenek ve Renk Tespit Yazılımı v1.2.*
        > Afyon Kocatepe Üniversitesi. (Hazırlık aşamasında)

        **İletişim:** msert@aku.edu.tr
        """)


# ============================================================
# ANA PANEL — GÖRÜNTÜ + OVERLAY + METRİKLER
# ============================================================
# ============================================================
# ANA PANEL — Mode'a göre içerik
# ============================================================
app_mode = st.session_state.get('active_mode', 'pore')

# Mode banner
mode_banner_map = {
    'pore': (T('mode_pore_banner'), '#1e40af'),
    'palette': (T('mode_palette_banner'), '#7c2d12'),
    'aging': (T('mode_aging_banner'), '#14532d'),
    'collage': (T('collage_mode_title'), '#581c87'),
}
banner_text, banner_color = mode_banner_map.get(app_mode, ('Unknown mode', '#444'))
st.markdown(
    f'<div style="background:{banner_color}22; border-left:4px solid {banner_color}; '
    f'padding:8px 16px; border-radius:4px; margin-bottom:16px;">'
    f'<b>{banner_text}</b> — ' + T('banner_suffix') +
    f'</div>',
    unsafe_allow_html=True)

# ─── PORE MODE ───
if app_mode == 'pore' and st.session_state.image_rgb is None:
    _mi = st.container(key='mode_info_panel')
    _mi.info(T('load_image_left'))
    _ce1, _ce2, _ce3 = st.columns([1, 1, 1])
    with _ce2:
        if st.button(T('demo_sample'), use_container_width=True, key='demo_btn_main'):
            if _load_sample_image():
                st.rerun()
        st.caption(T('demo_caption'))
    if st.session_state.get('lang', 'en') == 'en':
        _mi.markdown("""
    ### Quick Start
    1. **Upload an image from the left** (jpg/png/tif)
    2. **Pick a stone type** (KT/GT/NT/PT) — palette loads automatically
    3. **Choose an algorithm** — DoG, MSER, Sauvola, Color Distance, or a combination
    4. **Adjust the sliders** — the overlay updates in real time
    5. **Mark pore colors** — which palette colors represent pores?
    6. **Save parameters** — store as a reusable preset
    
    ### Algorithm Guide
    - **DoG**: Blob detection. Good for small dark spots. Sigmas tune pore size.
    - **MSER**: Extremal regions. Ideal for stable dark blobs. Strong cross-stone generalization.
    - **Sauvola**: Local adaptive threshold. Robust to heterogeneous illumination.
    - **Color Distance**: Color-palette based. Most interpretable; addresses the cross-stone problem.
    """)
    else:
        _mi.markdown("""
    ### Hızlı Başlangıç
    1. **Soldan görüntü yükle** (jpg/png/tif)
    2. **Taş tipini seç** (KT/GT/NT/PT) — paleti otomatik yüklenir
    3. **Algoritma seç** — DoG, MSER, Sauvola, Color Distance veya kombinasyon
    4. **Sliderları oynat** — overlay anlık güncellenir
    5. **Pore renklerini işaretle** — paletteki hangi renkler pore?
    6. **Parametreleri kaydet** — preset olarak sakla
    
    ### Algoritma Rehberi
    - **DoG**: Blob detection. Küçük dark spotlar için iyi. Sigma'lar pore boyutunu ayarlar.
    - **MSER**: Extremal regions. Stable dark blob'lar için ideal. Cross-stone genelleme iyi.
    - **Sauvola**: Yerel adaptif eşik. Heterojen aydınlatma için uygun.
    - **Color Distance**: Renk paleti tabanlı. En yorumlanabilir; cross-stone problemini çözer.
    """)

# ─── PALETTE MODE — boş durum ───
elif app_mode == 'palette' and ('computed_palette' not in st.session_state or not st.session_state.get('computed_palette')):
    _mi = st.container(key='mode_info_panel')
    _mi.info(('👈 From the left **Color Palette** tab, upload an image and click "Compute Palette".'
              if st.session_state.get('lang','en')=='en'
              else '👈 Soldan **Renk Yelpazesi** sekmesinden görüntü yükle ve "Paleti Hesapla" tıkla.'))
    if st.session_state.get('lang','en') == 'en':
        _mi.markdown("""
    ### 🎨 Color Palette Mode — Quick Start
    1. **Choose an image** (loaded or new file)
    2. **Algorithm:** K-means (default) / GMM / MeanShift / Median Cut
    3. **Color space:** Lab (recommended, perceptually uniform) / RGB / HSV
    4. **Number of colors:** 7 (default, stone industry standard)
    5. **🎨 Compute Palette** → detailed visualization opens in the main panel

    ### What's next?
    - **Pie chart + table** → dominant colors extracted from the image
    - **L\*, a\*, b\*, Munsell** values for each color
    - **ΔE comparison** → perceptual distance between two colors
    - **Color uniformity** → image color homogeneity score (0-10)
    - **JSON/CSV/PNG** export → directly usable in papers
    """)
    else:
        _mi.markdown("""
    ### 🎨 Renk Paleti Modu — Hızlı Başlangıç
    1. **Görüntü seç** (yüklü veya yeni dosya)
    2. **Algoritma:** K-means (default) / GMM / MeanShift / Median Cut
    3. **Renk uzayı:** Lab (önerilen, perceptually uniform) / RGB / HSV
    4. **Renk sayısı:** 7 (default, taş endüstrisi standardı)
    5. **🎨 Paleti Hesapla** → ana panelde detaylı görselleştirme açılır

    ### Sonra ne yapacaksın?
    - **Pie chart + tablo** → görüntüden çıkan dominant renkler
    - **L\*, a\*, b\*, Munsell** değerleri her renk için
    - **ΔE karşılaştırma** → iki rengin perceptual mesafesi
    - **Color uniformity** → görüntünün renk homojenliği skoru (0-10)
    - **JSON/CSV/PNG** export → makaleye direkt kullanılabilir
    """)

# ─── AGING MODE — boş durum ───
elif app_mode == 'aging' and ('aging_results' not in st.session_state or not st.session_state.aging_results):
    _mi = st.container(key='mode_info_panel')
    _mi.info(('👈 From the left **Aging Analysis** tab, upload pre/post images and click "Run Comparison Analysis".'
              if st.session_state.get('lang','en')=='en'
              else '👈 Soldan **Aging Analizi** sekmesinden pre/post görüntülerini yükle ve "Karşılaştırma Analizini Çalıştır" tıkla.'))
    if st.session_state.get('lang','en') == 'en':
        _mi.markdown("""
    ### 🔄 Aging Analysis Mode — Quick Start
    1. **Choose mode:** Single pair (1+1) or Multi-specimen (N+N, open-ended)
    2. **Upload pre images** (before treatment, drag&drop)
    3. **Upload post images** (after treatment, equal count)
    4. **Pairing strategy:** alphabetic / upload order / manual
    5. **ΔE metric:** ΔE-2000 (recommended, modern CIE standard)
    6. **🔬 Run Comparison Analysis**

    ### What's next?
    - **Per-specimen table:** ΔL\*, Δa\*, Δb\*, ΔC\*, ΔH\*, ΔE for every sample
    - **Pre/Post color swatch grid** → visual comparison
    - **Bar chart** → with perceptual threshold lines (1, 3.5, 5, 10)
    - **4 paired tests** (ΔE, ΔL\*, Δa\*, Δb\*) — Shapiro-Wilk → t-test/Wilcoxon
    - **95% CI + Cohen's d** — effect size interpretation (Negligible/Small/Medium/Large)
    - **Automatic scientific interpretation** (TR Discussion + EN paper-ready)
    - **CSV/JSON/Markdown/TXT** export

    ### Standards
    This module complies with **TS EN 15886** (Natural stone, colour of surfaces) and 
    **Sharma et al. 2005** (CIEDE2000). Damage class is automatically assigned via the 
    Mokrzycki & Tatol (2011) classification.
    """)
    else:
        _mi.markdown("""
    ### 🔄 Yaşlandırma Analizi Modu — Hızlı Başlangıç
    1. **Mod seç:** Tek-çift (1+1) veya Çoklu numune (N+N, açık uçlu)
    2. **Pre görüntüleri** yükle (deney öncesi, drag&drop)
    3. **Post görüntüleri** yükle (deney sonrası, eşit sayı)
    4. **Eşleştirme stratejisi:** alfabetik / yükleme sırası / manuel
    5. **ΔE metriği:** ΔE-2000 (önerilen, modern CIE standardı)
    6. **🔬 Karşılaştırma Analizini Çalıştır**

    ### Sonra ne yapacaksın?
    - **Per-numune tablo:** ΔL\*, Δa\*, Δb\*, ΔC\*, ΔH\*, ΔE her örnekleme
    - **Pre/Post renk swatch grid** → görsel karşılaştırma
    - **Bar chart** → perceptual eşik çizgileri (1, 3.5, 5, 10) ile birlikte
    - **4 paired test** (ΔE, ΔL\*, Δa\*, Δb\*) — Shapiro-Wilk → t-test/Wilcoxon
    - **95% CI + Cohen's d** — effect size yorumu (Negligible/Small/Medium/Large)
    - **Otomatik bilimsel yorum** (TR Tartışma + EN paper-ready)
    - **CSV/JSON/Markdown/TXT** export

    ### Standartlar
    Bu modül **TS EN 15886** (Natural stone, colour of surfaces) ve **Sharma et al. 2005** 
    (CIEDE2000) standartlarına uyumludur. Mokrzycki & Tatol (2011) sınıflandırması ile 
    otomatik damage class belirler.
    """)

elif app_mode == 'pore' and st.session_state.image_rgb is not None:
    img = st.session_state.image_rgb
    H, W = img.shape[:2]
    
    # ────────────────────────────────────────────────────
    # SEGMENTASYON ÇALIŞTIR
    # ────────────────────────────────────────────────────
    # Algoritma seçimine göre raw mask üret
    algo_short = algo.split(' ')[0]  # DoG | MSER | Sauvola | Color
    
    raw_mask = None
    gray = None
    sam2_warning = None
    try:
        if algo == 'DoG (Difference of Gaussians)':
            raw_mask, gray = segmentation.segment_DoG(img, **params)
        elif algo == 'MSER (Extremal Regions)':
            raw_mask, gray = segmentation.segment_MSER(img, **params)
        elif algo == 'Sauvola (Adaptive Threshold)':
            raw_mask, gray = segmentation.segment_Sauvola(img, **params)
        elif algo == 'Multi-Otsu (Auto Multi-level)':
            raw_mask, gray = segmentation.segment_MultiOtsu(img, **params)
        elif algo == 'Auto Threshold (Triangle/Yen/Otsu)':
            raw_mask, gray = segmentation.segment_AutoThreshold(img, **params)
        elif algo == 'Bottom-Hat Morphology':
            raw_mask, gray = segmentation.segment_BottomHat(img, **params)
        elif algo == 'Frangi Vesselness':
            raw_mask, gray = segmentation.segment_Frangi(img, **params)
        elif algo == 'GMM (Gaussian Mixture)':
            raw_mask, gray = segmentation.segment_GMM(img, **params)
        elif algo == 'Watershed (Marker-Controlled)':
            raw_mask, gray = segmentation.segment_Watershed(img, **params)
        elif 'SAM 2' in algo:
            result = segmentation.segment_SAM2(img, **params)
            if result[2] is None:
                raw_mask, gray = result[0], result[1]
            else:
                sam2_warning = result[2]
                raw_mask = np.zeros(img.shape[:2], dtype=bool)
                gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        elif 'CellPose' in algo:
            result = segmentation.segment_CellPose(img, **params)
            if result[2] is None:
                raw_mask, gray = result[0], result[1]
            else:
                sam2_warning = result[2]
                raw_mask = np.zeros(img.shape[:2], dtype=bool)
                gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        elif algo == T('algo_color_distance'):
            # Pore renkleri = checkbox'lı + custom
            pore_colors = []
            if st.session_state.palette_data:
                pore_colors = palettes.palette_to_dict(st.session_state.palette_data, 
                                                       st.session_state.selected_pore_indices)
            pore_colors += st.session_state.custom_pore_colors
            if not pore_colors:
                st.warning(T('pm_select_pore_color'))
                raw_mask = np.zeros((H,W), dtype=bool)
                gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            else:
                raw_mask, gray = segmentation.segment_ColorDistance(img, pore_colors, **params)
        elif algo == 'DoG + Color Filter':
            # DoG run, sonra renk filtresi uygulanır
            dog_params = {k:v for k,v in params.items() if k not in ('color_space','max_distance')}
            raw_mask, gray = segmentation.segment_DoG(img, **dog_params)
            # Renk filtresi: sadece pore renklerine yakın olanları tut
            pore_colors = []
            if st.session_state.palette_data:
                pore_colors = palettes.palette_to_dict(st.session_state.palette_data, 
                                                       st.session_state.selected_pore_indices)
            pore_colors += st.session_state.custom_pore_colors
            if pore_colors:
                color_mask, _ = segmentation.segment_ColorDistance(img, pore_colors, 
                                                                     max_distance=params.get('max_distance',30),
                                                                     color_space=params.get('color_space','lab'))
                raw_mask = raw_mask & color_mask
        elif algo == 'MSER + Color Filter':
            mser_params = {k:v for k,v in params.items() if k not in ('color_space','max_distance')}
            raw_mask, gray = segmentation.segment_MSER(img, **mser_params)
            pore_colors = []
            if st.session_state.palette_data:
                pore_colors = palettes.palette_to_dict(st.session_state.palette_data, 
                                                       st.session_state.selected_pore_indices)
            pore_colors += st.session_state.custom_pore_colors
            if pore_colors:
                color_mask, _ = segmentation.segment_ColorDistance(img, pore_colors, 
                                                                     max_distance=params.get('max_distance',30),
                                                                     color_space=params.get('color_space','lab'))
                raw_mask = raw_mask & color_mask
    except Exception as e:
        st.error(T('segmentation_error') + f': {e}')
        raw_mask = np.zeros((H,W), dtype=bool)
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    
    # Filtreler uygula
    final_filter_params = dict(min_area=f_params['min_area'])
    if f_params['use_max_eccentricity']:
        final_filter_params['max_eccentricity'] = f_params['max_eccentricity']
    if f_params['use_min_solidity']:
        final_filter_params['min_solidity'] = f_params['min_solidity']
    if f_params['use_max_interior_std']:
        final_filter_params['max_interior_std'] = f_params['max_interior_std']
    if f_params['must_be_dark']:
        final_filter_params['must_be_dark'] = True
        final_filter_params['dark_thresh_factor'] = f_params['dark_thresh_factor']
    else:
        final_filter_params['must_be_dark'] = False
    
    final_mask, kept_props = filters.filter_components(raw_mask, gray, **final_filter_params)
    metrics = filters.compute_metrics(final_mask, kept_props)
    
    # Sonucu state'e koy
    st.session_state.last_result = {'mask': final_mask, 'metrics': metrics, 'params': params, 'f_params': f_params}
    
    # ────────────────────────────────────────────────────
    # GÖRSELLEŞTİR
    # ────────────────────────────────────────────────────
    st.subheader(f'📊 {st.session_state.image_name}  ({H}×{W} px)')
    
    display_max = 900
    img_display = utils.resize_for_display(img, display_max)
    
    # Overlay stili + dolgu rengi
    style_cols = st.columns([2, 2, 1.5])
    overlay_style = style_cols[0].radio(T('overlay_style_label'), 
                                         [T('style_fill'), T('style_outline')], 
                                         horizontal=True)
    
    # Renk presetleri — açık taş için koyu, koyu taş için açık
    color_presets = {
        T('preset_green_light'): (0, 255, 80),
        T('preset_yellow'):      (255, 230, 0),
        T('preset_red'):         (255, 40, 40),
        T('preset_pink'):        (255, 80, 200),
        T('preset_magenta'):     (255, 0, 255),
        T('preset_blue'):        (0, 120, 255),
        T('preset_cyan'):        (0, 255, 220),
        T('preset_white'):       (255, 255, 255),
        T('preset_black'):       (0, 0, 0),
        T('preset_orange'):      (255, 140, 0),
        T('preset_auto'):        'auto',
        T('preset_custom'):      'custom',
    }
    color_choice = style_cols[1].selectbox(T('fill_color_label'), 
                                            list(color_presets.keys()), 
                                            index=10)  # Auto default
    
    color_val = color_presets[color_choice]
    
    if color_val == 'auto':
        # Görüntü parlaklığına göre kontrastlı renk seç
        mean_brightness = float(img.mean())
        if mean_brightness > 160:    # açık taş (KT, PT gibi) → magenta-pembe
            fill_color = (220, 0, 200)
            auto_note = T('auto_note_magenta')
        elif mean_brightness > 100:  # orta tonda
            fill_color = (0, 255, 100)
            auto_note = T('auto_note_green')
        else:                         # koyu taş → parlak sarı
            fill_color = (255, 240, 0)
            auto_note = T('auto_note_yellow')
        style_cols[2].caption(T('auto_brightness_label') + f'={mean_brightness:.0f}')
        style_cols[2].caption(auto_note)
    elif color_val == 'custom':
        custom_hex = style_cols[2].color_picker(T('color_picker'), '#00ff50', label_visibility='collapsed')
        fill_color = tuple(utils.hex_to_rgb(custom_hex))
    else:
        fill_color = color_val
        # Renk önizleme kutusu
        hex_str = utils.rgb_to_hex(fill_color)
        style_cols[2].markdown(
            f'<div style="background:{hex_str};width:100%;height:36px;'
            f'border:2px solid #888;border-radius:6px;margin-top:24px"></div>',
            unsafe_allow_html=True)
    
    # Alpha (saydamlık) veya thickness (sınır kalınlığı)
    if overlay_style == T('style_fill'):
        alpha = st.slider(T('alpha'), 0.10, 0.95, 0.55, step=0.05,
                          help=T('pm_help_alpha'))
        overlay = utils.make_overlay(img, final_mask, color=fill_color, alpha=alpha)
    else:
        thickness = st.slider(T('outline_thickness'), 1, 8, 2,
                              help=T('pm_help_thickness'))
        overlay = utils.make_outline_overlay(img, final_mask, color=fill_color, thickness=thickness)
    overlay_display = utils.resize_for_display(overlay, display_max)
    
    col1, col2 = st.columns(2)
    with col1:
        st.image(img_display, caption=T('caption_original'), width='stretch')
    with col2:
        st.image(overlay_display, caption=T('caption_segmentation') + f' ({algo})', width='stretch')
    
    # SAM2/CellPose uyarısı
    if sam2_warning:
        st.warning(f'⚠️ {sam2_warning}')
    
    # Metrik kutuları
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric(T('metric_porosity'), f"{metrics['porosity_pct']:.2f} %")
    mc2.metric(T('metric_pore_count'), metrics['n_pores'])
    mc3.metric(T('metric_mean_area'), f"{metrics['mean_area_mm2']:.3f}")
    mc4.metric(T('metric_mean_circ'), f"{metrics['mean_circularity']:.3f}")

    # ── Güvenilirlik rozeti: gözeneklilik rejimine göre (Oğuz tarzı renkli kart) ──
    _pp = metrics['porosity_pct']
    _rpal = _chart_pal()
    if _pp < 2.0:
        _rc, _ric, _rlab, _rmsg = _rpal['green'], '🟢', T('rel_low'), T('rel_low_msg')
    elif _pp <= 8.0:
        _rc, _ric, _rlab, _rmsg = _rpal['gold'], '🟠', T('rel_mid'), T('rel_mid_msg')
    else:
        _rc, _ric, _rlab, _rmsg = _rpal['red'], '🔴', T('rel_high'), T('rel_high_msg')
    st.markdown(
        f'<div style="border-left:5px solid {_rc};background:{_rc}1f;'
        f'padding:10px 14px;border-radius:10px;margin:8px 0 4px;">'
        f'<span style="font-weight:700;color:{_rc};font-size:1.02rem">{_ric} {T("rel_title")}: {_rlab}</span><br>'
        f'<span style="font-size:.92rem;color:{_rpal["ink"]}">{_rmsg}</span></div>',
        unsafe_allow_html=True)
    
    # Karşılaştırma — deneysel değer biliniyorsa
    with st.expander(T('reference_compare')):
        exp_ref = st.number_input(T('pm_ref_porosity'), value=0.0, step=0.1)
        if exp_ref > 0:
            sapma = abs(metrics['porosity_pct'] - exp_ref)
            st.write('**' + T('pm_deviation') + f':** {sapma:.2f} pp')
            if sapma < 0.5: st.success(T('pm_excellent_match'))
            elif sapma < 1.5: st.info(T('pm_acceptable'))
            elif sapma < 3.0: st.warning(T('pm_improvable'))
            else: st.error(T('pm_high_deviation'))
    
    # Görüntüden renk seçme (basit form)
    with st.expander(T('pm_pick_color_title')):
        st.caption(T('pm_pick_caption'))
        cc1, cc2, cc3 = st.columns([1,1,2])
        px_x = cc1.number_input(T('pm_x_px'), min_value=0, max_value=W-1, value=W//2)
        px_y = cc2.number_input(T('pm_y_px'), min_value=0, max_value=H-1, value=H//2)
        if cc3.button(T('pm_add_color_btn')):
            rgb = utils.pick_color_at(img, int(px_x), int(px_y))
            st.session_state.custom_pore_colors.append(rgb)
            st.success(f'{T("pm_added")}: {utils.rgb_to_hex(rgb)} (RGB={rgb})')
            st.rerun()
    
    # Pore detay tablosu
    with st.expander(T('pm_pore_stats_title')):
        if kept_props:
            rows = []
            for i, p in enumerate(kept_props[:50]):
                rows.append({
                    '#': i+1, T('pm_col_area_px'): p.area, 
                    T('pm_col_area_mm2'): round(p.area * 0.091**2, 3),
                    T('pm_col_perimeter'): round(p.perimeter, 1),
                    T('pm_col_circularity'): round(4*np.pi*p.area/(p.perimeter**2) if p.perimeter>0 else 0, 3),
                    'Eccentricity': round(p.eccentricity, 3),
                    T('pm_col_mean_intensity'): round(p.mean_intensity, 1),
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
            
            csv_bytes = pd.DataFrame(rows).to_csv(index=False).encode('utf-8')
            st.download_button(T('pm_download_all_csv'), csv_bytes, 
                                file_name=f'{st.session_state.image_name}_pores.csv', mime='text/csv')
        else:
            st.write(T('pm_no_pores'))
    
    # Gözenek boyut dağılımı (MIP tarzı) — image-derived pore-size distribution
    with st.expander(T('psd_title')):
        if kept_props:
            st.caption(T('psd_intro'))
            _wsel = st.radio(T('psd_weight'), [T('psd_weight_area'), T('psd_weight_count')],
                             horizontal=True, key='psd_w')
            _wmode = 'area' if _wsel == T('psd_weight_area') else 'count'
            _dist = psize.pore_size_distribution(kept_props, pixel_scale_mm=0.091, weight=_wmode)
            if _dist:
                st.markdown(psize.psd_svg(_dist, title=T('psd_chart_title'), xlabel=T('psd_xlabel'),
                                          y_inc=T('psd_y_inc'), y_cum=T('psd_y_cum'), pal=_chart_pal()),
                            unsafe_allow_html=True)
                if _dist['d50'] == _dist['d50']:
                    st.metric(T('psd_d50'), f"{_dist['d50']:.3f} mm")
                st.info(T('psd_note'))
                _tbl = pd.DataFrame({
                    T('psd_xlabel'): [f"{_dist['bin_edges'][i]:.3f}-{_dist['bin_edges'][i+1]:.3f}"
                                      for i in range(len(_dist['inc_pct']))],
                    T('psd_y_inc'): _dist['inc_pct'].round(2),
                    T('psd_y_cum'): _dist['cum_pct'].round(2),
                    'n': _dist['counts'],
                })
                st.download_button(T('psd_download'), _tbl.to_csv(index=False).encode('utf-8'),
                                   file_name=f"{st.session_state.image_name}_pore_size_distribution.csv",
                                   mime='text/csv', key='psd_csv')
        else:
            st.write(T('pm_no_pores'))

    # Mask ve overlay indir
    with st.expander(T('pm_download_outputs')):
        ov_pil = Image.fromarray(overlay)
        buf = BytesIO(); ov_pil.save(buf, format='PNG')
        st.download_button('Overlay PNG', buf.getvalue(), 
                            file_name=f'{st.session_state.image_name}_overlay.png', mime='image/png')
        mask_pil = Image.fromarray((final_mask*255).astype(np.uint8))
        buf2 = BytesIO(); mask_pil.save(buf2, format='PNG')
        st.download_button('Binary mask PNG', buf2.getvalue(),
                            file_name=f'{st.session_state.image_name}_mask.png', mime='image/png')
        # Tüm çıktıları tek ZIP olarak indir (#3)
        import zipfile as _zip
        _nm = (st.session_state.image_name or 'image').rsplit('.', 1)[0]
        _zbuf = BytesIO()
        with _zip.ZipFile(_zbuf, 'w', _zip.ZIP_DEFLATED) as _zf:
            _b = BytesIO(); Image.fromarray(overlay).save(_b, format='PNG')
            _zf.writestr(f'{_nm}_overlay.png', _b.getvalue())
            _b = BytesIO(); Image.fromarray((final_mask * 255).astype(np.uint8)).save(_b, format='PNG')
            _zf.writestr(f'{_nm}_mask.png', _b.getvalue())
            _zf.writestr(f'{_nm}_metrics.json', safe_json_dumps(metrics, indent=2))
        st.download_button(T('dl_all_zip'), _zbuf.getvalue(),
                            file_name=f'{_nm}_outputs.zip', mime='application/zip',
                            use_container_width=True, key='dl_all_zip_btn')

    # ────────────────────────────────────────────────────
    # P2 — ÇOKLU-YÖNTEM POROZİTE YAYILIMI (yöntem-bağımlılığı / belirsizlik)
    # Aynı görüntü; birden çok algoritma; porozite yayılımını şeffaf raporla.
    # ────────────────────────────────────────────────────
    st.divider()
    with st.expander(T('p2_title'), expanded=False):
        st.caption(T('p2_intro'))
        P2_FAM = {'Sauvola':'Classical','Multi-Otsu':'Classical',
                  'DoG':'Blob/region','MSER':'Blob/region','Bottom-Hat':'Blob/region',
                  'Frangi':'Blob/region','GMM':'Clustering'}
        P2_FC = {'Classical':'#1f77b4','Blob/region':'#d62728','Clustering':'#2ca02c'}
        p2_all = comp.available_methods()
        p2_sel = st.multiselect(T('p2_methods'), p2_all, default=p2_all, key='p2_methods_sel')
        if st.button(T('p2_run_btn'), key='p2_run', use_container_width=True):
            if len(p2_sel) < 2:
                st.warning(T('p2_need_run'))
            else:
                rows = []
                prog = st.progress(0.0)
                with st.spinner(T('p2_running')):
                    for k, m in enumerate(p2_sel):
                        try:
                            _, por = comp.run_method(img, m, filter_params=final_filter_params)
                        except Exception:
                            por = float('nan')
                        rows.append({'method': m, 'family': P2_FAM.get(m, '-'), 'porosity': por})
                        prog.progress((k+1)/len(p2_sel))
                prog.empty()
                st.session_state['p2_spread'] = rows
        rows = st.session_state.get('p2_spread')
        if rows:
            vals = [r['porosity'] for r in rows if r['porosity'] == r['porosity']]
            if vals:
                vmin, vmax = min(vals), max(vals)
                sv = sorted(vals); med = sv[len(sv)//2] if len(sv)%2 else (sv[len(sv)//2-1]+sv[len(sv)//2])/2
                spread = vmax - vmin
                s1, s2, s3, s4 = st.columns(4)
                s1.metric(T('p2_median'), f'{med:.2f} %')
                s2.metric(T('p2_range'), f'{spread:.2f} pp')
                s3.metric(T('p2_min'),   f'{vmin:.2f} %')
                s4.metric(T('p2_max'),   f'{vmax:.2f} %')
                # ── inline-SVG horizontal lollipop chart (no matplotlib dependency) ──
                srt = sorted(rows, key=lambda r: (r['porosity'] != r['porosity'], -(r['porosity'] if r['porosity']==r['porosity'] else 0)))
                W, rh, gut, padR, top, botax = 640, 30, 104, 60, 30, 34
                plotW = W - gut - padR
                scale = (vmax * 1.18) if vmax > 0 else 1.0
                Hsvg = top + len(srt)*rh + botax
                med_x = gut + (med/scale)*plotW
                _pal = _chart_pal()
                parts = [f'<svg width="100%" viewBox="0 0 {W} {Hsvg}" xmlns="http://www.w3.org/2000/svg" font-family="Arial,Helvetica,sans-serif">']
                parts.append(f'<text x="{gut}" y="18" font-size="13" font-weight="bold" fill="{_pal["ink"]}">{T("p2_chart_title")}</text>')
                # median guide
                parts.append(f'<line x1="{med_x:.1f}" y1="{top-4}" x2="{med_x:.1f}" y2="{top+len(srt)*rh}" stroke="{_pal["muted"]}" stroke-width="1.4" stroke-dasharray="5,4"/>')
                for i, r in enumerate(srt):
                    y = top + i*rh + rh/2
                    fc = _pal['fam'].get(r['family'], '#888')
                    parts.append(f'<text x="{gut-8}" y="{y+4:.1f}" font-size="12" text-anchor="end" fill="{_pal["ink"]}">{r["method"]}</text>')
                    por = r['porosity']
                    if por == por:
                        bw = max((por/scale)*plotW, 2)
                        parts.append(f'<line x1="{gut}" y1="{y:.1f}" x2="{gut+bw:.1f}" y2="{y:.1f}" stroke="{fc}" stroke-width="7" stroke-linecap="round"/>')
                        parts.append(f'<circle cx="{gut+bw:.1f}" cy="{y:.1f}" r="5.5" fill="{fc}" stroke="{_pal["dot_ring"]}" stroke-width="1"/>')
                        parts.append(f'<text x="{gut+bw+10:.1f}" y="{y+4:.1f}" font-size="12" fill="{_pal["ink"]}">{por:.2f}%</text>')
                    else:
                        parts.append(f'<text x="{gut+6}" y="{y+4:.1f}" font-size="11" fill="{_pal["red"]}">{T("p2_failed")}</text>')
                # x axis
                axy = top + len(srt)*rh + 8
                parts.append(f'<line x1="{gut}" y1="{axy}" x2="{gut+plotW}" y2="{axy}" stroke="{_pal["grid"]}" stroke-width="1"/>')
                for t in range(0, 6):
                    xv = gut + (t/5)*plotW; lab = scale*(t/5)
                    parts.append(f'<line x1="{xv:.1f}" y1="{axy}" x2="{xv:.1f}" y2="{axy+4}" stroke="{_pal["axis"]}"/>')
                    parts.append(f'<text x="{xv:.1f}" y="{axy+16}" font-size="10" text-anchor="middle" fill="{_pal["muted"]}">{lab:.1f}</text>')
                # family legend
                lx = gut + plotW - 150
                for j, (fam, col) in enumerate(_pal['fam'].items()):
                    ly = top + 2 + j*15
                    parts.append(f'<rect x="{lx}" y="{ly-9}" width="11" height="11" fill="{col}" rx="2"/>')
                    parts.append(f'<text x="{lx+16}" y="{ly}" font-size="10" fill="{_pal["muted"]}">{fam}</text>')
                parts.append('</svg>')
                st.markdown(''.join(parts), unsafe_allow_html=True)
                st.info(T('p2_interpret').format(spread=f'{spread:.1f}'))
                p2_df = pd.DataFrame([{T('p2_method_col'): r['method'], T('p2_family'): r['family'],
                                       T('p2_porosity_col'): (round(r['porosity'],3) if r['porosity']==r['porosity'] else None)}
                                      for r in rows])
                st.dataframe(p2_df, use_container_width=True, hide_index=True)
                st.download_button(T('p2_download'),
                                   p2_df.to_csv(index=False).encode('utf-8'),
                                   file_name=f'{st.session_state.image_name}_method_spread.csv',
                                   mime='text/csv', key='p2_csv')

# ============================================================
# 🎨 RENK YELPAZESİ — Ana Panel Detaylı Görselleştirme
# (sidebar'da hesaplanmışsa burada gözükür)
# ============================================================
if app_mode == 'palette' and 'computed_palette' in st.session_state and st.session_state.get('computed_palette'):
    st.divider()
    with st.expander(T('pd_title'), expanded=True):
        palette = st.session_state.computed_palette
        meta = st.session_state.computed_palette_meta
        
        st.caption(f'**{T("pd_source")}:** {meta.get("source_image","-")} · **{T("pd_algorithm")}:** {meta.get("algorithm","-")} · **{T("color_space")}:** {meta.get("color_space","-")}')
        
        # İki sütun: sol palette swatches, sağ pie chart
        pc1, pc2 = st.columns([1, 1])
        
        with pc1:
            st.markdown('##### ' + T('pd_color_list'))
            # Tablo halinde göster
            pal_df = pd.DataFrame([{
                '#': i+1,
                'Hex': c['hex'],
                'RGB': f"({c['rgb'][0]}, {c['rgb'][1]}, {c['rgb'][2]})",
                T('pd_brightness'): round(c['brightness'], 0),
                'Fraction (%)': round(c['fraction_pct'], 2),
            } for i, c in enumerate(palette)])
            st.dataframe(pal_df, use_container_width=True, hide_index=True)
            
            # Hex değerleri tek satır (kopya için kolay)
            st.markdown('##### ' + T('pd_hex_values'))
            hex_string = ' '.join(c['hex'] for c in palette)
            st.code(hex_string, language=None)
        
        with pc2:
            st.markdown('##### ' + T('pd_pie'))
            # Pure SVG pie chart — matplotlib bağımlılığı olmadan
            import math
            size = 400
            cx, cy = size // 2, size // 2
            radius = size // 2 - 30
            svg_parts = [f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">']
            total = sum(c['fraction_pct'] for c in palette) or 1
            start_angle = -90
            for c in palette:
                angle = c['fraction_pct'] / total * 360
                end_angle = start_angle + angle
                x1 = cx + radius * math.cos(math.radians(start_angle))
                y1 = cy + radius * math.sin(math.radians(start_angle))
                x2 = cx + radius * math.cos(math.radians(end_angle))
                y2 = cy + radius * math.sin(math.radians(end_angle))
                large_arc = 1 if angle > 180 else 0
                if angle >= 359.9:
                    # Tek bir renk hakimse tam daire çiz
                    svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{c["hex"]}" stroke="white" stroke-width="2"/>')
                else:
                    path = f'M {cx} {cy} L {x1:.1f} {y1:.1f} A {radius} {radius} 0 {large_arc} 1 {x2:.1f} {y2:.1f} Z'
                    svg_parts.append(f'<path d="{path}" fill="{c["hex"]}" stroke="white" stroke-width="2"/>')
                # Etiket — yeterince büyük dilim ise
                if c['fraction_pct'] > 3:
                    mid_angle = (start_angle + end_angle) / 2
                    label_r = radius * 0.65
                    lx = cx + label_r * math.cos(math.radians(mid_angle))
                    ly = cy + label_r * math.sin(math.radians(mid_angle))
                    text_color = '#000' if c['brightness'] > 128 else '#fff'
                    svg_parts.append(f'<text x="{lx:.1f}" y="{ly:.1f}" fill="{text_color}" font-family="Arial" font-size="14" font-weight="bold" text-anchor="middle" dominant-baseline="middle">{c["fraction_pct"]:.1f}%</text>')
                start_angle = end_angle
            svg_parts.append('</svg>')
            svg_html = ''.join(svg_parts)
            st.markdown(f'<div style="display:flex; justify-content:center;">{svg_html}</div>', unsafe_allow_html=True)
            
            # Renk lejantı (pie altında)
            legend = '<div style="display:flex; flex-wrap:wrap; gap:8px; justify-content:center; margin-top:12px;">'
            for c in palette:
                legend += f'<div style="display:flex; align-items:center; gap:6px; font-size:14px;">'
                legend += f'<div style="background:{c["hex"]}; width:18px; height:18px; border:1px solid #888; border-radius:3px;"></div>'
                legend += f'<span><code>{c["hex"]}</code> {c["fraction_pct"]:.1f}%</span></div>'
            legend += '</div>'
            st.markdown(legend, unsafe_allow_html=True)
        
        # Tek-satır büyük palette bandı
        # Her bölüme hex+fraction yazılır; dar bölümlerde ellipsis ile kesilir,
        # imleç üstüne gelince native tooltip (title attribute) tam bilgiyi gösterir
        st.markdown('##### ' + T('pd_band'))
        band_html = '<div style="display:flex; height:72px; border-radius:8px; overflow:hidden; border:1px solid #888;">'
        for c in palette:
            txt_color = '#fff' if c['brightness'] < 128 else '#000'
            lab_str = ''
            if 'lab' in c:
                lab_str = f' | L*={c["lab"]["L"]:.1f} a*={c["lab"]["a"]:+.1f} b*={c["lab"]["b"]:+.1f}'
            munsell_str = f' | Munsell {c["munsell"]}' if 'munsell' in c else ''
            tooltip = f'{c["hex"]} | RGB({c["rgb"][0]},{c["rgb"][1]},{c["rgb"][2]}){lab_str}{munsell_str} | {c["fraction_pct"]:.2f}%'
            band_html += (
                f'<div title="{tooltip}" '
                f'style="background:{c["hex"]}; flex:{c["fraction_pct"]}; '
                f'display:flex; align-items:center; justify-content:center; '
                f'overflow:hidden; padding:0 4px; cursor:default;">'
                f'<span style="color:{txt_color}; font-size:14px; font-weight:600; '
                f'white-space:nowrap; overflow:hidden; text-overflow:ellipsis; '
                f'max-width:100%; text-align:center;">'
                f'{c["hex"]}</span></div>'
            )
        band_html += '</div>'
        st.markdown(band_html, unsafe_allow_html=True)
        st.caption(T('pd_band_hint'))
        
        # Export
        st.markdown('---')
        st.markdown('##### ' + T('pd_download'))
        ec1, ec2, ec3 = st.columns(3)
        
        # CSV
        with ec1:
            csv_buf = pal_df.to_csv(index=False).encode('utf-8')
            st.download_button('📊 CSV', csv_buf, 
                                file_name=f'palette_{meta.get("source_image","custom")}.csv',
                                mime='text/csv', use_container_width=True)
        
        # JSON
        with ec2:
            import json
            json_str = json.dumps({
                'meta': meta,
                'colors': palette
            }, ensure_ascii=False, indent=2)
            st.download_button('🗂️ JSON', json_str.encode('utf-8'),
                                file_name=f'palette_{meta.get("source_image","custom")}.json',
                                mime='application/json', use_container_width=True)
        
        # PNG (palette band image)
        with ec3:
            from io import BytesIO
            from PIL import Image as PILImage
            band_img = PILImage.new('RGB', (1200, 200), (255,255,255))
            x = 0
            total = sum(c['fraction_pct'] for c in palette)
            for c in palette:
                w_pixel = int(1200 * c['fraction_pct'] / total)
                if w_pixel < 1: w_pixel = 1
                strip = PILImage.new('RGB', (w_pixel, 200), tuple(c['rgb']))
                band_img.paste(strip, (x, 0))
                x += w_pixel
            png_buf = BytesIO()
            band_img.save(png_buf, format='PNG')
            st.download_button('🖼️ PNG band', png_buf.getvalue(),
                                file_name=f'palette_band_{meta.get("source_image","custom")}.png',
                                mime='image/png', use_container_width=True)

        # ─────────────────────────────────────────────────────
        # ΔE Renk Karşılaştırma
        # ─────────────────────────────────────────────────────
        st.markdown('---')
        st.markdown('##### ' + T('de_title'))
        st.caption(T('de_caption'))
        
        # Palette renkleri + custom RGB inputu seçenekleri
        delta_options = [T('de_pick_from_palette')] + [f'{i+1}. {c["hex"]} ({c.get("fraction_pct",0):.1f}%)' for i,c in enumerate(palette)]
        
        dc1, dc2 = st.columns(2)
        with dc1:
            st.markdown('**' + T('de_color_a') + '**')
            color_a_choice = st.selectbox(T('de_pick'), delta_options, index=1, key='delta_color_a')
            if color_a_choice == T('de_pick_from_palette'):
                color_a_hex = st.color_picker('Custom A', '#1b1a13', key='delta_a_custom')
                color_a_rgb = utils.hex_to_rgb(color_a_hex)
            else:
                idx_a = int(color_a_choice.split('.')[0]) - 1
                color_a_rgb = palette[idx_a]['rgb']
                color_a_hex = palette[idx_a]['hex']
            # Renk önizleme
            st.markdown(f'<div style="background:{color_a_hex};width:100%;height:60px;border:2px solid #888;border-radius:6px;display:flex;align-items:center;justify-content:center;color:{"#fff" if sum(color_a_rgb)/3<128 else "#000"};font-weight:600;">{color_a_hex}</div>', unsafe_allow_html=True)
        
        with dc2:
            st.markdown('**' + T('de_color_b') + '**')
            color_b_choice = st.selectbox(T('de_pick'), delta_options, index=min(len(palette), 2) if len(palette)>=2 else 1, key='delta_color_b')
            if color_b_choice == T('de_pick_from_palette'):
                color_b_hex = st.color_picker('Custom B', '#e9caa2', key='delta_b_custom')
                color_b_rgb = utils.hex_to_rgb(color_b_hex)
            else:
                idx_b = int(color_b_choice.split('.')[0]) - 1
                color_b_rgb = palette[idx_b]['rgb']
                color_b_hex = palette[idx_b]['hex']
            st.markdown(f'<div style="background:{color_b_hex};width:100%;height:60px;border:2px solid #888;border-radius:6px;display:flex;align-items:center;justify-content:center;color:{"#fff" if sum(color_b_rgb)/3<128 else "#000"};font-weight:600;">{color_b_hex}</div>', unsafe_allow_html=True)
        
        # ΔE hesapla
        try:
            de76 = cs.delta_e_76(color_a_rgb, color_b_rgb)
            de94 = cs.delta_e_94(color_a_rgb, color_b_rgb)
            de2k = cs.delta_e_2000(color_a_rgb, color_b_rgb)
            interp = cs.interpret_delta_e(de2k)
            
            st.markdown('')
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric('ΔE-76 (CIE 1976)', f'{de76:.2f}', help=T('de_help_76'))
            mc2.metric('ΔE-94 (CIE 1994)', f'{de94:.2f}', help=T('de_help_94'))
            mc3.metric('ΔE-2000 (modern)', f'{de2k:.2f}', help=T('de_help_2k'))
            
            # Yorum
            if de2k < 1: color_box = '#22c55e'
            elif de2k < 3.5: color_box = '#3b82f6'
            elif de2k < 5: color_box = '#eab308'
            elif de2k < 10: color_box = '#f97316'
            else: color_box = '#ef4444'
            
            st.markdown(
                f'<div style="background:{color_box}22; border-left:4px solid {color_box}; '
                f'padding:12px 16px; border-radius:4px; margin-top:8px;">'
                f'<b>{T("de_visual_interp")}:</b> {translate_cs(interp)}'
                f'</div>',
                unsafe_allow_html=True)
            
            # Detay: Lab değerleri yan yana
            with st.expander(T('de_detail_expander')):
                L_a, a_a, b_a = cs.rgb_to_lab(color_a_rgb)
                L_b, a_b, b_b = cs.rgb_to_lab(color_b_rgb)
                _, C_a, h_a = cs.lab_to_lch(L_a, a_a, b_a)
                _, C_b, h_b = cs.lab_to_lch(L_b, a_b, b_b)
                detail_df = pd.DataFrame({
                    T('de_metric_col'): ['L* (Lightness)', 'a* (Green-Red)', 'b* (Blue-Yellow)', 
                                'C* (Chroma)', 'h° (Hue angle)', 'Munsell'],
                    T('de_color_a'): [f'{L_a:.2f}', f'{a_a:+.2f}', f'{b_a:+.2f}',
                                 f'{C_a:.2f}', f'{h_a:.1f}°',
                                 cs.lab_to_munsell_approx(L_a, a_a, b_a)],
                    T('de_color_b'): [f'{L_b:.2f}', f'{a_b:+.2f}', f'{b_b:+.2f}',
                                 f'{C_b:.2f}', f'{h_b:.1f}°',
                                 cs.lab_to_munsell_approx(L_b, a_b, b_b)],
                    'Δ': [f'{L_b-L_a:+.2f}', f'{a_b-a_a:+.2f}', f'{b_b-b_a:+.2f}',
                            f'{C_b-C_a:+.2f}', f'{h_b-h_a:+.1f}°', '-'],
                })
                st.dataframe(detail_df, use_container_width=True, hide_index=True)
                
                st.caption(T('de_scale_hint'))
        except Exception as e:
            st.error(f'{T("de_error")}: {e}')
        
        # ─────────────────────────────────────────────────────
        # 📐 RENK HOMOJENLİĞİ ANALİZİ (Seviye 4)
        # ─────────────────────────────────────────────────────
        st.markdown('---')
        st.markdown('##### ' + T('uni_title'))
        st.caption(T('uni_caption'))
        
        if st.session_state.image_rgb is not None:
            uni_sample_size = st.select_slider(T('uni_sample_size'), 
                                                  options=[5000, 10000, 20000, 50000, 100000],
                                                  value=20000, key='uni_sample',
                                                  help=T('uni_sample_help'))
            
            if st.button(T('uni_compute_btn'), use_container_width=True, key='compute_uni'):
                with st.spinner(T('computing')):
                    try:
                        u = cs.compute_uniformity(st.session_state.image_rgb, sample_size=uni_sample_size)
                        st.session_state.uniformity_result = u
                    except Exception as e:
                        st.error(f'{T("uni_error")}: {e}')
            
            if 'uniformity_result' in st.session_state and st.session_state.uniformity_result:
                u = st.session_state.uniformity_result
                
                # Üst sıra: ana metrikler
                um1, um2, um3 = st.columns([1.5, 1, 1])
                with um1:
                    # Mean color swatch
                    st.markdown('**' + T('uni_mean_color') + '**')
                    st.markdown(
                        f'<div style="background:{u["mean_color_hex"]}; '
                        f'width:100%; height:80px; border:2px solid #888; '
                        f'border-radius:8px; display:flex; align-items:center; '
                        f'justify-content:center; color:{"#fff" if u["mean_L"]<55 else "#000"}; '
                        f'font-weight:600; font-size:16px;">'
                        f'{u["mean_color_hex"]}'
                        f'</div>', unsafe_allow_html=True)
                with um2:
                    st.metric(T('uni_score'), f'{u["homogeneity_score_0_10"]:.1f}/10')
                with um3:
                    # Class olarak göster
                    st.markdown('**' + T('uni_classification') + '**')
                    st.markdown(f'<div style="padding:8px 12px; background:#1f2937; border-radius:6px; text-align:center; font-size:14px; margin-top:8px;">{translate_cs(u["uniformity_class"])}</div>', unsafe_allow_html=True)
                
                # Lab istatistikleri
                st.markdown('**' + T('uni_lab_stats') + '**')
                stats_df = pd.DataFrame({
                    T('uni_col_channel'): ['L* (Lightness)', 'a* (Green-Red)', 'b* (Blue-Yellow)'],
                    T('uni_col_mean'): [u['mean_L'], u['mean_a'], u['mean_b']],
                    T('uni_col_std'): [u['std_L'], u['std_a'], u['std_b']],
                    T('uni_col_interp'): [
                        T('uni_interp_L_var') if u['std_L'] > 8 else T('uni_interp_L_uniform'),
                        T('uni_interp_a_var') if u['std_a'] > 4 else T('uni_interp_a_uniform'),
                        T('uni_interp_b_var') if u['std_b'] > 4 else T('uni_interp_b_uniform'),
                    ],
                })
                st.dataframe(stats_df, use_container_width=True, hide_index=True)
                
                # ΔE-2000 istatistikleri
                st.markdown('**' + T('uni_de_dist') + '**')
                de1, de2, de3, de4 = st.columns(4)
                de1.metric(T('uni_de_avg'), f'{u["delta_e_avg_from_mean"]:.2f}')
                de2.metric(T('uni_de_std'), f'{u["delta_e_std"]:.2f}')
                de3.metric(T('uni_de_p95'), f'{u["delta_e_p95"]:.2f}', help=T('uni_de_p95_help'))
                de4.metric(T('uni_de_max'), f'{u["delta_e_max"]:.2f}', help=T('uni_de_max_help'))
                
                # Bilimsel yorumlama bloğu
                interp_text = ""
                if u['homogeneity_score_0_10'] >= 8:
                    interp_text = T('uni_interp_high')
                    interp_color = '#22c55e'
                elif u['homogeneity_score_0_10'] >= 6:
                    interp_text = T('uni_interp_mid')
                    interp_color = '#3b82f6'
                else:
                    interp_text = T('uni_interp_low')
                    interp_color = '#eab308'
                
                st.markdown(
                    f'<div style="background:{interp_color}22; border-left:4px solid {interp_color}; '
                    f'padding:12px 16px; border-radius:4px; margin-top:8px;">'
                    f'<b>{T("uni_sci_interp")}:</b> {interp_text}'
                    f'</div>', unsafe_allow_html=True)
                
                # Pre/Post karşılaştırma kaydetme
                st.markdown('---')
                save_col1, save_col2 = st.columns(2)
                with save_col1:
                    if st.button(T('uni_save_pre'), use_container_width=True):
                        st.session_state.uniformity_pre = u
                        st.success(T('uni_saved_pre'))
                with save_col2:
                    if st.button(T('uni_save_post'), use_container_width=True):
                        if 'uniformity_pre' in st.session_state:
                            comp = cs.compare_uniformity(st.session_state.uniformity_pre, u)
                            st.session_state.uniformity_compare = comp
                        else:
                            st.warning(T('uni_warn_pre'))
                
                # Karşılaştırma sonucu
                if 'uniformity_compare' in st.session_state and st.session_state.uniformity_compare:
                    comp = st.session_state.uniformity_compare
                    st.markdown('**' + T('uni_compare_title') + '**')
                    cc1, cc2, cc3 = st.columns(3)
                    cc1.metric('Δ Mean L*', f'{comp["delta_mean_L"]:+.2f}')
                    cc2.metric('Δ Homogeneity', f'{comp["delta_homogeneity"]:+.2f}')
                    cc3.metric('Mean Color ΔE-2000', f'{comp["mean_color_delta_e_2000"]:.2f}',
                                help=translate_cs(comp['mean_color_interpretation']))
                    st.caption(f'**{T("uni_damage_interp")}:** {translate_cs(comp["mean_color_interpretation"])}')
                
                # JSON export
                with st.expander(T('uni_json_expander')):
                    import json as _json
                    uni_json = safe_json_dumps(u, ensure_ascii=False, indent=2)
                    st.download_button('🗂️ uniformity.json', uni_json.encode('utf-8'),
                                        file_name=f'uniformity_{meta.get("source_image","custom")}.json',
                                        mime='application/json', use_container_width=True)
        else:
            st.info(T('uni_need_image'))

# ============================================================
# AGING ANALIZI Ana Panel Sonuclar
# ============================================================
if app_mode == 'aging' and 'aging_results' in st.session_state and st.session_state.aging_results:
    st.divider()
    with st.expander(T('aging_results_title'), expanded=True):
        ar = st.session_state.aging_results
        pairs = ar['pairs']
        agg = ar['aggregate']
        n = agg['n']
        
        st.caption(T('aging_n_samples').format(n=n, method=str(ar['method'])))
        
        # Genel ozet
        st.markdown(T('general_summary'))
        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric(T('metric_mean_dE'), '{:.2f} +/- {:.2f}'.format(agg['delta_e']['mean'], agg['delta_e']['std']))
        sc2.metric(T('metric_minmax_dE'), '{:.2f} / {:.2f}'.format(agg['delta_e']['min'], agg['delta_e']['max']))
        sc3.metric(T('metric_mean_dL'), '{:+.2f}'.format(agg['delta_L']['mean']))
        sc4.metric(T('metric_cv_dE'), '%{:.0f}'.format(agg['delta_e']['cv_pct']))
        
        # Per-pair tablo
        st.markdown(T('per_sample_table'))
        pair_rows = []
        for i, p in enumerate(pairs):
            pair_rows.append({
                '#': i+1, T('col_sample'): p['sample_name'][:25],
                'Pre': p['pre_color_hex'], 'Post': p['post_color_hex'],
                'dL*': p['delta_L'], 'da*': p['delta_a'], 'db*': p['delta_b'],
                'dC*': p['delta_C'], 'dH*': p['delta_H'], 'dE': p['delta_e'],
                T('col_class'): translate_cs(p['classification']),
            })
        pair_df = pd.DataFrame(pair_rows)
        st.dataframe(pair_df, use_container_width=True, hide_index=True)
        
        # Swatch grid
        st.markdown(T('color_compare_section'))
        swatch_parts = ['<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:12px;">']
        for p in pairs:
            if p['delta_e']<1: dc='#22c55e'
            elif p['delta_e']<3.5: dc='#3b82f6'
            elif p['delta_e']<5: dc='#eab308'
            elif p['delta_e']<10: dc='#f97316'
            else: dc='#ef4444'
            pre_txt = '#fff' if p['pre_L']<55 else '#000'
            post_txt = '#fff' if p['post_L']<55 else '#000'
            swatch_parts.append(
                '<div style="border:1px solid #444; border-radius:8px; overflow:hidden;">'
                '<div style="display:flex; height:80px;">'
                '<div style="background:' + p['pre_color_hex'] + '; flex:1; display:flex; align-items:center; justify-content:center; color:' + pre_txt + '; font-size:14px; font-weight:600;">PRE</div>'
                '<div style="background:' + p['post_color_hex'] + '; flex:1; display:flex; align-items:center; justify-content:center; color:' + post_txt + '; font-size:14px; font-weight:600;">POST</div>'
                '</div>'
                '<div style="padding:8px; background:#1f2937; color:#fff; font-size:12px;">'
                '<b>' + p['sample_name'][:22] + '</b><br>'
                '<span style="color:' + dc + '; font-weight:700;">dE = ' + '{:.2f}'.format(p['delta_e']) + '</span> | dL=' + '{:+.1f}'.format(p['delta_L']) + '</div></div>'
            )
        swatch_parts.append('</div>')
        st.markdown(''.join(swatch_parts), unsafe_allow_html=True)
        
        # Bar chart SVG
        st.markdown(T('bar_chart_section'))
        bar_w = 700
        bar_h = max(180, 35 * n + 60)
        max_de = max(p['delta_e'] for p in pairs) * 1.15 + 1
        left_margin = 160; right_margin = 50
        plot_w = bar_w - left_margin - right_margin
        bar_h_each = (bar_h - 50) / n
        svg = ['<svg width="' + str(bar_w) + '" height="' + str(bar_h) + '" xmlns="http://www.w3.org/2000/svg">']
        for thresh, tcolor in [(1,'#22c55e'),(3.5,'#eab308'),(5,'#f97316'),(10,'#ef4444')]:
            if thresh > max_de: continue
            x = left_margin + plot_w * thresh / max_de
            svg.append('<line x1="' + str(x) + '" y1="25" x2="' + str(x) + '" y2="' + str(bar_h-25) + '" stroke="' + tcolor + '" stroke-width="1" stroke-dasharray="3,3" opacity="0.5"/>')
            svg.append('<text x="' + str(x) + '" y="18" fill="' + tcolor + '" font-size="11" text-anchor="middle">' + str(thresh) + '</text>')
        for i, p in enumerate(pairs):
            y = 35 + i * bar_h_each
            bar_len = plot_w * p['delta_e'] / max_de
            if p['delta_e']<1: dc='#22c55e'
            elif p['delta_e']<3.5: dc='#3b82f6'
            elif p['delta_e']<5: dc='#eab308'
            elif p['delta_e']<10: dc='#f97316'
            else: dc='#ef4444'
            svg.append('<text x="' + str(left_margin-10) + '" y="' + str(y+bar_h_each/2+4) + '" fill="#aaa" font-size="12" text-anchor="end">' + p['sample_name'][:20] + '</text>')
            svg.append('<rect x="' + str(left_margin) + '" y="' + str(y) + '" width="' + str(bar_len) + '" height="' + str(bar_h_each-8) + '" fill="' + dc + '" rx="3"/>')
            svg.append('<text x="' + str(left_margin+bar_len+5) + '" y="' + str(y+bar_h_each/2+4) + '" fill="#fff" font-size="12" font-weight="600">' + '{:.2f}'.format(p['delta_e']) + '</text>')
        mean_x = left_margin + plot_w * agg['delta_e']['mean'] / max_de
        svg.append('<line x1="' + str(mean_x) + '" y1="25" x2="' + str(mean_x) + '" y2="' + str(bar_h-25) + '" stroke="#fff" stroke-width="2"/>')
        svg.append('<text x="' + str(mean_x) + '" y="' + str(bar_h-5) + '" fill="#fff" font-size="12" text-anchor="middle">mean=' + '{:.2f}'.format(agg['delta_e']['mean']) + '</text>')
        svg.append('</svg>')
        st.markdown(''.join(svg), unsafe_allow_html=True)
        st.caption(T('bar_chart_caption'))
        
        # Istatistik 4 sekme
        st.markdown(T('stat_analysis_section'))
        tab_dE, tab_L, tab_a, tab_b = st.tabs(['dE-2000', 'dL* Lightness', 'da* Green-Red', 'db* Blue-Yellow'])
        
        def render_stat(t):
            if 'error' in t:
                st.warning(t['error']); return
            tc1, tc2, tc3, tc4 = st.columns(4)
            tc1.metric(T('stat_test_label'), t['test_name'].split('(')[0].strip() if t.get('test_name') else '-')
            p_val = t.get('p_value')
            p_disp = '<0.001' if p_val and p_val < 0.001 else ('{:.4f}'.format(p_val) if p_val else '-')
            tc2.metric(T('stat_pvalue'), p_disp, T('stat_significant') if t.get('is_significant') else (T('stat_nonsignificant') if t.get('is_significant') is not None else None))
            tc3.metric(T('stat_cohen_d'), '{:.2f}'.format(t['cohen_d']) if t.get('cohen_d') else '-',
                       t.get('cohen_d_interpretation','').split(' (')[0])
            ci_str = '[{:.2f}, {:.2f}]'.format(t['ci_95_low'], t['ci_95_high']) if t.get('ci_95_low') is not None else '-'
            tc4.metric(T('stat_ci'), ci_str)
            st.markdown('**Test:** ' + str(t.get('test_name','-')) + ' | stat=`' + str(t.get('test_statistic','-')) + '`')
            normal_str = T('stat_normal_yes') if t.get('is_normal_distribution') else T('stat_normal_no')
            st.markdown('**Shapiro-Wilk p:** `' + str(t.get('normality_shapiro_p','-')) + '` -> ' + normal_str)
            st.markdown('**' + T('ag_mean_diff') + ':** `' + str(t.get('mean_diff','-')) + '` +/- `' + str(t.get('std_diff','-')) + '`')
        
        with tab_dE: render_stat(ar['stat_test_dE'])
        with tab_L:  render_stat(ar['stat_test_L'])
        with tab_a:  render_stat(ar['stat_test_a'])
        with tab_b:  render_stat(ar['stat_test_b'])
        
        # Otomatik yorum
        st.markdown('##### ' + T('ag_auto_interp_hdr'))
        interp = aa.auto_interpret(agg, ar['stat_test_dE'])
        if interp['damage_severity']=='minimal': damage_color='#22c55e'
        elif 'hafif' in interp['damage_severity']: damage_color='#3b82f6'
        elif 'orta' in interp['damage_severity']: damage_color='#eab308'
        elif 'belirgin' in interp['damage_severity']: damage_color='#f97316'
        else: damage_color='#ef4444'
        st.markdown('<div style="background:' + damage_color + '22; border-left:4px solid ' + damage_color + '; padding:12px 16px; border-radius:4px; margin:8px 0;"><b>' + T('label_tr_discussion') + '</b><br>' + interp['summary_tr'] + '</div>', unsafe_allow_html=True)
        st.markdown('<div style="background:#1f2937; border-left:4px solid #6366f1; padding:12px 16px; border-radius:4px; margin:8px 0; color:#fff;"><b>' + T('label_en_paper_ready') + '</b><br>' + interp['paper_ready_en'] + '</div>', unsafe_allow_html=True)
        
        # Export
        st.markdown('---')
        st.markdown(T('download_options'))
        ec1, ec2, ec3, ec4 = st.columns(4)
        with ec1:
            st.download_button(T('btn_per_pair_csv'), pair_df.to_csv(index=False).encode('utf-8'),
                file_name='aging_per_pair.csv', mime='text/csv', use_container_width=True)
        with ec2:
            import json as _json
            full_json = safe_json_dumps({'pairs':pairs,'aggregate':agg,
                'statistics':{'dE':ar['stat_test_dE'],'L*':ar['stat_test_L'],'a*':ar['stat_test_a'],'b*':ar['stat_test_b']},
                'interpretation':interp,
                'metadata':{'method':ar['method'],'depth':ar['depth'],'n':n}}, ensure_ascii=False, indent=2)
            st.download_button(T('btn_full_json'), full_json.encode('utf-8'),
                file_name='aging_full_results.json', mime='application/json', use_container_width=True)
        with ec3:
            md_lines = [
                '# Aging Analysis Report', '',
                '**N:** ' + str(n) + ' samples',
                '**Method:** ' + str(ar['method']),
                '**Generated:** ' + datetime.now().strftime('%Y-%m-%d %H:%M'),
                '', '## Summary', '',
                '- dE mean +/- std: {:.2f} +/- {:.2f}'.format(agg['delta_e']['mean'], agg['delta_e']['std']),
                '- dE range: {:.2f} to {:.2f}'.format(agg['delta_e']['min'], agg['delta_e']['max']),
                '- dL* mean: {:+.2f}'.format(agg['delta_L']['mean']),
                '', '## Paper-Ready Sentence', '', interp['paper_ready_en'],
                '', '## Per-Sample', '', 
                '| ' + ' | '.join(str(c) for c in pair_df.columns) + ' |',
                '|' + '|'.join('---' for _ in pair_df.columns) + '|',
            ] + ['| ' + ' | '.join(str(v) for v in row) + ' |' for row in pair_df.values.tolist()] + [
            ]
            st.download_button(T('btn_md_report'), '\n'.join(md_lines).encode('utf-8'),
                file_name='aging_report.md', mime='text/markdown', use_container_width=True)
        with ec4:
            para_lines = ['COLOR CHANGE ANALYSIS','','TURKISH:', interp['summary_tr'],'',
                'ENGLISH (paper-ready):', interp['paper_ready_en'],'','---','Stats:',
                '- N=' + str(n),
                '- Test: ' + str(ar['stat_test_dE'].get('test_name','-')),
                '- p = ' + str(ar['stat_test_dE'].get('p_value','-'))]
            if ar['stat_test_dE'].get('ci_95_low') is not None:
                para_lines.append('- 95% CI: [{:.2f}, {:.2f}]'.format(ar['stat_test_dE']['ci_95_low'], ar['stat_test_dE']['ci_95_high']))
            if ar['stat_test_dE'].get('cohen_d') is not None:
                para_lines.append('- Cohen d = {:.2f} ({})'.format(ar['stat_test_dE']['cohen_d'], ar['stat_test_dE'].get('cohen_d_interpretation','-')))
            st.download_button('Paragraf TXT', '\n'.join(para_lines).encode('utf-8'),
                file_name='aging_paragraph.txt', mime='text/plain', use_container_width=True)

# ============================================================
# KOLAJ Ana Panel — preview + render + download
# ============================================================
if app_mode == 'collage':
    # Bos durum mesaji
    if 'collage_result' not in st.session_state or st.session_state.collage_result is None:
        st.info(('👈 From the left **Collage Builder** tab, upload images and configure settings.'
                  if st.session_state.get('lang','en')=='en'
                  else '👈 Soldan **Kolaj Oluşturucu** sekmesinden görüntüleri yükle ve ayarları yap.'))
        st.markdown(T('collage_quickstart_md'))
    else:
        st.divider()
        with st.expander(T('collage_panel_title'), expanded=True):
            collage = st.session_state.collage_result
            meta = st.session_state.collage_meta
            
            cs_info = T('collage_cell_auto').format(meta.get('cell_size_px','?')) if meta.get('auto_fit') else T('collage_cell_manual').format(meta.get('cell_size_px','?'))
            st.caption(T('collage_meta_line').format(
                collage.size[0], collage.size[1], cs_info,
                meta.get('target_w_cm', '?'), meta.get('dpi', 300)))
            
            # Preview
            preview_max = 900
            preview = utils.resize_for_display(np.array(collage), preview_max)
            st.image(preview, caption=T('collage_preview_cap'), width='stretch')
            
            # Auto caption
            st.markdown('##### ' + T('collage_autocap_title'))
            ctx_map = {
                'general': 'general',
                'pore_segmentation': 'pore_segmentation',
                'aging': 'aging',
                'algorithm_comparison': 'algorithm_comparison',
            }
            cap_context = st.selectbox(T('collage_context'), 
                ['general', 'pore_segmentation', 'aging', 'algorithm_comparison'],
                index=0, key='collage_caption_ctx')
            
            cap = cb.auto_caption(
                meta['rows'], meta['cols'],
                col_headers=meta.get('col_headers'),
                context=cap_context)
            
            st.text_area(T('collage_caption_edit'), value=cap['en'], height=120, key='collage_caption_edit')
            
            # İndirme — multi-format
            st.markdown('---')
            st.markdown('##### ' + T('collage_formats_title'))
            
            ec1, ec2, ec3, ec4 = st.columns(4)
            target_w = meta.get('target_w_cm', 17.5)
            dpi_val = meta.get('dpi', 300)
            
            with ec1:
                png_data = cb.export_collage(collage, format='PNG', dpi=dpi_val, target_width_cm=target_w)
                st.download_button(f'📊 PNG ({dpi_val}dpi)', png_data,
                    file_name='kolaj.png', mime='image/png',
                    use_container_width=True, type='primary')
                st.caption('{:.1f} KB'.format(len(png_data)/1024))
            with ec2:
                pdf_data = cb.export_collage(collage, format='PDF', dpi=dpi_val, target_width_cm=target_w)
                st.download_button('📄 PDF', pdf_data,
                    file_name='kolaj.pdf', mime='application/pdf',
                    use_container_width=True)
                st.caption('{:.1f} KB'.format(len(pdf_data)/1024))
            with ec3:
                svg_data = cb.export_collage(collage, format='SVG', dpi=dpi_val, target_width_cm=target_w)
                st.download_button('🎨 SVG', svg_data,
                    file_name='kolaj.svg', mime='image/svg+xml',
                    use_container_width=True)
                st.caption('{:.1f} KB'.format(len(svg_data)/1024))
            with ec4:
                tiff_data = cb.export_collage(collage, format='TIFF', dpi=dpi_val, target_width_cm=target_w)
                st.download_button('📑 TIFF (LZW)', tiff_data,
                    file_name='kolaj.tiff', mime='image/tiff',
                    use_container_width=True)
                st.caption('{:.1f} KB'.format(len(tiff_data)/1024))

# ============================================================
# ALT BİLGİ
# ============================================================
st.divider()
st.caption(T('footer_text'))
