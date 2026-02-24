from PyQt5.QtCore import QThread, pyqtSignal
import uiautomator2 as u2
from logger_manager import get_logger, log_device_operation, log_thread_start, log_thread_complete
import os
import sys

# 创建日志记录器
logger = get_logger("ADBTools.U2ConnectThread")

# 检查是否在 Nuitka 环境中运行
IS_NUITKA = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

if IS_NUITKA:
    # Nuitka 环境中需要设置 u2 的资源路径
    import ntpath
    import uiautomator2
    import uiautomator2.assets as u2_assets
    from pathlib import Path
    
    # 获取当前脚本所在目录（在 Nuitka 中是可执行文件所在目录）
    if getattr(sys, 'frozen', False):
        # 可执行文件路径
        exe_dir = Path(sys.executable).parent
        u2_assets_dir = exe_dir / "uiautomator2" / "assets"
    else:
        # 源代码路径
        u2_assets_dir = Path(__file__).parent.parent / "uiautomator2" / "assets"
    
    # 设置 u2 的资源路径
    if u2_assets_dir.exists():
        # 确保路径是字符串类型，并且是绝对路径
        assets_path = str(u2_assets_dir.absolute())
        u2_assets._assets_dir = assets_path
        logger.info(f"设置 u2 资源路径为: {assets_path}")
        
        # 确保 u2 能够正确处理资源
        try:
            # 尝试访问 assets 目录
            if hasattr(u2_assets, '_assets'):
                # 重置资源管理器
                u2_assets._assets = None
            logger.info("已重置 u2 资源管理器")
            
            # 强制 u2 重新初始化资源
            u2_assets.init()
            logger.info("已强制 u2 重新初始化资源")
        except Exception as e:
            logger.warning(f"重置 u2 资源管理器时出现警告: {e}")
            
            # 如果 init() 失败，尝试手动复制资源文件
            try:
                import shutil
                import tempfile
                
                # 创建临时目录
                temp_dir = Path(tempfile.gettempdir()) / "u2_assets"
                temp_dir.mkdir(exist_ok=True)
                
                # 复制所有资源文件到临时目录
                for asset_file in u2_assets_dir.glob("*"):
                    if asset_file.is_file():
                        dest_file = temp_dir / asset_file.name
                        shutil.copy2(asset_file, dest_file)
                        logger.debug(f"已复制资源文件: {asset_file.name}")
                
                # 更新 u2 的资源路径为临时目录
                u2_assets._assets_dir = str(temp_dir.absolute())
                u2_assets.init()
                logger.info(f"已使用临时目录作为 u2 资源路径: {temp_dir}")
                
            except Exception as copy_error:
                logger.error(f"手动复制 u2 资源文件失败: {copy_error}")
    else:
        logger.warning("uiautomator2 assets 目录不存在，尝试使用默认路径")
        # 尝试使用 uiautomator2 的默认资源路径
        try:
            # 清除可能的错误路径
            u2_assets._assets_dir = None
            u2_assets.init()
            logger.info("已使用 uiautomator2 默认资源路径")
        except Exception as e:
            logger.error(f"使用 uiautomator2 默认资源路径失败: {e}")

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
            
            # 直接尝试u2连接，不进行额外测试
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