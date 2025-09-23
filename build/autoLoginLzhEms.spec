# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['..\\autoLogin.py'],
    pathex=[],
    binaries=[],
    datas=[('F:\\360Downloads\\BaiduNetdiskDownload\\WicToolDemo\\getBY_EMS_Data\\autoLoginLzhEms\\config.json', '.'), ('F:\\360Downloads\\BaiduNetdiskDownload\\WicToolDemo\\getBY_EMS_Data\\autoLoginLzhEms\\config.ini', '.'), ('F:\\360Downloads\\BaiduNetdiskDownload\\WicToolDemo\\getBY_EMS_Data\\autoLoginLzhEms\\email_config.json', '.'), ('F:\\360Downloads\\BaiduNetdiskDownload\\WicToolDemo\\getBY_EMS_Data\\autoLoginLzhEms\\readme.md', '.'), ('F:\\360Downloads\\BaiduNetdiskDownload\\WicToolDemo\\getBY_EMS_Data\\autoLoginLzhEms\\dataLog', 'dataLog'), ('F:\\360Downloads\\BaiduNetdiskDownload\\WicToolDemo\\getBY_EMS_Data\\autoLoginLzhEms\\downloaded_js', 'downloaded_js')],
    hiddenimports=['selenium', 'PIL', 'ddddocr', 'requests', 'PyQt5', 'PyQtWebEngine', 'webdriver_manager', 'websockets', 'aiohttp', 'pymysql', 'Crypto', 'websocket', 'psutil', 'tkinter'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy'],
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
    name='autoLoginLzhEms',
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
)
