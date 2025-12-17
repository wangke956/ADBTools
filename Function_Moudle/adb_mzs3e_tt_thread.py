from PyQt5.QtCore import QThread, pyqtSignal
import subprocess

class ADBMZS3E_TTEngineeringModeThread(QThread):
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, device_id):
        super().__init__()
        self.device_id = device_id

    def _check_app_installed(self, package_name):
        """检查应用是否已安装"""
        try:
            command = f"adb -s {self.device_id} shell pm list packages {package_name}"
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            
            # 确保stdout是字符串类型
            stdout = result.stdout
            if not isinstance(stdout, str):
                stdout = str(stdout) if stdout is not None else ""
            
            return package_name in stdout
        except Exception:
            return False

    def run(self):
        try:
            self.progress_signal.emit("开始进入MZS3E_TT工程模式...")
            
            # 检查com.saicmotor.diag应用是否安装
            if not self._check_app_installed("com.saicmotor.diag"):
                self.error_signal.emit("com.saicmotor.diag应用未安装，无法进入MZS3E_TT工程模式")
                return
            
            # 使用ADB命令启动应用
            command = f"adb -s {self.device_id} shell am start -n com.saicmotor.diag/.ui.main.MainActivity"
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.progress_signal.emit("成功进入MZS3E_TT工程模式")
            else:
                self.error_signal.emit(f"进入工程模式失败: {result.stderr}")
                
        except subprocess.CalledProcessError as e:
            self.error_signal.emit(f"进入工程模式失败: {str(e)}")
        except Exception as e:
            self.error_signal.emit(f"进入工程模式失败: {str(e)}")