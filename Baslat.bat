@echo off
chcp 65001 >nul
title Pore Segmentation Suite
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 goto nopython

if not exist ".kurulum_tamam" (
    echo Ilk kurulum: gerekli kutuphaneler yukleniyor, lutfen bekleyin...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo HATA: Kurulum basarisiz oldu. Internet baglantinizi kontrol edin.
        pause
        exit /b 1
    )
    echo ok > .kurulum_tamam
)

echo Uygulama baslatiliyor... Tarayicinizda http://localhost:8501 acilacak.
python -m streamlit run pore_tuner_v2.py
pause
exit /b 0

:nopython
echo.
echo HATA: Python bulunamadi.
echo Lutfen https://www.python.org/downloads/ adresinden Python kurun.
echo ONEMLI: Kurulum ekraninda "Add Python to PATH" kutusunu isaretleyin.
echo.
pause
exit /b 1
