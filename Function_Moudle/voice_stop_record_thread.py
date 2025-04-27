from PyQt6.QtCore import QThread, pyqtSignal
import subprocess

class VoiceStopRecordThread(QThread):
    voice_stop_record_signal = pyqtSignal(str)

    def __init__(self, device_id):
        super().__init__()
        self.device_id = device_id

    def run(self):
        command = f'adb -s {self.device_id} shell am broadcast -n com.microsoft.assistant.client/.VAExtendBroadcastReceiver --es cmd "DisableAudioDump"'
        # 执行这条指令
        res = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.voice_stop_record_signal.emit(f'录音启动成功：{res.stdout}')