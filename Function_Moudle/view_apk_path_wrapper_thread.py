from PyQt5.QtCore import QThread, pyqtSignal
import subprocess

class ViewApkPathWrapperThread(QThread):
    progress_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, device_id, package_name):
        super().__init__()
        self.device_id = device_id
        self.package_name = package_name

    def run(self):
        try:
            self.progress_signal.emit("正在查询应用安装路径...")
            result = subprocess.run(
                f'adb -s {self.device_id} shell pm path {self.package_name}',
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                # 安全解析路径，避免索引越界
                output = result.stdout.strip()
                if 'package:' in output:
                    parts = output.split('package:')
                    if len(parts) > 1 and parts[1].strip():
                        path = parts[1].strip()
                        self.result_signal.emit(f"应用安装路径: {path}")
                    else:
                        self.error_signal.emit("无法解析应用路径")
                else:
                    self.error_signal.emit(f"未找到应用 {self.package_name} 的安装路径，可能应用未安装")
            else:
                error_msg = result.stderr.strip() if result.stderr else "未知错误"
                self.error_signal.emit(f"查询失败: {error_msg}")
        except subprocess.TimeoutExpired:
            self.error_signal.emit("ADB命令执行超时")
        except Exception as e:
            self.error_signal.emit(f"发生未知错误: {str(e)}")