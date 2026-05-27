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

from modules import segmentation, filters, utils, palettes, presets, color_science as cs, aging_analysis as aa


# ============================================================
# SAYFA AYARLARI
# ============================================================
st.set_page_config(
    page_title='Gözenek & Renk Tespit Yazılımı',
    page_icon='🪨',
    layout='wide',
)


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

st.title('🪨 Gözenek ve Renk Tespit Yazılımı')
st.caption('Travertenler için interaktif segmentasyon — DoG / MSER / Sauvola / Color-Distance + per-stone renk paleti')


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
    # ─── ÜST BRANDING ──────────────────────────────
    st.markdown("""
    <div style="text-align:center; padding:12px 4px; margin-bottom:8px;
                border-bottom:1px solid #444; border-radius:4px;">
        <div style="font-size:18px; font-weight:600;">🪨 Gözenek & Renk Tespit</div>
        <div style="color:#888; font-size:12px; margin-top:2px;">v1.0 — Travertin Analizi</div>
    </div>
    """, unsafe_allow_html=True)
    
    # =============================================================
    # 📊 ANALİZE BAŞLA — ana iş akışı
    # =============================================================
    with st.expander('📊  **Analize Başla**', expanded=True):
        
        # ──────────── 1. GÖRÜNTÜ ────────────
        st.markdown('##### 📂 Görüntü Yükle')
        
        upload_mode = st.radio('Kaynak', ['📤 Dosya yükle', '📁 Klasörden seç'], 
                                 horizontal=True, label_visibility='collapsed')
        
        uploaded_file = None
        if upload_mode == '📤 Dosya yükle':
            uploaded_file = st.file_uploader('Travertin yüzey görüntüsü', 
                                              type=['jpg','jpeg','png','tif','tiff','bmp'],
                                              label_visibility='collapsed')
            if uploaded_file:
                st.session_state.image_rgb = utils.load_image(uploaded_file)
                st.session_state.image_name = uploaded_file.name
        else:
            folder = st.text_input('Klasör yolu', value=os.path.expanduser('~'))
            if folder and os.path.isdir(folder):
                imgs = sorted([f for f in os.listdir(folder) 
                              if f.lower().endswith(('.jpg','.jpeg','.png','.tif','.tiff','.bmp'))])
                if imgs:
                    pick = st.selectbox('Görüntü seç', imgs)
                    if pick:
                        full = os.path.join(folder, pick)
                        if st.button('🔄 Yükle', use_container_width=True):
                            st.session_state.image_rgb = utils.load_image(full)
                            st.session_state.image_name = pick
                else:
                    st.warning('Klasörde görüntü yok.')
        
        st.markdown('---')
        
        # ──────────── 2. TAŞ & PALET ────────────
        st.markdown('##### 🪨 Taş Tipi & Renk Paleti')
        
        available_palettes = palettes.list_palettes()
        stone_options = available_palettes + ['Custom (yeni)']
        selected_stone = st.selectbox('Taş kodu', stone_options, key='stone_select',
                                       label_visibility='collapsed')
        
        if selected_stone != 'Custom (yeni)' and (st.session_state.palette_data is None or 
                                                    st.session_state.palette_data.get('stone_code') != selected_stone):
            st.session_state.palette_data = palettes.load_palette(selected_stone)
            st.session_state.selected_pore_indices = list(st.session_state.palette_data.get('pore_candidate_indices', [0,1]))
        
        # Yeni palet hesaplama
        if st.session_state.image_rgb is not None:
            if st.button('🔄 Bu görüntüden K-means palet hesapla', use_container_width=True):
                with st.spinner('Hesaplanıyor...'):
                    colors = segmentation.extract_palette_kmeans(st.session_state.image_rgb, n_clusters=7)
                    st.session_state.palette_data = {
                        'stone_code': selected_stone if selected_stone != 'Custom (yeni)' else 'CUSTOM',
                        'stone_name': st.session_state.image_name or 'Custom',
                        'n_clusters': 7,
                        'colors': colors,
                        'source': 'K-means from current image',
                        'pore_candidate_indices': [0, 1],
                    }
                    st.session_state.selected_pore_indices = [0, 1]
                    st.success('Palet güncellendi.')
        
        # Palet gösterimi + checkbox'lar
        if st.session_state.palette_data:
            st.caption(f'**{st.session_state.palette_data.get("stone_name", "")}** — {st.session_state.palette_data["n_clusters"]} dominant renk')
            
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
                    role = '🕳️ pore' if checked else ('☁️ matriks' if c['brightness']>120 else '?')
                    st.caption(f'`{c["hex"]}` ({c["fraction_pct"]:.1f}%) {role}')
            st.session_state.selected_pore_indices = new_selected
        
        # Custom pore colors (görüntüden eklenmiş)
        if st.session_state.custom_pore_colors:
            st.caption('**Görüntüden eklenen renkler:**')
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
        st.markdown('##### 🔧 Algoritma')
        algo_categories = {
            '🔵 Klasik Eşikleme': [
                'Sauvola (Adaptive Threshold)',
                'Multi-Otsu (Auto Multi-level)',
                'Auto Threshold (Triangle/Yen/Otsu)',
            ],
            '🟢 Blob/Region Detection': [
                'DoG (Difference of Gaussians)',
                'MSER (Extremal Regions)',
                'Bottom-Hat Morphology',
                'Frangi Vesselness',
                'Watershed (Marker-Controlled)',
            ],
            '🟣 Renk/Clustering Tabanlı': [
                'Color Distance (Renk Mesafesi)',
                'GMM (Gaussian Mixture)',
            ],
            '🤝 Hibrit (Klasik + Renk)': [
                'DoG + Color Filter',
                'MSER + Color Filter',
            ],
            '🚀 Modern Deep Learning': [
                'SAM 2 (Segment Anything, Meta 2024)',
                'CellPose 3 (Pretrained)',
            ],
        }
        category = st.selectbox(
            'Yöntem',
            list(algo_categories.keys()),
            help='Yaklaşım ailesi: klasik eşikleme, blob tespiti, renk-tabanlı, hibrit veya modern derin öğrenme.')
        algo = st.selectbox(
            'Algoritma',
            algo_categories[category],
            help='Seçtiğin yöntem ailesindeki spesifik algoritma. Aşağıdaki sliderlar bu algoritmaya özgüdür.')
        
        params = {}
        
        # DoG
        if 'DoG' in algo and 'Color' not in algo or algo == 'DoG + Color Filter':
            st.caption('**DoG Parametreleri**')
            params['multiscale'] = st.checkbox('Multi-scale (3 ölçek union)', value=False)
            if not params['multiscale']:
                params['sigma1'] = st.slider('σ₁ (küçük ölçek)', 1, 10, 3)
                params['sigma2'] = st.slider('σ₂ (büyük ölçek)', 5, 30, 15)
            params['percentile'] = st.slider('Percentile (düşük = daha fazla pore)', 80, 99, 95)
        
        # MSER
        if 'MSER' in algo:
            st.caption('**MSER Parametreleri**')
            params['delta'] = st.slider('Delta (kararlılık)', 1, 10, 4)
            params['min_area'] = st.slider('Min alan (px)', 4, 100, 10)
            params['max_area'] = st.slider('Max alan (px)', 500, 10000, 3000)
        
        # Sauvola
        if 'Sauvola' in algo:
            st.caption('**Sauvola Parametreleri**')
            params['window_size'] = st.slider('Pencere boyutu', 11, 151, 51, step=10)
            params['k'] = st.slider('k', 0.05, 0.5, 0.20, step=0.05)
        
        # Color Distance (& hibrit)
        if 'Color Distance' in algo or 'Color Filter' in algo:
            st.caption('**Renk Mesafesi Parametreleri**')
            params['color_space'] = st.selectbox('Renk uzayı', ['lab', 'rgb', 'hsv'])
            params['max_distance'] = st.slider('Max renk mesafesi (Euclidean)', 5, 80, 25)
        
        # Multi-Otsu
        if 'Multi-Otsu' in algo:
            st.caption('**Multi-Otsu Parametreleri** (otomatik, parametresiz)')
            params['n_classes'] = st.slider('Sınıf sayısı', 2, 6, 3, 
                                              help='Histogram\'ı N seviyeye böler')
            params['dark_class_count'] = st.slider('En koyu kaç sınıfı pore say', 1, 
                                                      params.get('n_classes',3)-1, 1)
        
        # Auto Threshold
        if 'Auto Threshold' in algo:
            st.caption('**Otomatik Eşik** (sıfır parametre)')
            params['method'] = st.selectbox('Yöntem', 
                                              ['triangle','yen','isodata','otsu','mean','minimum'],
                                              help='triangle=histogram tepe-uzaklığı, yen=entropi, otsu=variance')
        
        # Bottom-Hat
        if 'Bottom-Hat' in algo:
            st.caption('**Bottom-Hat Morfoloji Parametreleri**')
            params['kernel_size'] = st.slider('Kernel boyutu (px)', 5, 81, 21, step=2)
            params['percentile'] = st.slider('Yanıt percentile (yüksek=daha az pore)', 80, 99, 90)
        
        # Frangi
        if 'Frangi' in algo:
            st.caption('**Frangi Vesselness** (uzamış/bağlantılı yapılar)')
            params['sigma_min'] = st.slider('σ_min', 1, 5, 1)
            params['sigma_max'] = st.slider('σ_max', 4, 20, 8)
            params['step'] = st.slider('σ adım', 1, 4, 2)
            params['dark'] = st.checkbox('Karanlık ridges', value=True)
            params['percentile'] = st.slider('Yanıt percentile', 80, 99, 90)
        
        # GMM
        if 'GMM' in algo:
            st.caption('**GMM Renk Kümeleme**')
            params['n_components'] = st.slider('Bileşen sayısı', 2, 7, 3)
            params['dark_component_count'] = st.slider('En koyu kaç bileşeni pore say', 1, 
                                                          params.get('n_components',3)-1, 1)
        
        # Watershed
        if 'Watershed' in algo:
            st.caption('**Watershed Parametreleri** (yapışık pore\'ları ayırır)')
            params['min_distance'] = st.slider('Min mesafe (px)', 5, 50, 10,
                                                  help='Local maxima arasındaki minimum mesafe')
            params['base_threshold'] = st.selectbox('Kaba eşik', ['otsu','triangle','multiotsu'])
        
        # SAM 2
        if 'SAM 2' in algo:
            sam_available = segmentation._check_sam2()
            if sam_available:
                st.caption('🚀 **SAM 2 (Meta 2024)** — zero-shot foundation model')
                params['model_name'] = st.selectbox('Model boyutu', 
                                                      ['sam2_t.pt (39MB, hızlı)', 
                                                       'sam2_s.pt (46MB)',
                                                       'sam2_b.pt (80MB, dengeli)',
                                                       'sam2_l.pt (224MB, en doğru)'])
                params['model_name'] = params['model_name'].split(' ')[0]
                params['mode'] = st.selectbox('Mod', ['auto','point'])
                st.info('İlk kullanımda model otomatik indirilir (~80MB).')
            else:
                st.error('⚠️ SAM 2 yüklü değil.')
                st.code('pip install ultralytics', language='bash')
                st.caption('Kurulumdan sonra uygulamayı yeniden başlat.')
        
        # CellPose
        if 'CellPose' in algo:
            cp_available = segmentation._check_cellpose()
            if cp_available:
                st.caption('🚀 **CellPose 3** — pretrained generalist segmenter')
                params['model_type'] = st.selectbox('Model', ['cyto3','cyto2','nuclei'])
                params['diameter'] = st.slider('Ortalama nesne çapı (px, 0=auto)', 0, 100, 0)
                if params['diameter'] == 0: params['diameter'] = None
                params['flow_threshold'] = st.slider('Flow threshold', 0.0, 1.0, 0.4, step=0.05)
                params['cellprob_threshold'] = st.slider('Cell probability threshold', -6.0, 6.0, 0.0, step=0.5)
            else:
                st.error('⚠️ CellPose yüklü değil.')
                st.code('pip install cellpose', language='bash')
                st.caption('Kurulumdan sonra uygulamayı yeniden başlat.')
        
        st.markdown('---')
        
        # ──────────── 4. YANLIŞ-POZİTİF FİLTRELERİ ────────────
        st.markdown('##### 🚫 Yanlış-Pozitif Filtreleri')
        f_params = {}
        f_params['min_area'] = st.slider('Min pore alanı (px)', 1, 200, 8)
        f_params['use_max_eccentricity'] = st.checkbox('Eccentricity filtresi (bantları reddet)', value=False)
        if f_params['use_max_eccentricity']:
            f_params['max_eccentricity'] = st.slider('Max eccentricity (1=çizgi, 0=daire)', 0.5, 1.0, 0.92, step=0.01)
        f_params['use_min_solidity'] = st.checkbox('Solidity filtresi (düzensiz şekilleri reddet)', value=False)
        if f_params['use_min_solidity']:
            f_params['min_solidity'] = st.slider('Min solidity (1=konveks, 0=düzensiz)', 0.0, 1.0, 0.55, step=0.05)
        f_params['use_max_interior_std'] = st.checkbox('Doku filtresi (fosil/mineralleri reddet)', value=False)
        if f_params['use_max_interior_std']:
            f_params['max_interior_std'] = st.slider('Max iç std (yüksek=dokulu, düşük=düz)', 5, 60, 25)
        f_params['must_be_dark'] = st.checkbox('Karanlık olmalı (median altı)', value=True)
        if f_params['must_be_dark']:
            f_params['dark_thresh_factor'] = st.slider('Karanlık eşik çarpanı', 0.5, 1.0, 0.95, step=0.05)
        
        st.markdown('---')
        
        # ──────────── 5. PRESET ────────────
        st.markdown('##### 💾 Preset Kaydet')
        preset_name = st.text_input('Preset adı', value='preset_1')
        preset_notes = st.text_area('Notlar', value='', height=60)
        if st.button('💾 Bu parametreleri kaydet', use_container_width=True):
            all_params = {'algorithm': algo, 'algo_params': params, 'filter_params': f_params,
                          'pore_color_indices': st.session_state.selected_pore_indices,
                          'custom_pore_colors': st.session_state.custom_pore_colors}
            metrics = st.session_state.last_result['metrics'] if st.session_state.last_result else None
            path = presets.save_preset(preset_name, selected_stone, algo.split(' ')[0], 
                                        all_params, metrics=metrics, notes=preset_notes)
            st.success(f'Kaydedildi: {os.path.basename(path)}')
    
    # =============================================================
    # 🎨 RENK YELPAZESİ — Standalone palet çıkarma
    # =============================================================
    with st.expander('🎨  **Renk Yelpazesi**', expanded=False):
        st.caption('Bir görüntüden dominant renkleri çıkarır (K-means tarzı kümeleme). Sonuç JSON palet olarak kaydedilebilir veya algoritmada kullanılabilir.')
        
        # Görüntü Kaynağı
        st.markdown('##### 📂 Kaynak Görüntü')
        pal_source = st.radio('Kaynak', 
                                ['🖼️ Yüklü görüntüyü kullan', '📤 Yeni görüntü yükle'],
                                key='palette_source', horizontal=False)
        
        pal_image = None
        if pal_source == '🖼️ Yüklü görüntüyü kullan':
            if st.session_state.image_rgb is not None:
                pal_image = st.session_state.image_rgb
                st.caption(f'✓ Aktif görüntü: **{st.session_state.image_name}**')
            else:
                st.warning('Önce Analize Başla sekmesinden görüntü yükle.')
        else:
            pal_upload = st.file_uploader('Görüntü dosyası', 
                                            type=['jpg','jpeg','png','tif','tiff','bmp'],
                                            key='palette_upload')
            if pal_upload:
                pal_image = utils.load_image(pal_upload)
                st.session_state.palette_source_name = pal_upload.name
        
        st.markdown('---')
        
        # Algoritma Ayarları
        st.markdown('##### ⚙️ Algoritma')
        pal_algo = st.selectbox(
            'Kümeleme algoritması',
            ['K-means (klasik)', 
             'MiniBatch K-means (hızlı)', 
             'GMM (probabilistik)',
             'MeanShift (otomatik küme sayısı)',
             'Median Cut (PIL klasik)'],
            help='K-means en yaygın. Median Cut görüntü kuantizasyonu için klasik. MeanShift küme sayısını kendi belirler.')
        algo_map = {
            'K-means (klasik)': 'kmeans',
            'MiniBatch K-means (hızlı)': 'minibatch_kmeans',
            'GMM (probabilistik)': 'gmm',
            'MeanShift (otomatik küme sayısı)': 'meanshift',
            'Median Cut (PIL klasik)': 'median_cut',
        }
        pal_algo_id = algo_map[pal_algo]
        
        if pal_algo_id != 'meanshift':
            pal_n = st.slider('Renk sayısı', 3, 15, 7, 
                                help='Görüntüden çıkarılacak dominant renk adedi')
        else:
            pal_n = None
        
        pal_space = st.selectbox(
            'Renk uzayı',
            ['Lab (perceptual - önerilen)', 'RGB', 'HSV'],
            help='Lab insan görüşüne yakın; RGB doğrudan; HSV hue/saturation ayrımı için iyi.')
        space_map = {
            'Lab (perceptual - önerilen)': 'lab',
            'RGB': 'rgb',
            'HSV': 'hsv',
        }
        pal_space_id = space_map[pal_space]
        
        pal_sample = st.select_slider(
            'Örnekleme boyutu (hız)',
            options=[5000, 10000, 30000, 50000, 100000, 'Tümü'],
            value=30000,
            help='Büyük görüntülerde sub-sampling hızı artırır')
        pal_sample_n = pal_image.shape[0]*pal_image.shape[1] if pal_sample == 'Tümü' and pal_image is not None else (pal_sample if pal_sample != 'Tümü' else 50000)
        
        # Hesapla Butonu
        if pal_image is not None:
            if st.button('🎨 Paleti Hesapla', use_container_width=True, type='primary'):
                with st.spinner('Hesaplanıyor...'):
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
                        st.success(f'✓ {len(result)} renk çıkarıldı')
                    except Exception as e:
                        st.error(f'Hata: {e}')
        else:
            st.info('Devam etmek için bir görüntü yükle.')
        
        # Kompakt Sonuç
        if 'computed_palette' in st.session_state and st.session_state.get('computed_palette'):
            st.markdown('---')
            st.markdown('##### 🎨 Çıkarılan Palet')
            
            for i, c in enumerate(st.session_state.computed_palette):
                cols = st.columns([0.5, 1.5, 3, 1])
                cols[0].markdown(f'**{i+1}**')
                cols[1].markdown(f'<div style="background:{c["hex"]};width:50px;height:25px;border:1px solid #888;border-radius:4px"></div>', 
                                  unsafe_allow_html=True)
                cols[2].caption(f'`{c["hex"]}` (RGB {tuple(c["rgb"])})')
                cols[3].caption(f'{c["fraction_pct"]:.1f}%')
            
            st.caption('💡 Detaylı görselleştirme ve indirme seçenekleri için ana panele bak.')
            
            # Aksiyon Butonları
            st.markdown('---')
            ac1, ac2 = st.columns(2)
            with ac1:
                pal_save_code = st.text_input('Taş kodu (opsiyonel)', value='CUSTOM', 
                                                 help='Bu paleti hangi taş için kaydet?')
                if st.button('💾 JSON kaydet', use_container_width=True):
                    palette_data = {
                        'stone_code': pal_save_code,
                        'stone_name': st.session_state.computed_palette_meta.get('source_image', 'Custom'),
                        'n_clusters': len(st.session_state.computed_palette),
                        'colors': st.session_state.computed_palette,
                        'source': f"computed: {st.session_state.computed_palette_meta.get('algorithm','?')} in {st.session_state.computed_palette_meta.get('color_space','?')}",
                        'pore_candidate_indices': [0, 1] if len(st.session_state.computed_palette) >= 2 else [0],
                    }
                    saved_path = palettes.save_palette(pal_save_code, palette_data)
                    st.success(f'✓ Kaydedildi: {os.path.basename(saved_path)}')
            with ac2:
                if st.button('🔗 Aktif palet yap', use_container_width=True,
                              help='Bu paleti Analize Başla sekmesinde aktif et'):
                    st.session_state.palette_data = {
                        'stone_code': 'COMPUTED',
                        'stone_name': st.session_state.computed_palette_meta.get('source_image', 'Custom'),
                        'n_clusters': len(st.session_state.computed_palette),
                        'colors': st.session_state.computed_palette,
                        'source': 'live computed',
                        'pore_candidate_indices': [0, 1] if len(st.session_state.computed_palette) >= 2 else [0],
                    }
                    st.session_state.selected_pore_indices = [0, 1]
                    st.success('Bu palet Analize Başla sekmesinde aktif edildi')
                    st.rerun()
    
        # =============================================================
    # 🔄 AGING ANALİZİ — Pre/Post yaşlandırma karşılaştırması
    # =============================================================
    with st.expander('🔄  **Aging Analizi (Pre/Post)**', expanded=False):
        st.caption('Yaşlandırma deneyi öncesi/sonrası yüzey renk değişimini ölçer (TS EN 15886 + CIEDE2000)')
        
        # ─── Mod Seçici ───
        aging_mode = st.radio(
            'Karşılaştırma Modu',
            ['🪞 Tek-çift (1 pre + 1 post)', '🔢 Çoklu numune (N pre + N post)'],
            key='aging_mode', horizontal=False)
        
        st.markdown('---')
        st.markdown('##### 📤 Deney Öncesi Görüntüleri')
        pre_files = st.file_uploader(
            'Pre-test', accept_multiple_files=True,
            type=['jpg','jpeg','png','tif','tiff','bmp'],
            key='aging_pre_files', label_visibility='collapsed')
        if pre_files:
            st.caption(f'✓ {len(pre_files)} pre-test görüntüsü')
        
        st.markdown('##### 📤 Deney Sonrası Görüntüleri')
        post_files = st.file_uploader(
            'Post-test', accept_multiple_files=True,
            type=['jpg','jpeg','png','tif','tiff','bmp'],
            key='aging_post_files', label_visibility='collapsed')
        if post_files:
            st.caption(f'✓ {len(post_files)} post-test görüntüsü')
        
        # Eşitlik kontrolü
        n_pre = len(pre_files) if pre_files else 0
        n_post = len(post_files) if post_files else 0
        if n_pre and n_post:
            if n_pre != n_post:
                st.error(f'⚠️ Eşit sayı gerekli: {n_pre} pre vs {n_post} post')
            else:
                st.success(f'✓ {n_pre} pre + {n_post} post = {n_pre} eşleştirilecek çift')
        
        # Mode tutarlılık
        if aging_mode.startswith('🪞 Tek-çift') and (n_pre > 1 or n_post > 1):
            st.warning('Tek-çift modunda 1\'er görüntü yükle. Daha fazlası varsa Çoklu moda geç.')
        
        st.markdown('---')
        
        # ─── Eşleştirme Stratejisi ───
        st.markdown('##### 🔗 Eşleştirme Stratejisi')
        pair_strategy = st.radio(
            'Strateji',
            ['🔤 Otomatik — alfabetik (dosya adına göre)',
             '🔢 Otomatik — yükleme sırası (1.pre ↔ 1.post)',
             '✋ Manuel eşleştirme (tablo)'],
            key='aging_pair_strategy', label_visibility='collapsed')
        
        # Manuel eşleştirme tablosu (eğer seçilmişse)
        manual_pairs = None
        if pair_strategy.startswith('✋ Manuel') and n_pre and n_post and n_pre == n_post:
            st.caption('Her pre-test için karşılık gelen post-test\'i seç:')
            manual_pairs = []
            post_names = [p.name for p in post_files]
            for i, pre_f in enumerate(pre_files):
                selected = st.selectbox(
                    f'**{pre_f.name}** eşleşir:', post_names,
                    index=i if i < len(post_names) else 0,
                    key=f'aging_manual_{i}')
                post_idx = post_names.index(selected)
                manual_pairs.append((i, post_idx))
        
        st.markdown('---')
        
        # ─── Analiz Parametreleri ───
        st.markdown('##### ⚙️ Analiz Parametreleri')
        delta_e_method = st.selectbox(
            'ΔE metriği',
            ['ΔE-2000 (modern, önerilen)', 'ΔE-94 (CIE 1994)', 'ΔE-76 (CIE 1976, klasik)'],
            key='aging_de_method')
        de_method_id = '2000' if '2000' in delta_e_method else ('94' if '94' in delta_e_method else '76')
        
        analysis_depth = st.radio(
            'Analiz Derinliği',
            ['📊 Standart (mean color + ΔE + istatistik)',
             '🔬 Detaylı (+ uniformity karşılaştırması)'],
            key='aging_depth', label_visibility='collapsed')
        
        sample_px = st.select_slider(
            'Pixel örnekleme boyutu',
            options=[5000, 10000, 20000, 50000, 100000],
            value=20000, key='aging_sample_size')
        
        # ─── Bilgilendirme ───
        if n_pre and n_post and n_pre == n_post:
            est_time = n_pre * 1.5  # ~1.5 sn/pair (CPU)
            st.info(f'⏱️ Tahmini süre: ~{est_time:.0f}s ({n_pre} numune)')
        
        # ─── Run Button ───
        if n_pre > 0 and n_post > 0 and n_pre == n_post:
            if st.button('🔬 Karşılaştırma Analizini Çalıştır', use_container_width=True, type='primary', key='aging_run'):
                with st.spinner(f'{n_pre} çift karşılaştırılıyor...'):
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
                            st.warning(f'{pre_f.name} işlenirken hata: {e}')
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
                        st.success(f'✓ {len(pair_results)} çift analiz edildi. Detaylar ana panelde.')
        else:
            st.info('Eşit sayıda pre ve post görüntü yükleyince butona tıklayabilirsin.')
    
        # =============================================================
    # ⚙️ AYARLAR — placeholder, gelecek özellikler
    # =============================================================
    with st.expander('⚙️  **Ayarlar**', expanded=False):
        st.caption('🚧 Bu bölüm geliştirme aşamasındadır.')
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
        st.caption('Özellik önerin mi var? GitHub issue aç veya e-posta gönder.')
    
    # =============================================================
    # ℹ️ HAKKINDA — bilim insanları için yardımcı bilgiler
    # =============================================================
    with st.expander('ℹ️  **Hakkında & Atıf**', expanded=False):
        st.markdown("""
        **Gözenek ve Renk Tespit Yazılımı v1.0**
        
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
        > Sert, M. ve diğ. (2026). *Gözenek ve Renk Tespit Yazılımı v1.0.*  
        > Afyon Kocatepe Üniversitesi. (Hazırlık aşamasında)
        
        **İletişim:** msert@aku.edu.tr
        """)


