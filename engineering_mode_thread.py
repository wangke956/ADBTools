from PyQt5.QtCore import QThread, pyqtSignal


class EngineeringModeThread(QThread):
    progress_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, d):
        super().__init__()
        self.d = d

    def run(self):
        try:
            self.progress_signal.emit("开始进入AS33_CR工程模式...")
            self.d.app_start("com.saicmotor.diag", "com.saicmotor.diag.view.LogMenuActivity")
            # self.d.app_start("com.tencent.mm", ".ui.LauncherUI")
            self.result_signal.emit("成功进入AS33_CR工程模式")
        except Exception as e:
            self.error_signal.emit(f"进入工程模式失败: {str(e)}")
