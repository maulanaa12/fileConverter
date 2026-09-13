"""
generate_icon.py
Menghasilkan icon aplikasi (.ico dan .png) untuk LocalPDF Studio
berdasarkan desain Noun Project PDF Icon #3179225.
"""
from PIL import Image, ImageDraw
from pathlib import Path
import urllib.request

def create_app_icon():
    base_dir = Path(__file__).resolve().parent.parent
    raw_noun_png = Path(__file__).resolve().parent / "raw_noun_icon.png"
    output_ico = base_dir / "static" / "app_icon.ico"
    output_png = base_dir / "static" / "app_icon.png"

    # Unduh aset jika belum ada
    if not raw_noun_png.exists():
        url = "https://static.thenounproject.com/png/pdf-icon-3179225-512.png"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp, open(raw_noun_png, "wb") as f:
            f.write(resp.read())

    # Buka gambar sumber
    src = Image.open(raw_noun_png).convert("RGBA")

    # Lapisi lembar kertas internal dengan warna putih agar terlihat jelas di berbagai tema/wallpaper desktop
    mask = Image.new("L", src.size, 0)
    for x in range(src.size[0]):
        for y in range(src.size[1]):
            if src.getpixel((x, y))[3] > 128:
                mask.putpixel((x, y), 255)

    paper_fill = Image.new("L", src.size, 0)
    ImageDraw.floodfill(paper_fill, (200, 200), 255)

    final_img = Image.new("RGBA", src.size, (0, 0, 0, 0))
    final_img.paste((255, 255, 255, 255), (0, 0), paper_fill)
    final_img.alpha_composite(src)

    # Simpan PNG resolusi tinggi (512x512)
    final_img.save(output_png, format="PNG")
    print(f"Icon PNG berhasil dibuat: {output_png}")

    # Simpan ICO multi-resolusi Windows
    icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    final_img.save(output_ico, format="ICO", sizes=icon_sizes)
    print(f"Icon ICO berhasil dibuat: {output_ico}")

if __name__ == "__main__":
    create_app_icon()
