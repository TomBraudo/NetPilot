# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['backend\\server.py'],
    pathex=['backend', 'backend/venv/Lib/site-packages'],
    binaries=[],
    datas=[],
    hiddenimports=['flask', 'flask.helpers', 'flask.app', 'flask.json', 'flask_cors', 'flask_cors.decorator', 'tinydb', 'paramiko', 'netifaces', 'scapy', 'requests', 'bcrypt', 'python-dotenv', 'endpoints.health', 'endpoints.config', 'endpoints.api', 'endpoints.db', 'endpoints.wifi', 'endpoints.whitelist'],
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
    name='server',
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
