from PyQt6.QtCore import QThread, pyqtSignal
import uiautomator2 as u2

class VRActivationThread(QThread):
    progress_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, device_id):
        super().__init__()
        self.device_id = device_id

    def run(self):
        try:
            self.progress_signal.emit("开始激活VR...")
            d = u2.connect(self.device_id)
            d.shell('input keyevent 287')
            self.result_signal.emit("VR激活指令发送成功")
            self.finished_signal.emit("VR激活操作完成")
        except Exception as e:
            self.error_signal.emit(f"激活VR失败: {str(e)}")