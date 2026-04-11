#!/usr/bin/env python3
"""
Nuitka 兼容性模块 - 解决 Nuitka 打包后 uiautomator2 和 adbutils 的资源读取问题

问题根源：
- Nuitka 打包后，importlib.resources.files() 返回的是 nuitka_resource_reader_files 对象
- 这个对象在传给 shutil.copy() 或 open() 时会失败
- 错误信息: "Invalid src type: <class 'nuitka_resource_reader_files'>"

解决方案：
1. 直接 Monkey-patch uiautomator2.utils.with_package_resource 函数
2. Monkey-patch importlib.resources.files 和 as_file
3. Monkey-patch shutil.copy 和 shutil.copy2

使用方法：
在任何使用 uiautomator2 或 adbutils 的模块开头添加：
    from nuitka_compat import ensure_nuitka_compatibility
    ensure_nuitka_compatibility()
"""

import sys
import os
import contextlib
from pathlib import Path

# 检查是否在 Nuitka 环境中运行
def _is_nuitka_environment():
    """检测是否在 Nuitka 编译环境中运行"""
    # 方法1: 检查 __compiled__ 标记 (Nuitka 在编译的模块中设置此变量)
    if "__compiled__" in globals():
        return True
    # 方法2: 检查主模块是否被编译
    main_mod = sys.modules.get("__main__")
    if main_mod and hasattr(main_mod, "__compiled__"):
        return True
    # 方法3: sys.frozen=True 且没有 _MEIPASS (排除 PyInstaller)
    if getattr(sys, 'frozen', False) and not hasattr(sys, '_MEIPASS'):
        return True
    return False

IS_NUITKA = _is_nuitka_environment()

# 全局状态
_NUITKA_COMPAT_INITIALIZED = False
_NUITKA_U2_ASSETS_DIR = None
_NUITKA_ADBUTILS_BINARIES_DIR = None


def _get_logger():
    """延迟导入 logger，避免循环导入"""
    try:
        from logger_manager import get_logger
        return get_logger("ADBTools.NuitkaCompat")
    except ImportError:
        import logging
        logger = logging.getLogger("ADBTools.NuitkaCompat")
        logger.setLevel(logging.DEBUG)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
        return logger


def _extract_nuitka_u2_resources():
    """
    从 Nuitka 嵌入的资源中提取 u2 assets 到临时目录
    Nuitka 的 nuitka_resource_reader_files 对象支持 read_bytes()，
    但无法直接传给 shutil.copy() 或 as_file()，所以需要手动提取到磁盘
    """
    logger = _get_logger()
    try:
        import importlib.resources as resources
        
        # 处理 Python < 3.9 (importlib.resources 没有 files 属性)
        if not hasattr(resources, 'files'):
            try:
                import importlib_resources as resources
            except ImportError:
                logger.warning("Python < 3.9 且未安装 importlib_resources，无法使用 files() API")
                return None
                
        import tempfile

        # 使用原始的 files() 获取 Nuitka 资源引用
        u2_pkg = resources.files("uiautomator2")
        assets_ref = u2_pkg / "assets"

        # 尝试读取已知文件来验证资源可访问
        test_ref = assets_ref / "u2.jar"
        test_data = test_ref.read_bytes()

        if not test_data:
            return None

        # 资源可访问，提取到临时目录
        tmp_dir = Path(tempfile.mkdtemp(prefix="u2_nuitka_"))
        assets_dir = tmp_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)

        # 提取已知文件
        for fname in ["u2.jar", "app-uiautomator.apk", "version.json", "sync.sh"]:
            try:
                data = (assets_ref / fname).read_bytes()
                (assets_dir / fname).write_bytes(data)
                logger.info(f"已从 Nuitka 资源提取: {fname} ({len(data)} bytes)")
            except Exception as e:
                logger.warning(f"提取资源 {fname} 失败: {e}")

        if (assets_dir / "u2.jar").exists():
            logger.info(f"Nuitka 资源提取成功: {assets_dir}")
            return assets_dir
        else:
            logger.warning("Nuitka 资源提取失败: u2.jar 未成功写入")
            return None

    except Exception as e:
        logger.warning(f"从 Nuitka 嵌入资源提取失败: {e}")
        return None


