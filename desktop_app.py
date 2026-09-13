"""
desktop_app.py
Launcher desktop untuk LocalPDF Studio.
Menjalankan server FastAPI di background thread dan membuka jendela aplikasi desktop
menggunakan Edge App Mode (bawaan Windows 10/11) atau pywebview jika tersedia.
"""
import sys
import os
import time
import socket
import threading
import subprocess
import shutil
from pathlib import Path

# Pastikan path aplikasi ditambahkan ke sys.path
APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# Proteksi stdout/stderr saat dijalankan tanpa konsol (PyInstaller windowed/noconsole mode)
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

# Import FastAPI instance
from app import app
import uvicorn


def find_free_port(preferred_port: int = 8000) -> int:
    """Cari port bebas, utamakan port 8000 jika belum dipakai."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            # Jika port belum dipakai (connect_ex != 0), pakai preferred_port
            if s.connect_ex(("127.0.0.1", preferred_port)) != 0:
                return preferred_port
    except Exception:
        pass

    # Cari port bebas otomatis
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class UvicornServerThread(threading.Thread):
    """Thread pembawa server Uvicorn/FastAPI."""
    def __init__(self, host: str, port: int):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.config = uvicorn.Config(
            app=app,
            host=self.host,
            port=self.port,
            log_level="warning",
            access_log=False
        )
        self.server = uvicorn.Server(config=self.config)

    def run(self):
        self.server.run()

    def stop(self):
        if self.server:
            self.server.should_exit = True


def wait_for_server(host: str, port: int, timeout: float = 10.0) -> bool:
    """Menunggu server hingga siap menerima koneksi."""
    import urllib.request
    start_time = time.time()
    url = f"http://{host}:{port}/api/health"
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url, timeout=0.8) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(0.2)
    return False


def find_edge_executable() -> str | None:
    """Mencari path binary msedge.exe di Windows."""
    candidates = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    
    which_edge = shutil.which("msedge")
    if which_edge:
        return which_edge
    return None


def run_with_edge_app(url: str) -> bool:
    """Membuka jendela mandiri aplikasi via Microsoft Edge App Mode."""
    edge_path = find_edge_executable()
    if not edge_path:
        return False

    # Gunakan profile data terpisah agar tidak mengganggu profile browser pengguna
    user_data_dir = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "LocalPDFStudio" / "edge_profile"
    user_data_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        edge_path,
        f"--app={url}",
        f"--user-data-dir={user_data_dir}",
        "--window-size=1280,850",
        "--disable-extensions",
        "--disable-component-update",
        "--no-first-run",
        "--no-default-browser-check"
    ]

    try:
        # Jalankan Edge App dan tunggu hingga pengguna menutup jendela
        proc = subprocess.Popen(cmd)
        proc.wait()
        return True
    except Exception as e:
        print(f"Gagal membuka Edge App mode: {e}")
        return False


def run_with_pywebview(url: str) -> bool:
    """Membuka jendela menggunakan pywebview jika terpasang."""
    try:
        import webview
        webview.create_window(
            title="LocalPDF Studio",
            url=url,
            width=1280,
            height=850,
            min_size=(900, 600),
            resizable=True
        )
        webview.start()
        return True
    except Exception as e:
        print(f"pywebview tidak dapat dijalankan: {e}")
        return False


def main():
    host = "127.0.0.1"
    port = find_free_port(8000)
    url = f"http://{host}:{port}"

    print(f"Memulai LocalPDF Studio di {url} ...")

    # Jalankan server FastAPI di background thread
    server_thread = UvicornServerThread(host=host, port=port)
    server_thread.start()

    # Tunggu server aktif
    if not wait_for_server(host, port, timeout=12.0):
        print("Peringatan: Server membutuhkan waktu lebih lama untuk merespons.")

    # Coba jalankan antarmuka desktop (prioritas: Edge App Mode untuk Windows native, lalu pywebview, lalu browser default)
    launched = False

    # 1. Edge App Mode (Sangat ringan, 100% native di Windows 10/11 tanpa dependensi berat)
    if find_edge_executable():
        launched = run_with_edge_app(url)

    # 2. PyWebView (jika Edge App Mode gagal)
    if not launched:
        launched = run_with_pywebview(url)

    # 3. Fallback: Browser biasa
    if not launched:
        import webbrowser
        webbrowser.open(url)
        # Jaga proses tetap hidup
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    # Berhentikan server setelah jendela ditutup
    print("Menutup LocalPDF Studio...")
    server_thread.stop()


if __name__ == "__main__":
    main()
