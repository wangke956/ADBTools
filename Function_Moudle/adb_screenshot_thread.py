from PyQt5.QtCore import QThread, pyqtSignal
import subprocess
import os

class ADBScreenshotThread(QThread):
    signal = pyqtSignal(str)

    def __init__(self, device_id, file_path):
        super(ADBScreenshotThread, self).__init__()
        self.device_id = device_id
        self.file_path = file_path

    def run(self):
        try:
            # 使用ADB命令截图
            command = f"adb -s {self.device_id} shell screencap -p /sdcard/screenshot.png"
            subprocess.run(command, shell=True, check=True, capture_output=True, encoding='utf-8', errors='ignore')
            
            # 拉取截图文件到本地
            pull_command = f"adb -s {self.device_id} pull /sdcard/screenshot.png {self.file_path}"
            subprocess.run(pull_command, shell=True, check=True, capture_output=True, encoding='utf-8', errors='ignore')
            
            # 删除设备上的临时文件
            rm_command = f"adb -s {self.device_id} shell rm /sdcard/screenshot.png"
            subprocess.run(rm_command, shell=True, check=True, capture_output=True, encoding='utf-8', errors='ignore')
            
            self.signal.emit(f"已保存截图到：{self.file_path}")
        except subprocess.CalledProcessError as e:
            self.signal.emit(f"ADB截图失败！{e}")
        except Exception as e:
            self.signal.emit(f"截图失败！{e}")