from PyQt5.QtCore import QThread, pyqtSignal
import subprocess
import sys
import os

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from adb_utils import ADBUtils
except ImportError:
    # 如果直接导入失败，尝试相对导入
    import importlib.util
    spec = importlib.util.spec_from_file_location("adb_utils", os.path.join(project_root, "adb_utils.py"))
    adb_utils_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adb_utils_module)
    ADBUtils = adb_utils_module.ADBUtils


class DatongInputPasswordThread(QThread):
    """大通页面一键输入密码线程"""
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)

    def __init__(self, device_id, password="Kfs73p940a", connection_mode='adb', u2_device=None):
        """
        初始化密码输入线程
        
        Args:
            device_id: 设备ID
            password: 要输入的密码，默认为Kfs73p940a
            connection_mode: 连接模式，'adb'或'u2'
            u2_device: u2设备对象（仅当connection_mode='u2'时使用）
        """
        super().__init__()
        self.device_id = device_id
        self.password = password
        self.connection_mode = connection_mode
        self.u2_device = u2_device

    def run(self):
        """执行密码输入操作"""
        try:
            self.progress_signal.emit(f"开始输入密码到设备: {self.device_id}")
            
            if self.connection_mode == 'u2' and self.u2_device:
                # 使用uiautomator2方式输入
                self._input_via_u2()
            else:
                # 使用ADB命令方式输入
                self._input_via_adb()
                
            self.result_signal.emit(f"密码输入完成: {self.password}")
            
        except Exception as e:
            self.error_signal.emit(f"密码输入失败: {str(e)}")

    def _input_via_adb(self):
        """通过ADB命令输入密码"""
        try:
            # 构建ADB命令
            command = f"shell input text {self.password}"
            
            # 使用项目统一的ADB工具类执行命令
            result = ADBUtils.run_adb_command(
                command=command,
                device_id=self.device_id,
                timeout=10
            )
            
            if result.returncode == 0:
                self.progress_signal.emit(f"ADB命令执行成功: {command}")
                if result.stdout:
                    self.progress_signal.emit(f"输出: {result.stdout}")
            else:
                error_msg = f"ADB命令执行失败: {result.stderr}"
                self.error_signal.emit(error_msg)
                
        except subprocess.TimeoutExpired:
            self.error_signal.emit("ADB命令执行超时")
        except Exception as e:
            self.error_signal.emit(f"ADB命令执行异常: {str(e)}")

    def _input_via_u2(self):
        """通过uiautomator2输入密码"""
        try:
            # 使用u2的send_keys方法输入文本
            self.u2_device.send_keys(self.password)
            self.progress_signal.emit(f"通过u2输入密码: {self.password}")
        except Exception as e:
            # 如果u2方式失败，回退到ADB方式
            self.progress_signal.emit(f"u2输入失败，尝试ADB方式: {str(e)}")
            self._input_via_adb()