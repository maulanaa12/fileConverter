import os
import re
import zipfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from pypdf import PdfReader, PdfWriter

def parse_page_range(range_str: str, total_pages: int) -> List[int]:
    """
    Mengubah string range seperti '1-3, 5, 7-10' menjadi list integer [1, 2, 3, 5, 7, 8, 9, 10].
    """
    pages = set()
    parts = [p.strip() for p in range_str.split(",") if p.strip()]
    
    for part in parts:
        if "-" in part:
            bounds = part.split("-")
            if len(bounds) == 2:
                try:
                    start = int(bounds[0].strip())
                    end = int(bounds[1].strip())
                    for p in range(min(start, end), max(start, end) + 1):
                        if 1 <= p <= total_pages:
                            pages.add(p)
                except ValueError:
                    pass
        else:
            try:
                p = int(part)
                if 1 <= p <= total_pages:
                    pages.add(p)
            except ValueError:
                pass
                
    return sorted(list(pages))


def split_pdf(
    pdf_path: str | Path,
    output_path: str | Path,
    mode: str = "ranges", # "ranges", "single_pages", "extract_selected"
    ranges_str: str = "", # e.g. "1-2, 3-5"
    selected_pages: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Memisahkan halaman PDF berdasarkan rentang atau menjadi halaman-halaman tunggal.
    """
    pdf_path = Path(pdf_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    reader = PdfReader(str(pdf_path))
    total_pages = len(reader.pages)
    
    if total_pages == 0:
        raise ValueError("File PDF kosong.")
        
    stem = pdf_path.stem
    
    if mode == "extract_selected":
        # Ekstrak halaman-halaman yang dipilih menjadi 1 PDF tunggal
        if not selected_pages:
            selected_pages = parse_page_range(ranges_str, total_pages)
            
        if not selected_pages:
            raise ValueError("Tidak ada halaman valid yang dipilih untuk diekstrak.")
            
        writer = PdfWriter()
        for p in selected_pages:
            writer.add_page(reader.pages[p - 1])
            
        target_pdf = output_path if output_path.suffix == ".pdf" else output_path.with_suffix(".pdf")
        with open(target_pdf, "wb") as f_out:
            writer.write(f_out)
            
        return {
            "success": True,
            "mode": "extract_selected",
            "output_path": str(target_pdf),
            "filename": target_pdf.name,
            "total_extracted_pages": len(selected_pages),
            "file_size": target_pdf.stat().st_size
        }
        
    elif mode == "single_pages":
        # Setiap halaman jadi 1 file PDF, disimpan dalam ZIP
        zip_path = output_path if output_path.suffix == ".zip" else output_path.with_suffix(".zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for idx in range(total_pages):
                writer = PdfWriter()
                writer.add_page(reader.pages[idx])
                
                single_pdf_bytes = io_write_pdf(writer)
                file_name = f"{stem}_page_{idx + 1:03d}.pdf"
                zipf.writestr(file_name, single_pdf_bytes)
                
        return {
            "success": True,
            "mode": "single_pages",
            "output_path": str(zip_path),
            "filename": zip_path.name,
            "total_files": total_pages,
            "file_size": zip_path.stat().st_size
        }
        
    else: # mode == "ranges" (misal "1-3, 4-6")
        range_blocks = [r.strip() for r in ranges_str.split(",") if r.strip()]
        if not range_blocks:
            raise ValueError("Harap tentukan rentang halaman (contoh: 1-3, 4-5).")
            
        zip_path = output_path if output_path.suffix == ".zip" else output_path.with_suffix(".zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for idx, block in enumerate(range_blocks):
                pages_in_block = parse_page_range(block, total_pages)
                if not pages_in_block:
                    continue
                writer = PdfWriter()
                for p in pages_in_block:
                    writer.add_page(reader.pages[p - 1])
                
                block_slug = block.replace("-", "_to_")
                file_name = f"{stem}_part_{idx + 1}_{block_slug}.pdf"
                zipf.writestr(file_name, io_write_pdf(writer))
                
        return {
            "success": True,
            "mode": "ranges",
            "output_path": str(zip_path),
            "filename": zip_path.name,
            "total_files": len(range_blocks),
            "file_size": zip_path.stat().st_size
        }


def organize_pdf_pages(
    pdf_path: str | Path,
    output_path: str | Path,
    page_operations: List[Dict[str, Any]] # [{"page": 1, "rotation": 0, "delete": False}, ...]
) -> Dict[str, Any]:
    """
    Menyusun ulang, memutar, atau menghapus halaman pada PDF.
    """
    pdf_path = Path(pdf_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    reader = PdfReader(str(pdf_path))
    total_pages = len(reader.pages)
    
    writer = PdfWriter()
    added_count = 0
    
    for op in page_operations:
        if op.get("delete", False):
            continue
        p_num = int(op.get("page", 1))
        rot = int(op.get("rotation", 0)) % 360
        
        if 1 <= p_num <= total_pages:
            page = reader.pages[p_num - 1]
            if rot != 0:
                page.rotate(rot)
            writer.add_page(page)
            added_count += 1
            
    if added_count == 0:
        raise ValueError("Semua halaman dihapus atau tidak ada halaman yang valid.")
        
    target_pdf = output_path if output_path.suffix == ".pdf" else output_path.with_suffix(".pdf")
    with open(target_pdf, "wb") as f_out:
        writer.write(f_out)
        
    return {
        "success": True,
        "output_path": str(target_pdf),
        "filename": target_pdf.name,
        "total_pages": added_count,
        "file_size": target_pdf.stat().st_size
    }


def io_write_pdf(writer: PdfWriter) -> bytes:
    import io
    b = io.BytesIO()
    writer.write(b)
    return b.getvalue()
