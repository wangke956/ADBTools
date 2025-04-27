from PyQt6.QtCore import QThread, pyqtSignal


class AS33UpgradePageThread(QThread):
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, d):
        super().__init__()
        self.d = d

    def run(self):
        try:
            self.progress_signal.emit("正在尝试打开延峰升级页面...")
            # self.d.shell('am start com.yfve.usbupdate/.MainActivity')
            self.d.app_start('com.yfve.usbupdate', '.MainActivity')
            # self.d.app_start("com.tencent.mm", ".ui.LauncherUI")
            self.progress_signal.emit("延峰升级页面打开成功！")
        except Exception as e:
            self.error_signal.emit(f"执行异常: {str(e)}")