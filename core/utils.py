import os
import re
import uuid
import time
import shutil
import base64
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def natural_sort_key(s: str) -> List[Any]:
    """Kunci pengurutan alami (misal: 1, 2, 10 alih-alih 1, 10, 2)."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(s))]


def format_bytes(size_bytes: int) -> str:
    """Format byte size ke string yang ramah dibaca (KB, MB, GB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def generate_task_id() -> str:
    """Membuat ID unik untuk sesi proses/tugas."""
    return str(uuid.uuid4())


def get_task_dirs(task_id: str) -> tuple[Path, Path]:
    """Membuat dan mengembalikan direktori upload dan output untuk task tertentu."""
    task_upload = UPLOAD_DIR / task_id
    task_output = OUTPUT_DIR / task_id
    task_upload.mkdir(parents=True, exist_ok=True)
    task_output.mkdir(parents=True, exist_ok=True)
    return task_upload, task_output


def cleanup_old_files(max_age_seconds: int = 3600):
    """Menghapus folder tugas sementara yang lebih lama dari max_age_seconds."""
    now = time.time()
    for root_dir in [UPLOAD_DIR, OUTPUT_DIR]:
        if not root_dir.exists():
            continue
        for item in root_dir.iterdir():
            if item.is_dir():
                try:
                    mtime = item.stat().st_mtime
                    if now - mtime > max_age_seconds:
                        shutil.rmtree(item, ignore_errors=True)
                except Exception:
                    pass


def get_pdf_info(pdf_path: str | Path) -> Dict[str, Any]:
    """Mendapatkan metadata PDF seperti jumlah halaman, ukuran file, dll."""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"File PDF tidak ditemukan: {pdf_path}")
    
    file_size = pdf_path.stat().st_size
    info = {
        "filename": pdf_path.name,
        "size_bytes": file_size,
        "size_formatted": format_bytes(file_size),
        "page_count": 0,
        "pages": []
    }
    
    if fitz:
        try:
            doc = fitz.open(str(pdf_path))
            info["page_count"] = len(doc)
            for i, page in enumerate(doc):
                rect = page.rect
                info["pages"].append({
                    "page_number": i + 1,
                    "width": int(rect.width),
                    "height": int(rect.height),
                    "rotation": page.rotation
                })
            doc.close()
        except Exception as e:
            info["error"] = str(e)
            
    return info


def generate_pdf_thumbnail(pdf_path: str | Path, page_num: int = 0, dpi: int = 72) -> Optional[str]:
    """Menghasilkan thumbnail halaman PDF dalam format Data URI Base64 PNG."""
    if not fitz:
        return None
    try:
        doc = fitz.open(str(pdf_path))
        if page_num >= len(doc) or page_num < 0:
            page_num = 0
        page = doc[page_num]
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_bytes = pix.tobytes("png")
        doc.close()
        b64 = base64.b64encode(img_bytes).decode('utf-8')
        return f"data:image/png;base64,{b64}"
    except Exception as e:
        print(f"Error rendering thumbnail for {pdf_path}: {e}")
        return None


def safe_delete_local_file(file_path: str | Path, to_recycle_bin: bool = True) -> tuple[bool, str]:
    """
    Menghapus file lokal dengan aman.
    Jika to_recycle_bin=True dan OS Windows, memindahkan file ke Recycle Bin (tempat sampah) agar dapat di-restore.
    Jika bukan Windows atau jika to_recycle_bin=False atau Recycle Bin gagal, menggunakan os.remove().
    """
    try:
        p = Path(file_path).resolve()
        if not p.exists():
            return False, f"File '{p.name}' tidak ditemukan."
        if not p.is_file():
            return False, f"Path '{p.name}' bukan merupakan file."

        if to_recycle_bin and os.name == 'nt':
            try:
                import sys
                import ctypes
                from ctypes import wintypes

                class SHFILEOPSTRUCTW(ctypes.Structure):
                    _fields_ = [
                        ('hwnd', wintypes.HWND),
                        ('wFunc', wintypes.UINT),
                        ('pFrom', wintypes.LPCWSTR),
                        ('pTo', wintypes.LPCWSTR),
                        ('fFlags', wintypes.WORD),
                        ('fAnyOperationsAborted', wintypes.BOOL),
                        ('hNameMappings', wintypes.LPVOID),
                        ('lpszProgressTitle', wintypes.LPCWSTR),
                    ]

                FO_DELETE = 0x0003
                FOF_ALLOWUNDO = 0x0040
                FOF_NOCONFIRMATION = 0x0010
                FOF_SILENT = 0x0004

                abs_path_str = str(p)
                p_from = abs_path_str + '\0\0'
                fileop = SHFILEOPSTRUCTW()
                fileop.hwnd = 0
                fileop.wFunc = FO_DELETE
                fileop.pFrom = p_from
                fileop.pTo = None
                fileop.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT
                fileop.fAnyOperationsAborted = False
                fileop.hNameMappings = None
                fileop.lpszProgressTitle = None

                res = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(fileop))
                if res == 0 and not p.exists():
                    return True, f"File '{p.name}' berhasil dipindahkan ke Recycle Bin."
            except Exception as bin_err:
                print(f"Recycle bin operation failed for {p}, falling back to os.remove: {bin_err}")

        # Fallback to direct os.remove
        p.unlink(missing_ok=True)
        return True, f"File '{p.name}' berhasil dihapus."
    except Exception as e:
        return False, f"Gagal menghapus '{Path(file_path).name}': {str(e)}"

