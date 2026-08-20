import os
import io
import zipfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image, ImageOps

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None

from .utils import natural_sort_key

# Standar ukuran kertas dalam points (72 points = 1 inch)
PAGE_SIZES = {
    "fit": None,
    "a4": (595, 842),       # A4 Portrait: 210 x 297 mm
    "letter": (612, 792),   # Letter Portrait: 8.5 x 11 inch
    "legal": (612, 1008),   # Legal Portrait
}

MARGINS = {
    "none": 0,
    "small": 20,
    "big": 40
}


def prepare_image_for_pdf(image_path: str | Path) -> Image.Image:
    """Mempersiapkan gambar dengan orientasi EXIF yang benar dan background putih jika ada transparansi."""
    img = Image.open(image_path)
    img = ImageOps.exif_transpose(img)
    
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        rgb_img.paste(img, mask=img.split()[3])
        return rgb_img
    else:
        return img.convert('RGB')


def fit_image_to_page(img: Image.Image, page_size: tuple[int, int], margin: int = 0) -> Image.Image:
    """Menempatkan gambar di dalam kanvas ukuran kertas tertentu dengan margin."""
    page_w, page_h = page_size
    avail_w = max(10, page_w - (2 * margin))
    avail_h = max(10, page_h - (2 * margin))
    
    # Rasio skala agar gambar pas di dalam area yang tersedia tanpa terdistorsi
    img_w, img_h = img.size
    scale = min(avail_w / img_w, avail_h / img_h)
    new_w = int(img_w * scale)
    new_h = int(img_h * scale)
    
    resized_img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Buat halaman putih baru
    page = Image.new("RGB", (page_w, page_h), (255, 255, 255))
    pos_x = margin + (avail_w - new_w) // 2
    pos_y = margin + (avail_h - new_h) // 2
    page.paste(resized_img, (pos_x, pos_y))
    return page


def create_image_groups(
    total_images: int,
    group_size: int = 1,
    custom_groups_str: Optional[str] = None
) -> List[List[int]]:
    """
    Mengembalikan list of list indices (0-indexed) untuk pembagian kelompok gambar.
    Contoh group_size=2 pada 4 gambar: [[0, 1], [2, 3]]
    """
    if custom_groups_str and custom_groups_str.strip():
        groups = []
        parts = [p.strip() for p in custom_groups_str.split(",") if p.strip()]
        for part in parts:
            if "-" in part:
                bounds = part.split("-")
                if len(bounds) == 2:
                    try:
                        s = int(bounds[0].strip())
                        e = int(bounds[1].strip())
                        grp = [i - 1 for i in range(min(s, e), max(s, e) + 1) if 1 <= i <= total_images]
                        if grp:
                            groups.append(grp)
                    except ValueError:
                        pass
            else:
                try:
                    s = int(part)
                    if 1 <= s <= total_images:
                        groups.append([s - 1])
                except ValueError:
                    pass
        if groups:
            return groups

    # Auto group size
    g_size = max(1, group_size)
    groups = []
    for i in range(0, total_images, g_size):
        groups.append(list(range(i, min(i + g_size, total_images))))
    return groups


