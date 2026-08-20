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

def compress_pdf(
    pdf_path: str | Path,
    output_path: str | Path,
    level: str = "medium" # "low", "medium", "high"
) -> Dict[str, Any]:
    """
    Mengompresi ukuran file PDF dengan optimasi stream dan garbage collection.
    """
    pdf_path = Path(pdf_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    orig_size = pdf_path.stat().st_size
    
    if fitz:
        doc = fitz.open(str(pdf_path))
        # Parameter PyMuPDF untuk kompresi: garbage=4 (dedup & unreferenced obj cleanup), deflate=True, clean=True
        doc.save(
            str(output_path),
            garbage=4,
            deflate=True,
            clean=True
        )
        doc.close()
    else:
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
        "saved_percent": round(percent_saved, 1)
    }
