from PyQt6.QtCore import QThread, pyqtSignal


class SwitchVrEnvThread(QThread):
    progress_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, d):
        super().__init__()
        self.d = d

    def run(self):
        try:
            self.d.app_start("com.saicmotor.voiceservice", 'com.saicmotor.voiceagent.VREngineModeActivity')
            # self.d.app_start("com.tencent.mm", ".ui.LauncherUI")
            self.result_signal.emit("页面正在打开，请稍等...")
        except Exception as e:
            self.error_signal.emit(str(e))