def convert_images_to_pdf(
    image_paths: List[Any], # List of str | Path | Dict[str, Any]
    output_path: str | Path,
    mode: str = "combine", # "combine" (1 PDF) atau "individual" / "separated" (ZIP)
    paper_size: str = "fit", # "fit", "a4", "letter"
    orientation: str = "auto", # "auto", "portrait", "landscape"
    margin_size: str = "none", # "none", "small", "big"
    group_size: int = 1, # Berapa gambar per file PDF (misal 2 gambar jadi 1 PDF)
    custom_groups_str: Optional[str] = None, # Rentang custom misal "1-2, 3-4"
    naming_mode: str = "original", # "original" | "sequence"
    prefix: str = "",
    start_num: int = 1,
    step: int = 1,
    padding: int = 0,
    suffix: str = ""
) -> Dict[str, Any]:
    """Mengonversi sekumpulan gambar menjadi PDF dengan opsi grouping dan penamaan canggih."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    parsed_items = []
    for item in image_paths:
        if isinstance(item, dict):
            p = Path(item.get("path", ""))
            rot = int(item.get("rotation", 0)) % 360
        else:
            p = Path(str(item))
            rot = 0
        if p.exists() and p.is_file():
            parsed_items.append((p, rot))

    if not parsed_items:
        raise ValueError("Tidak ada file gambar valid yang ditemukan.")
        
    margin = MARGINS.get(margin_size.lower(), 0)
    base_page_size = PAGE_SIZES.get(paper_size.lower(), None)
    
    processed_images = []
    
    for p, rot in parsed_items:
        img = prepare_image_for_pdf(p)
        if rot != 0:
            img = img.rotate(-rot, expand=True)
        
        # Tentukan ukuran halaman
        if base_page_size is not None:
            pw, ph = base_page_size
            if orientation == "landscape":
                target_size = (max(pw, ph), min(pw, ph))
            elif orientation == "portrait":
                target_size = (min(pw, ph), max(pw, ph))
            else: # auto
                if img.width > img.height:
                    target_size = (max(pw, ph), min(pw, ph))
                else:
                    target_size = (min(pw, ph), max(pw, ph))
            
            page_img = fit_image_to_page(img, target_size, margin=margin)
            processed_images.append(page_img)
        else:
            # Mode "fit" (ukuran asli gambar)
            if margin > 0:
                target_size = (img.width + (2 * margin), img.height + (2 * margin))
                page_img = fit_image_to_page(img, target_size, margin=margin)
                processed_images.append(page_img)
            else:
                processed_images.append(img)
                
    total_imgs = len(processed_images)

    if mode == "combine":
        # Simpan semua gambar ke dalam satu file PDF tunggal
        first_img = processed_images[0]
        other_imgs = processed_images[1:] if total_imgs > 1 else []
        first_img.save(
            output_path,
            "PDF",
            resolution=100.0,
            save_all=True,
            append_images=other_imgs
        )
        return {
            "success": True,
            "mode": "combine",
            "output_path": str(output_path),
            "filename": output_path.name,
            "total_images": total_imgs,
            "total_files": 1,
            "file_size": output_path.stat().st_size
        }
    else:
        # Mode Terpisah (Individual / Grouping per N Gambar) -> Dikemas ke ZIP
        zip_output_path = output_path.with_suffix(".zip")
        groups = create_image_groups(total_imgs, group_size=group_size, custom_groups_str=custom_groups_str)
        
        seen_names = set()
        generated_files_count = 0

        with zipfile.ZipFile(zip_output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for g_idx, indices in enumerate(groups):
                if not indices:
                    continue
                first_img = processed_images[indices[0]]
                other_imgs = [processed_images[i] for i in indices[1:]] if len(indices) > 1 else []
                
                # Tentukan nama file
                if naming_mode == "sequence":
                    cur_val = start_num + (g_idx * step)
                    num_str = f"{cur_val:0{padding}d}" if padding > 0 else str(cur_val)
                    pdf_name = f"{prefix}{num_str}{suffix}.pdf"
                else:
                    # Naming mode: original
                    if len(indices) == 1:
                        base_stem = parsed_items[indices[0]][0].stem
                        pdf_name = f"{prefix}{base_stem}{suffix}.pdf"
                    else:
                        first_stem = parsed_items[indices[0]][0].stem
                        last_stem = parsed_items[indices[-1]][0].stem
                        if first_stem == last_stem:
                            pdf_name = f"{prefix}{first_stem}_{g_idx + 1}{suffix}.pdf"
                        else:
                            pdf_name = f"{prefix}{first_stem}_{last_stem}{suffix}.pdf"
                
                # Hindari tabrakan nama kembar
                base_pdf_name = pdf_name
                dup_counter = 1
                while pdf_name in seen_names:
                    pdf_name = f"{Path(base_pdf_name).stem}_{dup_counter}.pdf"
                    dup_counter += 1
                seen_names.add(pdf_name)

                pdf_bytes_io = io.BytesIO()
                first_img.save(
                    pdf_bytes_io,
                    "PDF",
                    resolution=100.0,
                    save_all=(len(other_imgs) > 0),
                    append_images=other_imgs
                )
                zipf.writestr(pdf_name, pdf_bytes_io.getvalue())
                generated_files_count += 1
                
        return {
            "success": True,
            "mode": "individual",
            "output_path": str(zip_output_path),
            "filename": zip_output_path.name,
            "total_images": total_imgs,
            "total_files": generated_files_count,
            "group_size": group_size,
            "file_size": zip_output_path.stat().st_size
        }


def convert_pdf_to_images(
    pdf_path: str | Path,
    output_dir_or_zip: str | Path,
    image_format: str = "jpg", # "jpg" atau "png"
    dpi: int = 150,
    page_selection: Optional[List[int]] = None # List nomor halaman 1-indexed
) -> Dict[str, Any]:
    """Mengekstrak halaman PDF menjadi gambar (JPG/PNG), disimpan dalam ZIP."""
    if not fitz:
        raise RuntimeError("PyMuPDF (fitz) diperlukan untuk konversi PDF ke Gambar.")
        
    pdf_path = Path(pdf_path)
    output_path = Path(output_dir_or_zip)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"File PDF tidak ditemukan: {pdf_path}")
        
    doc = fitz.open(str(pdf_path))
    total_doc_pages = len(doc)
    
    if page_selection:
        target_pages = [p - 1 for p in page_selection if 1 <= p <= total_doc_pages]
    else:
        target_pages = list(range(total_doc_pages))
        
    if not target_pages:
        doc.close()
        raise ValueError("Tidak ada halaman yang dipilih.")
        
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    
    fmt = image_format.lower()
    if fmt not in ["jpg", "jpeg", "png"]:
        fmt = "jpg"
    ext = "jpg" if fmt in ["jpg", "jpeg"] else "png"
    
    # Jika hanya 1 halaman dan output adalah single image
    if len(target_pages) == 1 and not output_path.name.endswith(".zip"):
        page = doc[target_pages[0]]
        pix = page.get_pixmap(matrix=mat, alpha=(fmt == "png"))
        single_img_path = output_path.with_suffix(f".{ext}")
        pix.save(str(single_img_path))
        doc.close()
        return {
            "success": True,
            "output_path": str(single_img_path),
            "filename": single_img_path.name,
            "page_count": 1,
            "file_size": single_img_path.stat().st_size
        }
        
    # Jika banyak halaman, bungkus dalam ZIP
    zip_path = output_path if output_path.suffix == ".zip" else output_path.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for p_idx in target_pages:
            page = doc[p_idx]
            pix = page.get_pixmap(matrix=mat, alpha=(fmt == "png"))
            img_data = pix.tobytes(ext)
            file_name = f"{pdf_path.stem}_page_{p_idx + 1:03d}.{ext}"
            zipf.writestr(file_name, img_data)
            
    doc.close()
    return {
        "success": True,
        "output_path": str(zip_path),
        "filename": zip_path.name,
        "page_count": len(target_pages),
        "file_size": zip_path.stat().st_size
    }
