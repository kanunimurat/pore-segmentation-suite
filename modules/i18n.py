"""
i18n.py — Internationalization (TR / EN) for Pore Segmentation Suite
====================================================================

Provides:
- TRANSLATIONS dictionary (key -> {tr: ..., en: ...})
- T(key) — returns localized string based on st.session_state.lang
- render_language_selector() — sidebar flag buttons (🇹🇷 / 🇬🇧)
- DEFAULT_LANG = 'en' (so screenshots are English by default)

Usage in main app:
    from modules.i18n import T, render_language_selector, init_language
    init_language()              # at top of main()
    render_language_selector()   # inside sidebar (top)
    st.title(T('app_title'))
    st.button(T('btn_compute_palette'))
"""

import streamlit as st

DEFAULT_LANG = 'en'

# ============================================================================
# TRANSLATIONS DICTIONARY
# Add new keys as needed. Format: 'key': {'tr': 'TR string', 'en': 'EN string'}
# Keys are namespaced by section for readability.
# ============================================================================

TRANSLATIONS = {
    # ---------------------------------------------------------------- App meta
    'app_title':            {'tr': '🪨 Gözenek ve Renk Tespit Yazılımı',
                             'en': '🪨 Pore Segmentation Suite'},
    'app_caption':          {'tr': 'Travertenler için interaktif segmentasyon — DoG / MSER / Sauvola / Color-Distance + per-stone renk paleti',
                             'en': 'Interactive segmentation for travertines — DoG / MSER / Sauvola / Color-Distance + per-stone color palettes'},
    'language':             {'tr': 'Dil', 'en': 'Language'},

    # ---------------------------------------------------------------- Mode selector
    'mode_pore':            {'tr': '🔬 Gözenek Bölütleme',
                             'en': '🔬 Pore Segmentation'},
    'mode_palette':         {'tr': '🎨 Renk Paleti',
                             'en': '🎨 Color Palette'},
    'mode_aging':           {'tr': '⏱️ Yaşlandırma Analizi',
                             'en': '⏱️ Aging Analysis'},
    'mode_collage':         {'tr': '🖼️ Kolaj Oluşturucu',
                             'en': '🖼️ Collage Builder'},
    'select_mode':          {'tr': 'Çalışma Modu',
                             'en': 'Work Mode'},

    # ---------------------------------------------------------------- Image upload
    'analyze_start':        {'tr': '📊 Analize Başla',
                             'en': '📊 Start Analysis'},
    'upload_image':         {'tr': '📂 Görüntü Yükle',
                             'en': '📂 Upload Image'},
    'source':               {'tr': 'Kaynak',
                             'en': 'Source'},
    'src_upload_file':      {'tr': '📤 Dosya yükle',
                             'en': '📤 Upload file'},
    'src_from_folder':      {'tr': '📁 Klasörden seç',
                             'en': '📁 Pick from folder'},
    'image_input_label':    {'tr': 'Travertin yüzey görüntüsü',
                             'en': 'Travertine surface image'},
    'folder_path':          {'tr': 'Klasör yolu',
                             'en': 'Folder path'},
    'pick_image':           {'tr': 'Görüntü seç',
                             'en': 'Pick image'},
    'load_btn':             {'tr': '🔄 Yükle',
                             'en': '🔄 Load'},
    'no_images_in_folder':  {'tr': 'Klasörde görüntü yok.',
                             'en': 'No images in folder.'},

    # ---------------------------------------------------------------- Stone type + palette
    'stone_palette':        {'tr': '🪨 Taş Tipi & Renk Paleti',
                             'en': '🪨 Stone Type & Color Palette'},
    'stone_code':           {'tr': 'Taş kodu',
                             'en': 'Stone code'},
    'compute_palette':      {'tr': '🔄 Bu görüntüden K-means palet hesapla',
                             'en': '🔄 Compute K-means palette from this image'},
    'computing':            {'tr': 'Hesaplanıyor...',
                             'en': 'Computing...'},
    'palette_updated':      {'tr': 'Palet güncellendi.',
                             'en': 'Palette updated.'},
    'colors_from_image':    {'tr': '**Görüntüden eklenen renkler:**',
                             'en': '**Colors added from image:**'},

    # ---------------------------------------------------------------- Algorithm families
    'algo_family':          {'tr': 'Algoritma Ailesi',
                             'en': 'Algorithm Family'},
    'family_classical':     {'tr': '🔵 Klasik Eşikleme',
                             'en': '🔵 Classical Thresholding'},
    'family_blob':          {'tr': '🟢 Blob / Bölge',
                             'en': '🟢 Blob / Region'},
    'family_color':         {'tr': '🟣 Renk / Kümeleme',
                             'en': '🟣 Color / Clustering'},
    'family_hybrid':        {'tr': '🤝 Hibrit',
                             'en': '🤝 Hybrid'},
    'family_modern':        {'tr': '🚀 Modern Derin Öğrenme',
                             'en': '🚀 Modern Deep Learning'},
    'algorithm':            {'tr': 'Algoritma',
                             'en': 'Algorithm'},

    # ---------------------------------------------------------------- Common params
    'multiscale_3':         {'tr': 'Multi-scale (3 ölçek union)',
                             'en': 'Multi-scale (3-octave union)'},
    'sigma_small':          {'tr': 'σ₁ (küçük ölçek)',
                             'en': 'σ₁ (small scale)'},
    'sigma_large':          {'tr': 'σ₂ (büyük ölçek)',
                             'en': 'σ₂ (large scale)'},
    'percentile_low_more':  {'tr': 'Percentile (düşük = daha fazla pore)',
                             'en': 'Percentile (lower = more pores)'},
    'percentile_high_less': {'tr': 'Yanıt percentile (yüksek=daha az pore)',
                             'en': 'Response percentile (higher = fewer pores)'},
    'delta_stability':      {'tr': 'Delta (kararlılık)',
                             'en': 'Delta (stability)'},
    'color_space':          {'tr': 'Renk uzayı',
                             'en': 'Color space'},
    'n_classes':            {'tr': 'Sınıf sayısı',
                             'en': 'Number of classes'},
    'darkest_classes_pore': {'tr': 'En koyu kaç sınıfı pore say',
                             'en': 'How many darkest classes count as pore'},
    'auto_thresh_caption':  {'tr': '**Otomatik Eşik** (sıfır parametre)',
                             'en': '**Auto Threshold** (zero parameter)'},
    'method':               {'tr': 'Yöntem',
                             'en': 'Method'},
    'frangi_caption':       {'tr': '**Frangi Vesselness** (uzamış/bağlantılı yapılar)',
                             'en': '**Frangi Vesselness** (elongated / connected structures)'},
    'sigma_step':           {'tr': 'σ adım',
                             'en': 'σ step'},
    'dark_ridges':           {'tr': 'Karanlık ridges',
                              'en': 'Dark ridges'},

    # ---------------------------------------------------------------- Filters
    'filters_section':      {'tr': '🚫 Yanlış-Pozitif Filtreleri',
                             'en': '🚫 False-Positive Filters'},
    'min_area_px':          {'tr': 'Min. alan (piksel)',
                             'en': 'Min. area (pixels)'},
    'max_eccentricity':     {'tr': 'Maks. eccentricity',
                             'en': 'Max. eccentricity'},
    'min_solidity':         {'tr': 'Min. solidity',
                             'en': 'Min. solidity'},
    'min_texture_std':      {'tr': 'Min. doku std',
                             'en': 'Min. texture std'},
    'must_be_dark':         {'tr': 'Karanlık olmalı (median altı)',
                             'en': 'Must be dark (below median)'},

    # ---------------------------------------------------------------- Overlay
    'overlay_section':      {'tr': '🎯 Overlay Görselleştirme',
                             'en': '🎯 Overlay Visualization'},
    'overlay_style':        {'tr': 'Stil',
                             'en': 'Style'},
    'style_fill':           {'tr': 'Dolgu (saydam)',
                             'en': 'Fill (transparent)'},
    'style_outline':        {'tr': 'Sadece sınırlar',
                             'en': 'Outline only'},
    'overlay_color':        {'tr': 'Overlay rengi',
                             'en': 'Overlay color'},
    'color_auto':           {'tr': 'Otomatik (kontrasta göre)',
                             'en': 'Auto (contrast-based)'},
    'color_custom':         {'tr': 'Özel (hex)',
                             'en': 'Custom (hex)'},
    'alpha':                {'tr': 'Şeffaflık (alpha)',
                             'en': 'Transparency (alpha)'},
    'outline_thickness':    {'tr': 'Sınır kalınlığı (px)',
                             'en': 'Outline thickness (px)'},

    # ---------------------------------------------------------------- Results
    'results':              {'tr': '📊 Sonuçlar',
                             'en': '📊 Results'},
    'porosity_pct':         {'tr': 'Gözeneklilik (%)',
                             'en': 'Porosity (%)'},
    'pore_count':           {'tr': 'Gözenek sayısı',
                             'en': 'Pore count'},
    'processing_time':      {'tr': 'İşlem süresi (s)',
                             'en': 'Processing time (s)'},
    'save_params':          {'tr': '💾 Bu parametreleri kaydet',
                             'en': '💾 Save these parameters'},

    # ---------------------------------------------------------------- Color palette mode
    'palette_mode_title':   {'tr': '🎨 Renk Paleti Çıkarma',
                             'en': '🎨 Color Palette Extraction'},
    'clustering_algo':      {'tr': 'Kümeleme algoritması',
                             'en': 'Clustering algorithm'},
    'n_colors':             {'tr': 'Renk sayısı',
                             'en': 'Number of colors'},
    'compute_palette_btn':  {'tr': '🎨 Paleti hesapla',
                             'en': '🎨 Compute palette'},
    'save_palette':         {'tr': '💾 Paleti JSON olarak kaydet',
                             'en': '💾 Save palette as JSON'},

    # ---------------------------------------------------------------- Aging analysis mode
    'aging_mode_title':     {'tr': '⏱️ Yaşlandırma Analizi',
                             'en': '⏱️ Aging Analysis'},
    'upload_pre':           {'tr': 'Öncesi (pre) görüntüleri',
                             'en': 'Pre (before) images'},
    'upload_post':          {'tr': 'Sonrası (post) görüntüleri',
                             'en': 'Post (after) images'},
    'pairing_strategy':     {'tr': 'Eşleştirme stratejisi',
                             'en': 'Pairing strategy'},
    'pair_alphabetic':      {'tr': 'Alfabetik (dosya adına göre)',
                             'en': 'Alphabetic (by filename)'},
    'pair_upload_order':    {'tr': 'Yükleme sırası',
                             'en': 'Upload order'},
    'pair_manual':          {'tr': 'Manuel',
                             'en': 'Manual'},
    'delta_e_formula':      {'tr': 'ΔE formülü',
                             'en': 'ΔE formula'},
    'compute_aging':        {'tr': '🧪 Hesapla',
                             'en': '🧪 Compute'},
    'paper_ready_output':   {'tr': '📄 Makale-hazır çıktı',
                             'en': '📄 Paper-ready output'},

    # ---------------------------------------------------------------- Collage builder
    'collage_mode_title':   {'tr': '🖼️ Kolaj Oluşturucu',
                             'en': '🖼️ Collage Builder'},
    'collage_mode':         {'tr': 'Mod',
                             'en': 'Mode'},
    'mode_manual':          {'tr': '✏️ Manuel',
                             'en': '✏️ Manual'},
    'mode_quick':           {'tr': '⚡ Quick (yaşlandırmadan)',
                             'en': '⚡ Quick (from aging)'},
    'mode_template':        {'tr': '📋 Şablon',
                             'en': '📋 Template'},
    'rows':                 {'tr': 'Satır',
                             'en': 'Rows'},
    'cols':                 {'tr': 'Sütun',
                             'en': 'Columns'},
    'cell_width_px':        {'tr': 'Hücre genişliği (px)',
                             'en': 'Cell width (px)'},
    'font_size_mode':       {'tr': 'Font boyutu',
                             'en': 'Font size'},
    'font_auto':            {'tr': 'Otomatik',
                             'en': 'Auto'},
    'font_small':           {'tr': 'Küçük',
                             'en': 'Small'},
    'font_medium':          {'tr': 'Orta',
                             'en': 'Medium'},
    'font_large':           {'tr': 'Büyük',
                             'en': 'Large'},
    'font_custom':          {'tr': 'Özel',
                             'en': 'Custom'},
    'label_position':       {'tr': 'Etiket pozisyonu',
                             'en': 'Label position'},
    'export_format':        {'tr': 'Çıktı formatı',
                             'en': 'Export format'},
    'render_collage':       {'tr': '🎨 Kolajı oluştur',
                             'en': '🎨 Render collage'},
    'download_collage':     {'tr': '⬇️ Kolajı indir',
                             'en': '⬇️ Download collage'},

    # ---------------------------------------------------------------- Generic messages
    'no_image_loaded':      {'tr': '⚠️ Önce bir görüntü yükle.',
                             'en': '⚠️ Upload an image first.'},
    'computing_overlay':    {'tr': 'Overlay hesaplanıyor...',
                             'en': 'Computing overlay...'},
    'parameters_saved':     {'tr': '✓ Parametreler kaydedildi.',
                             'en': '✓ Parameters saved.'},
    'error_generic':        {'tr': 'Hata oluştu',
                             'en': 'An error occurred'},

    # ---- Phase 4 additions ----
    'algorithm_section': {'tr': '##### 🔧 Algoritma', 'en': '##### 🔧 Algorithm'},
    'algorithm_method': {'tr': 'Yöntem', 'en': 'Method'},
    'help_algo_family': {'tr': 'Yaklaşım ailesi: klasik eşikleme, blob tespiti, renk-tabanlı, hibrit veya modern derin öğrenme.', 'en': 'Approach family: classical thresholding, blob detection, color-based, hybrid, or modern deep learning.'},
    'help_algo_specific': {'tr': 'Seçtiğin yöntem ailesindeki spesifik algoritma. Aşağıdaki sliderlar bu algoritmaya özgüdür.', 'en': 'Specific algorithm within the selected family. The sliders below are specific to this algorithm.'},
    'family_classical_full': {'tr': '🔵 Klasik Eşikleme', 'en': '🔵 Classical Thresholding'},
    'family_blob_full': {'tr': '🟢 Blob/Region Detection', 'en': '🟢 Blob/Region Detection'},
    'family_color_full': {'tr': '🟣 Renk/Clustering Tabanlı', 'en': '🟣 Color/Clustering-Based'},
    'family_hybrid_full': {'tr': '🤝 Hibrit (Klasik + Renk)', 'en': '🤝 Hybrid (Classical + Color)'},
    'family_modern_full': {'tr': '🚀 Modern Deep Learning', 'en': '🚀 Modern Deep Learning'},
    'p_dog': {'tr': '**DoG Parametreleri**', 'en': '**DoG Parameters**'},
    'p_mser': {'tr': '**MSER Parametreleri**', 'en': '**MSER Parameters**'},
    'p_sauvola': {'tr': '**Sauvola Parametreleri**', 'en': '**Sauvola Parameters**'},
    'p_color': {'tr': '**Renk Mesafesi Parametreleri**', 'en': '**Color Distance Parameters**'},
    'p_multiotsu': {'tr': '**Multi-Otsu Parametreleri** (otomatik, parametresiz)', 'en': '**Multi-Otsu Parameters** (automatic, parameter-free)'},
    'p_bottomhat': {'tr': '**Bottom-Hat Morfoloji Parametreleri**', 'en': '**Bottom-Hat Morphology Parameters**'},
    'p_watershed': {'tr': '**Watershed Parametreleri** (yapışık pore\'ları ayırır)', 'en': '**Watershed Parameters** (separates touching pores)'},
    'window_size': {'tr': 'Pencere boyutu', 'en': 'Window size'},
    'analysis_params': {'tr': '##### ⚙️ Analiz Parametreleri', 'en': '##### ⚙️ Analysis Parameters'},
    'banner_suffix': {'tr': 'soldan ayarları yap, sonuçları burada gör.', 'en': 'configure settings on the left, see results here.'},
    'load_image_left': {'tr': '👈 Soldan görüntü yükle.', 'en': '👈 Upload an image from the left.'},
    'mode_pore_banner': {'tr': '🔬 Gözenek Analizi Modu', 'en': '🔬 Pore Segmentation Mode'},
    'mode_palette_banner': {'tr': '🎨 Renk Paleti Modu', 'en': '🎨 Color Palette Mode'},
    'mode_aging_banner': {'tr': '🔄 Yaşlandırma Analizi Modu', 'en': '🔄 Aging Analysis Mode'},
    'footer_text': {'tr': 'Gözenek ve Renk Tespit Yazılımı v1.2 — 2026  |  Murat SERT — AKÜ', 'en': 'Pore Segmentation Suite v1.2.0 — 2026  |  Murat SERT — Afyon Kocatepe University'},
    'dominant_colors_label': {'tr': 'dominant renk', 'en': 'dominant colors'},

    # ---- Phase 6 additions (Aging Analysis i18n) ----
    'aging_sidebar_title': {'tr': '🔄  **Aging Analizi (Pre/Post)**', 'en': '🔄  **Aging Analysis (Pre/Post)**'},
    'aging_sidebar_descr': {'tr': 'Yaşlandırma deneyi öncesi/sonrası yüzey renk değişimini ölçer (TS EN 15886 + CIEDE2000)', 'en': 'Measures surface color change before/after aging treatment (TS EN 15886 + CIEDE2000)'},
    'aging_compare_mode': {'tr': 'Karşılaştırma Modu', 'en': 'Comparison Mode'},
    'aging_mode_single': {'tr': '🪞 Tek-çift (1 pre + 1 post)', 'en': '🪞 Single pair (1 pre + 1 post)'},
    'aging_mode_multi': {'tr': '🔢 Çoklu numune (N pre + N post)', 'en': '🔢 Multi-specimen (N pre + N post)'},
    'pre_images_section': {'tr': '##### 📤 Deney Öncesi Görüntüleri', 'en': '##### 📤 Pre-treatment Images'},
    'post_images_section': {'tr': '##### 📤 Deney Sonrası Görüntüleri', 'en': '##### 📤 Post-treatment Images'},
    'pairs_ready_template': {'tr': '✓ {npre} pre + {npost} post = {npairs} eşleştirilecek çift', 'en': '✓ {npre} pre + {npost} post = {npairs} pairs to compare'},
    'single_mode_warn': {'tr': 'Tek-çift modunda 1\'er görüntü yükle. Daha fazlası varsa Çoklu moda geç.', 'en': 'Upload one image each in Single-pair mode. Use Multi-specimen mode for more.'},
    'aging_results_title': {'tr': 'Yaslandirma Karsilastirma Sonuclari (Pre/Post)', 'en': 'Aging Comparison Results (Pre/Post)'},
    'aging_n_samples': {'tr': '{n} numune | {method}', 'en': '{n} samples | {method}'},
    'general_summary': {'tr': '##### Genel Ozet', 'en': '##### Summary'},
    'metric_mean_dE': {'tr': 'Ortalama dE', 'en': 'Mean ΔE'},
    'metric_minmax_dE': {'tr': 'Min/Max dE', 'en': 'Min/Max ΔE'},
    'metric_mean_dL': {'tr': 'Ortalama dL*', 'en': 'Mean ΔL*'},
    'metric_cv_dE': {'tr': 'CV (dE)', 'en': 'CV (ΔE)'},
    'per_sample_table': {'tr': '##### Numune Karsilastirma Tablosu', 'en': '##### Per-sample Comparison Table'},
    'col_sample': {'tr': 'Numune', 'en': 'Sample'},
    'col_class': {'tr': 'Sinif', 'en': 'Class'},
    'color_compare_section': {'tr': '##### Renk Karsilastirma (Pre / Post)', 'en': '##### Color Comparison (Pre / Post)'},
    'bar_chart_section': {'tr': '##### Numune x dE Bar Chart', 'en': '##### Per-sample ΔE Bar Chart'},
    'bar_chart_caption': {'tr': 'Dikey kesikli cizgiler perceptual esiklerdir: 1=just noticeable, 3.5=barely visible, 5=clear, 10=marked', 'en': 'Dashed vertical lines mark perceptual thresholds: 1=just noticeable, 3.5=barely visible, 5=clear, 10=marked'},
    'stat_analysis_section': {'tr': '##### Istatistiksel Analiz (Paired)', 'en': '##### Statistical Analysis (Paired)'},
    'stat_test_label': {'tr': 'Test', 'en': 'Test'},
    'stat_pvalue': {'tr': 'p-deger', 'en': 'p-value'},
    'stat_significant': {'tr': 'Anlamli', 'en': 'Significant'},
    'stat_nonsignificant': {'tr': 'Anlamsiz', 'en': 'Not significant'},
    'stat_cohen_d': {'tr': 'Cohen d', 'en': 'Cohen\'s d'},
    'stat_ci': {'tr': '95% CI', 'en': '95% CI'},
    'stat_test_prefix': {'tr': '**Test:**', 'en': '**Test:**'},
    'stat_normal_yes': {'tr': 'Normal kabul', 'en': 'Normal accepted'},
    'stat_normal_no': {'tr': 'Normal degil (non-param)', 'en': 'Non-normal (non-parametric)'},
    'stat_shapiro_prefix': {'tr': '**Shapiro-Wilk p:**', 'en': '**Shapiro-Wilk p:**'},

    # ---- Phase 7 additions (Pairing strategy + Downloads + classification map) ----
    'pair_strategy_section': {'tr': '##### 🔗 Eşleştirme Stratejisi', 'en': '##### 🔗 Pairing Strategy'},
    'pair_strategy_label': {'tr': 'Strateji', 'en': 'Strategy'},
    'pair_opt_alpha': {'tr': '🔤 Otomatik — alfabetik (dosya adına göre)', 'en': '🔤 Auto — alphabetic (by filename)'},
    'pair_opt_order': {'tr': '🔢 Otomatik — yükleme sırası (1.pre ↔ 1.post)', 'en': '🔢 Auto — upload order (1.pre ↔ 1.post)'},
    'pair_opt_manual': {'tr': '✋ Manuel eşleştirme (tablo)', 'en': '✋ Manual pairing (table)'},
    'pair_manual_caption': {'tr': 'Her pre-test için karşılık gelen post-test\'i seç:', 'en': 'Select the matching post-test for each pre-test:'},
    'pair_manual_match_prefix': {'tr': 'eşleşir', 'en': 'matches'},
    'dE_metric_label': {'tr': 'ΔE metriği', 'en': 'ΔE metric'},
    'dE_2000_opt': {'tr': 'ΔE-2000 (modern, önerilen)', 'en': 'ΔE-2000 (modern, recommended)'},
    'dE_94_opt': {'tr': 'ΔE-94 (CIE 1994)', 'en': 'ΔE-94 (CIE 1994)'},
    'dE_76_opt': {'tr': 'ΔE-76 (CIE 1976, klasik)', 'en': 'ΔE-76 (CIE 1976, classical)'},
    'analysis_depth_label': {'tr': 'Analiz Derinliği', 'en': 'Analysis Depth'},
    'depth_standard': {'tr': '📊 Standart (mean color + ΔE + istatistik)', 'en': '📊 Standard (mean color + ΔE + statistics)'},
    'depth_detailed': {'tr': '🔬 Detaylı (+ uniformity karşılaştırması)', 'en': '🔬 Detailed (+ uniformity comparison)'},
    'pixel_sample_size': {'tr': 'Pixel örnekleme boyutu', 'en': 'Pixel sample size'},
    'estimated_time_template': {'tr': '⏱️ Tahmini süre: ~{secs:.0f}s ({n} numune)', 'en': '⏱️ Estimated time: ~{secs:.0f}s ({n} samples)'},
    'download_options': {'tr': '##### İndirme Seçenekleri', 'en': '##### Download Options'},
    'btn_per_pair_csv': {'tr': 'Per-pair CSV', 'en': 'Per-pair CSV'},
    'btn_full_json': {'tr': 'Full JSON', 'en': 'Full JSON'},
    'btn_md_report': {'tr': 'Markdown rapor', 'en': 'Markdown report'},
    'btn_txt_summary': {'tr': 'TXT özet', 'en': 'TXT summary'},
    'label_tr_discussion': {'tr': 'TR (Tartışma için):', 'en': 'TR (for Discussion):'},
    'label_en_paper_ready': {'tr': 'EN (Paper-ready):', 'en': 'EN (Paper-ready):'},

    # ---- Phase 8 additions (Pore Segmentation result + overlay presets) ----
    'caption_original': {'tr': 'Orijinal', 'en': 'Original'},
    'caption_segmentation': {'tr': 'Segmentasyon', 'en': 'Segmentation'},
    'metric_porosity': {'tr': 'Görüntü Porozitesi', 'en': 'Image Porosity'},
    'metric_pore_count': {'tr': 'Pore Sayısı', 'en': 'Pore Count'},
    'metric_mean_area': {'tr': 'Ort. Alan (mm²)', 'en': 'Mean Area (mm²)'},
    'metric_mean_circ': {'tr': 'Ort. Dairesellik', 'en': 'Mean Circularity'},
    # -- P2: multi-method porosity spread (method-dependence / uncertainty) --
    'p2_title': {'tr': '🔬 Çoklu-yöntem porozite yayılımı (belirsizlik)',
                 'en': '🔬 Multi-method porosity spread (uncertainty)'},
    'p2_intro': {'tr': 'Aynı görüntüyü birden çok algoritma ile bölütleyip elde edilen porozite değerlerinin yayılımını gösterir. Tek bir "doğru sayı" yerine, ölçümün yönteme bağımlılığını ve buna bağlı belirsizliği şeffaf biçimde ortaya koyar.',
                 'en': 'Segments the same image with several algorithms and shows the spread of the resulting porosity values. Instead of a single "true number", it makes the method-dependence of the measurement and its associated uncertainty explicit.'},
    'p2_methods': {'tr': 'Çalıştırılacak algoritmalar', 'en': 'Algorithms to run'},
    'p2_run_btn': {'tr': '▶ Tüm seçili algoritmaları çalıştır', 'en': '▶ Run all selected algorithms'},
    'p2_running': {'tr': 'Algoritmalar aynı görüntü üzerinde çalıştırılıyor…', 'en': 'Running the algorithms on the same image…'},
    'p2_need_run': {'tr': 'En az iki algoritma seçip "Çalıştır"a basın.', 'en': 'Select at least two algorithms and press "Run".'},
    'p2_median': {'tr': 'Medyan porozite', 'en': 'Median porosity'},
    'p2_range': {'tr': 'Yayılım (aralık)', 'en': 'Spread (range)'},
    'p2_min': {'tr': 'En düşük', 'en': 'Minimum'},
    'p2_max': {'tr': 'En yüksek', 'en': 'Maximum'},
    'p2_chart_title': {'tr': 'Algoritmaya göre porozite (%) — kesikli çizgi: medyan', 'en': 'Porosity by algorithm (%) — dashed line: median'},
    'p2_interpret': {'tr': 'Seçilen yöntemler arasında porozite {spread} puan yayılım göstermektedir; bu, bildirilen porozitenin algoritma seçimine güçlü biçimde bağlı olduğu anlamına gelir. Yazılım bu bağımlılığı gizlemek yerine açıkça raporlar.',
                     'en': 'Across the selected methods, porosity spans {spread} percentage points; the reported porosity therefore depends strongly on the chosen algorithm. The software reports this dependence explicitly rather than hiding it.'},
    'p2_family': {'tr': 'Aile', 'en': 'Family'},
    'p2_method_col': {'tr': 'Algoritma', 'en': 'Algorithm'},
    'p2_porosity_col': {'tr': 'Porozite (%)', 'en': 'Porosity (%)'},
    'p2_download': {'tr': 'Yayılım tablosunu indir (CSV)', 'en': 'Download spread table (CSV)'},
    'p2_failed': {'tr': '(çalıştırılamadı)', 'en': '(failed)'},
    'reference_compare': {'tr': '🧪 Deneysel referans karşılaştırması (opsiyonel)', 'en': '🧪 Experimental reference comparison (optional)'},
    'segmentation_error': {'tr': 'Segmentasyon hatası', 'en': 'Segmentation error'},
    'overlay_style_label': {'tr': 'Overlay stili', 'en': 'Overlay style'},
    'fill_color_label': {'tr': 'Dolgu rengi', 'en': 'Fill color'},
    'color_picker': {'tr': 'Renk seç', 'en': 'Pick color'},
    'preset_green_light': {'tr': '🟢 Yeşil (açık taş)', 'en': '🟢 Green (light stone)'},
    'preset_yellow': {'tr': '🟡 Sarı parlak (universal)', 'en': '🟡 Bright yellow (universal)'},
    'preset_red': {'tr': '🔴 Kırmızı (alarm)', 'en': '🔴 Red (alarm)'},
    'preset_pink': {'tr': '🌸 Pembe (koyu taş)', 'en': '🌸 Pink (dark stone)'},
    'preset_magenta': {'tr': '🟣 Magenta (koyu taş)', 'en': '🟣 Magenta (dark stone)'},
    'preset_blue': {'tr': '🔵 Mavi (kontrast)', 'en': '🔵 Blue (contrast)'},
    'preset_cyan': {'tr': '🟦 Cyan/Turkuaz', 'en': '🟦 Cyan/Turquoise'},
    'preset_white': {'tr': '⚪ Beyaz (çok koyu taş)', 'en': '⚪ White (very dark stone)'},
    'preset_black': {'tr': '⚫ Siyah (çok açık taş)', 'en': '⚫ Black (very light stone)'},
    'preset_orange': {'tr': '🟠 Turuncu', 'en': '🟠 Orange'},
    'preset_auto': {'tr': '🤖 Auto (görüntüye göre)', 'en': '🤖 Auto (image-based)'},
    'preset_custom': {'tr': '🎨 Custom (kendin seç)', 'en': '🎨 Custom (pick your own)'},
    'auto_note_magenta': {'tr': '→ Magenta (açık taş tespit edildi)', 'en': '→ Magenta (light stone detected)'},
    'auto_note_green': {'tr': '→ Yeşil (orta tonda)', 'en': '→ Green (medium tone)'},
    'auto_note_yellow': {'tr': '→ Sarı (koyu taş tespit edildi)', 'en': '→ Yellow (dark stone detected)'},
    'auto_brightness_label': {'tr': '**Auto**: parlaklık', 'en': '**Auto**: brightness'},
    'role_pore': {'tr': '🕳️ pore', 'en': '🕳️ pore'},
    'role_matrix': {'tr': '☁️ matriks', 'en': '☁️ matrix'},

    # ------------------------------------------------ Palette detail panel (main)
    'pd_title':             {'tr': '🎨 Renk Yelpazesi — Detaylı Görselleştirme',
                             'en': '🎨 Color Palette — Detailed Visualization'},
    'pd_source':            {'tr': 'Kaynak', 'en': 'Source'},
    'pd_algorithm':         {'tr': 'Algoritma', 'en': 'Algorithm'},
    'pd_color_list':        {'tr': 'Renk Listesi (karanlıktan açığa)',
                             'en': 'Color List (dark → light)'},
    'pd_brightness':        {'tr': 'Parlaklık', 'en': 'Brightness'},
    'pd_hex_values':        {'tr': 'Hex değerleri (kopyala)',
                             'en': 'Hex Values (copy)'},
    'pd_pie':               {'tr': 'Renk Oranları (Pie Chart)',
                             'en': 'Color Proportions (Pie Chart)'},
    'pd_band':              {'tr': 'Palette Bandı (görsel)',
                             'en': 'Palette Band (visual)'},
    'pd_band_hint':         {'tr': '💡 Bant üzerinde imleci bekleterek tam hex+RGB+oran bilgisini görebilirsin.',
                             'en': '💡 Hover over the band to see the full hex + RGB + ratio info.'},
    'pd_download':          {'tr': '📥 İndir', 'en': '📥 Download'},

    # ------------------------------------------------ Delta-E comparison
    'de_title':             {'tr': '🔬 ΔE Renk Karşılaştırma (CIE)',
                             'en': '🔬 ΔE Color Comparison (CIE)'},
    'de_caption':           {'tr': 'İki rengin perceptual (algısal) farkını ölç. ΔE-2000 modern CIE standardıdır (Sharma et al. 2005).',
                             'en': 'Measure the perceptual difference between two colors. ΔE-2000 is the modern CIE standard (Sharma et al. 2005).'},
    'de_pick_from_palette': {'tr': "🎨 Palette'ten seç", 'en': '🎨 Pick from palette'},
    'de_color_a':           {'tr': 'Renk A', 'en': 'Color A'},
    'de_color_b':           {'tr': 'Renk B', 'en': 'Color B'},
    'de_pick':              {'tr': 'Seç', 'en': 'Select'},
    'de_help_76':           {'tr': 'Klasik Euclidean Lab mesafesi',
                             'en': 'Classic Euclidean Lab distance'},
    'de_help_94':           {'tr': 'Chroma/hue ağırlıklı', 'en': 'Chroma/hue weighted'},
    'de_help_2k':           {'tr': 'CIEDE2000 — Q1 dergi standardı (Sharma 2005)',
                             'en': 'CIEDE2000 — Q1 journal standard (Sharma 2005)'},
    'de_visual_interp':     {'tr': 'Görsel Yorum', 'en': 'Visual Interpretation'},
    'de_detail_expander':   {'tr': '🔍 Detaylı Lab/LCh değerleri',
                             'en': '🔍 Detailed Lab/LCh values'},
    'de_metric_col':        {'tr': 'Metrik', 'en': 'Metric'},
    'de_scale_hint':        {'tr': '💡 ΔE < 1: fark edilmez | 1-2: eğitimli göz | 2-3.5: zar zor | 3.5-5: belirgin | 5-10: net | >10: çok farklı',
                             'en': '💡 ΔE < 1: imperceptible | 1-2: trained eye | 2-3.5: barely | 3.5-5: noticeable | 5-10: clear | >10: very different'},
    'de_error':             {'tr': 'ΔE hesaplama hatası', 'en': 'ΔE computation error'},

    # ------------------------------------------------ Color homogeneity (uniformity)
    'uni_title':            {'tr': '📐 Renk Homojenliği Analizi (CIE Lab Uniformity)',
                             'en': '📐 Color Homogeneity Analysis (CIE Lab Uniformity)'},
    'uni_caption':          {'tr': 'Görüntü genelinde renk dağılımının ne kadar homojen olduğunu ölçer. Taş kalite kontrolü ve tuz hasarı değerlendirmesi için.',
                             'en': 'Measures how homogeneous the color distribution is across the image. For stone quality control and salt-damage assessment.'},
    'uni_sample_size':      {'tr': 'Örnekleme boyutu', 'en': 'Sample size'},
    'uni_sample_help':      {'tr': 'Yüksek = daha doğru, daha yavaş',
                             'en': 'Higher = more accurate, slower'},
    'uni_compute_btn':      {'tr': '📐 Homojenlik Skorunu Hesapla',
                             'en': '📐 Compute Homogeneity Score'},
    'uni_error':            {'tr': 'Uniformity hesaplama hatası',
                             'en': 'Uniformity computation error'},
    'uni_mean_color':       {'tr': 'Görüntünün Ortalama Rengi', 'en': 'Image Mean Color'},
    'uni_score':            {'tr': 'Homojenlik Skoru', 'en': 'Homogeneity Score'},
    'uni_classification':   {'tr': 'Sınıflandırma', 'en': 'Classification'},
    'uni_lab_stats':        {'tr': 'CIE Lab İstatistikleri', 'en': 'CIE Lab Statistics'},
    'uni_col_channel':      {'tr': 'Kanal', 'en': 'Channel'},
    'uni_col_mean':         {'tr': 'Ortalama', 'en': 'Mean'},
    'uni_col_std':          {'tr': 'Standart Sapma (σ)', 'en': 'Standard Deviation (σ)'},
    'uni_col_interp':       {'tr': 'Yorum', 'en': 'Interpretation'},
    'uni_interp_L_var':     {'tr': 'Parlaklık değişkenliği', 'en': 'Brightness variability'},
    'uni_interp_L_uniform': {'tr': 'Düzgün parlaklık', 'en': 'Uniform brightness'},
    'uni_interp_a_var':     {'tr': 'Yeşil-kırmızı değişkenliği', 'en': 'Green-red variability'},
    'uni_interp_a_uniform': {'tr': 'Tutarlı a* renk', 'en': 'Consistent a* color'},
    'uni_interp_b_var':     {'tr': 'Mavi-sarı değişkenliği', 'en': 'Blue-yellow variability'},
    'uni_interp_b_uniform': {'tr': 'Tutarlı b* renk', 'en': 'Consistent b* color'},
    'uni_de_dist':          {'tr': 'ΔE-2000 Renk Dağılımı (ortalama renkten sapma)',
                             'en': 'ΔE-2000 Color Distribution (deviation from mean color)'},
    'uni_de_avg':           {'tr': 'Ortalama ΔE', 'en': 'Mean ΔE'},
    'uni_de_std':           {'tr': 'Std ΔE', 'en': 'Std ΔE'},
    'uni_de_p95':           {'tr': 'p95 ΔE', 'en': 'p95 ΔE'},
    'uni_de_p95_help':      {'tr': 'En aykırı %5 piksel', 'en': 'Most deviant 5% of pixels'},
    'uni_de_max':           {'tr': 'Max ΔE', 'en': 'Max ΔE'},
    'uni_de_max_help':      {'tr': 'En uç piksel (outlier)', 'en': 'Most extreme pixel (outlier)'},
    'uni_sci_interp':       {'tr': 'Bilimsel Yorum', 'en': 'Scientific Interpretation'},
    'uni_interp_high':      {'tr': 'Bu taş **görsel olarak çok tutarlı**. Cephe kaplaması, batch tutarlılığı gerektiren uygulamalar için ideal.',
                             'en': 'This stone is **visually very consistent**. Ideal for façade cladding and applications that require batch consistency.'},
    'uni_interp_mid':       {'tr': 'Bu taş **kabul edilebilir homojenlikte**. Dekoratif kullanım için uygun, fakat kritik renk eşleştirme gerekiyorsa örnek değiştirmek faydalı olabilir.',
                             'en': 'This stone has **acceptable homogeneity**. Suitable for decorative use, but if critical color matching is required, switching the sample may help.'},
    'uni_interp_low':       {'tr': 'Bu taş **belirgin renk heterojenliği** gösteriyor (örn. bantlı yapı, fosil içeriği, alterasyon). Bu, doğal karakter olabilir ama tutarlılık kritikse alternatif batch düşünülmeli.',
                             'en': 'This stone shows **marked color heterogeneity** (e.g. banding, fossil content, alteration). This may be natural character, but if consistency is critical an alternative batch should be considered.'},
    'uni_save_pre':         {'tr': '💾 Pre-test referansı olarak kaydet',
                             'en': '💾 Save as pre-test reference'},
    'uni_saved_pre':        {'tr': '✓ Pre-test uniformity kaydedildi',
                             'en': '✓ Pre-test uniformity saved'},
    'uni_save_post':        {'tr': '💾 Post-test sonuç olarak karşılaştır',
                             'en': '💾 Compare as post-test result'},
    'uni_warn_pre':         {'tr': 'Önce pre-test referansı kaydet.',
                             'en': 'Save a pre-test reference first.'},
    'uni_compare_title':    {'tr': '🔄 Pre vs Post Karşılaştırma:',
                             'en': '🔄 Pre vs Post Comparison:'},
    'uni_damage_interp':    {'tr': 'Görsel Hasar Yorumu', 'en': 'Visual Damage Interpretation'},
    'uni_json_expander':    {'tr': '📥 Uniformity sonucunu JSON olarak indir',
                             'en': '📥 Download uniformity result as JSON'},
    'uni_need_image':       {'tr': 'Önce bir görüntü yükle.', 'en': 'Upload an image first.'},

    # ------------------------------------------------ Collage builder (main panel)
    'collage_panel_title':  {'tr': '🖼️ Oluşturulan Kolaj — Önizleme ve İndirme',
                             'en': '🖼️ Generated Collage — Preview & Download'},
    'collage_meta_line':    {'tr': 'Kolaj: {} × {} px | Hücre: {} | Hedef: {} cm @ {} DPI',
                             'en': 'Collage: {} × {} px | Cell: {} | Target: {} cm @ {} DPI'},
    'collage_cell_auto':    {'tr': '{} px (auto-fit)', 'en': '{} px (auto-fit)'},
    'collage_cell_manual':  {'tr': '{} px (manuel)', 'en': '{} px (manual)'},
    'collage_preview_cap':  {'tr': 'Önizleme (web çözünürlüğü)', 'en': 'Preview (web resolution)'},
    'collage_autocap_title':{'tr': '📝 Otomatik Caption (figür açıklaması)',
                             'en': '📝 Auto Caption (figure description)'},
    'collage_context':      {'tr': 'Bağlam', 'en': 'Context'},
    'collage_caption_edit': {'tr': 'Caption (düzenleyebilirsin)', 'en': 'Caption (editable)'},
    'collage_formats_title':{'tr': '📥 İndirilebilir Formatlar', 'en': '📥 Downloadable Formats'},
    'collage_quickstart_md':{'tr': "### 🖼️ Kolaj Oluşturucu — Hızlı Başlangıç\n1. **Mod seç:** Manuel / Quick (Aging'den) / Template\n2. **Grid boyutu** belirle (satır × sütun)\n3. **Görüntüleri yükle** (toplu drag&drop alfabetik sıraya göre dağıtılır)\n4. **Etiket içeriği** seç (Sample ID, % değerleri, ΔE...)\n5. **Etiket pozisyonu** seç:\n   - **inside_*** → görsel üzerinde kontrastlı banner\n   - **outside_*** → SEM tarzı, görsel dışında beyaz alan\n   - **none** → sadece görsel\n6. **Sütun başlıkları** + opsiyonel satır etiketleri\n7. **Dergi presetı** seç (Elsevier/Springer/ACS tek-veya çift-sütun)\n8. **DPI** seç (300 = print standart, 600 = ultra)\n9. **🎨 Kolajı Oluştur** → ana panelde önizleme + indirme\n\n### Çıktı formatları\n- **PNG** (default, baskı kalitesi)\n- **PDF** (vektör + raster, Adobe Acrobat)\n- **SVG** (Inkscape'te düzenlenebilir, PNG-embed)\n- **TIFF** (LZW compression, akademik dergi standart)\n\n### Standartlar\nKolaj boyutları **Elsevier/Springer/ACS** dergi figür yönergelerine uygundur (8.5 cm tek-sütun, 17.5 cm çift-sütun @ 300 DPI).",
                             'en': '### 🖼️ Collage Builder — Quick Start\n1. **Select mode:** Manual / Quick (from Aging) / Template\n2. **Set grid size** (rows × columns)\n3. **Upload images** (bulk drag & drop distributed in alphabetical order)\n4. **Choose label content** (Sample ID, % values, ΔE...)\n5. **Choose label position:**\n   - **inside_*** → contrast banner over the image\n   - **outside_*** → SEM-style, white area outside the image\n   - **none** → image only\n6. **Column headers** + optional row labels\n7. **Select journal preset** (Elsevier/Springer/ACS single- or double-column)\n8. **Select DPI** (300 = print standard, 600 = ultra)\n9. **🎨 Build Collage** → preview + download in the main panel\n\n### Output formats\n- **PNG** (default, print quality)\n- **PDF** (vector + raster, Adobe Acrobat)\n- **SVG** (editable in Inkscape, PNG-embed)\n- **TIFF** (LZW compression, academic journal standard)\n\n### Standards\nCollage dimensions comply with **Elsevier/Springer/ACS** journal figure guidelines (8.5 cm single-column, 17.5 cm double-column @ 300 DPI).'},

    # ============ Full-coverage batch (sidebar + main panels) ============
    'stone_custom_new': {'tr': 'Custom (yeni)', 'en': 'Custom (new)'},
    'algo_color_distance': {'tr': 'Color Distance (Renk Mesafesi)', 'en': 'Color Distance'},
    'ps_max_color_dist': {'tr': 'Max renk mesafesi (Euclidean)', 'en': 'Max color distance (Euclidean)'},
    'ps_help_multiotsu': {'tr': "Histogram'ı N seviyeye böler", 'en': 'Splits the histogram into N levels'},
    'ps_method': {'tr': 'Yöntem', 'en': 'Method'},
    'ps_help_autothresh': {'tr': 'triangle=histogram tepe-uzaklığı, yen=entropi, otsu=variance', 'en': 'triangle=histogram peak-distance, yen=entropy, otsu=variance'},
    'ps_kernel_size': {'tr': 'Kernel boyutu (px)', 'en': 'Kernel size (px)'},
    'ps_response_pct': {'tr': 'Yanıt percentile', 'en': 'Response percentile'},
    'ps_gmm_caption': {'tr': '**GMM Renk Kümeleme**', 'en': '**GMM Color Clustering**'},
    'ps_n_components': {'tr': 'Bileşen sayısı', 'en': 'Number of components'},
    'ps_dark_components': {'tr': 'En koyu kaç bileşeni pore say', 'en': 'How many darkest components count as pore'},
    'ps_min_dist': {'tr': 'Min mesafe (px)', 'en': 'Min distance (px)'},
    'ps_help_mindist': {'tr': 'Local maxima arasındaki minimum mesafe', 'en': 'Minimum distance between local maxima'},
    'ps_base_thresh': {'tr': 'Kaba eşik', 'en': 'Coarse threshold'},
    'ps_model_size': {'tr': 'Model boyutu', 'en': 'Model size'},
    'ps_sam_t': {'tr': 'sam2_t.pt (39MB, hızlı)', 'en': 'sam2_t.pt (39MB, fast)'},
    'ps_sam_b': {'tr': 'sam2_b.pt (80MB, dengeli)', 'en': 'sam2_b.pt (80MB, balanced)'},
    'ps_sam_l': {'tr': 'sam2_l.pt (224MB, en doğru)', 'en': 'sam2_l.pt (224MB, most accurate)'},
    'ps_sam_download': {'tr': 'İlk kullanımda model otomatik indirilir (~80MB).', 'en': 'The model is downloaded automatically on first use (~80MB).'},
    'ps_sam_not_installed': {'tr': '⚠️ SAM 2 yüklü değil.', 'en': '⚠️ SAM 2 is not installed.'},
    'ps_restart_after_install': {'tr': 'Kurulumdan sonra uygulamayı yeniden başlat.', 'en': 'Restart the app after installation.'},
    'ps_obj_diameter': {'tr': 'Ortalama nesne çapı (px, 0=auto)', 'en': 'Average object diameter (px, 0=auto)'},
    'ps_cellpose_not_installed': {'tr': '⚠️ CellPose yüklü değil.', 'en': '⚠️ CellPose is not installed.'},
    'ps_min_pore_area': {'tr': 'Min pore alanı (px)', 'en': 'Min pore area (px)'},
    'ps_ecc_filter': {'tr': 'Eccentricity filtresi (bantları reddet)', 'en': 'Eccentricity filter (reject bands)'},
    'ps_max_ecc': {'tr': 'Max eccentricity (1=çizgi, 0=daire)', 'en': 'Max eccentricity (1=line, 0=circle)'},
    'ps_sol_filter': {'tr': 'Solidity filtresi (düzensiz şekilleri reddet)', 'en': 'Solidity filter (reject irregular shapes)'},
    'ps_min_sol': {'tr': 'Min solidity (1=konveks, 0=düzensiz)', 'en': 'Min solidity (1=convex, 0=irregular)'},
    'ps_texture_filter': {'tr': 'Doku filtresi (fosil/mineralleri reddet)', 'en': 'Texture filter (reject fossils/minerals)'},
    'ps_max_interior_std': {'tr': 'Max iç std (yüksek=dokulu, düşük=düz)', 'en': 'Max interior std (high=textured, low=flat)'},
    'ps_dark_thresh_factor': {'tr': 'Karanlık eşik çarpanı', 'en': 'Dark threshold factor'},
    'ps_preset_save_hdr': {'tr': '💾 Preset Kaydet', 'en': '💾 Save Preset'},
    'ps_preset_name': {'tr': 'Preset adı', 'en': 'Preset name'},
    'ps_notes': {'tr': 'Notlar', 'en': 'Notes'},
    'ps_saved': {'tr': 'Kaydedildi', 'en': 'Saved'},
    'cp_expander_title': {'tr': '🎨  **Renk Yelpazesi**', 'en': '🎨  **Color Palette**'},
    'cp_intro': {'tr': 'Bir görüntüden dominant renkleri çıkarır (K-means tarzı kümeleme). Sonuç JSON palet olarak kaydedilebilir veya algoritmada kullanılabilir.', 'en': 'Extracts dominant colors from an image (K-means style clustering). The result can be saved as a JSON palette or used in the algorithm.'},
    'cp_source_img': {'tr': '📂 Kaynak Görüntü', 'en': '📂 Source Image'},
    'cp_use_loaded': {'tr': '🖼️ Yüklü görüntüyü kullan', 'en': '🖼️ Use loaded image'},
    'cp_upload_new': {'tr': '📤 Yeni görüntü yükle', 'en': '📤 Upload new image'},
    'cp_active_img': {'tr': 'Aktif görüntü', 'en': 'Active image'},
    'cp_warn_load_first': {'tr': 'Önce Analize Başla sekmesinden görüntü yükle.', 'en': 'First upload an image from the Start Analysis tab.'},
    'cp_image_file': {'tr': 'Görüntü dosyası', 'en': 'Image file'},
    'cp_algo_kmeans': {'tr': 'K-means (klasik)', 'en': 'K-means (classic)'},
    'cp_algo_minibatch': {'tr': 'MiniBatch K-means (hızlı)', 'en': 'MiniBatch K-means (fast)'},
    'cp_algo_gmm': {'tr': 'GMM (probabilistik)', 'en': 'GMM (probabilistic)'},
    'cp_algo_meanshift': {'tr': 'MeanShift (otomatik küme sayısı)', 'en': 'MeanShift (auto cluster count)'},
    'cp_algo_mediancut': {'tr': 'Median Cut (PIL klasik)', 'en': 'Median Cut (PIL classic)'},
    'cp_help_algo': {'tr': 'K-means en yaygın. Median Cut görüntü kuantizasyonu için klasik. MeanShift küme sayısını kendi belirler.', 'en': 'K-means is most common. Median Cut is classic for image quantization. MeanShift determines the cluster count itself.'},
    'cp_help_ncolors': {'tr': 'Görüntüden çıkarılacak dominant renk adedi', 'en': 'Number of dominant colors to extract from the image'},
    'cp_space_lab': {'tr': 'Lab (perceptual - önerilen)', 'en': 'Lab (perceptual - recommended)'},
    'cp_help_space': {'tr': 'Lab insan görüşüne yakın; RGB doğrudan; HSV hue/saturation ayrımı için iyi.', 'en': 'Lab is close to human vision; RGB is direct; HSV is good for hue/saturation separation.'},
    'cp_sample_size': {'tr': 'Örnekleme boyutu (hız)', 'en': 'Sample size (speed)'},
    'cp_all': {'tr': 'Tümü', 'en': 'All'},
    'cp_help_sample': {'tr': 'Büyük görüntülerde sub-sampling hızı artırır', 'en': 'Sub-sampling speeds up processing on large images'},
    'cp_compute_btn': {'tr': '🎨 Paleti Hesapla', 'en': '🎨 Compute Palette'},
    'cp_colors_extracted': {'tr': 'renk çıkarıldı', 'en': 'colors extracted'},
    'err_generic': {'tr': 'Hata', 'en': 'Error'},
    'cp_info_load': {'tr': 'Devam etmek için bir görüntü yükle.', 'en': 'Upload an image to continue.'},
    'cp_extracted_palette': {'tr': '🎨 Çıkarılan Palet', 'en': '🎨 Extracted Palette'},
    'cp_detail_hint': {'tr': '💡 Detaylı görselleştirme ve indirme seçenekleri için ana panele bak.', 'en': '💡 See the main panel for detailed visualization and download options.'},
    'cp_stone_code_opt': {'tr': 'Taş kodu (opsiyonel)', 'en': 'Stone code (optional)'},
    'cp_help_save_code': {'tr': 'Bu paleti hangi taş için kaydet?', 'en': 'Which stone should this palette be saved for?'},
    'cp_json_save': {'tr': '💾 JSON kaydet', 'en': '💾 Save JSON'},
    'cp_make_active': {'tr': '🔗 Aktif palet yap', 'en': '🔗 Make active palette'},
    'cp_help_make_active': {'tr': 'Bu paleti Analize Başla sekmesinde aktif et', 'en': 'Activate this palette in the Start Analysis tab'},
    'cp_activated': {'tr': 'Bu palet Analize Başla sekmesinde aktif edildi', 'en': 'This palette was activated in the Start Analysis tab'},
    'ag_intro': {'tr': 'Yaşlandırma deneyi öncesi/sonrası yüzey renk değişimini ölçer (TS EN 15886 + CIEDE2000)', 'en': 'Measures pre/post aging surface color change (TS EN 15886 + CIEDE2000)'},
    'ag_pretest_imgs': {'tr': 'pre-test görüntüsü', 'en': 'pre-test image(s)'},
    'ag_posttest_imgs': {'tr': 'post-test görüntüsü', 'en': 'post-test image(s)'},
    'ag_equal_required': {'tr': 'Eşit sayı gerekli', 'en': 'Equal counts required'},
    'ag_run_btn': {'tr': '🔬 Karşılaştırma Analizini Çalıştır', 'en': '🔬 Run Comparison Analysis'},
    'ag_comparing': {'tr': 'çift karşılaştırılıyor...', 'en': 'pairs being compared...'},
    'ag_processing_error': {'tr': 'işlenirken hata', 'en': 'error while processing'},
    'ag_analyzed': {'tr': 'çift analiz edildi. Detaylar ana panelde.', 'en': 'pairs analyzed. Details in the main panel.'},
    'ag_info_equal': {'tr': 'Eşit sayıda pre ve post görüntü yükleyince butona tıklayabilirsin.', 'en': 'Once you upload equal numbers of pre and post images, you can click the button.'},
    'ag_mean_diff': {'tr': 'Ortalama fark', 'en': 'Mean difference'},
    'ag_auto_interp_hdr': {'tr': 'Otomatik Bilimsel Yorum', 'en': 'Automatic Scientific Interpretation'},
    'cb_intro': {'tr': 'Q1 dergi standardında figür kolajı üret (PNG/PDF/SVG/TIFF)', 'en': 'Generate a figure collage at Q1 journal standard (PNG/PDF/SVG/TIFF)'},
    'cb_mode_manual': {'tr': '🅰️ Manuel (sıfırdan)', 'en': '🅰️ Manual (from scratch)'},
    'cb_mode_quick': {'tr': '🅱️ Quick (Aging sonuçlarından)', 'en': '🅱️ Quick (from Aging results)'},
    'cb_mode_template': {'tr': '🅲️ Template (hazır şablon)', 'en': '🅲️ Template (ready template)'},
    'cb_grid_size': {'tr': '📐 Grid Boyutu', 'en': '📐 Grid Size'},
    'cb_images_hdr': {'tr': '📤 Görüntüler', 'en': '📤 Images'},
    'cb_bulk_upload': {'tr': 'Toplu yükle (alfabetik sıraya göre dağıt)', 'en': 'Bulk upload (distributed alphabetically)'},
    'cb_images_word': {'tr': 'görüntü', 'en': 'images'},
    'cb_cells_word': {'tr': 'hücre', 'en': 'cells'},
    'cb_uploaded_word': {'tr': 'yükledin', 'en': 'uploaded'},
    'cb_aging_ready': {'tr': 'Aging sonucu hazır', 'en': 'Aging result ready'},
    'cb_pairs_word': {'tr': 'çift', 'en': 'pairs'},
    'cb_grid_auto': {'tr': 'Grid otomatik olarak pre/post 2-sütun düzenine geçer', 'en': 'The grid automatically switches to a pre/post 2-column layout'},
    'cb_warn_run_aging': {'tr': 'Önce Yaşlandırma Analizi sekmesinden bir analiz çalıştır', 'en': 'First run an analysis from the Aging Analysis tab'},
    'cb_template_label': {'tr': 'Şablon', 'en': 'Template'},
    'cb_tpl_algo': {'tr': 'Algoritma karşılaştırma (orig + N alg)', 'en': 'Algorithm comparison (orig + N alg)'},
    'cb_tpl_aging': {'tr': 'Pre/Post yaşlandırma (6 örnek × pre+post)', 'en': 'Pre/Post aging (6 samples × pre+post)'},
    'cb_tpl_matrix': {'tr': 'Stone × Salt matriks (4×4)', 'en': 'Stone × Salt matrix (4×4)'},
    'cb_tpl_hint': {'tr': 'Şablon seçtikten sonra görüntüleri sırayla yükle', 'en': 'After selecting a template, upload images in order'},
    'cb_images_label': {'tr': 'Görüntüler', 'en': 'Images'},
    'cb_label_content': {'tr': '🏷️ Etiket İçeriği', 'en': '🏷️ Label Content'},
    'cb_label_which': {'tr': 'Hangi metrikler etiket olarak gözüksün?', 'en': 'Which metrics should appear as labels?'},
    'cb_metrics': {'tr': 'Metrikler', 'en': 'Metrics'},
    'cb_opt_algo_pct': {'tr': 'Algoritma %', 'en': 'Algorithm %'},
    'cb_opt_exp_pct': {'tr': 'Deneysel %', 'en': 'Experimental %'},
    'cb_opt_pore_count': {'tr': 'Pore sayısı', 'en': 'Pore count'},
    'cb_label_fmt': {'tr': 'Etiket format şablonu', 'en': 'Label format template'},
    'cb_label_pos_hdr': {'tr': '📍 Etiket Pozisyonu', 'en': '📍 Label Position'},
    'cb_position': {'tr': 'Pozisyon', 'en': 'Position'},
    'cb_pos_outside_bottom': {'tr': 'outside_bottom (SEM tarzı, beyaz alanda)', 'en': 'outside_bottom (SEM-style, in white area)'},
    'cb_pos_outside_top': {'tr': 'outside_top (üst beyaz şerit)', 'en': 'outside_top (top white strip)'},
    'cb_pos_outside_left': {'tr': 'outside_left (sol beyaz şerit)', 'en': 'outside_left (left white strip)'},
    'cb_pos_outside_right': {'tr': 'outside_right (sağ beyaz şerit)', 'en': 'outside_right (right white strip)'},
    'cb_pos_none': {'tr': 'none (etiket yok)', 'en': 'none (no label)'},
    'cb_help_pos': {'tr': 'Inside = görsel üzerinde banner. Outside = SEM tarzı, görsel dışında beyaz alanda', 'en': 'Inside = banner over the image. Outside = SEM-style, white area outside the image'},
    'cb_label_bg': {'tr': 'Etiket arka plan', 'en': 'Label background'},
    'cb_label_tc': {'tr': 'Etiket yazı rengi', 'en': 'Label text color'},
    'cb_font_size_label': {'tr': '🔤 Yazı Boyutu', 'en': '🔤 Font Size'},
    'cb_font_auto': {'tr': '🎯 Auto (cell boyutuna oranlı, önerilen)', 'en': '🎯 Auto (proportional to cell size, recommended)'},
    'cb_font_small': {'tr': '🔹 Küçük', 'en': '🔹 Small'},
    'cb_font_medium': {'tr': '🔸 Orta', 'en': '🔸 Medium'},
    'cb_font_large': {'tr': '🔶 Büyük', 'en': '🔶 Large'},
    'cb_font_custom': {'tr': '⚙️ Custom (manuel slider)', 'en': '⚙️ Custom (manual slider)'},
    'cb_help_font': {'tr': 'Auto: render boyutu büyüdükçe yazılar otomatik orantılı büyür (Q1 dergiler için optimum).', 'en': 'Auto: as the render size grows, text scales proportionally (optimal for Q1 journals).'},
    'cb_font_px': {'tr': 'Etiket font (px)', 'en': 'Label font (px)'},
    'cb_cell_spacing': {'tr': 'Hücre arası boşluk (px)', 'en': 'Cell spacing (px)'},
    'cb_cell_res_hdr': {'tr': '🖼️ Hücre Çözünürlüğü', 'en': '🖼️ Cell Resolution'},
    'cb_autofit': {'tr': "🎯 Auto-fit (dergi boyutu × DPI'ya göre otomatik)", 'en': '🎯 Auto-fit (automatic from journal size × DPI)'},
    'cb_help_autofit': {'tr': 'AÇIK: hücre boyutu hedef genişlik ve sütun sayısından hesaplanır → tam DPI uyumu. KAPALI: manuel seç.', 'en': 'ON: cell size is computed from target width and column count → exact DPI match. OFF: select manually.'},
    'cb_cell_size': {'tr': 'Hücre boyutu (px)', 'en': 'Cell size (px)'},
    'cb_help_cellsize': {'tr': 'Yüksek = daha keskin görüntü, daha büyük dosya. 600+ önerilir akademik kalite için.', 'en': 'Higher = sharper image, larger file. 600+ recommended for academic quality.'},
    'cb_headers_hdr': {'tr': '📝 Sütun & Satır Başlıkları', 'en': '📝 Column & Row Headers'},
    'cb_col_headers': {'tr': 'Sütun başlıkları ({n} adet, virgülle)', 'en': 'Column headers ({n}, comma-separated)'},
    'cb_row_labels': {'tr': 'Satır etiketleri ({n} adet, virgülle, boş bırak)', 'en': 'Row labels ({n}, comma-separated, leave empty)'},
    'cb_output_size_hdr': {'tr': '📐 Çıktı Boyutu (Akademik Standart)', 'en': '📐 Output Size (Academic Standard)'},
    'cb_journal_preset': {'tr': 'Dergi presetı', 'en': 'Journal preset'},
    'jp_elsevier_single': {'tr': 'Elsevier tek-sütun (8.5 cm)', 'en': 'Elsevier single-column (8.5 cm)'},
    'jp_elsevier_double': {'tr': 'Elsevier çift-sütun (17.5 cm)', 'en': 'Elsevier double-column (17.5 cm)'},
    'jp_springer_single': {'tr': 'Springer tek-sütun (8.4 cm)', 'en': 'Springer single-column (8.4 cm)'},
    'jp_springer_double': {'tr': 'Springer çift-sütun (17.4 cm)', 'en': 'Springer double-column (17.4 cm)'},
    'jp_acs_single': {'tr': 'ACS tek-sütun (8.25 cm)', 'en': 'ACS single-column (8.25 cm)'},
    'jp_acs_double': {'tr': 'ACS çift-sütun (17.78 cm)', 'en': 'ACS double-column (17.78 cm)'},
    'cb_custom_width': {'tr': 'Custom genişlik (cm)', 'en': 'Custom width (cm)'},
    'cb_help_dpi': {'tr': '72=web, 150=print preview, 300=print (standart), 600=ultra', 'en': '72=web, 150=print preview, 300=print (standard), 600=ultra'},
    'cb_footer_add': {'tr': 'Footer ekle (watermark/atıf)', 'en': 'Add footer (watermark/citation)'},
    'cb_footer_text': {'tr': 'Footer metni', 'en': 'Footer text'},
    'cb_footer_default': {'tr': 'Generated by Gözenek ve Renk Tespit Yazılımı v1.2 (Sert et al. 2026)', 'en': 'Generated by Pore Segmentation Suite v1.2 (Sert et al. 2026)'},
    'cb_render_btn': {'tr': '🎨 Kolajı Oluştur', 'en': '🎨 Build Collage'},
    'cb_rendering': {'tr': 'Kolaj oluşturuluyor...', 'en': 'Building collage...'},
    'cb_quick_warn': {'tr': "Quick mode: Aging görüntü kaynakları sidebar'da BytesIO olarak tutulmuyor; manuel modda yükle.", 'en': 'Quick mode: Aging image sources are not kept as BytesIO in the sidebar; upload in manual mode.'},
    'cb_no_image': {'tr': 'Görüntü yüklenmedi.', 'en': 'No image uploaded.'},
    'cb_collage_built': {'tr': 'Kolaj oluşturuldu', 'en': 'Collage built'},
    'set_title': {'tr': '⚙️  **Ayarlar**', 'en': '⚙️  **Settings**'},
    'set_wip': {'tr': '🚧 Bu bölüm geliştirme aşamasındadır.', 'en': '🚧 This section is under development.'},
    'set_feedback': {'tr': 'Özellik önerin mi var? GitHub issue aç veya e-posta gönder.', 'en': 'Have a feature suggestion? Open a GitHub issue or send an email.'},
    'about_title': {'tr': 'ℹ️  **Hakkında & Atıf**', 'en': 'ℹ️  **About & Citation**'},
    'pm_select_pore_color': {'tr': '⚠️ Lütfen paletten en az bir pore rengi seç.', 'en': '⚠️ Please select at least one pore color from the palette.'},
    'pm_help_alpha': {'tr': 'Düşük=daha saydam (orijinal daha görünür), Yüksek=daha opak', 'en': 'Low=more transparent (original more visible), High=more opaque'},
    'pm_help_thickness': {'tr': 'Kontur çizgisi kalınlığı', 'en': 'Contour line thickness'},
    'pm_ref_porosity': {'tr': 'TS EN 1936 açık porozite (%) — biliniyorsa', 'en': 'TS EN 1936 open porosity (%) — if known'},
    'pm_deviation': {'tr': 'Sapma', 'en': 'Deviation'},
    'pm_excellent_match': {'tr': '✓ Mükemmel uyum', 'en': '✓ Excellent match'},
    'pm_acceptable': {'tr': 'Kabul edilebilir', 'en': 'Acceptable'},
    'pm_improvable': {'tr': 'Geliştirilebilir', 'en': 'Could be improved'},
    'pm_high_deviation': {'tr': 'Yüksek sapma', 'en': 'High deviation'},
    'pm_pick_color_title': {'tr': '🎯 Görüntüden pore rengi seç (manuel)', 'en': '🎯 Pick pore color from image (manual)'},
    'pm_pick_caption': {'tr': 'Görüntüde bir pore üzerine tıkladığında pixel koordinatlarını gir (sol-üst köşe 0,0):', 'en': 'Enter the pixel coordinates when you click on a pore in the image (top-left corner 0,0):'},
    'pm_x_px': {'tr': 'X (piksel)', 'en': 'X (pixel)'},
    'pm_y_px': {'tr': 'Y (piksel)', 'en': 'Y (pixel)'},
    'pm_add_color_btn': {'tr': '🎯 Bu noktadaki rengi pore listesine ekle', 'en': '🎯 Add the color at this point to the pore list'},
    'pm_added': {'tr': 'Eklendi', 'en': 'Added'},
    'pm_pore_stats_title': {'tr': '🔎 Detaylı pore istatistikleri (ilk 50)', 'en': '🔎 Detailed pore statistics (first 50)'},
    'pm_col_area_px': {'tr': 'Alan (px)', 'en': 'Area (px)'},
    'pm_col_area_mm2': {'tr': 'Alan (mm²)', 'en': 'Area (mm²)'},
    'pm_col_perimeter': {'tr': 'Çevre (px)', 'en': 'Perimeter (px)'},
    'pm_col_circularity': {'tr': 'Dairesellik', 'en': 'Circularity'},
    'pm_col_mean_intensity': {'tr': 'Ortalama yoğunluk', 'en': 'Mean intensity'},
    'pm_download_all_csv': {'tr': '📥 Tüm pore detaylarını CSV indir', 'en': '📥 Download all pore details as CSV'},
    'pm_no_pores': {'tr': 'Pore tespit edilmedi.', 'en': 'No pores detected.'},
    'pm_download_outputs': {'tr': '📥 Çıktıları indir', 'en': '📥 Download outputs'},
    'set_planned_md': {'tr': '**Planlanan özellikler:**\n- 🌍 Dil seçimi (TR / EN / DE)\n- 🎨 Görünüm teması (Light / Dark)\n- 📏 Piksel ölçeği (mm/px) — kamera/zoom başına preset\n- 💾 Varsayılan çıktı klasörü\n- 📤 Toplu işlem (192 görüntü → tek tıkla)\n- 🔄 Varsayılan algoritma & parametreler\n- 📊 CSV ayraç tercihi (`,` vs `;`)\n- 🌐 Konfigürasyon paylaşımı (.json export/import)\n- 🔬 Custom palet yükleme (kendi colors.xlsx dosyalarınız)\n- 📐 Ölçek çubuğu (scale bar) overlay\n- 🎯 IoU/Dice metrik hesaplama (ground truth ile)', 'en': '**Planned features:**\n- 🌍 Language selection (TR / EN / DE)\n- 🎨 Appearance theme (Light / Dark)\n- 📏 Pixel scale (mm/px) — preset per camera/zoom\n- 💾 Default output folder\n- 📤 Batch processing (192 images → one click)\n- 🔄 Default algorithm & parameters\n- 📊 CSV separator preference (`,` vs `;`)\n- 🌐 Configuration sharing (.json export/import)\n- 🔬 Custom palette loading (your own colors.xlsx files)\n- 📐 Scale bar overlay\n- 🎯 IoU/Dice metric computation (with ground truth)'},
    'about_md': {'tr': '**Gözenek ve Renk Tespit Yazılımı v1.2**\n\nTravertenler ve benzer doğal yapı taşlarının yüzey gözenekliliğini  \ngörüntü işleme teknikleriyle tespit eden açık kaynak araç.\n\n---\n**Geliştirici:** Dr. Öğr. Üyesi Murat SERT  \nAfyon Kocatepe Üniversitesi  \nMermer ve Doğaltaş Teknolojileri Uygulama ve Araştırma Merkezi\n\n**Proje:** 24.MÜH.03 — AKÜ BAP\n\n---\n**Kullanılan kütüphaneler:** \nOpenCV · scikit-image · scikit-learn · Streamlit · NumPy\n\n**Lisans:** MIT (önerilen) — bilim için açık.\n\n---\n**Bu aracı kullanırsanız lütfen atıf yapın:**  \n> Sert, M. ve diğ. (2026). *Gözenek ve Renk Tespit Yazılımı v1.2.*  \n> Afyon Kocatepe Üniversitesi. (Hazırlık aşamasında)\n\n**İletişim:** msert@aku.edu.tr', 'en': '**Pore Segmentation Suite v1.2**\n\nAn open-source tool that detects the surface porosity of travertines and  \nsimilar natural building stones using image processing techniques.\n\n---\n**Developer:** Assist. Prof. Dr. Murat SERT  \nAfyon Kocatepe University  \nMarble and Natural Stone Technologies Application and Research Center\n\n**Project:** 24.MÜH.03 — AKÜ BAP\n\n---\n**Libraries used:** \nOpenCV · scikit-image · scikit-learn · Streamlit · NumPy\n\n**License:** MIT (recommended) — open for science.\n\n---\n**If you use this tool, please cite:**  \n> Sert, M. et al. (2026). *Pore Segmentation Suite v1.2.*  \n> Afyon Kocatepe University. (In preparation)\n\n**Contact:** msert@aku.edu.tr'},
    'cb_cmp_title': {'tr': '🆚 Karşılaştırma Kolajı (örnek × yöntem × öncesi/sonrası)', 'en': '🆚 Comparison Collage (sample × method × before/after)'},
    'cb_cmp_caption': {'tr': "Yüklenen görüntülere seçili yöntemleri uygular; orijinal + overlay panellerini, yönteme özel renkli 'Method: img% | Exp: ref%' etiketleriyle dergi-hazır bir kolaj olarak dizer.", 'en': "Runs the selected methods on the uploaded images and assembles original + overlay panels into a journal-ready collage with method-coloured 'Method: img% | Exp: ref%' labels."},
    'cb_cmp_before': {'tr': 'Öncesi (before) görüntüleri', 'en': 'Before images'},
    'cb_cmp_after': {'tr': 'Sonrası (after) görüntüleri — opsiyonel', 'en': 'After images — optional'},
    'cb_cmp_methods': {'tr': 'Yöntemler (her biri ayrı renk)', 'en': 'Methods (each gets its own colour)'},
    'cb_cmp_cell': {'tr': 'Hücre boyutu (px)', 'en': 'Cell size (px)'},
    'cb_cmp_use_ref': {'tr': 'Deneysel referans (Exp%) kullan', 'en': 'Use experimental reference (Exp%)'},
    'cb_cmp_ref': {'tr': 'Referans tablosu (her satır: SampleID: before, after)', 'en': 'Reference table (each line: SampleID: before, after)'},
    'cb_cmp_build': {'tr': '🆚 Karşılaştırma kolajını oluştur', 'en': '🆚 Build comparison collage'},
    'cb_cmp_need_before': {'tr': "Önce 'before' görüntülerini yükle.", 'en': "Upload 'before' images first."},
    'cb_cmp_need_method': {'tr': 'En az bir yöntem seç.', 'en': 'Select at least one method.'},
    'cb_cmp_running': {'tr': 'Karşılaştırma kolajı oluşturuluyor...', 'en': 'Building comparison collage...'},
    'cb_cmp_hdr_fs': {'tr': 'Başlık yazı boyutu', 'en': 'Header font size'},
    'cb_cmp_lbl_fs': {'tr': 'Panel etiketi yazı boyutu', 'en': 'Panel label font size'},
    'cb_cmp_vertical': {'tr': 'Satır etiketlerini dikey yaz', 'en': 'Vertical row labels'},
    'cb_cmp_colors': {'tr': 'Yöntem renkleri', 'en': 'Method colours'},
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def init_language():
    """Initialize language in session state. Call at top of app."""
    if 'lang' not in st.session_state:
        st.session_state.lang = DEFAULT_LANG


def T(key: str, fallback: str | None = None) -> str:
    """
    Translate a key to the current language.

    Args:
        key: Translation key (must exist in TRANSLATIONS dict)
        fallback: If key not found, use this (default: return key itself)

    Returns:
        Localized string
    """
    if 'lang' not in st.session_state:
        st.session_state.lang = DEFAULT_LANG
    lang = st.session_state.lang
    entry = TRANSLATIONS.get(key)
    if entry is None:
        return fallback if fallback is not None else key
    return entry.get(lang, entry.get(DEFAULT_LANG, key))


def render_language_selector(location='sidebar', label_visible: bool = False):
    """
    Render TR / EN flag selector.

    Args:
        location: 'sidebar' (default) or 'main' — where to place the selector
        label_visible: If True, show "Language / Dil" label above buttons
    """
    container = st.sidebar if location == 'sidebar' else st
    if label_visible:
        container.caption(T('language') + ' / Dil')

    col1, col2 = container.columns(2)

    current = st.session_state.get('lang', DEFAULT_LANG)

    # Use button type to indicate active language
    tr_type = 'primary' if current == 'tr' else 'secondary'
    en_type = 'primary' if current == 'en' else 'secondary'

    if col1.button('🇹🇷 TR', key='lang_btn_tr', type=tr_type, use_container_width=True):
        st.session_state.lang = 'tr'
        st.rerun()
    if col2.button('🇬🇧 EN', key='lang_btn_en', type=en_type, use_container_width=True):
        st.session_state.lang = 'en'
        st.rerun()


def get_current_language() -> str:
    """Returns current language code ('tr' or 'en')."""
    return st.session_state.get('lang', DEFAULT_LANG)

# ============================================================================
# CLASSIFICATION LABEL TRANSLATION (Aging Analysis)
# ============================================================================

CLASSIFICATION_TR_TO_EN = {
    'gorsel olarak fark edilmez (perceptually identical)': 'perceptually identical (not perceived)',
    'sadece egitimli goz fark eder (just noticeable)': 'just noticeable (trained eye only)',
    'egitimsiz goz zar zor gorur (barely visible)': 'barely visible (untrained eye)',
    'acik gorsel fark (clear difference)': 'clear difference',
    'belirgin gorsel hasar (marked damage)': 'marked visual damage',
}

COLOR_SCIENCE_TR_TO_EN = {
    # interpret_delta_e returns
    "Fark edilmez (perceptually identical)": "Imperceptible (perceptually identical)",
    "Sadece eğitimli göz fark eder (just noticeable)": "Only a trained eye notices (just noticeable)",
    "Eğitimsiz göz farkı zar zor görür": "Untrained eye barely sees the difference",
    "Açık fark (clear difference)": "Clear difference",
    "Belirgin görsel fark": "Marked visual difference",
    "Çok farklı (different color)": "Very different (different color)",
    # uniformity_class returns
    "🟢 Çok homojen": "🟢 Very homogeneous",
    "🔵 Homojen": "🔵 Homogeneous",
    "🟡 Orta heterojen": "🟡 Moderately heterogeneous",
    "🟠 Heterojen": "🟠 Heterogeneous",
    "🔴 Çok heterojen": "🔴 Very heterogeneous",
}

def translate_cs(label: str) -> str:
    """Translate a color_science.py output string to current language."""
    if st.session_state.get('lang', DEFAULT_LANG) == 'tr':
        return label
    return COLOR_SCIENCE_TR_TO_EN.get(label, label)


def translate_classification(label: str) -> str:
    """Translate aging analysis classification string from internal TR to current language."""
    if st.session_state.get('lang', 'en') == 'tr':
        return label
    # EN mode: lookup in map, fallback to original
    return CLASSIFICATION_TR_TO_EN.get(label, label)


# ---- Pore size distribution (MIP-style) feature ----
TRANSLATIONS.update({
 'psd_title': {'tr': '🔬 Gözenek Boyut Dağılımı (MIP tarzı)', 'en': '🔬 Pore Size Distribution (MIP-style)'},
 'psd_intro': {'tr': 'Segmentlenen gözeneklerin eşdeğer çap dağılımı (MIP grafiğine benzer artımsal + kümülatif gösterim).',
               'en': 'Equivalent-diameter distribution of the segmented pores (MIP-style incremental + cumulative view).'},
 'psd_weight': {'tr': 'Ağırlıklandırma', 'en': 'Weighting'},
 'psd_weight_area': {'tr': 'Alan ağırlıklı (MIP benzeri)', 'en': 'Area-weighted (MIP-like)'},
 'psd_weight_count': {'tr': 'Sayı ağırlıklı', 'en': 'Count-weighted'},
 'psd_chart_title': {'tr': 'Gözenek boyut dağılımı', 'en': 'Pore size distribution'},
 'psd_xlabel': {'tr': 'Eşdeğer gözenek çapı (mm)', 'en': 'Equivalent pore diameter (mm)'},
 'psd_y_inc': {'tr': 'Artımsal (%)', 'en': 'Incremental (%)'},
 'psd_y_cum': {'tr': 'Kümülatif (%)', 'en': 'Cumulative (%)'},
 'psd_d50': {'tr': 'Medyan çap (alanca, D50)', 'en': 'Median diameter (area-based, D50)'},
 'psd_note': {'tr': 'Not: Bu, görüntüden türetilen 2B, yüzey, alan-ağırlıklı bir gözenek-gövdesi dağılımıdır. Cıva porozimetresine (MIP) bir benzeridir, onun yerini tutmaz. MIP 3B gözenek boğazlarını hacimce ölçer.',
              'en': 'Note: this is an image-derived 2D, surface, area-weighted distribution of pore bodies. It is an analogue to, not a substitute for, mercury intrusion porosimetry (MIP), which probes 3D pore throats by volume.'},
 'psd_download': {'tr': 'Dağılım tablosunu indir (CSV)', 'en': 'Download distribution table (CSV)'},
})


# Güvenilirlik rozeti (gözeneklilik rejimi) — boundary-condition bulgusu
TRANSLATIONS.update({
 'rel_title':    {'tr': 'Güvenilirlik', 'en': 'Reliability'},
 'rel_low':      {'tr': 'Güvenilir', 'en': 'Reliable'},
 'rel_mid':      {'tr': 'Tutarlı', 'en': 'Consistent'},
 'rel_high':     {'tr': 'Temkinli', 'en': 'Caution'},
 'rel_low_msg':  {'tr': 'Düşük gözeneklilik rejimi (<%2). Yöntem bu aralıkta en güvenilirdir (kalibrasyon MAE ≈ 0,59 puan).',
                  'en': 'Low-porosity regime (<2%). The method is most reliable in this range (calibration MAE ≈ 0.59 pp).'},
 'rel_mid_msg':  {'tr': 'Orta gözeneklilik rejimi (%2–8). Tutarlı sonuç beklenir (kalibrasyon MAE ≈ 1,24 puan).',
                  'en': 'Mid-porosity regime (2–8%). Consistent results are expected (calibration MAE ≈ 1.24 pp).'},
 'rel_high_msg': {'tr': 'Yüksek gözeneklilik rejimi (>%8). Sonuç temkinli yorumlanmalı: kalibrasyon hatası belirgin artar (MAE ≈ 4,07 puan) ve bu aralık az sayıda numuneye dayanır.',
                  'en': 'High-porosity regime (>8%). Interpret with caution: calibration error rises sharply (MAE ≈ 4.07 pp) and this range rests on few samples.'},
})


# Örnek görüntü / toplu indirme (#3)
TRANSLATIONS.update({
 'demo_sample':  {'tr': '🧪 Örnek görüntü dene', 'en': '🧪 Try a sample image'},
 'demo_caption': {'tr': 'Yüklemeden hızlıca denemek için sentetik bir traverten yüzeyi.',
                  'en': 'A synthetic travertine surface to try the tool without uploading.'},
 'demo_loaded':  {'tr': 'Örnek traverten yüklendi. Sol menüden algoritma seçip sliderları oynatabilirsin.',
                  'en': 'Sample travertine loaded. Pick an algorithm on the left and adjust the sliders.'},
 'dl_all_zip':   {'tr': '🗂️ Tüm çıktıları indir (ZIP)', 'en': '🗂️ Download all outputs (ZIP)'},
})
