from PyQt5.QtCore import QThread, pyqtSignal
import subprocess

class simulate_long_press_dialog_thread(QThread):
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    def __init__(self, d):
        super().__init__()
        self.d = d

    def run(self):
        result = subprocess.run("adb kill-server", capture_output=True, text=True)
        if result.returncode == 0:
            self.result_signal.emit("杀死ADB服务成功！")
            self.result_signal.emit(result.stdout)
        else:
            self.result_signal.emit("命令执行失败!")
            self.result_signal.emit(result.stderr)
        result_2 = subprocess.run("adb start-server", capture_output=True, text=True)
        if result_2.returncode == 0:
            self.result_signal.emit("ADB服务启动成功!")
            self.result_signal.emit(result.stdout)
        else:
            self.result_signal.emit("ADB服务启动失败!")
            self.result_signal.emit(result.stderr)