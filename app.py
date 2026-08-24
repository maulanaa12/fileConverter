import io
import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from core.utils import (
    BASE_DIR, UPLOAD_DIR, OUTPUT_DIR,
    generate_task_id, get_task_dirs, cleanup_old_files,
    get_pdf_info, generate_pdf_thumbnail, format_bytes, natural_sort_key
)
from core.merger import merge_pdf_files
from core.image_converter import convert_images_to_pdf, convert_pdf_to_images
from core.renamer import (
    calculate_new_names, process_rename_uploaded,
    process_rename_local_folder, undo_rename_local_folder
)
from core.splitter import split_pdf, organize_pdf_pages
from core.compressor import compress_pdf


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Bersihkan file sampah saat startup
    cleanup_old_files(max_age_seconds=7200)
    yield


app = FastAPI(
    title="LocalPDF Studio",
    description="Aplikasi Web Lokal Pengolah PDF Serbaguna",
    version="1.0.0",
    lifespan=lifespan
)

# Mounting static files & templates
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def handle_custom_save(source_file: Path, custom_output_dir: Optional[str]) -> Optional[str]:
    """Menyimpan salinan file output ke folder kustom yang ditentukan pengguna jika ada."""
    if not custom_output_dir or not custom_output_dir.strip():
        return None
    try:
        import zipfile
        clean_dir = Path(custom_output_dir.strip('"\'')).resolve()
        clean_dir.mkdir(parents=True, exist_ok=True)
        dest_file = clean_dir / source_file.name
        shutil.copy2(source_file, dest_file)

        # Jika file adalah zip, ekstrak juga isi file PDF/gambarnya langsung ke folder tujuan
        if source_file.suffix.lower() == '.zip':
            try:
                with zipfile.ZipFile(source_file, 'r') as z:
                    z.extractall(clean_dir)
            except Exception:
                pass

        return str(dest_file)
    except Exception as e:
        print(f"Gagal menyimpan ke folder kustom '{custom_output_dir}': {e}")
        return None


# ==========================================
# PAGE ROUTES (UI)
# ==========================================

@app.get("/", response_class=HTMLResponse)
async def page_index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"active_tool": "index"})

@app.get("/tool/merge", response_class=HTMLResponse)
async def page_merge(request: Request):
    return templates.TemplateResponse(request=request, name="merge.html", context={"active_tool": "merge"})

@app.get("/tool/image-to-pdf", response_class=HTMLResponse)
async def page_image_to_pdf(request: Request):
    return templates.TemplateResponse(request=request, name="image_to_pdf.html", context={"active_tool": "image_to_pdf"})

@app.get("/tool/pdf-to-image", response_class=HTMLResponse)
async def page_pdf_to_image(request: Request):
    return templates.TemplateResponse(request=request, name="pdf_to_image.html", context={"active_tool": "pdf_to_image"})

@app.get("/tool/rename", response_class=HTMLResponse)
async def page_rename(request: Request):
    return templates.TemplateResponse(request=request, name="rename.html", context={"active_tool": "rename"})

@app.get("/tool/split", response_class=HTMLResponse)
async def page_split(request: Request):
    return templates.TemplateResponse(request=request, name="split.html", context={"active_tool": "split"})

@app.get("/tool/organize", response_class=HTMLResponse)
async def page_organize(request: Request):
    return templates.TemplateResponse(request=request, name="organize.html", context={"active_tool": "organize"})

@app.get("/tool/compress", response_class=HTMLResponse)
async def page_compress(request: Request):
    return templates.TemplateResponse(request=request, name="compress.html", context={"active_tool": "compress"})


# ==========================================
# PYDANTIC SCHEMAS FOR API
# ==========================================

class MergeItem(BaseModel):
    path: str
    rotation: int = 0
    pages: Optional[List[int]] = None

class MergeRequest(BaseModel):
    files: List[MergeItem]
    output_filename: str = "merged_document.pdf"
    auto_natural_sort: bool = False
    custom_output_dir: Optional[str] = None

class ImageToPdfRequest(BaseModel):
    images: List[Any] # List of str or dict {"path": "...", "rotation": 0}
    mode: str = "combine"
    paper_size: str = "fit"
    orientation: str = "auto"
    margin_size: str = "none"
    output_filename: str = "images_converted.pdf"
    group_size: int = 1
    custom_groups_str: Optional[str] = None
    naming_mode: str = "original"
    prefix: str = ""
    start_num: int = 1
    step: int = 1
    padding: int = 0
    suffix: str = ""
    custom_output_dir: Optional[str] = None

class PdfToImageRequest(BaseModel):
    pdf_path: str
    format: str = "jpg"
    dpi: int = 150
    pages: Optional[List[int]] = None
    custom_output_dir: Optional[str] = None

