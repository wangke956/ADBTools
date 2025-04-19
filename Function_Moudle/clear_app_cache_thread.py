from PyQt5.QtCore import QThread, pyqtSignal


class ClearAppCacheThread(QThread):
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, d):
        super().__init__()
        self.d = d
        self.current_app = None
        self.package_name = None


    def run(self):
        try:
            self.current_app = self.d.app_current()  # 获取当前正在运行的应用
            self.package_name = self.current_app['package']
            self.d.app_clear(self.package_name)
            self.progress_signal.emit("清除应用缓存成功！")
        except Exception as e:
            self.error_signal.emit(str(e))
