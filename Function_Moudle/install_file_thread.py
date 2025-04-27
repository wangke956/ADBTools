import os

from PyQt6.QtCore import QThread, pyqtSignal

class InstallFileThread(QThread):
    progress_signal = pyqtSignal(int)
    signal_status = pyqtSignal(str)

    def __init__(self, d, package_path):
        super().__init__()
        self.d = d
        self.package_path = package_path

    def run(self):
        self.signal_status.emit("正在开始安装...")
        # self.d.app_install(self.package_path)
        command = "adb install -r " + self.package_path
        os.system(command)
        self.signal_status.emit("安装成功！")