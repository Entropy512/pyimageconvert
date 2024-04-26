# -*- mode: python ; coding: utf-8 -*-

import platform
import os

pystack_a = Analysis(
    ['pystack.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=['./pyi_hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pystack_pyz = PYZ(pystack_a.pure)

pystack_exe = EXE(
    pystack_pyz,
    pystack_a.scripts,
    [],
    exclude_binaries=True,
    name='pystack',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)


libraw2dng_a = Analysis(
    ['libraw2dng.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['imagecodecs._cms', 'imagecodecs._imcd'],
    hookspath=['./pyi_hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
libraw2dng_pyz = PYZ(libraw2dng_a.pure)

libraw2dng_exe = EXE(
    libraw2dng_pyz,
    libraw2dng_a.scripts,
    [],
    exclude_binaries=True,
    name='libraw2dng',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

imagecodec2tif_a = Analysis(
    ['imagecodec2tif.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=['./pyi_hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
imagecodec2tif_pyz = PYZ(imagecodec2tif_a.pure)

imagecodec2tif_exe = EXE(
    imagecodec2tif_pyz,
    imagecodec2tif_a.scripts,
    [],
    exclude_binaries=True,
    name='imagecodec2tif',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    imagecodec2tif_exe,
    imagecodec2tif_a.binaries,
    imagecodec2tif_a.datas,
    pystack_exe,
    pystack_a.binaries,
    pystack_a.datas,
    libraw2dng_exe,
    libraw2dng_a.binaries,
    libraw2dng_a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='pyimageconvert',
)
