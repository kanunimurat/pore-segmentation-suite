# v1.2.0 Yayın Rehberi — GitHub + Zenodo (adım adım)

Repo: https://github.com/kanunimurat/pore-segmentation-suite
Zenodo concept DOI (her zaman en son sürüme gider): 10.5281/zenodo.20416896

---

## A. HANGİ DOSYALAR GİDECEK?

GİDECEK olanlar (gerçek kaynak):
- pore_tuner_v2.py  (aktif uygulama)
- modules/  -> tüm .py dosyaları (yeni: pore_size.py dahil)
- sample_images/sample_travertine.png  (YENİ - demo görüntü, mutlaka ekle)
- palettes/*.json , presets/*.json , assets/*
- README.md , CHANGELOG.md , CITATION.cff , LICENSE , ZENODO_SETUP.md
- requirements.txt , requirements-modern.txt
- *.command başlatıcılar , icon.png , .gitignore (YENİ)

GİTMEYECEK olanlar (yeni .gitignore bunları otomatik dışlar):
- *.bak / *.backup yedek dosyaları (47 adet)
- __pycache__/ , *.pyc
- .DS_Store
- outputs/

Not: .gitignore dosyasını ekledim. Terminal yolunu kullanırsan bu dosyalar
kendiliğinden hariç tutulur, ekstra iş yok.

---

## B. YOL 1 — TERMINAL (git ile, önerilen, hızlı)

Terminal aç ve sırayla:

1) Klasöre gir:
   cd "/Users/muratsert/Desktop/Mesleki Dosyalar/BİLİMSEL ÇALIŞMALARIM/DEVAM EDEN ÇALIŞMALAR/Makale_02  |  GÖRÜNTÜ İŞLEME/Gözenek ve Renk Tespit Yazılımı"

2) Repo bağlı mı bak:
   git status
   (Eğer "not a git repository" derse -> Yol 2'ye geç ya da aşağıdaki "İLK KEZ" bloğunu çalıştır.)

3) Değişiklikleri ekle ve kaydet:
   git add -A
   git commit -m "v1.2.0: görsel yenileme, gözenek boyut dağılımı, güvenilirlik rozeti, demo+ZIP"

4) GitHub'a gönder:
   git push

5) Sürüm etiketi at ve gönder:
   git tag v1.2.0
   git push --tags

--- (Sadece git ilk kez kuruluyorsa) İLK KEZ bloğu ---
   git init
   git add -A
   git commit -m "v1.2.0"
   git branch -M main
   git remote add origin https://github.com/kanunimurat/pore-segmentation-suite.git
   git push -u origin main
   git tag v1.2.0 && git push --tags

---

## C. YOL 2 — GITHUB WEB ARAYÜZÜ (terminal istemiyorsan)

1) https://github.com/kanunimurat/pore-segmentation-suite adresine git.
2) "Add file" -> "Upload files" tıkla.
3) Değişen/yeni dosyaları sürükle-bırak:
   - pore_tuner_v2.py
   - modules/  içindeki güncel .py dosyaları (pore_size.py dahil)
   - sample_images/sample_travertine.png
   - README.md, CHANGELOG.md, CITATION.cff
   (Yedek .bak dosyalarını YÜKLEME.)
4) Altta "Commit changes" -> mesaj: "v1.2.0" -> Commit.

---

## D. RELEASE OLUŞTUR (DOI'yi bu tetikler - ZORUNLU adım)

1) Repo sayfasında sağdaki "Releases" -> "Draft a new release".
2) "Choose a tag" -> v1.2.0 yaz -> "Create new tag: v1.2.0 on publish".
3) Release title: Pore Segmentation Suite v1.2.0
4) Açıklama: CHANGELOG.md'deki [1.2.0] bölümünü kopyala-yapıştır.
5) "Publish release" tıkla.

---

## E. ZENODO (otomatik)

- Zenodo-GitHub entegrasyonu v1.1.0'da açıldıysa, release yayınlanınca
  Zenodo ~10 dakika içinde yeni bir SÜRÜM DOI'si üretir.
- Kontrol: https://zenodo.org -> oturum aç -> Upload/GitHub bölümünde
  yeni v1.2.0 kaydını gör.
- Yeni sürüm DOI'si gelince bana söyle:
  * CITATION.cff'teki doi satırını güncelleyeyim,
  * README'ye DOI rozetini ekleyeyim,
  * makale "Software Availability" cümlesine işleyeyim.

(Entegrasyon kapalıysa: Zenodo -> Settings -> GitHub -> repoyu Sync edip
 toggle'ı ON yap, sonra release'i tekrar publish et ya da mevcut release'i kullan.)

---

## ÖZET
git add -A  ->  commit  ->  push  ->  tag v1.2.0  ->  GitHub Release  ->  Zenodo DOI
