#!/bin/bash
# =====================================================================
#  Pore Segmentation Suite — v1.2.0 GitHub + Zenodo yayin script'i
#  Cift tikla calistir. Hicbir uzak dosya silinmez.
# =====================================================================
cd "$(dirname "$0")" || exit 1

REPO="https://github.com/kanunimurat/pore-segmentation-suite.git"
TAG="v1.2.0"
MSG="v1.2.0: gorsel yenileme, gozenek boyut dagilimi, guvenilirlik rozeti, demo+ZIP"

clear
echo "============================================================"
echo "   Pore Segmentation Suite  ->  $TAG  yayin"
echo "============================================================"
echo ""

command -v git >/dev/null 2>&1 || { echo "HATA: git bulunamadi. Xcode Command Line Tools kur: xcode-select --install"; read -p "Enter..."; exit 1; }

if [ -d .git ]; then
  echo "[i] Bu klasor zaten bir git deposu. Buradan yayinlanacak."
  WORK="."
else
  WORK="../_pss_release_$TAG"
  echo "[i] Bu klasor git deposu degil."
  echo "    Uzak depo klonlanacak ve guncel dosyalar uzerine kopyalanacak:"
  echo "    $WORK"
  echo ""
  read -p "Devam icin Enter, iptal icin Ctrl+C... "
  rm -rf "$WORK"
  git clone "$REPO" "$WORK" || { echo "HATA: klon basarisiz (internet / repo erisimi?)"; read -p "Enter..."; exit 1; }
  echo "[i] Guncel dosyalar klona kopyalaniyor (yedek/onbellek haric)..."
  rsync -a \
    --exclude '.git' --exclude '__pycache__' --exclude '*.pyc' \
    --exclude '*.bak' --exclude '*.bak_*' --exclude '*.backup' --exclude '*.backup_*' \
    --exclude '.DS_Store' --exclude 'outputs' \
    ./ "$WORK"/
fi

cd "$WORK" || exit 1
echo ""
echo "[i] Degisiklikler:"
git add -A
git status --short
echo ""
read -p "Yukar?dakileri commit + push edelim mi? Enter=evet, Ctrl+C=iptal... "

if git diff --cached --quiet; then
  echo "[i] Yeni degisiklik yok, commit atlandi."
else
  git commit -m "$MSG"
fi

echo "[i] push..."
git push || git push -u origin HEAD

echo "[i] etiket $TAG..."
git tag "$TAG" 2>/dev/null && git push origin "$TAG" || echo "[i] Etiket zaten var ya da gonderildi."

echo ""
echo "============================================================"
echo "   RELEASE (DOI'yi bu tetikler)"
echo "============================================================"
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  echo "[i] GitHub CLI bulundu, release otomatik olusturuluyor..."
  NOTES="$(awk '/^## \[1.2.0\]/{f=1} /^## \[1.1.0\]/{f=0} f' CHANGELOG.md)"
  gh release create "$TAG" --title "Pore Segmentation Suite $TAG" --notes "$NOTES" \
     && echo "[OK] Release olusturuldu. Zenodo ~10 dk icinde DOI uretir." \
     || echo "[!] gh release olusturulamadi, web'den olustur: acilan sayfayi kullan."
  command -v open >/dev/null 2>&1 && open "https://github.com/kanunimurat/pore-segmentation-suite/releases"
else
  echo "[i] GitHub CLI yok. Release'i web'den olustur (tarayici aciliyor):"
  echo "    Tag: $TAG   Baslik: Pore Segmentation Suite $TAG"
  echo "    Aciklama: CHANGELOG'daki [1.2.0] bolumunu yapistir, Publish."
  command -v open >/dev/null 2>&1 && open "https://github.com/kanunimurat/pore-segmentation-suite/releases/new?tag=$TAG"
fi

echo ""
echo "[OK] Bitti. Release publish edilince Zenodo otomatik arsivler."
echo "     Yeni surum DOI'sini Kerem'e ilet -> CITATION.cff + README rozeti guncellensin."
read -p "Pencereyi kapatmak icin Enter..."
