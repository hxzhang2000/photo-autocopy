# -*- mode: python ; coding: utf-8 -*-

import sys
import os

# 添加项目根目录到 pathex
root_dir = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    ['photo_autocopy.py'],
    pathex=[root_dir],
    binaries=[],
    datas=[],
    hiddenimports=['core', 'core.config', 'core.exif', 'core.organizer'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PhotoAutocopy',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
