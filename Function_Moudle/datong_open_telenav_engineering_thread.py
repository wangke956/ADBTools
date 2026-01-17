from PyQt5.QtCore import QThread, pyqtSignal


class DatongOpenTelenavEngineeringThread(QThread):
    progress_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, device_id):
        super().__init__()
        self.device_id = device_id

    def run(self):
        try:
            self.progress_signal.emit("正在打开泰维地图工程模式...")
            
            # 使用ADB命令启动泰维地图工程模式
            import subprocess
            command = f"adb -s {self.device_id} shell am start -n com.autonavi.minimap/.engineering.EngineeringActivity"
            result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            if result.returncode == 0:
                self.result_signal.emit("成功打开泰维地图工程模式")
            else:
                self.error_signal.emit(f"打开泰维地图工程模式失败: {result.stderr}")
        except Exception as e:
            self.error_signal.emit(f"打开泰维地图工程模式失败: {str(e)}")