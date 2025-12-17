from PyQt5.QtCore import QThread, pyqtSignal
import subprocess

class ADBEnterEngineeringModeThread(QThread):
    progress_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, device_id):
        super().__init__()
        self.device_id = device_id

    def run(self):
        try:
            # 使用ADB命令启动应用
            command = f"adb -s {self.device_id} shell am start -n com.saicmotor.hmi.engmode/com.saicmotor.hmi.engmode.home.ui.EngineeringModeActivity"
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.result_signal.emit("工程模式打开成功")
            else:
                self.error_signal.emit("打开页面失败，请检查设备连接是否正常。")
                
        except subprocess.CalledProcessError as e:
            self.error_signal.emit("打开页面失败，请检查设备连接是否正常。")
        except Exception as e:
            self.error_signal.emit("打开页面失败，请检查设备连接是否正常。")