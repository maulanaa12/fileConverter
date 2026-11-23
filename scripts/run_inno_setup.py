"""
run_inno_setup.py — Cari dan jalankan Inno Setup Compiler (ISCC.exe)
untuk menghasilkan installer dengan nomor versi pada nama file.
"""
import os
import subprocess
import shutil
import re
import sys
from pathlib import Path

def main():
    project_dir = Path(__file__).resolve().parent.parent
    installer_script = project_dir / 'installer' / 'installer.iss'
    version = re.search(r'^#define MyAppVersion "([^"]+)"', installer_script.read_text(encoding='utf-8'), re.MULTILINE).group(1)
    output_file = project_dir / 'installer' / 'output' / f'LocalPDF_Studio_Setup_{version}.exe'
    candidates = [
        r'C:\Users\azmi maulana\AppData\Local\Programs\Inno Setup 6\ISCC.exe',
        Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'Inno Setup 6' / 'ISCC.exe',
        Path(os.environ.get('ProgramFiles(x86)', '')) / 'Inno Setup 6' / 'ISCC.exe',
        Path(os.environ.get('ProgramFiles', '')) / 'Inno Setup 6' / 'ISCC.exe',
    ]
    iscc = None
    for c in candidates:
        p = Path(c)
        if p.exists():
            iscc = str(p)
            break

    if not iscc:
        iscc = shutil.which('ISCC.exe')

    if iscc:
        print(f'[INFO] Inno Setup ditemukan: {iscc}')
        print(f'[INFO] Mengompilasi {output_file.name}...')
        output_file.parent.mkdir(parents=True, exist_ok=True)
        res = subprocess.run([iscc, str(installer_script)], cwd=project_dir)
        if res.returncode == 0:
            print('')
            print('======================================================================')
            print(f'[SELESAI] Installer v{version} siap dibagikan!')
            print(f'File Setup: {output_file}')
            print('======================================================================')
        else:
            print(f'[PERINGATAN] Kompilasi installer gagal dengan kode exit {res.returncode}.')
        return res.returncode
    else:
        print('[CATATAN] Inno Setup 6 tidak ditemukan. Anda dapat menggunakan folder di dist/LocalPDFStudio/')
        return 1

if __name__ == '__main__':
    sys.exit(main())
