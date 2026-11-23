import os
import zipfile
from tempfile import TemporaryDirectory
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
    with Image.open(image_path) as source:
        with ImageOps.exif_transpose(source) as img:
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                with img.convert('RGBA') as rgba:
                    rgb_img = Image.new('RGB', rgba.size, (255, 255, 255))
                    with rgba.getchannel('A') as alpha:
                        rgb_img.paste(rgba, mask=alpha)
                    return rgb_img
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
    Jika custom_groups_str diisi (misal '105-108'), halaman di dalam rentang
    akan digabungkan sesuai rentang tersebut, sedangkan halaman lainnya di luar rentang
    akan digabungkan sesuai default `group_size` (misal per 1, 2, 3, dst.).
    """
    g_size = max(1, group_size)

    if custom_groups_str and custom_groups_str.strip():
        explicit_ranges = []
        parts = [p.strip() for p in custom_groups_str.split(",") if p.strip()]
        for part in parts:
            if "-" in part:
                bounds = part.split("-")
                if len(bounds) == 2:
                    try:
                        s = int(bounds[0].strip())
                        e = int(bounds[1].strip())
                        start_p = min(s, e)
                        end_p = max(s, e)
                        if 1 <= start_p <= total_images:
                            end_p = min(end_p, total_images)
                            explicit_ranges.append((start_p, end_p))
                    except ValueError:
                        pass
            else:
                try:
                    s = int(part)
                    if 1 <= s <= total_images:
                        explicit_ranges.append((s, s))
                except ValueError:
                    pass

        if explicit_ranges:
            explicit_ranges.sort(key=lambda r: r[0])
            groups = []
            cur_p = 1
            range_ptr = 0

            while cur_p <= total_images:
                # Cek apakah cur_p cocok dengan rentang khusus
                matched_range = None
                while range_ptr < len(explicit_ranges):
                    r_start, r_end = explicit_ranges[range_ptr]
                    if r_end < cur_p:
                        range_ptr += 1
                        continue
                    if r_start <= cur_p <= r_end:
                        matched_range = (r_start, r_end)
                    break

                if matched_range:
                    r_start, r_end = matched_range
                    grp = [p - 1 for p in range(cur_p, r_end + 1)]
                    groups.append(grp)
                    cur_p = r_end + 1
                    range_ptr += 1
                else:
                    # Halaman reguler: kelompokkan per g_size tanpa melompati rentang khusus berikutnya
                    next_start = None
                    if range_ptr < len(explicit_ranges):
                        next_start = explicit_ranges[range_ptr][0]

                    if next_start and next_start > cur_p:
                        max_avail = next_start - cur_p
                        chunk_len = min(g_size, max_avail)
                    else:
                        max_avail = total_images - cur_p + 1
                        chunk_len = min(g_size, max_avail)

                    grp = [p - 1 for p in range(cur_p, cur_p + chunk_len)]
                    groups.append(grp)
                    cur_p += chunk_len

            return groups

    # Auto group size murni
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
        if not p.is_file():
            raise FileNotFoundError(f"Gambar sumber tidak ditemukan: {p.name}")
        parsed_items.append((p, rot))

    if not parsed_items:
        raise ValueError("Tidak ada file gambar valid yang ditemukan.")
        
    margin = MARGINS.get(margin_size.lower(), 0)
    base_page_size = PAGE_SIZES.get(paper_size.lower(), None)
    
    if not fitz:
        raise RuntimeError("PyMuPDF diperlukan untuk konversi gambar ke PDF.")
    from .image_pdf_writer import write_image_pdf

    total_imgs = len(parsed_items)
    combined = mode == "combine"
    groups = [list(range(total_imgs))] if combined else create_image_groups(
        total_imgs, group_size=group_size, custom_groups_str=custom_groups_str
    )
    final_path = output_path if combined else output_path.with_suffix(".zip")
    seen_names = set()
    generated_files_count = 0

    with TemporaryDirectory(prefix=".image-pdf-", dir=final_path.parent) as scratch:
        scratch_path = Path(scratch)
        staged_output = scratch_path / ("result.pdf" if combined else "result.zip")
        if combined:
            write_image_pdf(parsed_items, staged_output, scratch_path, base_page_size,
                            orientation, margin, prepare_image_for_pdf)
            generated_files_count = 1
        else:
            with zipfile.ZipFile(staged_output, "w", zipfile.ZIP_DEFLATED) as zipf:
                for g_idx, indices in enumerate(groups):
                    if naming_mode == "sequence":
                        cur_val = start_num + g_idx * step
                        num_str = f"{cur_val:0{padding}d}" if padding > 0 else str(cur_val)
                        pdf_name = f"{prefix}{num_str}{suffix}.pdf"
                    else:
                        first_stem = parsed_items[indices[0]][0].stem
                        last_stem = parsed_items[indices[-1]][0].stem
                        if len(indices) == 1:
                            stem = first_stem
                        elif first_stem == last_stem:
                            stem = f"{first_stem}_{g_idx + 1}"
                        else:
                            stem = f"{first_stem}_{last_stem}"
                        pdf_name = f"{prefix}{stem}{suffix}.pdf"
                    base_pdf_name = pdf_name
                    dup_counter = 1
                    while pdf_name in seen_names:
                        pdf_name = f"{Path(base_pdf_name).stem}_{dup_counter}.pdf"
                        dup_counter += 1
                    seen_names.add(pdf_name)
                    group_file = scratch_path / "group.pdf"
                    write_image_pdf((parsed_items[i] for i in indices), group_file,
                                    scratch_path, base_page_size, orientation, margin,
                                    prepare_image_for_pdf)
                    zipf.write(group_file, arcname=pdf_name)
                    group_file.unlink()
                    generated_files_count += 1
            with zipfile.ZipFile(staged_output) as archive:
                if len(archive.infolist()) != len(groups):
                    raise RuntimeError("Jumlah file PDF tidak sesuai kelompok.")
        os.replace(staged_output, final_path)

    result = {
        "success": True,
        "mode": "combine" if combined else "individual",
        "output_path": str(final_path),
        "filename": final_path.name,
        "total_images": total_imgs,
        "total_files": generated_files_count,
        "file_size": final_path.stat().st_size,
    }
    if not combined:
        result["group_size"] = group_size
    return result


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
