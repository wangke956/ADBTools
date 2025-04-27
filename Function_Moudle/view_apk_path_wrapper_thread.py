from PyQt6.QtCore import QThread, pyqtSignal
import subprocess

class ViewApkPathWrapperThread(QThread):
    progress_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, device_id, package_name):
        super().__init__()
        self.device_id = device_id
        self.package_name = package_name

    def run(self):
        try:
            self.progress_signal.emit("正在查询应用安装路径...")
            result = subprocess.run(
                f'adb -s {self.device_id} shell pm path {self.package_name}',
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                path = result.stdout.split('package:')[1].strip()
                self.result_signal.emit(f"应用安装路径: {path}")
            else:
                self.error_signal.emit(f"查询失败: {result.stderr}")
        except subprocess.TimeoutExpired:
            self.error_signal.emit("ADB命令执行超时")
        except Exception as e:
            self.error_signal.emit(f"发生未知错误: {str(e)}")