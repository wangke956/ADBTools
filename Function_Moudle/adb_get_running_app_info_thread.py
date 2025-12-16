from PyQt5.QtCore import QThread, pyqtSignal
from Function_Moudle.adb_utils import get_foreground_app_info, get_app_version

class ADBGetRunningAppInfoThread(QThread):
    progress_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, device_id):
        super().__init__()
        self.device_id = device_id

    def run(self):
        try:
            self.progress_signal.emit("正在获取应用信息...")
            
            # 获取前台应用信息
            success, app_info = get_foreground_app_info(self.device_id)
            if not success:
                self.error_signal.emit(app_info)
                return
            
            # 解析包名
            if "包名:" in app_info:
                package_name = app_info.split("包名: ")[1].split(",")[0].strip()
                
                self.progress_signal.emit("正在获取包名...")
                self.progress_signal.emit("正在获取应用版本信息...")
                
                # 获取应用版本信息
                version_success, version_info = get_app_version(self.device_id, package_name)
                if version_success:
                    self.result_signal.emit(f"应用 {package_name} 版本号: {version_info}")
                else:
                    self.error_signal.emit(f"应用 {package_name} 版本信息获取失败: {version_info}")
            else:
                self.error_signal.emit("无法解析前台应用信息")
                
        except Exception as e:
            self.error_signal.emit(f"获取运行应用信息失败: {str(e)}")