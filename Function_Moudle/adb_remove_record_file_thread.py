from PyQt5.QtCore import QThread, pyqtSignal
import subprocess

class ADBRemoveRecordFileThread(QThread):
    signal_remove_voice_record_file = pyqtSignal(str)

    def __init__(self, device_id, device_record_file_path):
        super().__init__()
        self.device_id = device_id
        self.device_record_file_path = device_record_file_path

    def run(self):
        try:
            self.signal_remove_voice_record_file.emit('正在删除录音文件...')
            
            # 使用ADB命令删除文件
            command = f"adb -s {self.device_id} shell rm -rf {self.device_record_file_path}"
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.signal_remove_voice_record_file.emit('录音文件删除成功！')
            else:
                self.signal_remove_voice_record_file.emit(f'删除录音文件失败: {result.stderr}')
                
        except subprocess.CalledProcessError as e:
            self.signal_remove_voice_record_file.emit(f'删除录音文件失败！{e}')
        except Exception as e:
            self.signal_remove_voice_record_file.emit(f'删除录音文件失败！{e}')