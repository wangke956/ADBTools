from PyQt5.QtCore import QThread, pyqtSignal


class GetForegroundPackageThread(QThread):
    signal_package = pyqtSignal(str)

    def __init__(self, d):
        super().__init__()
        self.d = d

    def run(self):
        current_app = self.d.app_current()  # 获取当前正在运行的应用
        if current_app:
            package_name = current_app['package']
            activity_name = current_app['activity']
            self.signal_package.emit(f"包名: {package_name}, 活动名: {activity_name}")
        else:
            self.signal_package.emit("当前没有正在运行的应用")