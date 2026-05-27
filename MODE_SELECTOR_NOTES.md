# MODE_SELECTOR_NOTES — Top-Level Mode Selector Prototipi

**Tarih:** 2026-05-26 (gece)  
**Versiyon:** v2 prototype (side-by-side, mevcut v1 etkilenmedi)  
**Geliştirici notu:** Sen dinlenirken yapıldı — sabah inceleyip karar vereceğin **bağımsız bir prototip**.

---

## 🎯 Ne Değişti?

Yazılım artık **3 ana çalışma modu** ile organize:

### Önceki (v1)
```
SIDEBAR:
├── 📊 Analize Başla (her zaman görünür)
├── 🎨 Renk Yelpazesi (her zaman görünür)
├── 🔄 Aging Analizi (her zaman görünür)
├── ⚙️ Ayarlar
└── ℹ️ Hakkında

→ 3 ana özellik aynı anda sidebar'da, kullanıcı hangisini seçeceğini doğrudan görür ama UI yoğun
```

### Yeni (v2 prototype)
```
SIDEBAR:
├── 🪨 [Brand header]
├── 🎯 Çalışma Modu (radio button — 3 seçenek)
│   ⦿ 🔬 Gözenek Analizi
│   ○ 🎨 Renk Paleti
│   ○ 🔄 Yaşlandırma Analizi
├── ─── (mode-specific expander) ───
│   📊 Analize Başla     (sadece 🔬 modunda)
│   🎨 Renk Yelpazesi    (sadece 🎨 modunda)
│   🔄 Aging Analizi     (sadece 🔄 modunda)
├── ─── (her zaman görünür) ───
├── ⚙️ Ayarlar
└── ℹ️ Hakkında

→ Tek mod focus, temiz UI, scientific suite paradigması
```

**Ana Panel:**
- Aktif mode'un ismini gösteren **renkli banner** (mavi/turuncu/yeşil)
- Aktif mode'a uygun **boş durum mesajı** (hızlı başlangıç rehberi ile)
- Aktif mode'un sonuçları sadece o modda görünür (diğer modların verileri korunur ama gösterilmez)

---

## 🚀 Nasıl Çalıştırılır?

### Yan yana karşılaştırma (önerilen ilk adım)

**v1 (mevcut, çalışan):**
```bash
cd "/Users/muratsert/.../Gözenek ve Renk Tespit Yazılımı"
streamlit run pore_tuner.py
```
→ Port 8501

**v2 (yeni prototip, paralel):**
```bash
# Aynı klasörde, farklı port:
streamlit run pore_tuner_v2.py --server.port 8502
```
→ Port 8502

İki tarayıcı sekmesini yan yana açıp karşılaştırırsın.

---

## ✅ Beğenirsen — Swap (5 dakika)

v2'yi resmi versiyon yapmak istiyorsan:

```bash
cd "/Users/muratsert/.../Gözenek ve Renk Tespit Yazılımı"

# Mevcut v1'i v1.backup olarak sakla
mv pore_tuner.py pore_tuner_v1.py

# v2'yi resmi yap
mv pore_tuner_v2.py pore_tuner.py

# Test
streamlit run pore_tuner.py
```

Otomatik yedek (`pore_tuner.py.backup_2026-05-26`) zaten var — komple geri dönüş gerekirse oradan alabilirsin.

---

## ❌ Beğenmezsen — Sil Git

```bash
rm pore_tuner_v2.py
rm MODE_SELECTOR_NOTES.md  # bu dosya
```

Hiçbir şey kaybetmedik — v1 dokunulmadan çalışıyor.

---

## 🔧 Teknik Detaylar

### Değişen tek dosya: `pore_tuner_v2.py`
- v1: 82,050 bytes
- v2: 89,174 bytes (+~7 KB)
- Eklenen: mode selector, conditional sidebar/main panel, 3 mode-specific empty state

### Değişmeyen tüm modüller:
- `modules/segmentation.py`
- `modules/color_science.py`
- `modules/aging_analysis.py`
- `modules/filters.py`
- `modules/palettes.py`
- `modules/presets.py`
- `modules/utils.py`
- `requirements.txt`

### Session state davranışı:
- **Veriler tüm modlarda korunur** — mode değiştirince image_rgb, computed_palette, aging_results vb. silinmez
- Sadece **UI** değişir — yüklü görüntün varsa ve Aging mode'a geçersen, görüntü hala session'da ama Aging mode bunu kullanmaz (sadece pre/post yükleme bekler)
- Geri pore mode'a dönünce yüklü görüntü hala orada

---

## 💎 Avantajlar (v2 ne kazandırır?)

