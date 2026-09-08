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

:: 6. Cek apakah Inno Setup Compiler (ISCC.exe) terpasang
set "ISCC_PATH="
if exist "%LocalAppData%\Programs\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"
) else if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
) else if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=%ProgramFiles%\Inno Setup 6\ISCC.exe"
) else (
    where ISCC.exe >nul 2>&1
    if !errorlevel! equ 0 (
        set "ISCC_PATH=ISCC.exe"
    )
)

if defined ISCC_PATH (
    echo [INFO] Inno Setup ditemukan: "!ISCC_PATH!"
    echo [INFO] Mengompilasi installer tunggal LocalPDF_Studio_Setup.exe...
    if not exist "installer\output" mkdir "installer\output"
    "!ISCC_PATH!" "installer\installer.iss"
    if !errorlevel! equ 0 (
        echo.
        echo ======================================================================
        echo [SELESAI] Installer siap dibagikan!
        echo File Setup: %~dp0installer\output\LocalPDF_Studio_Setup.exe
        echo ======================================================================
    ) else (
        echo [PERINGATAN] Gagal mengompilasi installer Inno Setup. Anda tetap bisa menggunakan folder di dist\LocalPDFStudio\
    )
) else (
    echo [CATATAN] Inno Setup 6 belum terpasang di komputer ini.
    echo Anda dapat langsung membagikan folder portabel:
    echo   %~dp0dist\LocalPDFStudio\
    echo Atau download Inno Setup gratis di https://jrsoftware.org/isdl.php
    echo untuk membuat file single-installer LocalPDF_Studio_Setup.exe
)

echo.
echo Tekan tombol apa saja untuk menutup jendela ini...
pause >nul
