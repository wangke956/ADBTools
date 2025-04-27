from PyQt6.QtCore import QThread, pyqtSignal
import subprocess
import time


class AdbRootWrapperThread(QThread):
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, device_id):
        super().__init__()
        self.device_id = device_id

    def run(self):
        try:
            self.progress_signal.emit("正在尝试获取root权限...")
            result = subprocess.run(f"adb -s {self.device_id} root",
                                    shell=True,
                                    capture_output=True,
                                    text=True,
                                    timeout=10)

            time.sleep(3)
            if "adbd cannot run as root in production builds" in result.stdout:
                self.progress_signal.emit(result.stdout)
                self.progress_signal.emit("该设备无法以root权限运行，请检查设备设置")
            else:
                self.error_signal.emit(f"执行失败: {result.stderr}")
        except subprocess.TimeoutExpired:
            self.error_signal.emit("ADB命令执行超时")
        except Exception as e:
            self.error_signal.emit(f"发生未知错误: {str(e)}")