class RenamePreviewRequest(BaseModel):
    filenames: List[str]
    rule_options: Dict[str, Any]

class RenameUploadRequest(BaseModel):
    files: List[List[str]] # [[temp_path, original_name], ...]
    rule_options: Dict[str, Any]
    output_zip_name: str = "renamed_files.zip"
    custom_output_dir: Optional[str] = None

class RenameLocalRequest(BaseModel):
    folder_path: str
    rule_options: Dict[str, Any]

class UndoLocalRequest(BaseModel):
    folder_path: str

class SplitRequest(BaseModel):
    pdf_path: str
    mode: str = "ranges"
    ranges_str: str = ""
    selected_pages: Optional[List[int]] = None
    custom_output_dir: Optional[str] = None

class OrganizeRequest(BaseModel):
    pdf_path: str
    output_filename: str = "organized_document.pdf"
    operations: List[Dict[str, Any]]
    custom_output_dir: Optional[str] = None

class CompressRequest(BaseModel):
    pdf_path: str
    level: str = "medium"
    custom_output_dir: Optional[str] = None

class OpenFolderRequest(BaseModel):
    path: str


# ==========================================
# API ENDPOINTS
# ==========================================

@app.post("/api/upload")
async def api_upload(files: List[UploadFile] = File(...)):
    """Mengunggah satu atau beberapa file ke direktori task sementara."""
    task_id = generate_task_id()
    task_upload, _ = get_task_dirs(task_id)
    
    uploaded_info = []
    
    for file in files:
        safe_filename = Path(file.filename).name
        dest_path = task_upload / safe_filename
        
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        file_size = dest_path.stat().st_size
        item_info = {
            "id": f"{task_id}_{len(uploaded_info)}",
            "task_id": task_id,
            "filename": safe_filename,
            "temp_path": str(dest_path),
            "size_bytes": file_size,
            "size_formatted": format_bytes(file_size),
            "page_count": 1,
            "thumbnail_url": None
        }
        
        # Ekstrak info PDF & thumbnail jika file adalah PDF
        if safe_filename.lower().endswith(".pdf"):
            try:
                pdf_meta = get_pdf_info(dest_path)
                item_info["page_count"] = pdf_meta.get("page_count", 1)
                item_info["thumbnail_url"] = generate_pdf_thumbnail(dest_path, page_num=0)
            except Exception as e:
                print(f"Gagal memuat info PDF {safe_filename}: {e}")
                
        # Jika file adalah Gambar, generate base64 data uri untuk preview instan
        elif dest_path.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff'):
            try:
                import base64
                from PIL import Image as PILImage
                with PILImage.open(dest_path) as im:
                    # Create small thumbnail preview
                    thumb = im.copy()
                    thumb.thumbnail((400, 400))
                    thumb_buf = io.BytesIO()
                    if thumb.mode in ('RGBA', 'LA') or (thumb.mode == 'P' and 'transparency' in thumb.info):
                        thumb.save(thumb_buf, format="PNG")
                        mime = "image/png"
                    else:
                        rgb_thumb = thumb.convert("RGB")
                        rgb_thumb.save(thumb_buf, format="JPEG", quality=85)
                        mime = "image/jpeg"
                    b64 = base64.b64encode(thumb_buf.getvalue()).decode('utf-8')
                    item_info["thumbnail_url"] = f"data:{mime};base64,{b64}"
            except Exception as e:
                print(f"Gagal generate thumbnail gambar {safe_filename}: {e}")
                
        uploaded_info.append(item_info)
        
    return JSONResponse({
        "success": True,
        "task_id": task_id,
        "files": uploaded_info
    })


@app.post("/api/merge")
async def api_merge(req: MergeRequest):
    """Menggabungkan file-file PDF yang telah diunggah."""
    try:
        task_id = generate_task_id()
        _, task_output = get_task_dirs(task_id)
        
        safe_out_name = Path(req.output_filename).name
        if not safe_out_name.lower().endswith(".pdf"):
            safe_out_name += ".pdf"
            
        out_path = task_output / safe_out_name
        
        result = merge_pdf_files(
            [item.dict() for item in req.files],
            output_path=out_path,
            auto_natural_sort=req.auto_natural_sort
        )
        
        result["download_url"] = f"/api/download/{task_id}/{safe_out_name}"
        result["saved_to_folder"] = handle_custom_save(out_path, req.custom_output_dir)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=400)


