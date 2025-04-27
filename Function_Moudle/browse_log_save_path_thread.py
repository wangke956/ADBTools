from PyQt6.QtCore import QThread, pyqtSignal
import subprocess
import datetime
import os
import time

class PullLogSaveThread(QThread):
    progress_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, d, device_id, file_path):
        super().__init__()
        self.d = d
        self.device_id = device_id
        self.file_path = file_path
        self.is_running = True
        self.process = None

    def run(self):
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(self.file_path, f"logcat_{timestamp}.txt")
            self.progress_signal.emit(f"开始拉取日志，保存到：{log_file}")
            self.process = subprocess.Popen(["adb", "-s", self.device_id, "logcat"], 
                                           stdout=subprocess.PIPE, 
                                           stderr=subprocess.PIPE, 
                                           text=True, 
                                           encoding="utf-8", 
                                           errors="replace")
            
            with open(log_file, "w", encoding="utf-8", errors="replace") as f:
                while self.is_running and self.process.poll() is None:
                    try:
                        line = self.process.stdout.readline()
                        if line:
                            f.write(line)
                            f.flush()
                    except Exception as line_error:
                        f.write(f"[ERROR] 读取日志行出错: {str(line_error)}\n")
                        f.flush()
                        time.sleep(0.1)  # 避免CPU占用过高
                        
            # 确保进程已终止并记录最终状态
            if self.process and self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=2)  # 等待进程终止，最多2秒
                except subprocess.TimeoutExpired:
                    self.process.kill()  # 如果terminate后仍未结束，强制kill
                    
            self.progress_signal.emit("日志拉取已停止并保存")
            self.result_signal.emit(f"日志已保存到: {log_file}")
            
        except Exception as e:
            self.error_signal.emit(f"日志拉取过程中发生错误: {str(e)}")
            # 尝试关闭可能仍在运行的进程
            if self.process and self.process.poll() is None:
                try:
                    self.process.kill()
                except:
                    pass

    def stop(self):
        self.is_running = False
        self.progress_signal.emit("正在停止日志拉取...")
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                try:
                    self.process.wait(timeout=2)  # 等待进程终止，最多2秒
                except subprocess.TimeoutExpired:
                    self.process.kill()  # 如果terminate后仍未结束，强制kill
            except Exception as e:
                self.error_signal.emit(f"停止日志进程时出错: {str(e)}")

