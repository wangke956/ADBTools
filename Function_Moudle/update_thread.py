from PyQt6.QtCore import QThread, pyqtSignal
import uiautomator2 as u2


class UpdateThread(QThread):
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, d):
        super().__init__()
        self.d = d

    def run(self):

        try:
            self.progress_signal.emit("正在尝试启动更新页面...")
            self.d.app_start("com.saicmotor.update", ".view.MainActivity")
            self.progress_signal.emit(f"启动更新页面成功！")
        except Exception as e:
            self.error_signal.emit(f"更新页面启动失败: {str(e)}")
