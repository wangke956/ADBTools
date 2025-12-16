from PyQt5.QtCore import QThread, pyqtSignal
import subprocess

class ADBVRActivationThread(QThread):
    progress_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, device_id):
        super(ADBVRActivationThread, self).__init__()
        self.device_id = device_id

    def run(self):
        try:
            self.progress_signal.emit("开始激活VR...")
            
            # 使用ADB命令发送VR激活按键
            command = f"adb -s {self.device_id} shell input keyevent 287"
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.result_signal.emit("VR激活指令发送成功")
                self.finished_signal.emit("VR激活操作完成")
            else:
                self.error_signal.emit(f"VR激活失败: {result.stderr}")
        except subprocess.CalledProcessError as e:
            self.error_signal.emit(f"激活VR失败: {str(e)}")
        except Exception as e:
            self.error_signal.emit(f"激活VR失败: {str(e)}")