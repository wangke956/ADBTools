from PyQt5.QtCore import QThread, pyqtSignal
import subprocess

class ActivateVrThread(QThread):
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    
    def __init__(self, device_id, keyevent_value, connection_mode='adb', u2_device=None):
        super().__init__()
        self.device_id = device_id
        self.keyevent_value = keyevent_value
        self.connection_mode = connection_mode
        self.u2_device = u2_device
        
    def run(self):
        try:
            if self.connection_mode == 'u2' and self.u2_device:
                # 使用u2的shell方法执行keyevent命令
                keycode = int(self.keyevent_value)
                self.progress_signal.emit(f"执行VR唤醒命令: u2 shell input keyevent {keycode}")
                
                try:
                    self.u2_device.shell(f'input keyevent {keycode}')
                    self.progress_signal.emit("VR唤醒命令执行成功！(u2模式)")
                except Exception as u2_error:
                    self.error_signal.emit(f"u2 shell命令执行失败: {u2_error}")
                    
            elif self.connection_mode == 'adb':
                # 使用ADB命令
                self.progress_signal.emit(f"执行VR唤醒命令: adb shell input keyevent {self.keyevent_value}")
                
                command = f"adb -s {self.device_id} shell input keyevent {self.keyevent_value}"
                result = subprocess.run(
                    command, 
                    shell=True, 
                    capture_output=True, 
                    text=True
                )
                
                if result.returncode == 0:
                    self.progress_signal.emit("VR唤醒命令执行成功！(ADB模式)")
                else:
                    self.error_signal.emit(f"VR唤醒命令执行失败: {result.stderr}")
            else:
                self.error_signal.emit("不支持的连接模式或设备未连接")
                
        except Exception as e:
            self.error_signal.emit(f"执行VR唤醒命令失败: {e}")