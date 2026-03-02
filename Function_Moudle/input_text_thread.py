from PyQt5.QtCore import QThread, pyqtSignal
import subprocess

class InputTextThread(QThread):
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, d, text_to_input):
        super().__init__()
        self.d = d
        self.text = str(text_to_input)


    def run(self):
        try:
            # 检查设备是否有效
            if not self.d:
                self.error_signal.emit("设备对象无效")
                return
                
            # 获取设备ID
            device_id = None
            if hasattr(self.d, 'serial'):
                device_id = self.d.serial
            elif hasattr(self.d, 'device_id'):
                device_id = self.d.device_id
            elif isinstance(self.d, str):
                device_id = self.d
                
            if not device_id:
                self.error_signal.emit("无法获取设备ID")
                return
            
            # 构建带设备ID的ADB命令
            adb_cmd = ["adb", "-s", device_id, "shell", "input", "text", str(self.text)]
            
            result = subprocess.run(
                adb_cmd,
                capture_output=True,
                text=True,
                check=False  # 不抛出异常，手动检查返回码
            )
            
            if result.returncode == 0:
                self.progress_signal.emit(f"文本输入成功到设备 {device_id}: {self.text}")
            else:
                error_msg = f"ADB命令执行失败: {result.stderr}"
                self.error_signal.emit(error_msg)
                print(f"ADB错误: {error_msg}")
        except Exception as e:
            error_msg = f"执行ADB命令时发生异常: {str(e)}"
            self.error_signal.emit(error_msg)
            print(f"异常: {error_msg}")