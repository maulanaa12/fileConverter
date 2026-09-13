from pathlib import Path
from typing import Dict, Any

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None

from pypdf import PdfReader, PdfWriter

# Konfigurasi parameter kompresi per level
# Setiap level mendefinisikan parameter save() dan rewrite_images() yang berbeda
COMPRESS_LEVELS = {
    "low": {
        "label": "Kompresi Ringan",
        "save_params": {
            "garbage": 3,
            "deflate": True,
            "use_objstms": True,
        },
        "rewrite_images": None,  # Tidak menyentuh gambar (lossless only)
    },
    "medium": {
        "label": "Kompresi Optimal",
        "save_params": {
            "garbage": 4,
            "deflate": True,
            "clean": True,
            "use_objstms": True,
        },
        "rewrite_images": {
            "quality": 85,
            "dpi_threshold": 300,
            "dpi_target": 150,
        },
    },
    "high": {
        "label": "Kompresi Maksimal",
        "save_params": {
            "garbage": 4,
            "deflate": True,
            "clean": True,
            "use_objstms": True,
            "compression_effort": 100,
        },
        "rewrite_images": {
            "quality": 50,
            "dpi_threshold": 200,
            "dpi_target": 96,
        },
    },
}


def compress_pdf(
    pdf_path: str | Path,
    output_path: str | Path,
    level: str = "medium"  # "low", "medium", "high"
) -> Dict[str, Any]:
    """
    Mengompresi ukuran file PDF dengan strategi berbeda berdasarkan level:
    - low:    Lossless — garbage collection + deflate, gambar tidak diubah
    - medium: Balanced — lossless + mild image recompression (quality 85, DPI 150)
    - high:   Aggressive — max compression + heavy image recompression (quality 50, DPI 96)
    """
    pdf_path = Path(pdf_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    orig_size = pdf_path.stat().st_size

    # Ambil konfigurasi level, fallback ke medium jika level tidak dikenal
    config = COMPRESS_LEVELS.get(level, COMPRESS_LEVELS["medium"])

    if fitz:
        doc = fitz.open(str(pdf_path))

        # Tahap 1: Rewrite images (jika level memerlukan)
        rewrite_cfg = config["rewrite_images"]
        if rewrite_cfg is not None:
            try:
                doc.rewrite_images(
                    quality=rewrite_cfg["quality"],
                    dpi_threshold=rewrite_cfg["dpi_threshold"],
                    dpi_target=rewrite_cfg["dpi_target"],
                )
            except Exception as e:
                # rewrite_images bisa gagal pada PDF tertentu (encrypted, corrupted images)
                # Lanjutkan dengan save saja tanpa image rewrite
                print(f"rewrite_images skipped: {e}")

        # Tahap 2: Save dengan parameter kompresi yang sesuai level
        doc.save(str(output_path), **config["save_params"])
        doc.close()
    else:
        # Fallback ke pypdf — hanya stream compression dasar (level tidak berdampak)
        reader = PdfReader(str(pdf_path))
        writer = PdfWriter()
        for page in reader.pages:
            page.compress_content_streams()
            writer.add_page(page)

        with open(output_path, "wb") as f_out:
            writer.write(f_out)

    new_size = output_path.stat().st_size
    saved_bytes = max(0, orig_size - new_size)
    percent_saved = (saved_bytes / orig_size) * 100 if orig_size > 0 else 0

    return {
        "success": True,
        "output_path": str(output_path),
        "filename": output_path.name,
        "original_size": orig_size,
        "compressed_size": new_size,
        "saved_bytes": saved_bytes,
        "saved_percent": round(percent_saved, 1),
        "level_used": level,
        "level_label": config["label"],
    }
