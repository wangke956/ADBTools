from PyQt6.QtCore import QThread, pyqtSignal


class GetRunningAppInfoThread(QThread):
    progress_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, d):
        super().__init__()
        self.d = d
        # self.package_name = package_name
        self.current_app = None
        self.package_name = None

    def run(self):
        try:
            self.progress_signal.emit("正在获取应用信息...")
            self.current_app = self.d.app_current()
            self.progress_signal.emit("正在获取包名...")
            self.package_name = self.current_app['package']
            self.progress_signal.emit("正在获取应用版本信息...")
            app_info = self.d.app_info(self.package_name)
            if app_info:
                version_name = app_info.get('versionName', '未知版本')
                self.result_signal.emit(f"应用 {self.package_name} 版本号: {version_name}")
            else:
                self.error_signal.emit(f"应用 {self.package_name} 不存在")
        except Exception as e:
            self.error_signal.emit(str(e))