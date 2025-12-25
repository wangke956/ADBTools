from PyQt5.QtCore import QThread, pyqtSignal
import subprocess

class AaptGetPackageNameThread(QThread):
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    
    def __init__(self, apk_path):
        super().__init__()
        self.apk_path = apk_path
        
    def run(self):
        try:
            quoted_apk_path = f'"{self.apk_path}"'
            command = f"aapt dump badging {quoted_apk_path} | findstr name"
            
            result = subprocess.run(
                command, 
                shell=True, 
                check=True, 
                capture_output=True, 
                text=True, 
                encoding='utf-8', 
                errors='ignore'
            )
            
            package_name = result.stdout.strip().split('\'')[1]
            self.result_signal.emit(f"包名: {package_name}")
            
        except subprocess.CalledProcessError as e:
            self.error_signal.emit(f"获取包名失败: {e}")
        except Exception as e:
            self.error_signal.emit(f"发生未知错误: {str(e)}")