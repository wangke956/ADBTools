from PyQt5.QtCore import QThread, pyqtSignal
import subprocess
import os

class ADBPullFilesThread(QThread):
    signal = pyqtSignal(str)

    def __init__(self, device_id, device_files_path, local_files_path, apk_file_name):
        super(ADBPullFilesThread, self).__init__()
        self.device_id = device_id
        self.apk_file_name = apk_file_name
        self.device_files_path = device_files_path
        self.local_files_path = os.path.join(local_files_path, apk_file_name)

    def run(self):
        try:
            # 确保本地目录存在
            os.makedirs(os.path.dirname(self.local_files_path), exist_ok=True)
            
            # 使用ADB命令拉取文件
            command = f"adb -s {self.device_id} pull {self.device_files_path} {self.local_files_path}"
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.signal.emit(self.device_files_path)
                self.signal.emit(self.local_files_path)
                self.signal.emit("拉取文件完成!")
            else:
                self.signal.emit(f"拉取文件失败: {result.stderr}")
                
        except subprocess.CalledProcessError as e:
            self.signal.emit(f"ADB命令执行失败: {str(e)}")
        except Exception as e:
            self.signal.emit(f"拉取文件失败: {str(e)}")