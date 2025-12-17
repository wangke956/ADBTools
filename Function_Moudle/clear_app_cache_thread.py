from PyQt5.QtCore import QThread, pyqtSignal


class ClearAppCacheThread(QThread):
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, d, package_name=None):
        super().__init__()
        self.d = d
        self.package_name = package_name

    def run(self):
        try:
            if not self.package_name:
                self.error_signal.emit("未指定应用包名")
                return
                
            self.d.app_clear(self.package_name)
            self.progress_signal.emit("清除应用缓存成功！")
        except Exception as e:
            self.error_signal.emit(str(e))
