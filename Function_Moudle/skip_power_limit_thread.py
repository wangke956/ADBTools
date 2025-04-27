from PyQt6.QtCore import QThread, pyqtSignal
import subprocess
import time

class SkipPowerLimitThread(QThread):
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, device_id):
        super().__init__()
        self.device_id = device_id

    def run(self):
        try:
            self.progress_signal.emit("正在尝试跳过电源挡位限制...")
            
            # 执行ADB root命令
            root_result = subprocess.run(f"adb -s {self.device_id} root", 
                                       shell=True, 
                                       capture_output=True,
                                       text=True,
                                       timeout=10)
            
            time.sleep(3)
            
            # 检查root结果
            if "adbd cannot run as root in production builds" in root_result.stdout:
                self.progress_signal.emit(root_result.stdout)
                self.error_signal.emit("该设备无法获取root权限")
                return
            
            # 执行设置属性命令
            setprop_result = subprocess.run(f'adb -s {self.device_id} shell "setprop bmi.service.adb.root 1"',
                                          shell=True,
                                          capture_output=True,
                                          text=True,
                                          timeout=10)
            
            if setprop_result.returncode == 0:
                self.progress_signal.emit("成功跳过电源挡位限制")
            else:
                self.error_signal.emit(f"执行失败: {setprop_result.stderr}")
            
        except subprocess.TimeoutExpired:
            self.error_signal.emit("ADB命令执行超时")
        except Exception as e:
            self.error_signal.emit(f"发生未知错误: {str(e)}")