from PyQt5.QtCore import QThread, pyqtSignal
import os
import time
from datetime import datetime
import psutil
import subprocess

class PullLogThread(QThread):
    progress_signal = pyqtSignal(int)
    error_signal = pyqtSignal(str)
    # cmd_process = pyqtSignal()

    def __init__(self, file_path, device_id):
        super().__init__()
        self.file_path = file_path
        self.device_id = device_id
        self.cmd_process = None

    def run(self):
        # 在file_path目录打开一个cmd窗口，执行adb -s device_id logcat > file_path/log.txt命令， 且用当前时间命名
        # 检查文件路径是否存在，如果不存在则创建
        if not os.path.exists(self.file_path):  # 判断路径是否存在
            try:
                os.makedirs(self.file_path)
                print(f"已创建目录: {self.file_path}")
            except OSError as e:
                print(f"创建目录时出现错误: {e}")
                return

        # 获取当前时间并格式化为字符串
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 构建日志文件的完整路径
        log_file = os.path.join(self.file_path, f"log_{current_time}.txt")
        print(f"日志文件路径: {self.file_path}")
        # print(f"日志文件名: {log_file}")
        # log_file = os.path.join(f'"{self.file_path}"', f"log_{current_time}.txt")
        
        # 构建要执行的命令，使用 start 命令在新窗口打开 cmd 并执行 adb 命令
        # command = f'start cmd /k "cd /d {self.file_path} && adb -s {self.device_id} logcat > {log_file}"'
        # command = f'start cmd /k "cd /d {self.file_path}" & cmd /c "adb -s {self.device_id} logcat > {log_file}"'
        command = f'start cmd /k "cd /d \"{self.file_path}\" && adb -s {self.device_id} logcat > {current_time}.txt"'
        try:
            # 执行命令
            print(f"完整命令: {command}")
            print(f"日志文件绝对路径: {log_file}")
            os.system(command)
            print(f"已在 {self.file_path} 目录下打开命令提示符窗口，并开始记录日志到 {log_file}")
        except Exception as e:
            print(f"执行命令时出现错误: {e}")

