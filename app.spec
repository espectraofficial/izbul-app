# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


APP_VERSION = Path('VERSION').read_text(encoding='utf-8').strip()


a = Analysis(
    ['ui/app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('VERSION', '.'),
        ('packaging/update_public_key.txt', '.'),
    ],
    hiddenimports=[],
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
    name='Izbul',
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
    icon=['icon.icns'],
)
app = BUNDLE(
    exe,
    name='Izbul.app',
    icon='icon.icns',
    bundle_identifier='com.umitegeguldez.izbul',
    info_plist={
        'CFBundleDisplayName': 'İzbul',
        'CFBundleName': 'İzbul',
        'CFBundleShortVersionString': APP_VERSION,
        'CFBundleVersion': APP_VERSION,
    },
)
