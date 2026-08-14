from PyQt6.QtCore import QThread, pyqtSignal


class MZS3E_TTEngineeringModeThread(QThread):
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, d):
        super().__init__()
        self.d = d

    def run(self):
        try:
            self.progress_signal.emit("开始进入MZS3E_TT工程模式...")
            self.d.app_start("com.saicmotor.diag", ".ui.main.MainActivity")
            self.progress_signal.emit("成功进入MZS3E_TT工程模式")
        except Exception as e:
            self.error_signal.emit(f"进入工程模式失败: {str(e)}")