#!/usr/bin/env bash

# Pastikan script berjalan dari direktori tempat script ini berada
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================================"
echo "       LOCALPDF STUDIO - ALAT PDF LOKAL TERPADU        "
echo "========================================================"
echo ""

# 1. Cek ketersediaan Python 3
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "[ERROR] Python 3 tidak ditemukan di sistem Anda."
    echo "Silakan install terlebih dahulu (contoh di Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip)"
    exit 1
fi

# 2. Siapkan Virtual Environment (venv)
VENV_DIR="$SCRIPT_DIR/venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "[INFO] Menyiapkan virtual environment baru di: $VENV_DIR ..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "[ERROR] Gagal membuat virtual environment."
        echo "Pastikan paket python3-venv sudah terpasang (contoh: sudo apt install python3-venv)"
        exit 1
    fi

    echo "[INFO] Menginstal dependensi dari requirements.txt..."
    "$VENV_DIR/bin/pip" install --upgrade pip
    "$VENV_DIR/bin/pip" install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[ERROR] Terjadi kegagalan saat menginstal dependensi."
        exit 1
    fi
else
    # Cek apakah fastapi terinstall, jika belum lakukan install
    if [ ! -f "$VENV_DIR/bin/uvicorn" ]; then
        echo "[INFO] Dependensi belum lengkap, menginstal requirements.txt..."
        "$VENV_DIR/bin/pip" install -r requirements.txt
    fi
fi

# 3. Buka browser secara otomatis di background jika di lingkungan desktop (GUI)
PORT="${PORT:-8000}"
HOST="${HOST:-127.0.0.1}"

if [ -n "$DISPLAY" ] || [ -n "$WAYLAND_DISPLAY" ]; then
    (
        sleep 1.5
        if command -v xdg-open >/dev/null 2>&1; then
            xdg-open "http://127.0.0.1:${PORT}" >/dev/null 2>&1
        elif command -v gio >/dev/null 2>&1; then
            gio open "http://127.0.0.1:${PORT}" >/dev/null 2>&1
        elif command -v sensible-browser >/dev/null 2>&1; then
            sensible-browser "http://127.0.0.1:${PORT}" >/dev/null 2>&1
        fi
    ) &
fi

echo "[INFO] Menjalankan server LocalPDF Studio..."
echo "Akses web di: http://${HOST}:${PORT}"
echo "Tekan Ctrl + C untuk menghentikan server."
echo ""

# 4. Jalankan aplikasi
"$VENV_DIR/bin/python" app.py
