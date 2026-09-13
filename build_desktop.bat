@echo off
setlocal enabledelayedexpansion

echo ======================================================================
echo           LOCALPDF STUDIO - DESKTOP EXECUTABLE BUILDER
echo ======================================================================
echo.

cd /d "%~dp0"

:: 1. Cek Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python tidak ditemukan. Pastikan Python terpasang dan ada di PATH.
    pause
    exit /b 1
)

:: 2. Cek dependensi build (pyinstaller)
python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Menginstal PyInstaller...
    pip install pyinstaller pywebview
)

:: 3. Pastikan icon aplikasi sudah dibuat
if not exist "static\app_icon.ico" (
    echo [INFO] Menghasilkan icon aplikasi...
    python scripts\generate_icon.py
)

:: 4. Bersihkan build lama
echo [INFO] Membersihkan direktori build lama...
if exist "build" rd /s /q "build"
if exist "dist\LocalPDFStudio" rd /s /q "dist\LocalPDFStudio"

:: 5. Jalankan PyInstaller
echo.
echo [INFO] Memulai proses bundling PyInstaller...
echo Mohon tunggu, proses ini membutuhkan waktu 1-2 menit...
echo.
pyinstaller --noconfirm localpdf.spec

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Proses bundling PyInstaller gagal! Silakan periksa pesan error di atas.
    pause
    exit /b 1
)

echo.
echo [BERHASIL] Bundel aplikasi desktop berhasil dibuat di:
echo %~dp0dist\LocalPDFStudio\
echo.

:: 6. Cek dan jalankan Inno Setup Compiler
echo [INFO] Memeriksa Inno Setup Compiler...
python scripts\run_inno_setup.py

echo.
echo Tekan tombol apa saja untuk menutup jendela ini...
pause >nul
