@echo off
chcp 65001 > nul
title LocalPDF Studio - Offline PDF Web Tools
echo ========================================================
echo        LOCALPDF STUDIO - ALAT PDF LOKAL TERPADU
echo ========================================================
echo.
echo Menyiapkan server lokal...
echo Membuka aplikasi di browser...
echo.

:: Gunakan port dari variabel lingkungan PORT (default: 8000)
if "%PORT%"=="" set PORT=8000
if "%HOST%"=="" set HOST=127.0.0.1

:: Tunggu 1 detik lalu buka browser
start "" "http://127.0.0.1:%PORT%"

:: Jalankan server web FastAPI
python app.py
pause
