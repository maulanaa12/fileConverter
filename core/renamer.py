import os
import re
import json
import uuid
import zipfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from .utils import natural_sort_key

def calculate_new_names(
    file_names: List[str],
    rule_type: str,
    prefix: str = "",
    suffix: str = "",
    start_num: int = 1,
    step: int = 1,
    padding: int = 0,
    find_text: str = "",
    replace_text: str = "",
    is_regex: bool = False,
    case_transform: str = "none", # "none", "upper", "lower", "title"
    shift_offset: int = 0,
    shift_min_num: Optional[int] = None, # Hanya shift jika nomor >= min_num
    shift_max_num: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Menghitung nama baru untuk daftar file dan mendeteksi potensi duplikasi.
    """
    results = []
    seen_names = set()
    
    for idx, orig_name in enumerate(file_names):
        p = Path(orig_name)
        stem = p.stem
        ext = p.suffix
        new_stem = stem
        
        if rule_type == "sequence":
            current_num = start_num + (idx * step)
            num_str = f"{current_num:0{padding}d}" if padding > 0 else str(current_num)
            new_stem = f"{prefix}{num_str}{suffix}"
            
        elif rule_type == "shift":
            # Cari angka dalam nama file (mengambil angka pertama atau angka utama)
            match = re.search(r'(\d+)', stem)
            if match:
                num_val = int(match.group(1))
                # Cek batas filter jika ditentukan
                in_range = True
                if shift_min_num is not None and num_val < shift_min_num:
                    in_range = False
                if shift_max_num is not None and num_val > shift_max_num:
                    in_range = False
                    
                if in_range:
                    new_val = max(0, num_val + shift_offset)
                    pad_len = padding if padding > 0 else len(match.group(1))
                    new_num_str = f"{new_val:0{pad_len}d}"
                    # Ganti angka yang cocok
                    new_stem = stem[:match.start(1)] + new_num_str + stem[match.end(1):]
            if prefix or suffix:
                new_stem = f"{prefix}{new_stem}{suffix}"
                
        elif rule_type == "replace":
            if find_text:
                if is_regex:
                    try:
                        new_stem = re.sub(find_text, replace_text, stem)
                    except Exception:
                        new_stem = stem
                else:
                    new_stem = stem.replace(find_text, replace_text)
            if prefix or suffix:
                new_stem = f"{prefix}{new_stem}{suffix}"
                
        elif rule_type == "add_prefix_suffix":
            new_stem = f"{prefix}{stem}{suffix}"
            
        # Transformasi huruf kapital/kecil
        if case_transform == "upper":
            new_stem = new_stem.upper()
        elif case_transform == "lower":
            new_stem = new_stem.lower()
        elif case_transform == "title":
            new_stem = new_stem.title()
            
        new_filename = f"{new_stem}{ext}"
        
        status = "ok"
        if new_filename in seen_names:
            status = "duplicate"
        seen_names.add(new_filename)
        
        results.append({
            "original_name": orig_name,
            "new_name": new_filename,
            "changed": (orig_name != new_filename),
            "status": status
        })
        
    return results


def process_rename_uploaded(
    uploaded_files: List[tuple[str, str]], # [(temp_path, original_name), ...]
    rule_options: Dict[str, Any],
    output_zip_path: str | Path
) -> Dict[str, Any]:
    """
    Memproses rename untuk file yang diunggah dan menyimpannya ke file ZIP.
    """
    output_zip_path = Path(output_zip_path)
    output_zip_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_names = [orig_name for _, orig_name in uploaded_files]
    previews = calculate_new_names(file_names, **rule_options)
    
    with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for idx, (temp_path, _) in enumerate(uploaded_files):
            new_name = previews[idx]["new_name"]
            zipf.write(temp_path, arcname=new_name)
            
    return {
        "success": True,
        "output_path": str(output_zip_path),
        "filename": output_zip_path.name,
        "total_files": len(uploaded_files),
        "file_size": output_zip_path.stat().st_size,
        "renamed_items": previews
    }


def process_rename_local_folder(
    folder_path: str | Path,
    rule_options: Dict[str, Any],
    file_extensions: tuple = ('.pdf', '.jpg', '.jpeg', '.png')
) -> Dict[str, Any]:
    """
    Memproses rename langsung pada folder lokal komputer dengan pengamanan two-pass
    dan membuat file rename_history.json untuk fitur undo.
    """
    folder = Path(folder_path).resolve()
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"Folder lokal '{folder}' tidak ditemukan.")
        
    # Ambil file yang sesuai
    files = [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in file_extensions]
    files.sort(key=lambda f: natural_sort_key(f.name))
    
    if not files:
        raise ValueError(f"Tidak ada file yang cocok ditemukan di '{folder}'.")
        
    file_names = [f.name for f in files]
    previews = calculate_new_names(file_names, **rule_options)
    
    records = []
    # Two-pass rename menggunakan nama sementara UUID untuk mencegah tabrakan nama (overwrite collision)
    temp_renames = []
    
    for idx, file_obj in enumerate(files):
        item = previews[idx]
        old_name = item["original_name"]
        new_name = item["new_name"]
        
        if old_name != new_name:
            old_path = folder / old_name
            temp_name = f"__tmp_{uuid.uuid4().hex}_{new_name}"
            temp_path = folder / temp_name
            
            # Pass 1: Rename ke temporary
            old_path.rename(temp_path)
            temp_renames.append((temp_path, folder / new_name, old_name, new_name))
            
    # Pass 2: Rename dari temporary ke new_name
    for temp_path, target_path, old_name, new_name in temp_renames:
        temp_path.rename(target_path)
        records.append({
            "old_path": str(folder / old_name),
            "new_path": str(target_path),
            "old_name": old_name,
            "new_name": new_name
        })
        
    # Simpan history ke JSON di folder tersebut
    history_data = {
        "folder": str(folder),
        "total_renamed": len(records),
        "records": records
    }
    history_file = folder / "rename_history.json"
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history_data, f, indent=2, ensure_ascii=False)
        
    return {
        "success": True,
        "folder": str(folder),
        "total_files": len(files),
        "renamed_count": len(records),
        "history_file": str(history_file),
        "records": records
    }


def undo_rename_local_folder(folder_or_history_path: str | Path) -> Dict[str, Any]:
    """
    Mengembalikan nama file ke semula berdasarkan file rename_history.json.
    """
    target = Path(folder_or_history_path).resolve()
    if target.is_dir():
        history_file = target / "rename_history.json"
    else:
        history_file = target
        
    if not history_file.exists():
        raise FileNotFoundError(f"File riwayat rename_history.json tidak ditemukan di '{history_file}'.")
        
    with open(history_file, "r", encoding="utf-8") as f:
        history_data = json.load(f)
        
    records = history_data.get("records", [])
    restored_count = 0
    
    # Reverse records and rename back
    for rec in reversed(records):
        cur_path = Path(rec["new_path"])
        orig_path = Path(rec["old_path"])
        if cur_path.exists():
            cur_path.rename(orig_path)
            restored_count += 1
            
    # Hapus history file setelah berhasil undo
    try:
        history_file.unlink()
    except Exception:
        pass
        
    return {
        "success": True,
        "restored_count": restored_count,
        "total_records": len(records)
    }
