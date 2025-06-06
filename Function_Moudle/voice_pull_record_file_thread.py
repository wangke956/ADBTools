from PyQt5.QtCore import QThread, pyqtSignal
import os

class VoicePullRecordFileThread(QThread):
    signal_voice_pull_record_file = pyqtSignal(str)

    def __init__(self, device_id, file_path):
        super().__init__()
        self.device_id = device_id
        self.record_file_path = file_path

    def run(self):
        if not os.path.exists(self.record_file_path):  # 判断路径是否存在
            try:
                os.makedirs(self.record_file_path)
                print(f"已创建目录: {self.record_file_path}")
            except OSError as e:
                print(f"创建目录时出现错误: {e}")
                return
        self.signal_voice_pull_record_file.emit('开始录音文件拉取...')
        command = f'start cmd /k "cd /d \"{self.record_file_path}\" && adb -s {self.device_id} pull /vr/speech/assistant/files/tmp/audioDump"'

        self.signal_voice_pull_record_file.emit(f'执行命令：{command}')
        try:
            os.system(command)
        except Exception as e:
            self.signal_voice_pull_record_file.emit(f'执行命令失败：{e}')
