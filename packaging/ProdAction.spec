# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


ROOT = Path(SPECPATH).parent


datas = [
    (str(ROOT / "packaging" / "runtime" / "app_settings.json"), "."),
    (str(ROOT / "packaging" / "runtime" / "projects_list.json"), "."),
    (str(ROOT / "tools" / "tool_catalog.csv"), "tools"),
    (str(ROOT / "tools" / "maestro_baselines" / "Pieza.xml"), "tools/maestro_baselines"),
    (str(ROOT / "tools" / "maestro_baselines" / "Pieza.epl"), "tools/maestro_baselines"),
    (str(ROOT / "tools" / "maestro_baselines" / "def.tlgx"), "tools/maestro_baselines"),
]


a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "cairocffi",
        "cairosvg",
        "cssselect2",
        "tinycss2",
        "vtk",
        "panda3d",
        "matplotlib",
        "pytest",
        "IPython",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ProdAction",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="ProdAction",
    contents_directory=".",
)
