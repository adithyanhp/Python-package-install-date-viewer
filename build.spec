# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for PyPackage Manager Pro
#
# Build with:  pyinstaller build.spec
# (build.bat / build.ps1 do this for you)

import customtkinter
from pathlib import Path

block_cipher = None

ctk_path = Path(customtkinter.__file__).parent

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        (str(ctk_path), 'customtkinter'),
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'PIL._tkinter_finder',
        'openpyxl',
        'reportlab',
        'reportlab.graphics.barcode',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PyPackageManagerPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icons/app.ico',
)
