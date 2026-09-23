"""
run_inno_setup.py — Cari dan jalankan Inno Setup Compiler (ISCC.exe)
untuk menghasilkan installer tunggal LocalPDF_Studio_Setup.exe.
"""
import os
import subprocess
import shutil
from pathlib import Path

def main():
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
        print('[INFO] Mengompilasi installer tunggal LocalPDF_Studio_Setup.exe...')
        os.makedirs('installer/output', exist_ok=True)
        res = subprocess.run([iscc, 'installer/installer.iss'])
        if res.returncode == 0:
            print('')
            print('======================================================================')
            print('[SELESAI] Installer v1.2.1 siap dibagikan!')
            print(f'File Setup: {Path.cwd() / "installer" / "output" / "LocalPDF_Studio_Setup.exe"}')
            print('======================================================================')
        else:
            print(f'[PERINGATAN] Kompilasi installer gagal dengan kode exit {res.returncode}.')
    else:
        print('[CATATAN] Inno Setup 6 tidak ditemukan. Anda dapat menggunakan folder di dist/LocalPDFStudio/')

if __name__ == '__main__':
    main()
