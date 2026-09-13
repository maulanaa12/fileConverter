"""
path_security.py — Modul keamanan path untuk LocalPDF Studio.

Menyediakan AllowedDirRegistry (in-memory, thread-safe) yang membatasi
akses API hanya ke folder yang secara eksplisit dipilih pengguna melalui
native file picker dialog, beserta helper validation functions.
"""

import threading
from pathlib import Path
from typing import Set, Optional


class AllowedDirRegistry:
    """
    Registry in-memory untuk direktori yang diizinkan diakses oleh API.
    Thread-safe. Hanya folder yang didaftarkan secara eksplisit
    (via pick-folder dialog) atau subdirektori-nya yang boleh diakses.
    """

    def __init__(self):
        self._allowed_dirs: Set[Path] = set()
        self._lock = threading.Lock()

    def register(self, directory: str | Path) -> Path:
        """Mendaftarkan direktori ke registry. Mengembalikan resolved Path."""
        resolved = Path(directory).resolve()
        with self._lock:
            self._allowed_dirs.add(resolved)
        return resolved

    def is_allowed(self, target_path: str | Path) -> bool:
        """
        Cek apakah path target berada di dalam salah satu allowed directory.
        Subdirektori dari direktori yang terdaftar juga diizinkan.
        """
        resolved = Path(target_path).resolve()
        with self._lock:
            for allowed in self._allowed_dirs:
                try:
                    resolved.relative_to(allowed)
                    return True
                except ValueError:
                    continue
        return False

    def clear(self):
        """Reset seluruh registry (berguna untuk testing)."""
        with self._lock:
            self._allowed_dirs.clear()

    @property
    def registered_dirs(self) -> frozenset:
        """Mengembalikan salinan read-only dari direktori yang terdaftar."""
        with self._lock:
            return frozenset(self._allowed_dirs)


# ============================================================
# Singleton instance
# ============================================================
_registry = AllowedDirRegistry()


def get_registry() -> AllowedDirRegistry:
    """Mengembalikan singleton AllowedDirRegistry."""
    return _registry


# ============================================================
# Konstanta ekstensi file yang diizinkan
# ============================================================

# Ekstensi file yang diizinkan untuk preview/serving
ALLOWED_PREVIEW_EXTENSIONS = frozenset(
    {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff', '.pdf'}
)

# Ekstensi file yang diizinkan untuk dihapus
ALLOWED_DELETE_EXTENSIONS = frozenset(
    {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff'}
)


# ============================================================
# Validation helpers
# ============================================================

def validate_path_allowed(
    path: str | Path,
    registry: Optional[AllowedDirRegistry] = None
) -> Path:
    """
    Memvalidasi bahwa path berada di dalam allowed directory.

    Args:
        path: Path yang akan divalidasi (file atau direktori).
        registry: Instance registry (opsional, default ke singleton).

    Returns:
        Resolved Path jika valid.

    Raises:
        fastapi.HTTPException 403 jika path tidak diizinkan.
    """
    from fastapi import HTTPException

    reg = registry or _registry
    resolved = Path(path).resolve()

    if not reg.is_allowed(resolved):
        raise HTTPException(
            status_code=403,
            detail=(
                f"Akses ditolak. Folder '{resolved.parent}' belum dipilih "
                f"melalui file picker. Silakan pilih folder terlebih dahulu "
                f"menggunakan tombol 'Pilih Folder'."
            )
        )
    return resolved


def validate_file_extension(
    path: Path,
    allowed_extensions: frozenset
) -> None:
    """
    Memvalidasi bahwa file memiliki ekstensi yang diizinkan.

    Args:
        path: Path file yang akan diperiksa.
        allowed_extensions: Set ekstensi yang diperbolehkan (lowercase, dengan titik).

    Raises:
        fastapi.HTTPException 400 jika ekstensi tidak valid.
    """
    from fastapi import HTTPException

    if path.suffix.lower() not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Tipe file '{path.suffix}' tidak diizinkan. "
                f"Hanya file dengan ekstensi berikut yang diperbolehkan: "
                f"{', '.join(sorted(allowed_extensions))}"
            )
        )
