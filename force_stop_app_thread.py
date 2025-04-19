from PyQt5.QtCore import QThread, pyqtSignal


class ForceStopAppThread(QThread):
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, d):
        super().__init__()
        self.d = d
        self.current_app = self.d.app_current()  # 获取当前正在运行的应用
        self.package_name = self.current_app['package']

    def run(self):
        try:
            self.progress_signal.emit("正在停止应用...")
            self.d.app_stop(self.package_name)
            self.progress_signal.emit("应用停止成功！")
        except Exception as e:
            self.error_signal.emit(str(e))