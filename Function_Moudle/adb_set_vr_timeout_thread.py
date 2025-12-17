from PyQt5.QtCore import QThread, pyqtSignal
import subprocess

class ADBSetVrTimeoutThread(QThread):
    signal_timeout = pyqtSignal(str)

    def __init__(self, device_id):
        super().__init__()
        self.device_id = device_id

    def run(self):
        try:
            # 使用ADB命令发送广播
            command = f"adb -s {self.device_id} shell am broadcast -n com.microsoft.assistant.client/.VAExtendBroadcastReceiver --es cmd 'SetOnlineTimeout:10000'"
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.signal_timeout.emit(f"命令已执行: {result.stdout}")
            else:
                self.signal_timeout.emit(f"命令执行失败: {result.stderr}")
                
        except subprocess.CalledProcessError as e:
            self.signal_timeout.emit(f"命令执行失败: {str(e)}")
        except Exception as e:
            self.signal_timeout.emit(f"命令执行失败: {str(e)}")