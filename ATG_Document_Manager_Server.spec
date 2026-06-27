# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['server_onefile.py'],
    pathex=[],
    binaries=[],
    datas=[('app\\templates', 'app\\templates'), ('app\\static', 'app\\static'), ('icon.ico', '.'), ('logo.png', '.')],
    hiddenimports=['passlib.handlers.bcrypt', 'pymysql', 'pystray', 'pystray._win32', 'uvicorn.lifespan.on', 'uvicorn.loops.auto', 'uvicorn.protocols.http.auto', 'uvicorn.protocols.websockets.auto'],
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
    name='ATG_Document_Manager_Server',
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
    icon=['icon.ico'],
)
