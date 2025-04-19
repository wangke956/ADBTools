from PyQt5.QtCore import QThread, pyqtSignal


class ShowUninstallThread(QThread):
    progress_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, d, package_name=None):
        super().__init__()
        self.d = d
        self.package_name = package_name

    def run(self):
        try:
            self.progress_signal.emit("正在卸载...")
            self.d.app_uninstall(self.package_name)
            self.result_signal.emit("卸载完成!")
        except Exception as e:
            self.error_signal.emit(str(e))