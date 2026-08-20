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

:: Tunggu 1 detik lalu buka browser
start "" "http://127.0.0.1:8000"

:: Jalankan server web FastAPI
python app.py
pause
