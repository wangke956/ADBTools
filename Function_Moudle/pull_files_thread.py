from PyQt5.QtCore import QThread, pyqtSignal

class PullFilesThread(QThread):
    signal = pyqtSignal(str)

    def __init__(self, d, device_files_path, local_files_path, apk_file_name):
        super(PullFilesThread, self).__init__()
        self.d = d
        self.apk_file_name = apk_file_name
        self.device_files_path = device_files_path
        self.local_files_path = local_files_path + "/" + apk_file_name

    def run(self):
        try:
            # 检查设备连接是否有效
            if self.d is None:
                self.signal.emit("设备连接无效，无法拉取文件")
                return
            
            self.d.pull(self.device_files_path, self.local_files_path)
            self.signal.emit(self.device_files_path)
            self.signal.emit(self.local_files_path)
            self.signal.emit("拉取文件完成!")
        except Exception as e:
            self.signal.emit("Pull files failed! Error: " + str(e))