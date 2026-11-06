#!/usr/bin/env python3
"""
应用路径工具 - 统一获取程序真实所在目录（安装目录）

背景：
Nuitka onefile 模式下 exe 是自解压程序，运行时会解压到 %TEMP%\\onefile_xxx，
此时 sys.executable / __file__ / __nuitka_binary_dir 都指向临时解压目录
（程序退出即被删除），不能用于定位日志、配置等需要持久化的文件。

获取原始 exe 目录的可靠来源（按优先级）：
1. __compiled__.containing_dir —— Nuitka 官方推荐，onefile/standalone 通用
2. NUITKA_ONEFILE_BINARY 环境变量 —— onefile 引导程序注入的原始 exe 路径
3. sys.argv[0] —— onefile 模式下保留原始 exe 的绝对路径（官方文档说明）
"""

import os
import sys


def _is_onefile_temp_dir(path) -> bool:
    """判断是否为 Nuitka onefile 临时解压目录（退出即删除，不可用于持久化数据）"""
    try:
        import tempfile
        norm = os.path.normcase(os.path.abspath(str(path)))
        temp_root = os.path.normcase(os.path.abspath(tempfile.gettempdir()))
        return norm.startswith(temp_root + os.sep) and "onefile_" in norm
    except Exception:
        return False


def get_app_dir() -> str:
    """获取程序真实所在目录（打包后为安装目录，开发时为项目根目录）"""
    # 1. Nuitka 官方推荐：__compiled__.containing_dir 指向原始 exe 目录
    compiled = globals().get("__compiled__")
    containing_dir = getattr(compiled, "containing_dir", None)
    if containing_dir and not _is_onefile_temp_dir(containing_dir):
        return os.path.abspath(str(containing_dir))

    # 2. onefile 引导程序注入的环境变量：原始 exe 完整路径
    onefile_binary = os.environ.get("NUITKA_ONEFILE_BINARY")
    if onefile_binary:
        candidate = os.path.dirname(os.path.abspath(onefile_binary))
        if not _is_onefile_temp_dir(candidate):
            return candidate

    # 3. onefile 模式下 sys.argv[0] 保留原始 exe 的绝对路径
    try:
        argv0 = sys.argv[0]
        if argv0 and os.path.isabs(argv0) and os.path.isfile(argv0):
            candidate = os.path.dirname(os.path.abspath(argv0))
            if not _is_onefile_temp_dir(candidate):
                return candidate
    except Exception:
        pass

    # 4. __nuitka_binary_dir（onefile 下可能指向临时解压目录，需过滤）
    binary_dir = globals().get("__nuitka_binary_dir")
    if binary_dir and not _is_onefile_temp_dir(binary_dir):
        return os.path.abspath(str(binary_dir))

    # 5. PyInstaller 等其他打包方式：exe 所在目录即安装目录
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))

    # 6. 开发环境：本文件所在目录（项目根目录）
    return os.path.dirname(os.path.abspath(__file__))


def is_frozen() -> bool:
    """是否为打包运行状态"""
    return bool(globals().get("__nuitka_binary_dir")) or getattr(sys, 'frozen', False)


def find_resource(filename: str) -> str:
    """查找随包分发的资源文件（UI文件等），返回第一个存在的完整路径

    搜索顺序：
    1. 运行时目录（onefile 模式下资源随包解压到临时目录）
    2. 真实安装目录（standalone 模式 / 安装器额外复制的文件）
    3. 当前工作目录（开发环境即项目根目录）
    找不到时返回安装目录下的拼接路径（由调用方报错）
    """
    candidates = []
    if getattr(sys, 'frozen', False):
        candidates.append(os.path.dirname(os.path.abspath(sys.executable)))
    candidates.append(get_app_dir())
    candidates.append(os.getcwd())

    for base in candidates:
        path = os.path.join(base, filename)
        if os.path.isfile(path):
            return path

    return os.path.join(get_app_dir(), filename)