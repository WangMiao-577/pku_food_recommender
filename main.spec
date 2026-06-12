# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec - 北大食堂智能推荐
# 输出目录: dist/PKUFoodRecommender/

import os
from PyInstaller.utils.hooks import collect_submodules, collect_all

ROOT = os.path.abspath('.')

datas = [
    (os.path.join(ROOT, 'data'), 'data'),
    (os.path.join(ROOT, 'images'), 'images'),
    (os.path.join(ROOT, 'pku_map', 'pku_nodes.csv'), 'pku_map'),
    (os.path.join(ROOT, 'pku_map', 'pku_campus_map_hd.png'), 'pku_map'),
    (os.path.join(ROOT, 'pku_map', 'pku_map_mapper.py'), 'pku_map'),
    (os.path.join(ROOT, 'pku_map', '__init__.py'), 'pku_map'),
    (os.path.join(ROOT, 'my_logo.ico'), '.'),
]

# PIL(Pillow): 地图渲染需要 Image / ImageDraw / ImageFont 等完整子模块
pillow_datas, pillow_binaries, pillow_hiddenimports = collect_all('PIL')
numpy_datas, numpy_binaries, numpy_hiddenimports = collect_all('numpy')

hiddenimports = (
    collect_submodules('backend')
    + collect_submodules('frontend')
    + pillow_hiddenimports
    + numpy_hiddenimports
    + [
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'requests',
    ]
)

a = Analysis(
    ['main.py'],
    pathex=[ROOT],
    binaries=pillow_binaries + numpy_binaries,
    datas=datas + pillow_datas + numpy_datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name='PKUFoodRecommender',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[os.path.join(ROOT, 'my_logo.ico')],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PKUFoodRecommender',
)
