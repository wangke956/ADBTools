from PyQt5.QtCore import QThread, pyqtSignal

class SetVrTimeoutThread(QThread):
    signal_timeout = pyqtSignal(str)

    def __init__(self, d):
        super().__init__()
        self.d = d


    def run(self):
        try:
            res = self.d.shell("am broadcast -n com.microsoft.assistant.client/.VAExtendBroadcastReceiver --es cmd 'SetOnlineTimeout:10000'")
            self.signal_timeout.emit(f"命令已执行{res}")
        except Exception as e:
            self.signal_timeout.emit(f"命令执行失败{e}")
