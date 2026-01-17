from PyQt5.QtCore import QThread, pyqtSignal


class ClearAppCacheThread(QThread):
    """清除应用缓存线程"""
    progress_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    
    def __init__(self, d, package_name=None):
        super().__init__()
        self.d = d
        self.package_name = package_name

    def run(self):
        """执行清除应用缓存操作"""
        try:
            if not self.package_name:
                error_msg = "未指定应用包名"
                self.error_signal.emit(error_msg)
                return
            
            self.progress_signal.emit(f"正在清除应用 {self.package_name} 的缓存...")
            
            self.d.app_clear(self.package_name)
            
            success_msg = f"清除应用 {self.package_name} 缓存成功！"
            self.progress_signal.emit(success_msg)
            self.result_signal.emit(success_msg)
            
        except Exception as e:
            error_msg = f"清除应用缓存失败: {str(e)}"
            self.error_signal.emit(error_msg)
