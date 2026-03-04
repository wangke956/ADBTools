from PyQt5.QtCore import QThread, pyqtSignal
import uiautomator2 as u2
from logger_manager import get_logger, log_device_operation, log_thread_start, log_thread_complete
import os
import sys

# 创建日志记录器
logger = get_logger("ADBTools.U2ConnectThread")

# 检查是否在 Nuitka 环境中运行
IS_NUITKA = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

# 全局变量：存储找到的 assets 目录路径
_NUITKA_ASSETS_DIR = None

if IS_NUITKA:
    # Nuitka 环境中需要特殊处理 uiautomator2 的资源读取
    from pathlib import Path
    import shutil
    import tempfile
    
    logger.info("=" * 60)
    logger.info("检测到 Nuitka 环境，开始配置 uiautomator2 资源路径")
    logger.info("=" * 60)
    
    # 获取可执行文件所在目录
    exe_dir = Path(sys.executable).parent
    logger.info(f"可执行文件目录: {exe_dir}")
    
    # 查找 uiautomator2 assets 目录
    possible_assets_dirs = [
        exe_dir / "uiautomator2" / "assets",
        exe_dir / "uiautomator2_assets",
        exe_dir.parent / "uiautomator2" / "assets",
    ]
    
    for assets_dir in possible_assets_dirs:
        logger.info(f"检查资源目录: {assets_dir}，存在: {assets_dir.exists()}")
        if assets_dir.exists():
            _NUITKA_ASSETS_DIR = assets_dir
            break
    
    if _NUITKA_ASSETS_DIR and _NUITKA_ASSETS_DIR.exists():
        logger.info(f"找到 u2 assets 目录: {_NUITKA_ASSETS_DIR}")
        
        # 列出资源文件
        asset_files = list(_NUITKA_ASSETS_DIR.glob("*"))
        logger.info(f"找到 {len(asset_files)} 个资源文件:")
        for f in asset_files:
            logger.info(f"  - {f.name} ({f.stat().st_size} bytes)")
        
        # 关键修复：Monkey-patch importlib.resources 来解决 Nuitka 兼容性问题
        try:
            import importlib.resources as resources
            
            # 保存原始函数
            _original_files = resources.files
            
            def _patched_files(package):
                """
                修补后的 resources.files 函数
                当请求 uiautomator2.assets 时，返回文件系统路径而不是 Nuitka 资源读取器
                """
                package_name = package if isinstance(package, str) else package.__name__
                logger.debug(f"resources.files 被调用，包名: {package_name}")
                
                if 'uiautomator2.assets' in package_name or ('uiautomator2' in package_name and 'assets' in package_name):
                    # 返回文件系统路径
                    from pathlib import Path as PathlibPath
                    assets_path = PathlibPath(_NUITKA_ASSETS_DIR)
                    logger.info(f"返回 uiautomator2 assets 文件系统路径: {assets_path}")
                    return assets_path
                else:
                    # 其他包使用原始函数
                    return _original_files(package)
            
            # 应用 Monkey-patch
            resources.files = _patched_files
            logger.info("✓ 成功 Monkey-patch importlib.resources.files")
            
            # 同时检查 importlib_resources（某些版本可能使用这个）
            try:
                import importlib_resources
                _original_files_v2 = importlib_resources.files
                importlib_resources.files = _patched_files
                logger.info("✓ 成功 Monkey-patch importlib_resources.files")
            except ImportError:
                logger.debug("importlib_resources 未安装，跳过")
            
        except Exception as patch_error:
            logger.error(f"Monkey-patch 失败: {patch_error}")
            import traceback
            logger.error(traceback.format_exc())
            
            # 备用方案：复制资源到临时目录
            logger.info("尝试备用方案：复制资源到临时目录...")
            try:
                temp_dir = Path(tempfile.gettempdir()) / "u2_assets_runtime"
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                temp_dir.mkdir(parents=True, exist_ok=True)
                
                for asset_file in _NUITKA_ASSETS_DIR.glob("*"):
                    if asset_file.is_file():
                        shutil.copy2(asset_file, temp_dir / asset_file.name)
                        logger.info(f"  复制: {asset_file.name}")
                
                # 设置环境变量
                os.environ['UIAUTOMATOR2_ASSETS_DIR'] = str(temp_dir)
                logger.info(f"✓ 已设置环境变量 UIAUTOMATOR2_ASSETS_DIR = {temp_dir}")
                
            except Exception as copy_error:
                logger.error(f"备用方案失败: {copy_error}")
    else:
        logger.error("未找到 uiautomator2 assets 目录！")
        logger.error("U2 连接可能失败，将自动降级到 ADB 模式")
    
    logger.info("=" * 60)
    logger.info("Nuitka 环境配置完成")
    logger.info("=" * 60)
else:
    logger.debug("非 Nuitka 环境，使用默认配置")

