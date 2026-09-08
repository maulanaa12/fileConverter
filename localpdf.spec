# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

BASE_DIR = os.path.abspath(os.getcwd())

datas = [
    (os.path.join(BASE_DIR, 'templates'), 'templates'),
    (os.path.join(BASE_DIR, 'static'), 'static'),
    (os.path.join(BASE_DIR, 'core'), 'core'),
]

# Tambahkan data files otomatis dari dependensi utama
datas += collect_data_files('pymupdf')
datas += collect_data_files('pypdf')

hiddenimports = [
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.http.h11_impl',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespans',
    'uvicorn.lifespans.on',
    'uvicorn.lifespans.off',
    'fastapi',
    'fastapi.staticfiles',
    'fastapi.templating',
    'starlette',
    'starlette.routing',
    'starlette.middleware',
    'starlette.responses',
    'pydantic',
    'pymupdf',
    'fitz',
    'PIL',
    'PIL.Image',
    'pypdf',
    'jinja2',
    'multipart',
    'python_multipart',
    'clr_loader',
    'webview',
    'webview.platforms.winforms',
    'webview.platforms.edgechromium',
]

a = Analysis(
    ['desktop_app.py'],
    pathex=[BASE_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'pytest', 'IPython', 'torch', 'scipy', 'matplotlib'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LocalPDFStudio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(BASE_DIR, 'static', 'app_icon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LocalPDFStudio',
)
