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

import sys

if getattr(sys, 'frozen', False):
    # Dijalankan sebagai bundel PyInstaller
    BASE_DIR = Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent))
    app_data = os.environ.get("LOCALAPPDATA")
    if app_data:
        DATA_DIR = Path(app_data) / "LocalPDFStudio"
    else:
        DATA_DIR = Path.home() / ".localpdf_studio"
else:
    # Dijalankan langsung via interpreter Python
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR

UPLOAD_DIR = DATA_DIR / "uploads"
OUTPUT_DIR = DATA_DIR / "outputs"

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


def pick_modern_folder(title: str = "Pilih Folder", initial_dir: str = "") -> Optional[str]:
    """Membuka jendela File Explorer modern native Windows (IFileOpenDialog) untuk memilih folder."""
    cleaned_dir = initial_dir.strip('"\'') if initial_dir else ""

    if os.name == 'nt':
        try:
            import ctypes
            from ctypes import wintypes, POINTER, c_wchar_p, c_void_p, HRESULT, byref

            class GUID(ctypes.Structure):
                _fields_ = [
                    ("Data1", wintypes.DWORD),
                    ("Data2", wintypes.WORD),
                    ("Data3", wintypes.WORD),
                    ("Data4", wintypes.BYTE * 8)
                ]

            CLSID_FileOpenDialog = GUID(0xDC1C5A9C, 0xE88A, 0x4DDE, (wintypes.BYTE * 8)(0xA5, 0xA1, 0x60, 0xF8, 0x2A, 0x20, 0xAE, 0xF7))
            IID_IFileOpenDialog = GUID(0xD57C7288, 0xD4AD, 0x4768, (wintypes.BYTE * 8)(0xBE, 0x02, 0x9D, 0x96, 0x95, 0x32, 0xD9, 0x60))
            IID_IShellItem = GUID(0x43826D1E, 0xE718, 0x42EE, (wintypes.BYTE * 8)(0xBC, 0x55, 0xA1, 0xE2, 0x61, 0xC3, 0x7B, 0xFE))

            FOS_PICKFOLDERS = 0x00000020
            FOS_FORCEFILESYSTEM = 0x00000040
            SIGDN_FILESYSPATH = 0x80058000

            ole32 = ctypes.oledll.ole32
            ole32.CoInitialize(None)
            shell32 = ctypes.windll.shell32
            user32 = ctypes.windll.user32

            p_dialog = c_void_p()
            hr = ole32.CoCreateInstance(
                byref(CLSID_FileOpenDialog),
                None,
                1,  # CLSCTX_INPROC_SERVER
                byref(IID_IFileOpenDialog),
                byref(p_dialog)
            )

            if hr == 0 and p_dialog.value:
                try:
                    vtable = ctypes.cast(ctypes.cast(p_dialog, POINTER(c_void_p)).contents, POINTER(c_void_p))

                    # 1. GetOptions
                    GetOptions_proto = ctypes.WINFUNCTYPE(HRESULT, c_void_p, POINTER(wintypes.DWORD))
                    GetOptions = GetOptions_proto(vtable[10])
                    current_opts = wintypes.DWORD()
                    GetOptions(p_dialog, byref(current_opts))

                    # 2. SetOptions (FOS_PICKFOLDERS | FOS_FORCEFILESYSTEM)
                    SetOptions_proto = ctypes.WINFUNCTYPE(HRESULT, c_void_p, wintypes.DWORD)
                    SetOptions = SetOptions_proto(vtable[9])
                    SetOptions(p_dialog, current_opts.value | FOS_PICKFOLDERS | FOS_FORCEFILESYSTEM)

                    # 3. SetTitle
                    if title:
                        SetTitle_proto = ctypes.WINFUNCTYPE(HRESULT, c_void_p, c_wchar_p)
                        SetTitle = SetTitle_proto(vtable[17])
                        SetTitle(p_dialog, title)

                    # 4. SetOkButtonLabel
                    SetOk_proto = ctypes.WINFUNCTYPE(HRESULT, c_void_p, c_wchar_p)
                    SetOk = SetOk_proto(vtable[18])
                    SetOk(p_dialog, "Pilih Folder")

                    # 5. Set initial folder if exists
                    if cleaned_dir and Path(cleaned_dir).is_dir():
                        p_shell_item = c_void_p()
                        if shell32.SHCreateItemFromParsingName(c_wchar_p(cleaned_dir), None, byref(IID_IShellItem), byref(p_shell_item)) == 0:
                            SetFolder_proto = ctypes.WINFUNCTYPE(HRESULT, c_void_p, c_void_p)
                            SetFolder = SetFolder_proto(vtable[12])
                            SetFolder(p_dialog, p_shell_item)
                            # Release p_shell_item
                            item_vt = ctypes.cast(ctypes.cast(p_shell_item, POINTER(c_void_p)).contents, POINTER(c_void_p))
                            Release_item = ctypes.WINFUNCTYPE(wintypes.ULONG, c_void_p)(item_vt[2])
                            Release_item(p_shell_item)

                    # 6. Show dialog (menggunakan active foreground window sebagai owner)
                    hwnd_owner = user32.GetForegroundWindow()
                    Show_proto = ctypes.WINFUNCTYPE(HRESULT, c_void_p, wintypes.HWND)
                    Show = Show_proto(vtable[3])
                    show_res = Show(p_dialog, hwnd_owner)

                    # 7. Ambil hasil jika user menekan Pilih Folder (S_OK == 0)
                    if show_res == 0:
                        p_result_item = c_void_p()
                        GetResult_proto = ctypes.WINFUNCTYPE(HRESULT, c_void_p, POINTER(c_void_p))
                        GetResult = GetResult_proto(vtable[20])
                        if GetResult(p_dialog, byref(p_result_item)) == 0 and p_result_item.value:
                            item_vt = ctypes.cast(ctypes.cast(p_result_item, POINTER(c_void_p)).contents, POINTER(c_void_p))
                            GetDisplayName_proto = ctypes.WINFUNCTYPE(HRESULT, c_void_p, wintypes.DWORD, POINTER(c_wchar_p))
                            GetDisplayName = GetDisplayName_proto(item_vt[5])
                            psz_path = c_wchar_p()
                            if GetDisplayName(p_result_item, SIGDN_FILESYSPATH, byref(psz_path)) == 0 and psz_path.value:
                                res_path = str(psz_path.value)
                                ole32.CoTaskMemFree(ctypes.cast(psz_path, c_void_p))
                                Release_res = ctypes.WINFUNCTYPE(wintypes.ULONG, c_void_p)(item_vt[2])
                                Release_res(p_result_item)
                                return res_path
                finally:
                    Release_dlg = ctypes.WINFUNCTYPE(wintypes.ULONG, c_void_p)(vtable[2])
                    Release_dlg(p_dialog)
                    ole32.CoUninitialize()
        except Exception as win_err:
            print(f"Windows modern folder dialog error: {win_err}")

    # Fallback ke Tkinter jika non-Windows atau error
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        selected = filedialog.askdirectory(
            title=title,
            initialdir=cleaned_dir if cleaned_dir and Path(cleaned_dir).is_dir() else None
        )
        root.destroy()
        if selected and Path(selected).is_dir():
            return str(Path(selected).resolve())
    except Exception as tk_err:
        print(f"Tkinter fallback error: {tk_err}")

    return None


