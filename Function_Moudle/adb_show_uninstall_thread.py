from PyQt5.QtCore import QThread, pyqtSignal
import subprocess

class ADBShowUninstallThread(QThread):
    progress_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, device_id, package_name=None):
        super().__init__()
        self.device_id = device_id
        self.package_name = package_name

    def run(self):
        try:
            if not self.package_name:
                self.error_signal.emit("包名不能为空")
                return
            
            self.progress_signal.emit("正在卸载...")
            
            # 使用ADB命令卸载应用
            command = f"adb -s {self.device_id} uninstall {self.package_name}"
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.result_signal.emit("卸载完成!")
            else:
                self.error_signal.emit(f"卸载失败: {result.stderr}")
                
        except subprocess.CalledProcessError as e:
            self.error_signal.emit(str(e))
        except Exception as e:
            self.error_signal.emit(str(e))