class U2ConnectThread(QThread):
    """u2连接尝试线程（避免在主线程中阻塞）"""
    progress_signal = pyqtSignal(str)
    connected_signal = pyqtSignal(object, str)  # 发送连接成功的u2设备对象和设备ID
    error_signal = pyqtSignal(str)
    
    def __init__(self, device_id):
        """
        初始化u2连接线程
        
        Args:
            device_id: 要连接的设备ID
        """
        super().__init__()
        self.device_id = device_id
        logger.info(f"U2ConnectThread初始化: 目标设备 {device_id}")
        
    def run(self):
        """尝试u2连接，优化连接速度"""
        import time
        start_time = time.time()
        
        log_thread_start("U2ConnectThread", {"device_id": self.device_id})
        log_device_operation("u2_connect_start", self.device_id, {"mode": "u2"})
        
        try:
            self.progress_signal.emit(f"正在连接到设备: {self.device_id}")
            logger.info(f"开始u2连接: {self.device_id}")
            
            # 直接尝试u2连接
            # 注意：Nuitka 环境的资源处理已在模块加载时通过 Monkey-patch 完成
            d = u2.connect(self.device_id)
            
            if d:
                # 获取设备详细信息
                try:
                    info = d.info
                    device_info = {
                        'serial': self.device_id,
                        'model': info.get('model', 'Unknown'),
                        'brand': info.get('brand', 'Unknown'),
                        'version': info.get('version', 'Unknown'),
                        'sdk': info.get('sdk', 'Unknown'),
                        'manufacturer': info.get('manufacturer', 'Unknown')
                    }
                    
                    elapsed_time = time.time() - start_time
                    logger.info(f"u2连接成功: {self.device_id} | 耗时: {elapsed_time:.3f}s")
                    logger.info(f"设备信息: {device_info}")
                    
                    # 发送详细的成功信息
                    self.progress_signal.emit(f"u2连接成功: {self.device_id}")
                    self.progress_signal.emit(f"设备型号: {device_info['brand']} {device_info['model']}")
                    self.progress_signal.emit(f"Android版本: {device_info['version']}")
                    self.progress_signal.emit(f"SDK版本: {device_info['sdk']}")
                    
                    log_device_operation("u2_connect_success", self.device_id, {
                        "mode": "u2",
                        "status": "connected",
                        "device_info": device_info,
                        "elapsed_time": elapsed_time
                    })
                    
                    log_thread_complete("U2ConnectThread", "success", {
                        "device_id": self.device_id,
                        "elapsed_time": elapsed_time,
                        "device_info": device_info
                    })
                    
                    self.connected_signal.emit(d, self.device_id)
                except Exception as info_error:
                    # 如果获取设备信息失败，降级到ADB模式
                    elapsed_time = time.time() - start_time
                    logger.warning(f"u2连接成功但无法获取设备信息，降级到ADB模式: {self.device_id} | 错误: {info_error}")
                    
                    # 不再发送设备信息，直接发送降级消息
                    self.progress_signal.emit(f"u2连接无法获取设备信息，降级到ADB模式: {self.device_id}")
                    self.progress_signal.emit(f"原因: {str(info_error)}")
                    
                    log_device_operation("u2_connect_fallback_to_adb", self.device_id, {
                        "mode": "u2_to_adb",
                        "status": "fallback",
                        "reason": str(info_error),
                        "elapsed_time": elapsed_time
                    })
                    
                    log_thread_complete("U2ConnectThread", "fallback", {
                        "device_id": self.device_id,
                        "elapsed_time": elapsed_time,
                        "fallback_mode": "adb",
                        "reason": str(info_error)
                    })
                    
                    # 发送降级信号（None表示U2失败，触发ADB模式）
                    self.connected_signal.emit(None, self.device_id)
            else:
                elapsed_time = time.time() - start_time
                error_msg = f"u2连接失败: 无法连接到设备 {self.device_id}"
                logger.error(f"{error_msg} | 耗时: {elapsed_time:.3f}s")
                self.error_signal.emit(error_msg)
                
                log_device_operation("u2_connect_failed", self.device_id, {
                    "mode": "u2",
                    "status": "failed",
                    "reason": "无法连接到设备",
                    "elapsed_time": elapsed_time
                })
                
                log_thread_complete("U2ConnectThread", "failed", {
                    "device_id": self.device_id,
                    "elapsed_time": elapsed_time,
                    "reason": "无法连接到设备"
                })
                
                self.connected_signal.emit(None, self.device_id)
                
        except Exception as e:
            elapsed_time = time.time() - start_time
            error_msg = f"u2连接异常: {str(e)}"
            logger.error(f"{error_msg} | 耗时: {elapsed_time:.3f}s")
            logger.exception("u2连接异常详情:")
            
            self.error_signal.emit(error_msg)
            
            log_device_operation("u2_connect_exception", self.device_id, {
                "mode": "u2",
                "status": "error",
                "error": str(e),
                "elapsed_time": elapsed_time
            })
            
            log_thread_complete("U2ConnectThread", "error", {
                "device_id": self.device_id,
                "elapsed_time": elapsed_time,
                "error": str(e)
            })
            
            self.connected_signal.emit(None, self.device_id)