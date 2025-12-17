from PyQt5.QtCore import QThread, pyqtSignal
import subprocess
class InstallFileThread(QThread):
    progress_signal = pyqtSignal(int)
    signal_status = pyqtSignal(str)

    def __init__(self, d, package_path):
        super().__init__()
        self.d = d
        self.package_path = package_path

    def run(self):
        try:
            self.signal_status.emit("正在开始安装...")
            result = subprocess.run(
                ["adb", "install", "-r", self.package_path],
                capture_output=True,
                text=True,
                check=True
            )
            self.signal_status.emit(result.stdout)
        except Exception as e:
            self.signal_status.emit(str(e))