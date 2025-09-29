from PyQt5.QtCore import QThread, pyqtSignal

class DevicesScreenThread(QThread):
    signal = pyqtSignal(str)

    def __init__(self, d, file_path):
        super(DevicesScreenThread, self).__init__()
        self.d = d
        self.file_path = file_path

    def run(self):
        # 请使用uiautomator2中的screenshot()方法截取当前屏幕
        try:
            self.d.screenshot(f"{self.file_path}")
            self.signal.emit(f"已保存截图到：{self.file_path}")
        except Exception as e:
            self.signal.emit(f"截图失败！{e}")
