# -*- mode: python ; coding: utf-8 -*-

# 最小体积打包配置
# 使用: pyinstaller ADBTools_minimal_fixed.spec

import os

# 使用原始字符串避免转义问题
u2_jar_path = r'.venv\Lib\site-packages\uiautomator2\assets\u2.jar'
adb_exe_path = r'D:\work_tools\adb-1\adb.exe'
adb_api_dll_path = r'D:\work_tools\adb-1\AdbWinApi.dll'
adb_usb_dll_path = r'D:\work_tools\adb-1\AdbWinUsbApi.dll'

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('adbtool.ui', '.'), 
        (u2_jar_path, 'uiautomator2\\assets'), 
        (adb_exe_path, '.'), 
        (adb_api_dll_path, '.'), 
        (adb_usb_dll_path, '.')
    ],
    hiddenimports=[
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtWidgets', 
        'PyQt5.QtGui',
        'qdarkstyle',
        'uiautomator2',
        'openpyxl',
        'configparser',
        # 移除pandas以减小体积，如果确实需要再添加
        # 'pandas',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不必要的模块以减小体积
        'matplotlib',      # 绘图库，通常不需要
        'scipy',           # 科学计算，通常不需要
        'numpy',           # 数值计算，如果不需要可以排除
        'pandas',          # 数据处理，如果不需要可以排除
        'IPython',         # 交互式Python，不需要
        'jedi',            # 代码补全，不需要
        'pygments',        # 语法高亮，不需要
        'sqlalchemy',      # 数据库ORM，不需要
        'sqlite3',         # 数据库，如果不需要可以排除
        'test',            # 测试模块
        'unittest',        # 单元测试
        'pkg_resources',   # 包资源，但可能需要保留
    ],
    noarchive=False,
    optimize=2,  # 优化级别2，进行更多优化
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ADBTools_minimal',
    debug=False,  # 关闭调试信息
    bootloader_ignore_signals=False,
    strip=True,   # 剥离符号信息
    upx=True,     # 使用UPX压缩
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