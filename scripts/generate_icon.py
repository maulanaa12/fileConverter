"""
generate_icon.py
Menghasilkan icon aplikasi (.ico dan .png) dengan desain profesional untuk LocalPDF Studio.
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

def create_app_icon():
    base_dir = Path(__file__).resolve().parent.parent
    output_ico = base_dir / "static" / "app_icon.ico"
    output_png = base_dir / "static" / "app_icon.png"

    # Buat kanvas resolusi tinggi 512x512
    size = (512, 512)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background rounded rect (Gradien warna Indigo ke Violet)
    # Gambar sudut membulat dengan padding
    padding = 24
    corner_radius = 88
    
    # Base rounded rectangle background
    draw.rounded_rectangle(
        [padding, padding, size[0] - padding, size[1] - padding],
        radius=corner_radius,
        fill=(79, 70, 229, 255) # Indigo 600
    )

    # Accent shadow / secondary badge
    draw.rounded_rectangle(
        [padding + 8, padding + 8, size[0] - padding - 8, size[1] - padding - 8],
        radius=corner_radius - 6,
        outline=(129, 140, 248, 160), # Indigo 400
        width=6
    )

    # Gambar lambang dokumen lipat (Document sheet icon)
    doc_x0, doc_y0 = 130, 95
    doc_x1, doc_y1 = 382, 417
    fold_size = 70

    # Poligon lembar kertas putih
    paper_points = [
        (doc_x0, doc_y0),
        (doc_x1 - fold_size, doc_y0),
        (doc_x1, doc_y0 + fold_size),
        (doc_x1, doc_y1),
        (doc_x0, doc_y1)
    ]
    draw.polygon(paper_points, fill=(255, 255, 255, 250))

    # Lipatan sudut kertas (Fold triangle)
    fold_points = [
        (doc_x1 - fold_size, doc_y0),
        (doc_x1 - fold_size, doc_y0 + fold_size),
        (doc_x1, doc_y0 + fold_size)
    ]
    draw.polygon(fold_points, fill=(224, 231, 255, 255))
    draw.line([(doc_x1 - fold_size, doc_y0), (doc_x1 - fold_size, doc_y0 + fold_size), (doc_x1, doc_y0 + fold_size)], fill=(165, 180, 252, 255), width=3)

    # Garis-garis isi dokumen (baris teks simbolik)
    draw.rounded_rectangle([170, 180, 310, 198], radius=8, fill=(199, 210, 254, 255))
    draw.rounded_rectangle([170, 220, 340, 238], radius=8, fill=(199, 210, 254, 255))
    draw.rounded_rectangle([170, 260, 290, 278], radius=8, fill=(199, 210, 254, 255))

    # Badge merah bertuliskan PDF di bagian bawah dokumen
    draw.rounded_rectangle([150, 320, 362, 395], radius=16, fill=(239, 68, 68, 255)) # Red 500
    
    # Teks "PDF" di dalam badge
    try:
        font = ImageFont.truetype("arialbd.ttf", 46)
    except Exception:
        font = ImageFont.load_default()

    # Center text
    text = "PDF"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    text_x = 150 + (212 - text_w) / 2
    text_y = 320 + (75 - text_h) / 2 - 4
    draw.text((text_x, text_y), text, fill=(255, 255, 255, 255), font=font)

    # Simpan sebagai PNG resolusi tinggi
    img.save(output_png, format="PNG")
    print(f"Icon PNG berhasil dibuat: {output_png}")

    # Simpan sebagai ICO multi-resolusi (16, 24, 32, 48, 64, 128, 256)
    icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(output_ico, format="ICO", sizes=icon_sizes)
    print(f"Icon ICO berhasil dibuat: {output_ico}")

if __name__ == "__main__":
    create_app_icon()
