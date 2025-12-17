from PyQt5.QtCore import QThread, pyqtSignal
import os


class RemoveRecordFileThread(QThread):

    signal_remove_voice_record_file = pyqtSignal(str)

    def __init__(self, d, device_record_file_path):
        super().__init__()
        self.d = d
        self.device_record_file_path = device_record_file_path

    def run(self):
        try:
            self.signal_remove_voice_record_file.emit('正在删除录音文件...')
            # command = f'start cmd /k "adb -s {self.device_id}shell rm -rf /vr/speech/assistant/files/tmp/audioDump"'
            res = self.d.shell(f'rm -rf {self.device_record_file_path}')
            self.signal_remove_voice_record_file.emit(f'删除录音文件命令执行结果：{res}')
            # os.system(command)
            self.signal_remove_voice_record_file.emit('录音文件删除成功！')
        except Exception as e:
            self.signal_remove_voice_record_file.emit(f'删除录音文件失败！{e}')



