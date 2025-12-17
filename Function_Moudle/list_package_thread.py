from PyQt5.QtCore import QThread, pyqtSignal
import queue
import re
import subprocess

class ListPackageThread(QThread):
    # 定义信号
    progress_signal = pyqtSignal(str)  # 用于发送进度信息
    result_signal = pyqtSignal(list)   # 用于发送批次处理结果
    finished_signal = pyqtSignal(str)  # 用于发送完成信息
    error_signal = pyqtSignal(str)     # 用于发送错误信息

    def __init__(self, device, findstr=''):
        super().__init__()
        self.device = device
        self.findstr = findstr
        self.is_running = True

    def stop(self):
        self.is_running = False

    def process_app_batch(self, apps_batch):
        batch_output = []
        for app in apps_batch:
            if not self.is_running:
                break
            try:
                app_info = self.device.app_info(app)
                version_name = app_info.get('versionName', '未知版本')
                batch_output.append(f"{app}, 版本号: {version_name}")
            except Exception as e:
                batch_output.append(f"获取应用 {app} 信息失败: {str(e)}")
        return batch_output

    def run(self):
        try:
            app_list = self.device.app_list(self.findstr)
            total_apps = len(app_list)

            if self.findstr:
                self.progress_signal.emit(f"设备上共有 {total_apps} 个应用，包含关键字 {self.findstr}")
            else:
                self.progress_signal.emit(f"设备上共有 {total_apps} 个应用")
            self.progress_signal.emit("正在获取应用信息...")

            # 使用队列来管理输出，避免内存占用过大
            batch_size = 100  # 每批处理100个应用
            current_batch = []

            for i, app in enumerate(app_list):
                if not self.is_running:
                    break

                current_batch.append(app)

                if len(current_batch) >= batch_size or i == len(app_list) - 1:
                    # 处理当前批次
                    batch_results = self.process_app_batch(current_batch)
                    self.result_signal.emit(batch_results)

                    # 更新进度
                    progress = (i + 1) / total_apps * 100
                    self.progress_signal.emit(f"处理进度: {progress:.1f}% ({i + 1}/{total_apps})")

                    # 清空当前批次
                    current_batch = []

            if self.is_running:
                self.finished_signal.emit(f"\n完成! 共处理 {total_apps} 个应用")

        except Exception as e:
            self.error_signal.emit(f"获取应用列表失败: {e}")