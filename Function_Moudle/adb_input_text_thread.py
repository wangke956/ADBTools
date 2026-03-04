from PyQt5.QtCore import QThread, pyqtSignal
import sys
import os

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 明确从根目录导入adb_utils模块
import adb_utils as adb_utils_module


class ADBInputTextThread(QThread):
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, device_id, text_to_input):
        super().__init__()
        self.device_id = device_id
        self.text = str(text_to_input)

    def run(self):
        try:
            if not self.device_id:
                self.error_signal.emit("设备ID无效")
                return
            
            if not self.text:
                self.error_signal.emit("文本内容为空")
                return
            
            # 使用adb_utils模块的全局实例执行ADB命令
            result = adb_utils_module.adb_utils.run_adb_command(f"shell input text {self.text}", self.device_id)
            
            if result.returncode == 0:
                self.progress_signal.emit(f"文本输入成功到设备 {self.device_id}: {self.text}")
            else:
                error_msg = f"文本输入失败: {result.stderr}"
                if not error_msg.strip():
                    error_msg = f"文本输入失败，返回码: {result.returncode}"
                self.error_signal.emit(error_msg)
                
        except Exception as e:
            error_msg = f"执行ADB命令时发生异常: {str(e)}"
            self.error_signal.emit(error_msg)