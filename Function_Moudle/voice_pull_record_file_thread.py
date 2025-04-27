from PyQt6.QtCore import QThread, pyqtSignal
import os

class VoicePullRecordFileThread(QThread):
    signal_voice_pull_record_file = pyqtSignal(str)

    def __init__(self, device_id, record_file_path):
        super().__init__()
        self.device_id = device_id
        self.record_file_path = record_file_path

    def run(self):
        self.signal_voice_pull_record_file.emit('开始录音文件拉取...')
        command = f'start cmd /k "adb -s {self.device_id} pull /vr/speech/assistant/files/tmp/audioDump {self.record_file_path}'
        res = os.system(command)
        self.signal_voice_pull_record_file.emit(f'录音文件拉取完成：{res.imag}')