@app.post("/api/image-to-pdf")
async def api_image_to_pdf(req: ImageToPdfRequest):
    """Mengonversi sekumpulan gambar menjadi PDF."""
    try:
        task_id = generate_task_id()
        _, task_output = get_task_dirs(task_id)
        
        safe_out_name = Path(req.output_filename).name
        out_path = task_output / safe_out_name
        
        result = convert_images_to_pdf(
            image_paths=req.images,
            output_path=out_path,
            mode=req.mode,
            paper_size=req.paper_size,
            orientation=req.orientation,
            margin_size=req.margin_size,
            group_size=req.group_size,
            custom_groups_str=req.custom_groups_str,
            naming_mode=req.naming_mode,
            prefix=req.prefix,
            start_num=req.start_num,
            step=req.step,
            padding=req.padding,
            suffix=req.suffix
        )
        
        actual_path = Path(result["output_path"])
        actual_name = actual_path.name
        result["download_url"] = f"/api/download/{task_id}/{actual_name}"
        result["saved_to_folder"] = handle_custom_save(actual_path, req.custom_output_dir)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=400)


@app.post("/api/pdf-to-image")
async def api_pdf_to_image(req: PdfToImageRequest):
    """Mengekstrak halaman PDF menjadi gambar JPG/PNG (ZIP)."""
    try:
        task_id = generate_task_id()
        _, task_output = get_task_dirs(task_id)
        
        out_name = f"{Path(req.pdf_path).stem}_images.zip"
        out_path = task_output / out_name
        
        result = convert_pdf_to_images(
            pdf_path=req.pdf_path,
            output_dir_or_zip=out_path,
            image_format=req.format,
            dpi=req.dpi,
            page_selection=req.pages
        )
        
        actual_path = Path(result["output_path"])
        actual_name = actual_path.name
        result["download_url"] = f"/api/download/{task_id}/{actual_name}"
        result["saved_to_folder"] = handle_custom_save(actual_path, req.custom_output_dir)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=400)


@app.post("/api/rename/preview")
async def api_rename_preview(req: RenamePreviewRequest):
    """Menghitung pratinjau live sebelum eksekusi rename."""
    try:
        previews = calculate_new_names(req.filenames, **req.rule_options)
        return JSONResponse({"success": True, "previews": previews})
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=400)


@app.post("/api/rename/process-upload")
async def api_rename_process_upload(req: RenameUploadRequest):
    """Memproses rename file yang diunggah dan menghasilkan ZIP."""
    try:
        task_id = generate_task_id()
        _, task_output = get_task_dirs(task_id)
        
        out_path = task_output / req.output_zip_name
        result = process_rename_uploaded(
            uploaded_files=[(item[0], item[1]) for item in req.files],
            rule_options=req.rule_options,
            output_zip_path=out_path
        )
        
        result["download_url"] = f"/api/download/{task_id}/{req.output_zip_name}"
        result["saved_to_folder"] = handle_custom_save(out_path, req.custom_output_dir)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=400)


@app.post("/api/rename/process-local")
async def api_rename_process_local(req: RenameLocalRequest):
    """Memproses rename langsung pada folder lokal komputer dengan pengamanan 2-pass & history JSON."""
    try:
        result = process_rename_local_folder(
            folder_path=req.folder_path,
            rule_options=req.rule_options
        )
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=400)


@app.post("/api/rename/undo-local")
async def api_rename_undo_local(req: UndoLocalRequest):
    """Membatalkan (Undo) rename terakhir pada folder lokal."""
    try:
        result = undo_rename_local_folder(req.folder_path)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=400)


@app.get("/api/local-file-preview")
async def api_local_file_preview(path: str, thumb: bool = False):
    """Menyajikan preview thumbnail cepat atau gambar resolusi penuh dari harddisk lokal."""
    try:
        p = Path(path.strip("'\"")).resolve()
        if not p.exists() or not p.is_file():
            raise HTTPException(status_code=404, detail="File tidak ditemukan")

        ext = p.suffix.lower()
        if ext in ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff'):
            if thumb:
                import io
                from PIL import Image as PILImage, ImageOps
                from fastapi.responses import Response
                with PILImage.open(p) as im:
                    im = ImageOps.exif_transpose(im)
                    im.thumbnail((400, 400))
                    buf = io.BytesIO()
                    if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):
                        im.save(buf, format="PNG")
                        media_type = "image/png"
                    else:
                        rgb_im = im.convert("RGB")
                        rgb_im.save(buf, format="JPEG", quality=80)
                        media_type = "image/jpeg"
                    return Response(content=buf.getvalue(), media_type=media_type)
            else:
                return FileResponse(p)
        elif ext == '.pdf':
            thumb_b64 = generate_pdf_thumbnail(p, page_num=0)
            if thumb_b64 and thumb_b64.startswith("data:image/png;base64,"):
                import base64
                from fastapi.responses import Response
                img_data = base64.b64decode(thumb_b64.split(",", 1)[1])
                return Response(content=img_data, media_type="image/png")
            return FileResponse(p)
        else:
            return FileResponse(p)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/browse-local-dir")
