from PyQt6.QtCore import QThread, pyqtSignal
import subprocess
import time

class RebootDeviceThread(QThread):
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, device_id):
        super().__init__()
        self.device_id = device_id

    def run(self):
        try:
            self.progress_signal.emit("正在尝试重启设备...")
            result = subprocess.run(f"adb -s {self.device_id} reboot",
                                  shell=True,
                                  capture_output=True,
                                  text=True,
                                  timeout=30)
            
            time.sleep(3)
            
            if result.returncode == 0:
                self.progress_signal.emit("设备重启命令已成功发送")
            else:
                self.error_signal.emit(f"重启失败: {result.stderr}")
        except subprocess.TimeoutExpired:
            self.error_signal.emit("ADB命令执行超时")
        except Exception as e:
            self.error_signal.emit(f"发生未知错误: {str(e)}")