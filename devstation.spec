# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for DevStation
# Build: pyinstaller devstation.spec --noconfirm

import os
from pathlib import Path

block_cipher = None

# ── Locate Python's DLLs and TCL/TK data dirs ────────────────────────────────
import sys
_py_dir  = Path(sys.executable).parent
_dll_dir = _py_dir / "DLLs"
_tcl_dir = _py_dir / "tcl"

a = Analysis(
    ["theikdi_maung.py"],
    pathex=[],
    binaries=[
        # Core tkinter C extension
        (str(_dll_dir / "_tkinter.pyd"), "."),
        # TCL/TK shared libraries
        (str(_dll_dir / "tcl86t.dll"),   "."),
        (str(_dll_dir / "tk86t.dll"),    "."),
    ],
    datas=[
        # TCL and TK script libraries (required at runtime)
        (str(_tcl_dir / "tcl8.6"), "tcl8.6"),
        (str(_tcl_dir / "tk8.6"),  "tk8.6"),
    ],
    hiddenimports=[
        "_tkinter",
        "tkinter",
        "tkinter.scrolledtext",
        "tkinter.messagebox",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name="DevStation",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # set True temporarily to see tracebacks if needed
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon="icons/devstation.ico",   # uncomment once an .ico is placed in icons/
)
