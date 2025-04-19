from PyQt5.QtCore import QThread, pyqtSignal


class AppActionThread(QThread):
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, d, package_name, activity_name):
        super().__init__()
        self.d = d
        self.package_name = package_name
        self.activity_name = activity_name

    def run(self):
        try:
            self.progress_signal.emit("正在启动应用程序...")
            self.d.app_start(self.package_name, self.activity_name)
            # self.d.app_start("com.tencent.mm", ".ui.LauncherUI")
            self.progress_signal.emit("应用启动成功")
        except Exception as e:
            self.error_signal.emit(f"应用启动失败: {str(e)}")