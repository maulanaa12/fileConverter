import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from pypdf import PdfWriter, PdfReader
from .utils import natural_sort_key

def merge_pdf_files(
    file_items: List[Dict[str, Any]], 
    output_path: str | Path,
    auto_natural_sort: bool = False
) -> Dict[str, Any]:
    """
    Menggabungkan beberapa file PDF menjadi satu file PDF.
    
    file_items: List dictionary berformat:
      [
        {
          "path": "path/to/file1.pdf",
          "rotation": 0, # 0, 90, 180, 270 (opsional)
          "pages": [1, 2, 3] # list nomor halaman 1-indexed (opsional, default semua)
        }, ...
      ]
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if auto_natural_sort:
        file_items = sorted(file_items, key=lambda x: natural_sort_key(Path(x["path"]).name))
        
    writer = PdfWriter()
    total_pages_merged = 0
    merged_files_count = 0
    
    for item in file_items:
        file_path = Path(item["path"])
        if not file_path.exists():
            continue
            
        rotation = int(item.get("rotation", 0)) % 360
        selected_pages = item.get("pages", None)
        
        reader = PdfReader(str(file_path))
        num_pages = len(reader.pages)
        
        # Tentukan halaman yang akan dimasukkan
        if selected_pages is not None and isinstance(selected_pages, list):
            target_indices = [p - 1 for p in selected_pages if 1 <= p <= num_pages]
        else:
            target_indices = list(range(num_pages))
            
        for page_idx in target_indices:
            page = reader.pages[page_idx]
            if rotation != 0:
                page.rotate(rotation)
            writer.add_page(page)
            total_pages_merged += 1
            
        merged_files_count += 1
        
    if total_pages_merged == 0:
        raise ValueError("Tidak ada halaman yang dapat digabungkan!")
        
    with open(output_path, "wb") as f_out:
        writer.write(f_out)
        
    return {
        "success": True,
        "output_path": str(output_path),
        "filename": output_path.name,
        "merged_files_count": merged_files_count,
        "total_pages": total_pages_merged,
        "file_size": output_path.stat().st_size
    }
