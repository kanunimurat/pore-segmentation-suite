#!/bin/bash
# ============================================================
# Gözenek ve Renk Tespit Yazılımı v2 (PROTOTIP) — Başlatıcı
# Top-Level Mode Selector ile yeni UI mimarisi
# Port 8502 — v1 (8501) ile paralel çalışabilir
# ============================================================

cd "$(dirname "$0")"
SCRIPT_DIR="$(pwd)"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

clear
echo ""
echo -e "${PURPLE}════════════════════════════════════════════════${NC}"
echo -e "${PURPLE}  🪨 Gözenek ve Renk Tespit v2.0 (PROTOTIP)    ${NC}"
echo -e "${PURPLE}  Top-Level Mode Selector ile yeni UI          ${NC}"
echo -e "${PURPLE}════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}📁 Klasör:${NC} $SCRIPT_DIR"
echo -e "${YELLOW}⚠️  Bu PROTOTIP sürümdür — v1 (Başlat.command) dokunulmadı${NC}"
echo ""

# v2 dosyası mevcut mu?
if [ ! -f "pore_tuner_v2.py" ]; then
    echo -e "${RED}❌ pore_tuner_v2.py bulunamadı.${NC}"
    echo "    v2 prototipi henüz oluşturulmamış olabilir."
    echo ""
    read -p "Devam etmek için Enter'a bas..."
    exit 1
fi

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
    echo -e "${YELLOW}⚠️  Streamlit yüklü değil. Önce 'İlk Kurulum.command' çalıştır.${NC}"
    echo ""
    read -p "Devam etmek için Enter'a bas..."
    exit 1
fi

# Uygulamayı başlat
echo -e "${PURPLE}🚀 v2 prototipi başlatılıyor...${NC}"
echo -e "${PURPLE}   Port: 8502 (v1 ile paralel çalışabilir, v1 port 8501)${NC}"
echo -e "${PURPLE}   Tarayıcı: http://localhost:8502${NC}"
echo ""
echo -e "${YELLOW}   📋 Yan yana karşılaştırma için:${NC}"
echo -e "${YELLOW}      Başka terminalde 'Başlat.command' çalıştır → port 8501${NC}"
echo ""
echo -e "${YELLOW}   ⚡ Durdurmak için: Ctrl+C${NC}"
echo -e "${YELLOW}   📝 Bu pencereyi kapatma — kapanırsa uygulama da kapanır${NC}"
echo ""
echo -e "${PURPLE}════════════════════════════════════════════════${NC}"
echo ""

# Streamlit'i v2 olarak başlat
exec python3 -m streamlit run pore_tuner_v2.py \
    --server.port 8502 \
    --server.headless=false \
    --browser.gatherUsageStats=false
