from PyQt5.QtCore import QThread, pyqtSignal
import subprocess

class ADBEngineeringModeThread(QThread):
    progress_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, device_id):
        super().__init__()
        self.device_id = device_id

    def run(self):
        try:
            self.progress_signal.emit("开始进入AS33_CR工程模式...")
            
            # 使用ADB命令启动应用
            command = f"adb -s {self.device_id} shell am start -n com.saicmotor.diag/com.saicmotor.diag.view.LogMenuActivity"
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.result_signal.emit("成功进入AS33_CR工程模式")
            else:
                self.error_signal.emit(f"进入工程模式失败: {result.stderr}")
                
        except subprocess.CalledProcessError as e:
            self.error_signal.emit(f"进入工程模式失败: {str(e)}")
        except Exception as e:
            self.error_signal.emit(f"进入工程模式失败: {str(e)}")