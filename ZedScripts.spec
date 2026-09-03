# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import copy_metadata

# pygls/lsprotocol read their own package metadata at runtime (importlib.metadata),
# so it must be copied explicitly or entry points fail when frozen.
datas = copy_metadata("pygls") + copy_metadata("lsprotocol") + [
    ("src/ZedScripts/locale/*.json", "ZedScripts/locale"),
]

a = Analysis(
    ["src/ZedScripts/main.py"],
    pathex=["src"],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="ZedScripts",
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
