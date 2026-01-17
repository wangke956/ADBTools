from PyQt5.QtCore import QThread, pyqtSignal
import uiautomator2 as u2
from logger_manager import get_logger, log_device_operation, log_thread_start, log_thread_complete

# 创建日志记录器
logger = get_logger("ADBTools.U2ConnectThread")

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
                    # 如果获取设备信息失败，仍然返回连接成功
                    elapsed_time = time.time() - start_time
                    logger.warning(f"u2连接成功但无法获取设备信息: {self.device_id} | 错误: {info_error}")
                    
                    self.progress_signal.emit(f"u2连接成功: {self.device_id}")
                    self.progress_signal.emit(f"注意: 无法获取设备详细信息 - {str(info_error)}")
                    
                    log_device_operation("u2_connect_success_partial", self.device_id, {
                        "mode": "u2",
                        "status": "connected",
                        "warning": "无法获取设备详细信息",
                        "elapsed_time": elapsed_time
                    })
                    
                    log_thread_complete("U2ConnectThread", "success", {
                        "device_id": self.device_id,
                        "elapsed_time": elapsed_time,
                        "warning": "无法获取设备详细信息"
                    })
                    
                    self.connected_signal.emit(d, self.device_id)
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