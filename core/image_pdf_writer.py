from pathlib import Path
from collections.abc import Callable, Iterable

from PIL import Image
import pymupdf as fitz


# Incremental saves compare the existing file; larger bounded batches avoid excess disk reads.
CHECKPOINT_PAGES = 64
CHECKPOINT_BYTES = 256 * 1024 * 1024


def write_image_pdf(
    items: Iterable[tuple[Path, int]],
    destination: Path,
    scratch_dir: Path,
    page_size: tuple[int, int] | None,
    orientation: str,
    margin: int,
    prepare_image: Callable[[Path], Image.Image],
) -> None:
    """Write bounded batches to disk; reopening releases accumulated image streams."""
    destination = Path(destination)
    doc = fitz.open()
    saved = False
    pending_pages = pending_bytes = total = 0

    def checkpoint():
        nonlocal doc, saved, pending_pages, pending_bytes
        if saved:
            if not doc.can_save_incrementally():
                raise RuntimeError('PDF sementara tidak dapat dilanjutkan secara incremental.')
            doc.save(str(destination), incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP,
                     deflate=True)
        else:
            doc.save(str(destination), deflate=True)
            saved = True
        doc.close()
        fitz.TOOLS.store_shrink(100)
        doc = fitz.open(str(destination))
        if doc.is_repaired:
            raise RuntimeError('PDF sementara rusak saat dibuka kembali.')
        pending_pages = pending_bytes = 0

    try:
        for path, rotation in items:
            with Image.open(path) as source:
                width, height = source.size
                exif_orientation = source.getexif().get(274, 1)
                direct = (source.format == 'JPEG' and source.mode in ('RGB', 'L')
                          and exif_orientation in (1, 3, 6, 8) and rotation % 90 == 0)
            if direct:
                clockwise = ({1: 0, 3: 180, 6: 90, 8: 270}[exif_orientation] + rotation) % 360
                if clockwise in (90, 270):
                    width, height = height, width
                image_path = path
                pdf_rotation = (-clockwise) % 360
                estimated_bytes = path.stat().st_size
            else:
                # Account for decoded pixels, including the expanded canvas of free rotations.
                estimated_bytes = 3 * (width + height) ** 2 if rotation % 90 else width * height * 3
                pdf_rotation = 0
                image_path = Path(scratch_dir) / 'page.png'

            if pending_pages and (pending_pages >= CHECKPOINT_PAGES
                                  or pending_bytes + estimated_bytes > CHECKPOINT_BYTES):
                checkpoint()

            if not direct:
                with prepare_image(path) as img:
                    if rotation:
                        with img.rotate(-rotation, expand=True) as rotated:
                            width, height = rotated.size
                            rotated.save(image_path, format='PNG')
                    else:
                        width, height = img.size
                        img.save(image_path, format='PNG')

            if page_size is None:
                page_width, page_height = width * 0.72 + 2 * margin, height * 0.72 + 2 * margin
            else:
                landscape = orientation == 'landscape' or (orientation not in ('landscape', 'portrait')
                                                           and width > height)
                short, long = sorted(page_size)
                page_width, page_height = (long, short) if landscape else (short, long)

            page = doc.new_page(width=page_width, height=page_height)
            rect = fitz.Rect(margin, margin, page_width - margin, page_height - margin)
            page.insert_image(rect, filename=str(image_path), rotate=pdf_rotation,
                              keep_proportion=True)
            page = None
            if not direct:
                image_path.unlink()
            pending_pages += 1
            pending_bytes += estimated_bytes
            total += 1

        if pending_pages:
            checkpoint()
        if doc.page_count != total or total == 0:
            raise RuntimeError('Jumlah halaman PDF tidak sesuai dengan gambar sumber.')
    finally:
        if not doc.is_closed:
            doc.close()
        fitz.TOOLS.store_shrink(100)
