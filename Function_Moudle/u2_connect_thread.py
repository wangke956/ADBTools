from PyQt5.QtCore import QThread, pyqtSignal
import uiautomator2 as u2

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
        
    def run(self):
        """尝试u2连接"""
        try:
            self.progress_signal.emit(f"正在尝试u2连接到设备: {self.device_id}")
            
            # 尝试u2连接
            d = u2.connect(self.device_id)
            
            if d:
                # 测试连接是否有效
                try:
                    # 尝试获取设备信息
                    info = d.info
                    self.progress_signal.emit(f"u2连接成功: {self.device_id}")
                    self.progress_signal.emit(f"设备信息: {info}")
                    self.connected_signal.emit(d, self.device_id)
                except Exception as test_error:
                    self.error_signal.emit(f"u2连接测试失败: {test_error}")
                    self.connected_signal.emit(None, self.device_id)
            else:
                self.error_signal.emit(f"u2连接失败: 无法连接到设备 {self.device_id}")
                self.connected_signal.emit(None, self.device_id)
                
        except Exception as e:
            error_msg = f"u2连接异常: {str(e)}"
            self.error_signal.emit(error_msg)
            self.connected_signal.emit(None, self.device_id)