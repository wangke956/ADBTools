from PyQt6.QtCore import QThread, pyqtSignal


class enter_engineering_mode_thread(QThread):
    progress_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, d):
        super().__init__()
        self.d = d

    def run(self):
        try:
            result = self.d.app_start("com.saicmotor.hmi.engmode",
                                      "com.saicmotor.hmi.engmode.home.ui.EngineeringModeActivity")
            self.result_signal.emit("页面正在打开，请稍等...", result)
            # print("enter_engineering_mode_thread")
        except Exception as e:
            self.error_signal.emit("打开页面失败，请检查设备连接是否正常。")
