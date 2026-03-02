from PyQt5.QtCore import QThread, pyqtSignal
import subprocess

class simulate_long_press_dialog_thread(QThread):
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    def __init__(self, d):
        super().__init__()
        self.d = d

    def run(self):
        # 获取设备ID
        device_id = None
        if hasattr(self.d, 'serial'):
            device_id = self.d.serial
        elif hasattr(self.d, 'device_id'):
            device_id = self.d.device_id
        elif isinstance(self.d, str):
            device_id = self.d
            
        try:
            # 使用指定设备重启ADB服务
            if device_id:
                result = subprocess.run(f"adb -s {device_id} kill-server", capture_output=True, text=True)
                if result.returncode == 0:
                    self.result_signal.emit(f"杀死设备 {device_id} 的ADB服务成功！")
                    self.result_signal.emit(result.stdout)
                else:
                    self.result_signal.emit("命令执行失败!")
                    self.result_signal.emit(result.stderr)
                
                result_2 = subprocess.run(f"adb -s {device_id} start-server", capture_output=True, text=True)
                if result_2.returncode == 0:
                    self.result_signal.emit(f"设备 {device_id} 的ADB服务启动成功!")
                    self.result_signal.emit(result.stdout)
                else:
                    self.result_signal.emit("ADB服务启动失败!")
                    self.result_signal.emit(result.stderr)
            else:
                # 如果没有设备ID，使用全局命令
                result = subprocess.run("adb kill-server", capture_output=True, text=True)
                if result.returncode == 0:
                    self.result_signal.emit("杀死ADB服务成功！")
                    self.result_signal.emit(result.stdout)
                else:
                    self.result_signal.emit("命令执行失败!")
                    self.result_signal.emit(result.stderr)
                result_2 = subprocess.run("adb start-server", capture_output=True, text=True)
                if result_2.returncode == 0:
                    self.result_signal.emit("ADB服务启动成功!")
                    self.result_signal.emit(result.stdout)
                else:
                    self.result_signal.emit("ADB服务启动失败!")
                    self.result_signal.emit(result.stderr)
        except Exception as e:
            self.error_signal.emit(f"执行ADB命令时发生异常: {str(e)}")