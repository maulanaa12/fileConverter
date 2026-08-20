import os
import sys
import re
import argparse
from pathlib import Path
from PIL import Image, ImageOps


def natural_sort_key(s):
    """Kunci pengurutan alami (natural sort) agar IMG-2.jpg sebelum IMG-10.jpg."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(s))]


def get_image_files(folder_path):
    """Mengambil semua file gambar yang didukung dari folder sumber."""
    supported_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif')
    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        return []
    
    files = [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in supported_extensions]
    files.sort(key=lambda f: natural_sort_key(f.name))
    return files


def convert_image_to_pdf(image_path, output_pdf_path):
    """Mengonversi satu gambar menjadi satu file PDF dengan orientasi EXIF yang tepat."""
    try:
        with Image.open(image_path) as img:
            # Memperbaiki orientasi berdasarkan metadata EXIF
            img = ImageOps.exif_transpose(img)
            
            # Jika gambar memiliki transparansi (RGBA/LA/P), jadikan background putih
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                rgb_img.paste(img, mask=img.split()[3])
                rgb_img.save(output_pdf_path, 'PDF', resolution=100.0)
            else:
                img = img.convert('RGB')
                img.save(output_pdf_path, 'PDF', resolution=100.0)
        return True, None
    except Exception as e:
        return False, str(e)


def main():
    print("=" * 60)
    print("      PROGRAM KONVERSI GAMBAR (JPG/PNG) KE PDF")
    print("=" * 60)

    parser = argparse.ArgumentParser(description="Konversi gambar ke PDF dengan penomoran urut.")
    parser.add_argument("--input", "-i", help="Folder sumber gambar (contoh: ./jpg)")
    parser.add_argument("--output", "-o", help="Folder tujuan hasil PDF (contoh: ./file)")
    parser.add_argument("--start", "-s", type=int, help="Nomor awal penamaan file")
    parser.add_argument("--prefix", "-p", default="", help="Awalan nama file (opsional)")
    parser.add_argument("--pad", type=int, default=0, help="Jumlah digit padding (contoh: 3 untuk 001, 002)")

    args = parser.parse_args()

    # --- 1. Input Folder Sumber ---
    if args.input:
        input_folder = args.input.strip()
    else:
        default_input = "jpg" if os.path.exists("jpg") else "."
        input_prompt = input(f"1. Masukkan folder sumber gambar [Default: {default_input}]: ").strip()
        input_folder = input_prompt if input_prompt else default_input

    input_path = Path(input_folder).resolve()
    if not input_path.exists() or not input_path.is_dir():
        print(f"\n[ERROR] Folder '{input_folder}' tidak ditemukan!")
        input("\nTekan Enter untuk keluar...")
        sys.exit(1)

    image_files = get_image_files(input_path)
    if not image_files:
        print(f"\n[ERROR] Tidak ditemukan file gambar (.jpg, .jpeg, .png, dll) di folder '{input_path}'!")
        input("\nTekan Enter untuk keluar...")
        sys.exit(1)

    print(f"\n-> Ditemukan {len(image_files)} file gambar di folder sumber.")

    # --- 2. Input Folder Tujuan ---
    if args.output:
        output_folder = args.output.strip()
    else:
        default_output = "file"
        output_prompt = input(f"2. Masukkan folder tujuan hasil PDF [Default: {default_output}]: ").strip()
        output_folder = output_prompt if output_prompt else default_output

    output_path = Path(output_folder).resolve()
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"-> Folder tujuan: {output_path}")

    # --- 3. Input Nomor Mulai ---
    if args.start is not None:
        start_num = args.start
    else:
        while True:
            start_prompt = input("3. Penamaan file PDF dimulai dari nomor berapa? [Default: 1]: ").strip()
            if not start_prompt:
                start_num = 1
                break
            if start_prompt.isdigit():
                start_num = int(start_prompt)
                break
            print("[PERINGATAN] Harap masukkan angka yang valid!")

    # --- 4. Format Penamaan Tambahan (Opsional) ---
    prefix = args.prefix
    padding = args.pad

    if args.start is None and not args.prefix and args.pad == 0:
        print("\n4. Pilih gaya format nama file:")
        print(f"   [1] Angka langsung (contoh: {start_num}.pdf, {start_num+1}.pdf, ...)")
        print(f"   [2] Tiga digit / Padding nol (contoh: {start_num:03d}.pdf, {start_num+1:03d}.pdf, ...)")
        print("   [3] Kustom dengan awalan teks (contoh: doc_1.pdf)")
        
        pilihan_format = input("   Pilihan [1/2/3, Default: 1]: ").strip()
        if pilihan_format == "2":
            padding = 3
        elif pilihan_format == "3":
            prefix = input("   Masukkan awalan teks (prefix): ").strip()

    # Konfirmasi sebelum proses
    sample_first = f"{prefix}{start_num:0{padding}d}.pdf" if padding > 0 else f"{prefix}{start_num}.pdf"
    last_num = start_num + len(image_files) - 1
    sample_last = f"{prefix}{last_num:0{padding}d}.pdf" if padding > 0 else f"{prefix}{last_num}.pdf"

    print("\n" + "-" * 60)
    print("RINGKASAN KONVERSI:")
    print(f"- Total File      : {len(image_files)} gambar")
    print(f"- Folder Sumber   : {input_path}")
    print(f"- Folder Hasil    : {output_path}")
    print(f"- Penamaan        : {sample_first} s/d {sample_last}")
    print("-" * 60)

    if args.start is None:
        konfirmasi = input("Lanjutkan proses konversi? (Y/n): ").strip().lower()
        if konfirmasi in ('n', 'no', 'tidak'):
            print("Konversi dibatalkan.")
            sys.exit(0)

    print("\nMemulai proses konversi...\n")
    success_count = 0
    fail_count = 0

    for idx, img_file in enumerate(image_files):
        current_num = start_num + idx
        if padding > 0:
            pdf_name = f"{prefix}{current_num:0{padding}d}.pdf"
        else:
            pdf_name = f"{prefix}{current_num}.pdf"

        target_pdf_path = output_path / pdf_name
        success, err = convert_image_to_pdf(img_file, target_pdf_path)

        persen = int(((idx + 1) / len(image_files)) * 100)
        bar_length = 30
        filled_length = int(bar_length * (idx + 1) // len(image_files))
        bar = '=' * filled_length + '-' * (bar_length - filled_length)

        if success:
            success_count += 1
            status_text = f"[{idx+1}/{len(image_files)}] [{bar}] {persen}% -> {img_file.name} ==> {pdf_name}"
            print(status_text)
        else:
            fail_count += 1
            print(f"[{idx+1}/{len(image_files)}] [GAGAL] {img_file.name}: {err}")

    print("\n" + "=" * 60)
    print("PROSES SELESAI!")
    print(f"- Berhasil dikonversi : {success_count} file")
    if fail_count > 0:
        print(f"- Gagal dikonversi    : {fail_count} file")
    print(f"- Lokasi file PDF     : {output_path}")
    print("=" * 60)

    if args.start is None:
        input("\nTekan Enter untuk menutup...")


if __name__ == "__main__":
    main()
