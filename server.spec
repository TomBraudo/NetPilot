# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['backend\\server.py'],
    pathex=['./backend'],
    binaries=[],
    datas=[],
    hiddenimports=['endpoints.health', 'endpoints.config', 'endpoints.api', 'endpoints.db', 'endpoints.wifi', 'endpoints.whitelist', 'endpoints.blacklist', 'utils.path_utils', 'utils.ssh_client', 'utils.logging_config', 'utils.config_manager', 'utils.response_helpers', 'utils.network_utils', 'utils.commands', 'utils.traffic_control_helpers', 'services.whitelist_service', 'services.blacklist_service', 'services.wifi_management', 'services.speed_test', 'services.router_scanner', 'services.reset_rules', 'services.network_service', 'services.network_scanner', 'services.mode_state_service', 'services.config_service', 'services.block_ip', 'services.bandwidth_mode', 'services.subnets_manager', 'db.schema_initializer', 'db.tinydb_client', 'db.device_repository', 'db.device_groups_repository', 'db.whitelist_management', 'db.blacklist_management'],
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