# ============================================================
# ANA PANEL — GÖRÜNTÜ + OVERLAY + METRİKLER
# ============================================================
if st.session_state.image_rgb is None:
    st.info('👈 Soldan görüntü yükle.')
    st.markdown("""
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
else:
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
        elif algo == 'Color Distance (Renk Mesafesi)':
            # Pore renkleri = checkbox'lı + custom
            pore_colors = []
            if st.session_state.palette_data:
                pore_colors = palettes.palette_to_dict(st.session_state.palette_data, 
                                                       st.session_state.selected_pore_indices)
            pore_colors += st.session_state.custom_pore_colors
            if not pore_colors:
                st.warning('⚠️ Lütfen paletten en az bir pore rengi seç.')
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
        st.error(f'Segmentasyon hatası: {e}')
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
    overlay_style = style_cols[0].radio('Overlay stili', 
                                         ['Dolgu (saydam)', 'Sadece sınırlar'], 
                                         horizontal=True)
    
    # Renk presetleri — açık taş için koyu, koyu taş için açık
    color_presets = {
        '🟢 Yeşil (açık taş)': (0, 255, 80),
        '🟡 Sarı parlak (universal)': (255, 230, 0),
        '🔴 Kırmızı (alarm)': (255, 40, 40),
        '🌸 Pembe (koyu taş)': (255, 80, 200),
        '🟣 Magenta (koyu taş)': (255, 0, 255),
        '🔵 Mavi (kontrast)': (0, 120, 255),
        '🟦 Cyan/Turkuaz': (0, 255, 220),
        '⚪ Beyaz (çok koyu taş)': (255, 255, 255),
        '⚫ Siyah (çok açık taş)': (0, 0, 0),
        '🟠 Turuncu': (255, 140, 0),
        '🤖 Auto (görüntüye göre)': 'auto',
        '🎨 Custom (kendin seç)': 'custom',
    }
    color_choice = style_cols[1].selectbox('Dolgu rengi', 
                                            list(color_presets.keys()), 
                                            index=10)  # Auto default
    
    color_val = color_presets[color_choice]
    
    if color_val == 'auto':
        # Görüntü parlaklığına göre kontrastlı renk seç
        mean_brightness = float(img.mean())
        if mean_brightness > 160:    # açık taş (KT, PT gibi) → magenta-pembe
            fill_color = (220, 0, 200)
            auto_note = '→ Magenta (açık taş tespit edildi)'
        elif mean_brightness > 100:  # orta tonda
            fill_color = (0, 255, 100)
            auto_note = '→ Yeşil (orta tonda)'
        else:                         # koyu taş → parlak sarı
            fill_color = (255, 240, 0)
            auto_note = '→ Sarı (koyu taş tespit edildi)'
        style_cols[2].caption(f'**Auto**: parlaklık={mean_brightness:.0f}')
        style_cols[2].caption(auto_note)
    elif color_val == 'custom':
        custom_hex = style_cols[2].color_picker('Renk seç', '#00ff50', label_visibility='collapsed')
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
    if overlay_style == 'Dolgu (saydam)':
        alpha = st.slider('Saydamlık (alpha)', 0.10, 0.95, 0.55, step=0.05,
                          help='Düşük=daha saydam (orijinal daha görünür), Yüksek=daha opak')
        overlay = utils.make_overlay(img, final_mask, color=fill_color, alpha=alpha)
    else:
        thickness = st.slider('Sınır kalınlığı (px)', 1, 8, 2,
                              help='Kontur çizgisi kalınlığı')
        overlay = utils.make_outline_overlay(img, final_mask, color=fill_color, thickness=thickness)
    overlay_display = utils.resize_for_display(overlay, display_max)
    
    col1, col2 = st.columns(2)
    with col1:
        st.image(img_display, caption='Orijinal', use_column_width=True)
    with col2:
        st.image(overlay_display, caption=f'Segmentasyon ({algo})', use_column_width=True)
    
    # SAM2/CellPose uyarısı
    if sam2_warning:
        st.warning(f'⚠️ {sam2_warning}')
    
    # Metrik kutuları
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric('Görüntü Porozitesi', f"{metrics['porosity_pct']:.2f} %")
    mc2.metric('Pore Sayısı', metrics['n_pores'])
    mc3.metric('Ort. Alan (mm²)', f"{metrics['mean_area_mm2']:.3f}")
    mc4.metric('Ort. Dairesellik', f"{metrics['mean_circularity']:.3f}")
    
    # Karşılaştırma — deneysel değer biliniyorsa
    with st.expander('🧪 Deneysel referans karşılaştırması (opsiyonel)'):
        exp_ref = st.number_input('TS EN 1936 açık porozite (%) — biliniyorsa', value=0.0, step=0.1)
        if exp_ref > 0:
            sapma = abs(metrics['porosity_pct'] - exp_ref)
            st.write(f'**Sapma:** {sapma:.2f} pp')
            if sapma < 0.5: st.success('✓ Mükemmel uyum')
            elif sapma < 1.5: st.info('Kabul edilebilir')
            elif sapma < 3.0: st.warning('Geliştirilebilir')
            else: st.error('Yüksek sapma')
    
    # Görüntüden renk seçme (basit form)
    with st.expander('🎯 Görüntüden pore rengi seç (manuel)'):
        st.caption('Görüntüde bir pore üzerine tıkladığında pixel koordinatlarını gir (sol-üst köşe 0,0):')
        cc1, cc2, cc3 = st.columns([1,1,2])
        px_x = cc1.number_input('X (piksel)', min_value=0, max_value=W-1, value=W//2)
        px_y = cc2.number_input('Y (piksel)', min_value=0, max_value=H-1, value=H//2)
        if cc3.button('🎯 Bu noktadaki rengi pore listesine ekle'):
            rgb = utils.pick_color_at(img, int(px_x), int(px_y))
            st.session_state.custom_pore_colors.append(rgb)
            st.success(f'Eklendi: {utils.rgb_to_hex(rgb)} (RGB={rgb})')
            st.rerun()
    
    # Pore detay tablosu
    with st.expander('🔎 Detaylı pore istatistikleri (ilk 50)'):
        if kept_props:
            rows = []
            for i, p in enumerate(kept_props[:50]):
                rows.append({
                    '#': i+1, 'Alan (px)': p.area, 
                    'Alan (mm²)': round(p.area * 0.091**2, 3),
                    'Çevre (px)': round(p.perimeter, 1),
                    'Dairesellik': round(4*np.pi*p.area/(p.perimeter**2) if p.perimeter>0 else 0, 3),
                    'Eccentricity': round(p.eccentricity, 3),
                    'Ortalama yoğunluk': round(p.mean_intensity, 1),
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
            
            csv_bytes = pd.DataFrame(rows).to_csv(index=False).encode('utf-8')
            st.download_button('📥 Tüm pore detaylarını CSV indir', csv_bytes, 
                                file_name=f'{st.session_state.image_name}_pores.csv', mime='text/csv')
        else:
            st.write('Pore tespit edilmedi.')
    
    # Mask ve overlay indir
    with st.expander('📥 Çıktıları indir'):
        ov_pil = Image.fromarray(overlay)
        buf = BytesIO(); ov_pil.save(buf, format='PNG')
        st.download_button('Overlay PNG', buf.getvalue(), 
                            file_name=f'{st.session_state.image_name}_overlay.png', mime='image/png')
        mask_pil = Image.fromarray((final_mask*255).astype(np.uint8))
        buf2 = BytesIO(); mask_pil.save(buf2, format='PNG')
        st.download_button('Binary mask PNG', buf2.getvalue(),
                            file_name=f'{st.session_state.image_name}_mask.png', mime='image/png')

# ============================================================
# 🎨 RENK YELPAZESİ — Ana Panel Detaylı Görselleştirme
# (sidebar'da hesaplanmışsa burada gözükür)
# ============================================================
if 'computed_palette' in st.session_state and st.session_state.get('computed_palette'):
    st.divider()
    with st.expander('🎨 Renk Yelpazesi — Detaylı Görselleştirme', expanded=False):
        palette = st.session_state.computed_palette
        meta = st.session_state.computed_palette_meta
        
        st.caption(f'**Kaynak:** {meta.get("source_image","-")} · **Algoritma:** {meta.get("algorithm","-")} · **Renk uzayı:** {meta.get("color_space","-")}')
        
        # İki sütun: sol palette swatches, sağ pie chart
        pc1, pc2 = st.columns([1, 1])
        
        with pc1:
            st.markdown('##### Renk Listesi (karanlıktan açığa)')
            # Tablo halinde göster
            pal_df = pd.DataFrame([{
                '#': i+1,
                'Hex': c['hex'],
                'RGB': f"({c['rgb'][0]}, {c['rgb'][1]}, {c['rgb'][2]})",
                'Parlaklık': round(c['brightness'], 0),
                'Fraction (%)': round(c['fraction_pct'], 2),
            } for i, c in enumerate(palette)])
            st.dataframe(pal_df, use_container_width=True, hide_index=True)
            
            # Hex değerleri tek satır (kopya için kolay)
            st.markdown('##### Hex değerleri (kopyala)')
            hex_string = ' '.join(c['hex'] for c in palette)
            st.code(hex_string, language=None)
        
        with pc2:
            st.markdown('##### Renk Oranları (Pie Chart)')
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
        st.markdown('##### Palette Bandı (görsel)')
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
        st.caption('💡 Bant üzerinde imleci bekleterek tam hex+RGB+oran bilgisini görebilirsin.')
        
        # Export
        st.markdown('---')
        st.markdown('##### 📥 İndir')
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
        st.markdown('##### 🔬 ΔE Renk Karşılaştırma (CIE)')
        st.caption('İki rengin perceptual (algısal) farkını ölç. ΔE-2000 modern CIE standardıdır (Sharma et al. 2005).')
        
        # Palette renkleri + custom RGB inputu seçenekleri
        delta_options = ['🎨 Palette\'ten seç'] + [f'{i+1}. {c["hex"]} ({c.get("fraction_pct",0):.1f}%)' for i,c in enumerate(palette)]
        
        dc1, dc2 = st.columns(2)
        with dc1:
            st.markdown('**Renk A**')
            color_a_choice = st.selectbox('Seç', delta_options, index=1, key='delta_color_a')
            if color_a_choice == '🎨 Palette\'ten seç':
                color_a_hex = st.color_picker('Custom A', '#1b1a13', key='delta_a_custom')
                color_a_rgb = utils.hex_to_rgb(color_a_hex)
            else:
                idx_a = int(color_a_choice.split('.')[0]) - 1
                color_a_rgb = palette[idx_a]['rgb']
                color_a_hex = palette[idx_a]['hex']
            # Renk önizleme
            st.markdown(f'<div style="background:{color_a_hex};width:100%;height:60px;border:2px solid #888;border-radius:6px;display:flex;align-items:center;justify-content:center;color:{"#fff" if sum(color_a_rgb)/3<128 else "#000"};font-weight:600;">{color_a_hex}</div>', unsafe_allow_html=True)
        
        with dc2:
            st.markdown('**Renk B**')
            color_b_choice = st.selectbox('Seç', delta_options, index=min(len(palette), 2) if len(palette)>=2 else 1, key='delta_color_b')
            if color_b_choice == '🎨 Palette\'ten seç':
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
            mc1.metric('ΔE-76 (CIE 1976)', f'{de76:.2f}', help='Klasik Euclidean Lab mesafesi')
            mc2.metric('ΔE-94 (CIE 1994)', f'{de94:.2f}', help='Chroma/hue ağırlıklı')
            mc3.metric('ΔE-2000 (modern)', f'{de2k:.2f}', help='CIEDE2000 — Q1 dergi standardı (Sharma 2005)')
            
            # Yorum
            if de2k < 1: color_box = '#22c55e'
            elif de2k < 3.5: color_box = '#3b82f6'
            elif de2k < 5: color_box = '#eab308'
            elif de2k < 10: color_box = '#f97316'
            else: color_box = '#ef4444'
            
            st.markdown(
                f'<div style="background:{color_box}22; border-left:4px solid {color_box}; '
                f'padding:12px 16px; border-radius:4px; margin-top:8px;">'
                f'<b>Görsel Yorum:</b> {interp}'
                f'</div>',
                unsafe_allow_html=True)
            
            # Detay: Lab değerleri yan yana
            with st.expander('🔍 Detaylı Lab/LCh değerleri'):
                L_a, a_a, b_a = cs.rgb_to_lab(color_a_rgb)
                L_b, a_b, b_b = cs.rgb_to_lab(color_b_rgb)
                _, C_a, h_a = cs.lab_to_lch(L_a, a_a, b_a)
                _, C_b, h_b = cs.lab_to_lch(L_b, a_b, b_b)
                detail_df = pd.DataFrame({
                    'Metrik': ['L* (Lightness)', 'a* (Green-Red)', 'b* (Blue-Yellow)', 
                                'C* (Chroma)', 'h° (Hue angle)', 'Munsell'],
                    'Renk A': [f'{L_a:.2f}', f'{a_a:+.2f}', f'{b_a:+.2f}',
                                 f'{C_a:.2f}', f'{h_a:.1f}°',
                                 cs.lab_to_munsell_approx(L_a, a_a, b_a)],
                    'Renk B': [f'{L_b:.2f}', f'{a_b:+.2f}', f'{b_b:+.2f}',
                                 f'{C_b:.2f}', f'{h_b:.1f}°',
                                 cs.lab_to_munsell_approx(L_b, a_b, b_b)],
                    'Δ': [f'{L_b-L_a:+.2f}', f'{a_b-a_a:+.2f}', f'{b_b-b_a:+.2f}',
                            f'{C_b-C_a:+.2f}', f'{h_b-h_a:+.1f}°', '-'],
                })
                st.dataframe(detail_df, use_container_width=True, hide_index=True)
                
                st.caption('💡 ΔE < 1: fark edilmez | 1-2: eğitimli göz | 2-3.5: zar zor | 3.5-5: belirgin | 5-10: net | >10: çok farklı')
        except Exception as e:
            st.error(f'ΔE hesaplama hatası: {e}')
        
        # ─────────────────────────────────────────────────────
        # 📐 RENK HOMOJENLİĞİ ANALİZİ (Seviye 4)
        # ─────────────────────────────────────────────────────
        st.markdown('---')
        st.markdown('##### 📐 Renk Homojenliği Analizi (CIE Lab Uniformity)')
        st.caption('Görüntü genelinde renk dağılımının ne kadar homojen olduğunu ölçer. Taş kalite kontrolü ve tuz hasarı değerlendirmesi için.')
        
        if st.session_state.image_rgb is not None:
            uni_sample_size = st.select_slider('Örnekleme boyutu', 
                                                  options=[5000, 10000, 20000, 50000, 100000],
                                                  value=20000, key='uni_sample',
                                                  help='Yüksek = daha doğru, daha yavaş')
            
            if st.button('📐 Homojenlik Skorunu Hesapla', use_container_width=True, key='compute_uni'):
                with st.spinner('Hesaplanıyor...'):
                    try:
                        u = cs.compute_uniformity(st.session_state.image_rgb, sample_size=uni_sample_size)
                        st.session_state.uniformity_result = u
                    except Exception as e:
                        st.error(f'Uniformity hesaplama hatası: {e}')
            
            if 'uniformity_result' in st.session_state and st.session_state.uniformity_result:
                u = st.session_state.uniformity_result
                
                # Üst sıra: ana metrikler
                um1, um2, um3 = st.columns([1.5, 1, 1])
                with um1:
                    # Mean color swatch
                    st.markdown(f'**Görüntünün Ortalama Rengi**')
                    st.markdown(
                        f'<div style="background:{u["mean_color_hex"]}; '
                        f'width:100%; height:80px; border:2px solid #888; '
                        f'border-radius:8px; display:flex; align-items:center; '
                        f'justify-content:center; color:{"#fff" if u["mean_L"]<55 else "#000"}; '
                        f'font-weight:600; font-size:16px;">'
                        f'{u["mean_color_hex"]}'
                        f'</div>', unsafe_allow_html=True)
                with um2:
                    st.metric('Homojenlik Skoru', f'{u["homogeneity_score_0_10"]:.1f}/10')
                with um3:
                    # Class olarak göster
                    st.markdown('**Sınıflandırma**')
                    st.markdown(f'<div style="padding:8px 12px; background:#1f2937; border-radius:6px; text-align:center; font-size:14px; margin-top:8px;">{u["uniformity_class"]}</div>', unsafe_allow_html=True)
                
                # Lab istatistikleri
                st.markdown('**CIE Lab İstatistikleri**')
                stats_df = pd.DataFrame({
                    'Kanal': ['L* (Lightness)', 'a* (Green-Red)', 'b* (Blue-Yellow)'],
                    'Ortalama': [u['mean_L'], u['mean_a'], u['mean_b']],
                    'Standart Sapma (σ)': [u['std_L'], u['std_a'], u['std_b']],
                    'Yorum': [
                        'Parlaklık değişkenliği' if u['std_L'] > 8 else 'Düzgün parlaklık',
                        'Yeşil-kırmızı değişkenliği' if u['std_a'] > 4 else 'Tutarlı a* renk',
                        'Mavi-sarı değişkenliği' if u['std_b'] > 4 else 'Tutarlı b* renk',
                    ],
                })
                st.dataframe(stats_df, use_container_width=True, hide_index=True)
                
                # ΔE-2000 istatistikleri
                st.markdown('**ΔE-2000 Renk Dağılımı (ortalama renkten sapma)**')
                de1, de2, de3, de4 = st.columns(4)
                de1.metric('Ortalama ΔE', f'{u["delta_e_avg_from_mean"]:.2f}')
                de2.metric('Std ΔE', f'{u["delta_e_std"]:.2f}')
                de3.metric('p95 ΔE', f'{u["delta_e_p95"]:.2f}', help='En aykırı %5 piksel')
                de4.metric('Max ΔE', f'{u["delta_e_max"]:.2f}', help='En uç piksel (outlier)')
                
                # Bilimsel yorumlama bloğu
                interp_text = ""
                if u['homogeneity_score_0_10'] >= 8:
                    interp_text = "Bu taş **görsel olarak çok tutarlı**. Cephe kaplaması, batch tutarlılığı gerektiren uygulamalar için ideal."
                    interp_color = '#22c55e'
                elif u['homogeneity_score_0_10'] >= 6:
                    interp_text = "Bu taş **kabul edilebilir homojenlikte**. Dekoratif kullanım için uygun, fakat kritik renk eşleştirme gerekiyorsa örnek değiştirmek faydalı olabilir."
                    interp_color = '#3b82f6'
                else:
                    interp_text = "Bu taş **belirgin renk heterojenliği** gösteriyor (örn. bantlı yapı, fosil içeriği, alterasyon). Bu, doğal karakter olabilir ama tutarlılık kritikse alternatif batch düşünülmeli."
                    interp_color = '#eab308'
                
                st.markdown(
                    f'<div style="background:{interp_color}22; border-left:4px solid {interp_color}; '
                    f'padding:12px 16px; border-radius:4px; margin-top:8px;">'
                    f'<b>Bilimsel Yorum:</b> {interp_text}'
                    f'</div>', unsafe_allow_html=True)
                
                # Pre/Post karşılaştırma kaydetme
                st.markdown('---')
                save_col1, save_col2 = st.columns(2)
                with save_col1:
                    if st.button('💾 Pre-test referansı olarak kaydet', use_container_width=True):
                        st.session_state.uniformity_pre = u
                        st.success('✓ Pre-test uniformity kaydedildi')
                with save_col2:
                    if st.button('💾 Post-test sonuç olarak karşılaştır', use_container_width=True):
                        if 'uniformity_pre' in st.session_state:
                            comp = cs.compare_uniformity(st.session_state.uniformity_pre, u)
                            st.session_state.uniformity_compare = comp
                        else:
                            st.warning('Önce pre-test referansı kaydet.')
                
                # Karşılaştırma sonucu
                if 'uniformity_compare' in st.session_state and st.session_state.uniformity_compare:
                    comp = st.session_state.uniformity_compare
                    st.markdown('**🔄 Pre vs Post Karşılaştırma:**')
                    cc1, cc2, cc3 = st.columns(3)
                    cc1.metric('Δ Mean L*', f'{comp["delta_mean_L"]:+.2f}')
                    cc2.metric('Δ Homogeneity', f'{comp["delta_homogeneity"]:+.2f}')
                    cc3.metric('Mean Color ΔE-2000', f'{comp["mean_color_delta_e_2000"]:.2f}',
                                help=comp['mean_color_interpretation'])
                    st.caption(f'**Görsel Hasar Yorumu:** {comp["mean_color_interpretation"]}')
                
                # JSON export
                with st.expander('📥 Uniformity sonucunu JSON olarak indir'):
                    import json as _json
                    uni_json = safe_json_dumps(u, ensure_ascii=False, indent=2)
                    st.download_button('🗂️ uniformity.json', uni_json.encode('utf-8'),
                                        file_name=f'uniformity_{meta.get("source_image","custom")}.json',
                                        mime='application/json', use_container_width=True)
        else:
            st.info('Önce bir görüntü yükle.')

# ============================================================
# AGING ANALIZI Ana Panel Sonuclar
# ============================================================
if 'aging_results' in st.session_state and st.session_state.aging_results:
    st.divider()
    with st.expander('Yaslandirma Karsilastirma Sonuclari (Pre/Post)', expanded=True):
        ar = st.session_state.aging_results
        pairs = ar['pairs']
        agg = ar['aggregate']
        n = agg['n']
        
        st.caption(str(n) + ' numune | ' + str(ar['method']))
        
        # Genel ozet
        st.markdown('##### Genel Ozet')
        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric('Ortalama dE', '{:.2f} +/- {:.2f}'.format(agg['delta_e']['mean'], agg['delta_e']['std']))
        sc2.metric('Min/Max dE', '{:.2f} / {:.2f}'.format(agg['delta_e']['min'], agg['delta_e']['max']))
        sc3.metric('Ortalama dL*', '{:+.2f}'.format(agg['delta_L']['mean']))
        sc4.metric('CV (dE)', '%{:.0f}'.format(agg['delta_e']['cv_pct']))
        
        # Per-pair tablo
        st.markdown('##### Numune Karsilastirma Tablosu')
        pair_rows = []
        for i, p in enumerate(pairs):
            pair_rows.append({
                '#': i+1, 'Numune': p['sample_name'][:25],
                'Pre': p['pre_color_hex'], 'Post': p['post_color_hex'],
                'dL*': p['delta_L'], 'da*': p['delta_a'], 'db*': p['delta_b'],
                'dC*': p['delta_C'], 'dH*': p['delta_H'], 'dE': p['delta_e'],
                'Sinif': p['classification'],
            })
        pair_df = pd.DataFrame(pair_rows)
        st.dataframe(pair_df, use_container_width=True, hide_index=True)
        
        # Swatch grid
        st.markdown('##### Renk Karsilastirma (Pre / Post)')
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
        st.markdown('##### Numune x dE Bar Chart')
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
        st.caption('Dikey kesikli cizgiler perceptual esiklerdir: 1=just noticeable, 3.5=barely visible, 5=clear, 10=marked')
        
        # Istatistik 4 sekme
        st.markdown('##### Istatistiksel Analiz (Paired)')
        tab_dE, tab_L, tab_a, tab_b = st.tabs(['dE-2000', 'dL* Lightness', 'da* Green-Red', 'db* Blue-Yellow'])
        
        def render_stat(t):
            if 'error' in t:
                st.warning(t['error']); return
            tc1, tc2, tc3, tc4 = st.columns(4)
            tc1.metric('Test', t['test_name'].split('(')[0].strip() if t.get('test_name') else '-')
            p_val = t.get('p_value')
            p_disp = '<0.001' if p_val and p_val < 0.001 else ('{:.4f}'.format(p_val) if p_val else '-')
            tc2.metric('p-deger', p_disp, 'Anlamli' if t.get('is_significant') else ('Anlamsiz' if t.get('is_significant') is not None else None))
            tc3.metric('Cohen d', '{:.2f}'.format(t['cohen_d']) if t.get('cohen_d') else '-',
                       t.get('cohen_d_interpretation','').split(' (')[0])
            ci_str = '[{:.2f}, {:.2f}]'.format(t['ci_95_low'], t['ci_95_high']) if t.get('ci_95_low') is not None else '-'
            tc4.metric('95% CI', ci_str)
            st.markdown('**Test:** ' + str(t.get('test_name','-')) + ' | stat=`' + str(t.get('test_statistic','-')) + '`')
            normal_str = 'Normal kabul' if t.get('is_normal_distribution') else 'Normal degil (non-param)'
            st.markdown('**Shapiro-Wilk p:** `' + str(t.get('normality_shapiro_p','-')) + '` -> ' + normal_str)
            st.markdown('**Ortalama fark:** `' + str(t.get('mean_diff','-')) + '` +/- `' + str(t.get('std_diff','-')) + '`')
        
        with tab_dE: render_stat(ar['stat_test_dE'])
        with tab_L:  render_stat(ar['stat_test_L'])
        with tab_a:  render_stat(ar['stat_test_a'])
        with tab_b:  render_stat(ar['stat_test_b'])
        
        # Otomatik yorum
        st.markdown('##### Otomatik Bilimsel Yorum')
        interp = aa.auto_interpret(agg, ar['stat_test_dE'])
        if interp['damage_severity']=='minimal': damage_color='#22c55e'
        elif 'hafif' in interp['damage_severity']: damage_color='#3b82f6'
        elif 'orta' in interp['damage_severity']: damage_color='#eab308'
        elif 'belirgin' in interp['damage_severity']: damage_color='#f97316'
        else: damage_color='#ef4444'
        st.markdown('<div style="background:' + damage_color + '22; border-left:4px solid ' + damage_color + '; padding:12px 16px; border-radius:4px; margin:8px 0;"><b>TR (Tartisma icin):</b><br>' + interp['summary_tr'] + '</div>', unsafe_allow_html=True)
        st.markdown('<div style="background:#1f2937; border-left:4px solid #6366f1; padding:12px 16px; border-radius:4px; margin:8px 0; color:#fff;"><b>EN (Paper-ready):</b><br>' + interp['paper_ready_en'] + '</div>', unsafe_allow_html=True)
        
        # Export
        st.markdown('---')
        st.markdown('##### Indirme Secenekleri')
        ec1, ec2, ec3, ec4 = st.columns(4)
        with ec1:
            st.download_button('Per-pair CSV', pair_df.to_csv(index=False).encode('utf-8'),
                file_name='aging_per_pair.csv', mime='text/csv', use_container_width=True)
        with ec2:
            import json as _json
            full_json = safe_json_dumps({'pairs':pairs,'aggregate':agg,
                'statistics':{'dE':ar['stat_test_dE'],'L*':ar['stat_test_L'],'a*':ar['stat_test_a'],'b*':ar['stat_test_b']},
                'interpretation':interp,
                'metadata':{'method':ar['method'],'depth':ar['depth'],'n':n}}, ensure_ascii=False, indent=2)
            st.download_button('Full JSON', full_json.encode('utf-8'),
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
            st.download_button('Markdown rapor', '\n'.join(md_lines).encode('utf-8'),
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
# ALT BİLGİ
# ============================================================
st.divider()
st.caption('Gözenek ve Renk Tespit Yazılımı v1.0 — 2026  |  Murat SERT et al. — AKÜ')