def _find_resource_dirs():
    """
    查找 Nuitka 打包后的资源目录
    返回 (u2_assets_dir, adbutils_binaries_dir)
    """
    logger = _get_logger()
    exe_dir = Path(sys.executable).parent
    
    # 查找 uiautomator2 assets 目录
    # 尝试多种可能的目录结构
    u2_assets_dir = None
    possible_u2_dirs = [
        exe_dir / "uiautomator2" / "assets",
        exe_dir / "uiautomator2_assets",
        exe_dir / "assets",
        exe_dir.parent / "uiautomator2" / "assets",
    ]
    
    for d in possible_u2_dirs:
        if d.exists() and (d / "u2.jar").exists():
            u2_assets_dir = d
            break
    
    # 如果没找到，尝试只检查目录存在
    if u2_assets_dir is None:
        for d in possible_u2_dirs:
            if d.exists() and any(d.glob("*.jar")):
                u2_assets_dir = d
                break
    
    # 磁盘上找不到，尝试从 Nuitka 嵌入资源提取
    if u2_assets_dir is None:
        logger.info("磁盘上未找到 u2 assets，尝试从 Nuitka 嵌入资源提取...")
        u2_assets_dir = _extract_nuitka_u2_resources()
    
    # 查找 adbutils binaries 目录
    adbutils_dir = None
    possible_adb_dirs = [
        exe_dir / "adbutils" / "binaries",
        exe_dir / "adbutils_binaries",
        exe_dir.parent / "adbutils" / "binaries",
    ]
    
    for d in possible_adb_dirs:
        if d.exists():
            adbutils_dir = d
            break
    
    return u2_assets_dir, adbutils_dir


class _NuitkaTraversable:
    """
    一个兼容 importlib.abc.Traversable 的简单实现
    用于返回文件系统路径，而不是 Nuitka 的资源对象
    """
    def __init__(self, path):
        self._path = Path(path)
    
    def __truediv__(self, other):
        return _NuitkaTraversable(self._path / other)
    
    def __fspath__(self):
        return str(self._path)
    
    def exists(self):
        return self._path.exists()
    
    def is_dir(self):
        return self._path.is_dir()
    
    def is_file(self):
        return self._path.is_file()
    
    def open(self, mode='r', *args, **kwargs):
        return self._path.open(mode, *args, **kwargs)
    
    def iterdir(self):
        for p in self._path.iterdir():
            yield _NuitkaTraversable(p)
    
    def read_bytes(self):
        return self._path.read_bytes()
    
    def read_text(self):
        return self._path.read_text()
    
    @property
    def name(self):
        return self._path.name
    
    def __str__(self):
        return str(self._path)
    
    def __repr__(self):
        return f"_NuitkaTraversable({self._path})"


def _patch_shutil_for_nuitka():
    """
    修补 shutil.copy 和 shutil.copy2 以处理 Nuitka 资源对象
    这是解决 "Invalid src type: <class 'nuitka_resource_reader_files'>" 错误的关键
    """
    import shutil
    
    logger = _get_logger()
    
    _original_copy = shutil.copy
    _original_copy2 = shutil.copy2
    
    def _safe_str_path(path):
        """将任意路径对象安全转换为字符串"""
        if isinstance(path, str):
            return path
        if hasattr(path, '__fspath__'):
            return path.__fspath__()
        if hasattr(path, 'as_posix'):
            return str(path)
        # 尝试直接转换
        return str(path)
    
    def _patched_copy(src, dst, *args, **kwargs):
        try:
            src_str = _safe_str_path(src)
            dst_str = _safe_str_path(dst)
            return _original_copy(src_str, dst_str, *args, **kwargs)
        except Exception as e:
            logger.error(f"shutil.copy 失败: src={src}, dst={dst}, error={e}")
            raise
    
    def _patched_copy2(src, dst, *args, **kwargs):
        try:
            src_str = _safe_str_path(src)
            dst_str = _safe_str_path(dst)
            return _original_copy2(src_str, dst_str, *args, **kwargs)
        except Exception as e:
            logger.error(f"shutil.copy2 失败: src={src}, dst={dst}, error={e}")
            raise
    
    shutil.copy = _patched_copy
    shutil.copy2 = _patched_copy2
    logger.info("✓ 已 Monkey-patch shutil.copy 和 shutil.copy2")


