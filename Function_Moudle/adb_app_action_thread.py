from PyQt5.QtCore import QThread, pyqtSignal
import subprocess

class ADBAppActionThread(QThread):
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, device_id, package_name):
        super(ADBAppActionThread, self).__init__()
        self.device_id = device_id
        self.package_name = package_name

    def run(self):
        try:
            self.progress_signal.emit("正在启动应用程序...")
            
            # 使用ADB命令启动应用
            command = f"adb -s {self.device_id} shell am start -n {self.package_name}"
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.progress_signal.emit("应用启动成功")
            else:
                self.error_signal.emit(f"应用启动失败: {result.stderr}")
        except subprocess.CalledProcessError as e:
            self.error_signal.emit(f"应用启动失败: {str(e)}")
        except Exception as e:
            self.error_signal.emit(f"应用启动失败: {str(e)}")