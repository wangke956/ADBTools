from PyQt5.QtCore import QThread, pyqtSignal


class ForceStopAppThread(QThread):
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)

    def __init__(self, d, package_name=None):
        super().__init__()
        self.d = d
        self.package_name = package_name

    def run(self):
        try:
            if not self.package_name:
                self.error_signal.emit("未指定应用包名")
                return
                
            self.progress_signal.emit("正在停止应用...")
            self.d.app_stop(self.package_name)
            result_msg = "应用停止成功！"
            self.result_signal.emit(result_msg)
            self.progress_signal.emit(result_msg)
        except Exception as e:
            error_msg = str(e)
            self.error_signal.emit(error_msg)