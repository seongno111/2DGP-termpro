# -*-mode: python ; coding: utf-8 -*
import os
import pico2d

sdl2dll_path = os.getenv('PYSDL2_DLL_PATH')

a = Analysis(
    ['main.py'], # <====== 1. 메인소스파일을지정해야합니다.
    pathex=[],
    binaries=[(os.path.join(sdl2dll_path, '*.dll'), '.')],
    datas=[],
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
    name='mygame', # <====== 2. 생성될실행파일이름을지정해야합니다.
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,# <====== 3. 문제가발생했을때True 로해서확인.
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)