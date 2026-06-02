#!/bin/bash
# ============================================================
# Gözenek ve Renk Tespit Yazılımı — Otomatik Başlatıcı
# Çift tıkla → Terminal açılır → Streamlit başlar → Tarayıcı açılır
# ============================================================

# Script'in bulunduğu klasöre git
cd "$(dirname "$0")"
SCRIPT_DIR="$(pwd)"

# Renkli mesajlar
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

clear
echo ""
echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  🪨 Gözenek ve Renk Tespit Yazılımı v1.2     ${NC}"
echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}📁 Klasör:${NC} $SCRIPT_DIR"
echo ""

# Python kontrolü
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 bulunamadı.${NC}"
    echo "    Lütfen https://www.python.org/downloads/ adresinden yükle."
    echo ""
    read -p "Devam etmek için Enter'a bas..."
    exit 1
fi

PY_VERSION=$(python3 --version 2>&1)
echo -e "${GREEN}🐍 ${PY_VERSION}${NC}"
echo ""

# Streamlit kurulu mu?
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Streamlit yüklü değil. Kuruluyor...${NC}"
    echo -e "${YELLOW}    (Bu işlem ilk seferde 2-3 dakika sürer)${NC}"
    echo ""
    python3 -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo ""
        echo -e "${RED}❌ Kurulum başarısız.${NC}"
        echo "    Terminal'de manuel olarak şu komutu dene:"
        echo "    pip3 install -r requirements.txt"
        echo ""
        read -p "Devam etmek için Enter'a bas..."
        exit 1
    fi
    echo ""
    echo -e "${GREEN}✓ Kurulum tamamlandı.${NC}"
    echo ""
fi

# Uygulamayı başlat
echo -e "${BLUE}🚀 Uygulama başlatılıyor...${NC}"
echo -e "${BLUE}   Tarayıcı otomatik açılacak: http://localhost:8501${NC}"
echo ""
echo -e "${YELLOW}   ⚡ Durdurmak için: Ctrl+C${NC}"
echo -e "${YELLOW}   📝 Bu pencereyi kapatma — kapanırsa uygulama da kapanır${NC}"
echo ""
echo -e "${BLUE}────────────────────────────────────────────────${NC}"
echo ""

# Streamlit'i başlat
exec python3 -m streamlit run pore_tuner.py --server.headless=false --browser.gatherUsageStats=false
