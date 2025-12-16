from PyQt5.QtCore import QThread, pyqtSignal
import subprocess

class ADBUpdateThread(QThread):
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, device_id):
        super().__init__()
        self.device_id = device_id

    def run(self):
        try:
            self.progress_signal.emit("正在尝试启动更新页面...")
            
            # 使用ADB命令启动应用
            command = f"adb -s {self.device_id} shell am start -n com.saicmotor.update/.view.MainActivity"
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.progress_signal.emit("启动更新页面成功！")
            else:
                self.error_signal.emit(f"更新页面启动失败: {result.stderr}")
                
        except subprocess.CalledProcessError as e:
            self.error_signal.emit(f"更新页面启动失败: {str(e)}")
        except Exception as e:
            self.error_signal.emit(f"更新页面启动失败: {str(e)}")