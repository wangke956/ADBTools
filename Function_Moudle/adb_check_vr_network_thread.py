from PyQt5.QtCore import QThread, pyqtSignal
import subprocess

class ADBCheckVRNetworkThread(QThread):
    progress_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, device_id):
        super(ADBCheckVRNetworkThread, self).__init__()
        self.device_id = device_id

    def run(self):
        try:
            self.progress_signal.emit("页面正在打开...")
            
            # 使用ADB命令启动应用
            command = f"adb -s {self.device_id} shell am start -n com.microsoft.assistant.client/com.microsoft.assistant.client.MainActivity"
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.result_signal.emit("页面打开成功!")
            else:
                self.error_signal.emit(f"页面打开失败! 错误: {result.stderr}")
        except subprocess.CalledProcessError as e:
            self.error_signal.emit(f"页面打开失败: {str(e)}")
        except Exception as e:
            self.error_signal.emit(f"页面打开失败: {str(e)}")