async def api_browse_local_dir(path: str):
    """Membaca daftar file dari path folder lokal komputer beserta url preview."""
    try:
        import urllib.parse
        target_dir = Path(path.strip("'\"")).resolve()
        if not target_dir.exists() or not target_dir.is_dir():
            return JSONResponse({"success": False, "message": f"Folder '{path}' tidak ditemukan."}, status_code=404)
            
        img_ext = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff')
        supported_ext = ('.pdf',) + img_ext
        
        files = []
        for f in target_dir.iterdir():
            if f.is_file() and f.suffix.lower() in supported_ext:
                is_img = f.suffix.lower() in img_ext
                encoded_path = urllib.parse.quote(str(f))
                files.append({
                    "name": f.name,
                    "path": str(f),
                    "is_image": is_img,
                    "size_bytes": f.stat().st_size,
                    "size_formatted": format_bytes(f.stat().st_size),
                    "thumb_url": f"/api/local-file-preview?path={encoded_path}&thumb=true",
                    "preview_url": f"/api/local-file-preview?path={encoded_path}"
                })
                
        files.sort(key=lambda x: natural_sort_key(x["name"]))
        
        return JSONResponse({
            "success": True,
            "folder": str(target_dir),
            "files": files
        })
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=400)


@app.post("/api/split")
async def api_split(req: SplitRequest):
    """Memisahkan PDF berdasarkan rentang atau menjadi satu per satu halaman."""
    try:
        task_id = generate_task_id()
        _, task_output = get_task_dirs(task_id)
        
        out_name = f"{Path(req.pdf_path).stem}_split"
        out_path = task_output / out_name
        
        result = split_pdf(
            pdf_path=req.pdf_path,
            output_path=out_path,
            mode=req.mode,
            ranges_str=req.ranges_str,
            selected_pages=req.selected_pages
        )
        
        actual_path = Path(result["output_path"])
        actual_name = actual_path.name
        result["download_url"] = f"/api/download/{task_id}/{actual_name}"
        result["saved_to_folder"] = handle_custom_save(actual_path, req.custom_output_dir)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=400)


@app.post("/api/organize")
async def api_organize(req: OrganizeRequest):
    """Menyusun ulang, memutar, atau menghapus halaman PDF."""
    try:
        task_id = generate_task_id()
        _, task_output = get_task_dirs(task_id)
        
        safe_out_name = Path(req.output_filename).name
        if not safe_out_name.lower().endswith(".pdf"):
            safe_out_name += ".pdf"
            
        out_path = task_output / safe_out_name
        
        result = organize_pdf_pages(
            pdf_path=req.pdf_path,
            output_path=out_path,
            page_operations=req.operations
        )
        
        result["download_url"] = f"/api/download/{task_id}/{safe_out_name}"
        result["saved_to_folder"] = handle_custom_save(out_path, req.custom_output_dir)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=400)


@app.post("/api/compress")
async def api_compress(req: CompressRequest):
    """Mengompres ukuran dokumen PDF."""
    try:
        task_id = generate_task_id()
        _, task_output = get_task_dirs(task_id)
        
        safe_out_name = f"{Path(req.pdf_path).stem}_compressed.pdf"
        out_path = task_output / safe_out_name
        
        result = compress_pdf(
            pdf_path=req.pdf_path,
            output_path=out_path,
            level=req.level
        )
        
        result["download_url"] = f"/api/download/{task_id}/{safe_out_name}"
        result["saved_to_folder"] = handle_custom_save(out_path, req.custom_output_dir)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=400)


@app.post("/api/open-folder")
async def api_open_folder(req: OpenFolderRequest):
    """Membuka folder lokal langsung di Windows File Explorer."""
    try:
        target_path = Path(req.path.strip('"\'')).resolve()
        folder_to_open = target_path.parent if target_path.is_file() else target_path
        
        if not folder_to_open.exists():
            return JSONResponse({"success": False, "message": f"Folder tidak ditemukan: {folder_to_open}"}, status_code=404)
            
        if os.name == 'nt':
            os.startfile(str(folder_to_open))
        else:
            subprocess.Popen(["xdg-open", str(folder_to_open)])
            
        return JSONResponse({"success": True, "opened_path": str(folder_to_open)})
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=400)


@app.get("/api/download/{task_id}/{filename}")
async def api_download(task_id: str, filename: str):
    """Mengunduh file output yang dihasilkan."""
    file_path = OUTPUT_DIR / task_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File yang diminta tidak ditemukan atau sudah kedaluwarsa.")
        
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream"
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "127.0.0.1")
    print("=" * 60)
    print("       LOCALPDF STUDIO - SERVER AKTIF")
    print(f"       Akses melalui browser di: http://{host}:{port}")
    print("=" * 60)
    uvicorn.run("app:app", host=host, port=port, reload=True)
