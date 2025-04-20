from PyQt5.QtCore import QThread, pyqtSignal
import uiautomator2 as u2

class AS33UpgradePageThread(QThread):
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, d):
        super().__init__()
        self.d = d

    def run(self):
        try:
            self.progress_signal.emit("正在尝试打开延峰升级页面...")
            # result = self.d.shell('am start com.yfve.usbupdate/.MainActivity')
            # result = self.d.app_start('com.yfve.usbupdate', '.MainActivity', timeout=10)
            result = self.d.app_start("com.tencent.mm", ".ui.LauncherUI")
            if result.exit_code == 0:
                self.progress_signal.emit("延峰升级页面打开成功！")
            else:
                self.error_signal.emit(f"页面打开失败: {result.output}")
        except Exception as e:
            self.error_signal.emit(f"执行异常: {str(e)}")