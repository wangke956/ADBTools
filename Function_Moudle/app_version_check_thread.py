import time

from PyQt5.QtCore import QThread, pyqtSignal

class AppVersionCheckThread(QThread):
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    release_note_signal = pyqtSignal(dict)

    def __init__(self, d, releasenote_file):
        super().__init__()
        self.d = d
        self.releasenote_file = releasenote_file
        self.release_note_dict = {}

    def run(self):
        try:
            # 读取self.releasenote_file中指向的excel文件文件的的checkversion页B8单元格的值是否等于packageName
            import openpyxl
            wb = openpyxl.load_workbook(self.releasenote_file)
            ws = wb['checkversion']
            cell_value = ws['B8'].value
            # self.progress_signal.emit("单元格中的内容：", cell_value)
            if cell_value == "packageName":
                # 开始读取B9开始读取内容直到BN个为空则停止循环
                for i in range(9, 100):
                    time.sleep(0.1)
                    # self.progress_signal.emit(str(i))
                    packagename = ws.cell(row=i, column=2).value  # 获取到集成清单内的包名
                    version = ws.cell(row=i, column=4).value  # 获取到集成清单内的版本号
                    # 将packagename和version组合成字典的一对键值对添加到self.release_note_dict中
                    self.release_note_dict[packagename] = version
                    # self.progress_signal.emit(packagename)
                    # self.progress_signal.emit(version)
                    if packagename is None:
                        break
                self.release_note_signal.emit(self.release_note_dict)
            else:
                self.error_signal.emit("版本检查失败，请检查releasenote_file文件是否正确")
        except Exception as e:
            self.error_signal.emit(str(e))