def _patch_importlib_resources():
    """
    Monkey-patch importlib.resources.files 和 as_file
    作为额外的兼容性层
    """
    logger = _get_logger()
    
    try:
        import importlib.resources as resources
        
        # 处理 Python < 3.9
        if not hasattr(resources, 'files'):
            try:
                import importlib_resources as resources
            except ImportError:
                logger.debug("Python < 3.9 且未安装 importlib_resources，跳过 importlib.resources.files patch")
                return

        _original_files = resources.files
        _original_as_file = getattr(resources, 'as_file', None)
        
        def _patched_files(package):
            """修补后的 resources.files 函数"""
            package_name = package if isinstance(package, str) else getattr(package, '__name__', str(package))
            
            # 处理 uiautomator2 相关
            # _NUITKA_U2_ASSETS_DIR 指向 .../assets/ 目录
            # 但 files("uiautomator2") 应返回包根目录（assets/ 的上级）
            # 因为调用方会做 files("uiautomator2") / "assets" / "u2.jar"
            if 'uiautomator2' in package_name:
                if _NUITKA_U2_ASSETS_DIR:
                    return _NuitkaTraversable(_NUITKA_U2_ASSETS_DIR.parent)
            
            # 处理 adbutils 相关
            if 'adbutils' in package_name:
                if _NUITKA_ADBUTILS_BINARIES_DIR:
                    return _NuitkaTraversable(_NUITKA_ADBUTILS_BINARIES_DIR)
            
            return _original_files(package)
        
        resources.files = _patched_files
        logger.info("✓ 已 Monkey-patch importlib.resources.files")
        
        # patch as_file 如果存在
        if _original_as_file:
            @contextlib.contextmanager
            def _patched_as_file(traversable):
                """修补后的 as_file 函数"""
                if isinstance(traversable, _NuitkaTraversable):
                    yield Path(traversable._path)
                    return
                with _original_as_file(traversable) as f:
                    yield f
            
            resources.as_file = _patched_as_file
            logger.info("✓ 已 Monkey-patch importlib.resources.as_file")
        
        # 同时 patch importlib_resources（Python < 3.9 的备选方案）
        try:
            import importlib_resources
            importlib_resources.files = _patched_files
            if _original_as_file:
                importlib_resources.as_file = resources.as_file
            logger.info("✓ 已 Monkey-patch importlib_resources")
        except ImportError:
            pass
            
    except Exception as e:
        logger.error(f"Monkey-patch importlib.resources 失败: {e}")
        import traceback
        logger.error(traceback.format_exc())


def _patch_uiautomator2_utils():
    """
    直接 Monkey-patch uiautomator2.utils.with_package_resource 函数
    这是最根本的解决方案
    """
    logger = _get_logger()
    
    try:
        import uiautomator2.utils as u2_utils
        
        # 检查是否需要 patch
        if not hasattr(u2_utils, 'with_package_resource'):
            logger.debug("uiautomator2.utils 没有 with_package_resource，跳过 patch")
            return
            
        _original_with_package_resource = u2_utils.with_package_resource
        
        @contextlib.contextmanager
        def _patched_with_package_resource(filename: str):
            """
            修补后的 with_package_resource 函数
            在 Nuitka 环境中直接返回文件系统路径
            """
            # 首先检查我们已知的资源目录
            # _NUITKA_U2_ASSETS_DIR 指向 .../assets/ 目录
            # filename 是相对于包根的路径，如 "assets/u2.jar"
            # 所以用 parent 回到包根级别
            if _NUITKA_U2_ASSETS_DIR:
                resource_path = _NUITKA_U2_ASSETS_DIR.parent / filename
                if resource_path.exists():
                    logger.debug(f"使用 Nuitka 资源路径: {resource_path}")
                    yield resource_path
                    return
            
            # 尝试使用原始函数
            try:
                with _original_with_package_resource(filename) as path:
                    # 确保返回的是真正的 Path 对象
                    if not isinstance(path, Path):
                        path = Path(str(path))
                    yield path
                    return
            except Exception as e:
                logger.warning(f"原始 with_package_resource 失败: {e}")
            
            # 最后的备选方案：检查常见位置
            exe_dir = Path(sys.executable).parent
            filename_name = Path(filename).name
            fallback_paths = [
                exe_dir / "uiautomator2" / filename,
                exe_dir / "uiautomator2_assets" / filename_name,
                exe_dir / "assets" / filename_name,
                exe_dir / filename,
                exe_dir.parent / "uiautomator2" / filename,
            ]
            
            for fp in fallback_paths:
                if fp.exists():
                    logger.info(f"使用备选资源路径: {fp}")
                    yield fp
                    return
            
            raise FileNotFoundError(f"Resource {filename} not found in Nuitka environment")
        
        # 应用 patch 到 utils 模块
        u2_utils.with_package_resource = _patched_with_package_resource
        logger.info("✓ 已 Monkey-patch uiautomator2.utils.with_package_resource")
        
        # 关键：同时修补已通过 from ... import 导入的其他 u2 模块
        # core.py / _input.py / __main__.py 用 from uiautomator2.utils import with_package_resource
        # 这会创建模块级本地引用，不受 utils 模块修改影响，必须逐个修补
        for mod_name in ['uiautomator2.core', 'uiautomator2._input', 'uiautomator2.__main__']:
            mod = sys.modules.get(mod_name)
            if mod and hasattr(mod, 'with_package_resource'):
                mod.with_package_resource = _patched_with_package_resource
                logger.info(f"✓ 已 Monkey-patch {mod_name}.with_package_resource")
        
    except ImportError:
        logger.debug("uiautomator2 未安装，跳过 patch")
    except Exception as e:
        logger.error(f"Monkey-patch uiautomator2.utils 失败: {e}")
        import traceback
        logger.error(traceback.format_exc())


