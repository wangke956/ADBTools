from PyQt5.QtCore import QThread, pyqtSignal
import subprocess
import uiautomator2 as u2

class RefreshDevicesThread(QThread):
    progress_signal = pyqtSignal(str)
    devices_signal = pyqtSignal(list)  # 发送设备列表
    error_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.device_ids = []
        
    def run(self):
        try:
            self.progress_signal.emit("正在刷新设备列表...")
            
            # 执行 adb devices 命令
            result = subprocess.run(
                "adb devices", 
                shell=True, 
                check=True, 
                capture_output=True, 
                text=True, 
                encoding='utf-8', 
                errors='ignore'
            )
            
            devices = result.stdout.strip().split('\n')[1:]  # 获取设备列表
            device_ids = [line.split('\t')[0] for line in devices if line]  # 提取设备ID
            
            self.device_ids = device_ids
            
            if device_ids:
                device_ids_str = "\n".join(device_ids)
                self.progress_signal.emit(f"设备列表已刷新：")
                self.progress_signal.emit(device_ids_str)
                self.devices_signal.emit(device_ids)
            else:
                self.progress_signal.emit("未检测到任何设备")
                self.devices_signal.emit([])
                
        except subprocess.CalledProcessError as e:
            self.error_signal.emit(f"ADB命令执行失败: {e}")
        except Exception as e:
            self.error_signal.emit(f"刷新设备列表时发生错误: {str(e)}")