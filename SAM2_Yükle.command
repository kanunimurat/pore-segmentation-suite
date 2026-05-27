#!/bin/bash
# ============================================================
# SAM 2 + CellPose Otomatik Yükleyici
# Modern Deep Learning yöntemlerini kurar
# ============================================================

cd "$(dirname "$0")"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

clear
echo ""
echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  🚀 Modern DL Yükleyici (SAM 2 + CellPose)    ${NC}"
echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Bu işlem:${NC}"
echo "  • ~1-1.5 GB disk kullanır"
echo "  • 5-10 dakika sürer (internet hızına bağlı)"
echo "  • PyTorch + ultralytics + cellpose kurar"
echo ""

read -p "Devam etmek istiyor musun? [e/h]: " yn
if [[ ! ($yn == "e" || $yn == "E" || $yn == "y" || $yn == "Y") ]]; then
    echo "İptal edildi."
    exit 0
fi

echo ""
echo -e "${BLUE}🐍 Python sürümü:${NC}"
python3 --version
echo ""

# 1. PyTorch (CPU-only)
echo -e "${BLUE}[1/3]${NC} PyTorch kuruluyor (CPU-only, ~700 MB)..."
python3 -m pip install --upgrade torch torchvision \
    --index-url https://download.pytorch.org/whl/cpu

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${YELLOW}⚠️  CPU-only PyTorch başarısız. Standart sürümü deniyorum...${NC}"
    python3 -m pip install torch torchvision
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ PyTorch kurulamadı.${NC}"
        echo ""
        echo "Olası sebep: Python 3.14 için henüz PyTorch wheel'i yok."
        echo "Geçici çözüm: Python 3.13 kur:"
        echo "  brew install python@3.13"
        echo "  python3.13 -m pip install torch torchvision ultralytics cellpose"
        exit 1
    fi
fi
echo -e "${GREEN}✓ PyTorch kuruldu${NC}"
echo ""

# 2. Ultralytics (SAM 2)
echo -e "${BLUE}[2/3]${NC} Ultralytics (SAM 2) kuruluyor..."
python3 -m pip install ultralytics
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Ultralytics kurulamadı${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Ultralytics + SAM 2 kuruldu${NC}"
echo ""

# 3. CellPose
echo -e "${BLUE}[3/3]${NC} CellPose kuruluyor (opsiyonel)..."
python3 -m pip install cellpose
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  CellPose kurulamadı (kritik değil, SAM 2 zaten hazır)${NC}"
else
    echo -e "${GREEN}✓ CellPose kuruldu${NC}"
fi
echo ""

# Doğrulama
echo -e "${BLUE}🔍 Kurulum doğrulanıyor...${NC}"
echo ""

python3 - <<PYTEST
try:
    import torch
    print(f"  ✓ PyTorch {torch.__version__}")
except Exception as e:
    print(f"  ✗ PyTorch HATASI: {e}")
try:
    from ultralytics import SAM
    print(f"  ✓ SAM 2 import edilebilir")
except Exception as e:
    print(f"  ✗ SAM 2 HATASI: {e}")
try:
    from cellpose import models
    print(f"  ✓ CellPose import edilebilir")
except Exception as e:
    print(f"  ⚠️  CellPose import edilemedi: {e}")
PYTEST

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✓ Kurulum tamamlandı!                       ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}📝 İlk SAM 2 kullanımında:${NC}"
echo "    Model otomatik indirilir (~80 MB)"
echo "    Bu işlem yaklaşık 1-2 dakika sürer (tek seferlik)"
echo ""
echo "    Şimdi 'Başlat.command'a çift tıklayıp uygulamayı aç"
echo "    Algoritma listesinde SAM 2 ve CellPose görünecek"
echo ""
read -p "Pencereyi kapatmak için Enter'a bas..."
