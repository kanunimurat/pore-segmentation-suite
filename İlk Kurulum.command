#!/bin/bash
# Gözenek ve Renk Tespit Yazılımı — İlk Kurulum
# Bu script'i SADECE bir defa çalıştırman yeterli.
# Tüm Python bağımlılıklarını kurar.

cd "$(dirname "$0")"

clear
echo ""
echo "════════════════════════════════════════════════"
echo "  🛠️  İlk Kurulum — Gözenek ve Renk Tespit     "
echo "════════════════════════════════════════════════"
echo ""

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 bulunamadı. Önce şu adresten yükle:"
    echo "   https://www.python.org/downloads/"
    echo ""
    read -p "Devam etmek için Enter..."
    exit 1
fi

echo "🐍 $(python3 --version)"
echo ""
echo "📦 Klasik bağımlılıklar yükleniyor (zorunlu)..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
echo ""

echo "═══════════════════════════════════════════════"
echo ""
read -p "🚀 Modern Deep Learning yöntemlerini (SAM 2, CellPose) de kurmak ister misin? [e/h]: " yn
if [[ $yn == "e" || $yn == "E" || $yn == "y" || $yn == "Y" ]]; then
    echo ""
    echo "📥 Bu işlem ~500MB-2GB indirir, 5-10 dk sürebilir..."
    python3 -m pip install -r requirements-modern.txt
fi

echo ""
echo "════════════════════════════════════════════════"
echo "  ✓ Kurulum tamamlandı!                        "
echo "════════════════════════════════════════════════"
echo ""
echo "  Artık 'Başlat.command' dosyasına çift tıkla."
echo ""
read -p "Pencereyi kapatmak için Enter..."
