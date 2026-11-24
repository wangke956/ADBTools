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


def is_dir_writable(dir_path: str) -> tuple:
    """显式测试目录是否可写（不能仅依赖 makedirs(exist_ok=True)：目录已存在时不会报错）

    通过创建+删除探针文件的方式验证。安装到 Program Files 等 UAC 保护目录时，
    Users 组通常只有 ReadAndExecute 权限，此时探针会失败。

    Returns:
        (ok: bool, reason: str) —— ok=True 时可写；ok=False 时 reason 描述失败原因
    """
    if not dir_path:
        return False, "empty path"
    try:
        if not os.path.isdir(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
            except Exception as e:
                return False, f"makedirs failed: {type(e).__name__}: {e}"
        probe = os.path.join(dir_path, f".adbtools_probe_{os.getpid()}")
        try:
            with open(probe, 'w', encoding='utf-8') as f:
                f.write('probe')
            return True, "ok"
        except Exception as e:
            return False, f"write probe failed: {type(e).__name__}: {e}"
        finally:
            try:
                if os.path.exists(probe):
                    os.remove(probe)
            except Exception:
                pass
    except Exception as e:
        return False, f"unexpected: {type(e).__name__}: {e}"


def get_fallback_log_dirs() -> list:
    """当安装目录 logs 不可写时，按优先级返回候选兜底目录

    顺序：%LOCALAPPDATA%\\ADBTools\\logs → %APPDATA%\\ADBTools\\logs → %TEMP%\\ADBTools\\logs
    （仅在安装目录不可写的异常场景使用；正常场景日志仍统一存安装目录）
    """
    candidates = []
    for env_key in ('LOCALAPPDATA', 'APPDATA', 'TEMP', 'TMP'):
        base = os.environ.get(env_key)
        if base:
            candidates.append(os.path.join(base, 'ADBTools', 'logs'))
    # 去重（TEMP/TMP 常指向同一目录）
    seen = set()
    unique = []
    for c in candidates:
        norm = os.path.normcase(os.path.abspath(c))
        if norm not in seen:
            seen.add(norm)
            unique.append(c)
    return unique


def find_resource(filename: str) -> str:
    """查找随包分发的资源文件（UI文件等），返回第一个存在的完整路径

    搜索顺序：
    1. 运行时目录（onefile 模式下资源随包解压到临时目录）
    2. 真实安装目录（standalone 模式 / 安装器额外复制的文件）
    3. 当前工作目录（开发环境即项目根目录）
    找不到时返回安装目录下的拼接路径（由调用方报错）
    """
    candidates = []

    # PyInstaller 打包环境
    if getattr(sys, 'frozen', False):
        candidates.append(os.path.dirname(os.path.abspath(sys.executable)))

    # Nuitka 运行时目录（onefile 模式下资源解压到 sys.executable 所在的临时目录）
    try:
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        if exe_dir and exe_dir not in candidates:
            candidates.append(exe_dir)
    except Exception:
        pass

    # Nuitka __nuitka_binary_dir（编译模块中可用，指向二进制/资源所在目录）
    try:
        nuitka_dir = globals().get("__nuitka_binary_dir")
        if nuitka_dir:
            abs_nuitka = os.path.abspath(str(nuitka_dir))
            if abs_nuitka not in candidates:
                candidates.append(abs_nuitka)
    except Exception:
        pass

    # 真实安装目录（standalone / 开发环境为项目根目录）
    app_dir = get_app_dir()
    if app_dir not in candidates:
        candidates.append(app_dir)

    # 当前工作目录
    cwd = os.getcwd()
    if cwd not in candidates:
        candidates.append(cwd)

    for base in candidates:
        path = os.path.join(base, filename)
        if os.path.isfile(path):
            return path

    return os.path.join(app_dir, filename)