from PyQt5.QtCore import QThread, pyqtSignal
import subprocess

class ADBClearAppCacheThread(QThread):
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, device_id, package_name=None):
        super().__init__()
        self.device_id = device_id
        self.package_name = package_name

    def run(self):
        try:
            if not self.package_name:
                # 获取当前前台应用
                from Function_Moudle.adb_utils import get_foreground_app_info
                success, app_info = get_foreground_app_info(self.device_id)
                if not success:
                    self.error_signal.emit(f"获取前台应用失败: {app_info}")
                    return
                
                # 解析包名
                if "包名:" in app_info:
                    self.package_name = app_info.split("包名: ")[1].split(",")[0].strip()
                else:
                    self.error_signal.emit("无法解析当前应用包名")
                    return
            
            # 检查设备连接
            from Function_Moudle.adb_utils import check_device_connection
            is_connected, error_msg = check_device_connection(self.device_id)
            if not is_connected:
                self.error_signal.emit(error_msg)
                return
            
            # 清除应用缓存
            command = f"adb -s {self.device_id} shell pm clear {self.package_name}"
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.progress_signal.emit("清除应用缓存成功！")
            else:
                self.error_signal.emit(f"清除应用缓存失败: {result.stderr}")
                
        except subprocess.CalledProcessError as e:
            self.error_signal.emit(str(e))
        except Exception as e:
            self.error_signal.emit(str(e))