def _patch_adbutils_binaries():
    """
    为 adbutils 设置正确的 binaries 路径
    """
    logger = _get_logger()
    
    if not _NUITKA_ADBUTILS_BINARIES_DIR:
        logger.debug("未找到 adbutils binaries 目录，跳过")
        return
    
    try:
        import adbutils
        
        # 设置环境变量
        os.environ['ADBUTILS_BINARIES_DIR'] = str(_NUITKA_ADBUTILS_BINARIES_DIR)
        logger.info(f"✓ 已设置环境变量 ADBUTILS_BINARIES_DIR = {_NUITKA_ADBUTILS_BINARIES_DIR}")
        
    except ImportError:
        logger.debug("adbutils 未安装，跳过")
    except Exception as e:
        logger.error(f"设置 adbutils binaries 路径失败: {e}")


def ensure_nuitka_compatibility():
    """
    确保 Nuitka 环境的兼容性
    应该在任何使用 uiautomator2 或 adbutils 的代码之前调用
    """
    global _NUITKA_COMPAT_INITIALIZED, _NUITKA_U2_ASSETS_DIR, _NUITKA_ADBUTILS_BINARIES_DIR
    
    if _NUITKA_COMPAT_INITIALIZED:
        return
    
    logger = _get_logger()
    
    if not IS_NUITKA:
        logger.debug("非 Nuitka 环境，跳过兼容性配置")
        _NUITKA_COMPAT_INITIALIZED = True
        return
    
    logger.info("=" * 60)
    logger.info("检测到 Nuitka 环境，开始配置资源兼容性")
    logger.info("=" * 60)
    
    # 查找资源目录
    _NUITKA_U2_ASSETS_DIR, _NUITKA_ADBUTILS_BINARIES_DIR = _find_resource_dirs()
    
    logger.info(f"可执行文件目录: {Path(sys.executable).parent}")
    logger.info(f"u2 assets 目录: {_NUITKA_U2_ASSETS_DIR}")
    logger.info(f"adbutils binaries 目录: {_NUITKA_ADBUTILS_BINARIES_DIR}")
    
    # 设置环境变量
    if _NUITKA_U2_ASSETS_DIR:
        os.environ['UIAUTOMATOR2_ASSETS_DIR'] = str(_NUITKA_U2_ASSETS_DIR)
    
    # 应用所有 Monkey-patches（顺序很重要！）
    # 1. 首先修补 shutil，这是最底层的修复
    _patch_shutil_for_nuitka()
    
    # 2. 修补 importlib.resources，作为中间层
    _patch_importlib_resources()
    
    # 3. 直接修补 uiautomator2 的资源函数，这是最上层的修复
    _patch_uiautomator2_utils()
    
    # 4. 设置 adbutils binaries 路径
    _patch_adbutils_binaries()
    
    _NUITKA_COMPAT_INITIALIZED = True
    
    logger.info("=" * 60)
    logger.info("Nuitka 环境兼容性配置完成")
    logger.info("=" * 60)


# 模块加载时自动初始化（如果在 Nuitka 环境中）
if IS_NUITKA:
    ensure_nuitka_compatibility()