1. **Scientific Suite Paradigması** — Yazılım artık "tek özellikli app" değil, 3 ayrı analiz aracını barındıran bir suite
2. **Focused UI** — Her mod kendi içine odaklanmış, başka mod'un UI öğeleri görünmüyor → bilişsel yük azalır
3. **Mode-Spesifik Onboarding** — Yeni bir kullanıcı moda girince **hızlı başlangıç rehberi** görür (örn. "Aging mode için pre/post yükle, eşleştirme seç...")
4. **Daha Profesyonel** — Diğer bilim insanlarının kullandığı analiz suite'lerine (ImageJ, Fiji, Ilastik) benzer mode-aware yapı
5. **Genişlemeye Açık** — İleride 4. mod eklemek (ör. Pore Morphometry, U-Net Training, vb.) çok kolay
6. **Hangi modu kullandığını her zaman bilirsin** — Üst banner ile aktif mod net

---

## ⚠️ Bilinen Kısıtlar / Gözlemler

1. **İndentation:** Mevcut expander'ları `if` ile sardığımdan, içerik 8-space indent'te ama `with` 5-space'te. Python parser kabul ediyor ve syntax check geçti, ama optik olarak bir parça garip. Tam refactor (içeriği 12-space'e indent) yapmadım çünkü bu büyük bir mekanik değişiklik (~3000 satır indent değişimi). Çalıştığı sürece sorun yok.

2. **Sandbox testi mümkün değildi:** Streamlit benim sandbox'ta yok, sadece syntax test ettim. UI behavior'ı ilk sen test edeceksin.

3. **Mode değişiminde scroll pozisyonu:** Streamlit her rerun'da scroll'u sıfırlayabilir. Mode değiştirdiğinde sayfa başına dönebilir — bu Streamlit'in genel davranışı, normal.

4. **Renk Yelpazesi'ndeki "Renk Yelpazesi — Detaylı Görselleştirme" expander artık varsayılan açık (expanded=True)** — Palette mode'a girince hemen görsün diye. v1'de varsayılan kapalıydı.

---

## 🧪 Sabah Test Etmen Önerilen Senaryolar

### Test 1: Mode Geçişi Akıcılığı
1. v2'yi başlat
2. 🔬 Gözenek Analizi modunda KT-A1 görüntüsünü yükle, MSER ile segmente et
3. 🎨 Renk Paleti moduna geç → görüntü hala yüklü mü? Palet hesapla
4. 🔄 Yaşlandırma moduna geç → boş durum mesajı görüyor musun? 6 KT pre/post yükle, çalıştır
5. Tekrar 🔬 Gözeneğe dön → eski segmentasyon hala görünüyor mu?

**Beklenen:** Mode değişimleri akıcı, veriler kayıp olmuyor.

### Test 2: Empty State Mesajları
1. v2'yi temiz başlat (Cmd+R)
2. Hiçbir veri yüklemeden 🔬 → 🎨 → 🔄 mod gez
3. Her modda farklı **hızlı başlangıç rehberi** görüyor musun?

**Beklenen:** Her modun kendine özel onboarding mesajı.

### Test 3: Banner Görünümü
1. Her modda üstte **renkli banner** ("Gözenek Analizi Modu" gibi) var mı?
2. Renk mode'a göre değişiyor mu? (mavi/turuncu/yeşil)

**Beklenen:** Hangi modda olduğun her zaman net.

### Test 4: Ayarlar + Hakkında Her Yerde
1. 🔬'de Ayarlar açık mı?
2. 🎨'ya geç → Ayarlar hala görünür mü?
3. 🔄'a geç → Ayarlar hala görünür mü?

**Beklenen:** Bu iki menü her modda alt kısımda görünür.

---

## 📋 Karar Verirken Düşünmen Gerekenler

**Beğen:**
- Daha temiz UI istiyorsan
- Diğer bilim insanları kullanacaksa (scientific suite paradigması)
- Gelecekte yeni mod eklemeyi planlıyorsan
- "Tek odakta tek görev" felsefesini benimsiyorsan

**Beğenme:**
- Mode geçiş klick'i fazladan iş geliyorsa
- 3 özelliği aynı anda görmek istiyorsan
- Mevcut akış zaten alışkanlık haline geldiyse
- Mode değişiminde Streamlit rerun yavaşlatıyorsa

---

## 🔄 v1'e Geri Dönüş Garantisi

Mevcut `pore_tuner.py` **hiç dokunulmadı**. İstediğin zaman normal çalıştırabilirsin:
```bash
streamlit run pore_tuner.py
```

Ayrıca otomatik yedek var:
```bash
# pore_tuner.py'i kaybetsen bile:
cp pore_tuner.py.backup_2026-05-26 pore_tuner.py
```

---

## 🌅 Sabah Akşam Görüşürüz

İyi geceler Murat. Test ettiğinde ne düşündüğünü söyle:
- "Beğendim, swap yap" → 5 dakika
- "Beğendim ama X küçük değişiklik" → 10-15 dakika
- "v1 daha iyiydi" → silelim, devam edelim

**Önemli not:** Hangi yolu seçersen seç, yazılımın **tüm bilimsel motoru (algoritmalar + istatistik)** etkilenmiyor. Bu sadece UI organizasyonu hakkında.
