from PyQt6.QtCore import QThread, pyqtSignal


class CheckVRNetworkThread(QThread):
    progress_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, d):
        super().__init__()
        self.d = d

    def run(self):
        try:
            self.progress_signal.emit("页面正在打开...")
            # result = self.d.shell('am start -n com.microsoft.assistant.client/com.microsoft.assistant.client.MainActivity')
            result = self.d.app_start("com.microsoft.assistant.client", "com.microsoft.assistant.client.MainActivity")
            # result = self.d.app_start("com.tencent.mm", ".ui.LauncherUI")
            if result:
                self.result_signal.emit("页面打开成功!")
            else:
                self.error_signal.emit("页面打开失败!")
        except Exception as e:
            self.error_signal.emit(str(e))