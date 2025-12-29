from PyQt5.QtCore import QThread, pyqtSignal
import subprocess
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from adb_utils import adb_utils
except ImportError:
    # 如果导入失败，创建简单的回退
    class ADBUtilsFallback:
        @staticmethod
        def run_adb_command(command, device_id=None, **kwargs):
            adb_cmd = "adb"
            if device_id:
                full_command = f'{adb_cmd} -s {device_id} {command}'
            else:
                full_command = f'{adb_cmd} {command}'
            
            default_kwargs = {
                'shell': True,
                'capture_output': True,
                'text': True,
                'encoding': 'utf-8',
                'errors': 'ignore'
            }
            default_kwargs.update(kwargs)
            
            return subprocess.run(full_command, **default_kwargs)
    
    adb_utils = ADBUtilsFallback()


class ADBVerityThread(QThread):
    """执行adb enable-verity和adb disable-verity命令的线程"""
    
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)

    def __init__(self, device_id, connection_mode='adb', u2_device=None):
        """
        初始化线程
        
        Args:
            device_id: 设备ID
            connection_mode: 连接模式 ('u2' 或 'adb')
            u2_device: u2设备对象（仅当connection_mode='u2'时使用）
        """
        super(ADBVerityThread, self).__init__()
        self.device_id = device_id
        self.connection_mode = connection_mode
        self.u2_device = u2_device

    def _execute_adb_command(self, command):
        """执行ADB命令"""
        try:
            result = adb_utils.run_adb_command(command, self.device_id)
            return result
        except Exception as e:
            self.error_signal.emit(f"执行ADB命令失败: {str(e)}")
            return None

    def _execute_u2_command(self, command):
        """通过u2执行命令"""
        try:
            # u2模式下，使用shell命令执行
            result = self.u2_device.shell(command)
            return result
        except Exception as e:
            self.error_signal.emit(f"执行u2命令失败: {str(e)}")
            return None

    def _execute_command(self, command):
        """根据连接模式执行命令"""
        if self.connection_mode == 'u2' and self.u2_device:
            return self._execute_u2_command(command)
        else:
            return self._execute_adb_command(command)

    def _check_verity_status(self):
        """检查当前verity状态"""
        try:
            self.progress_signal.emit("正在检查当前verity状态...")
            
            # 执行adb shell getprop ro.boot.veritymode 命令
            result = self._execute_command("shell getprop ro.boot.veritymode")
            
            if result is None:
                self.error_signal.emit("检查verity状态失败")
                return None
            
            if self.connection_mode == 'u2':
                # u2模式返回的是字符串
                output = str(result).strip() if result else ""
            else:
                # adb模式返回的是subprocess.CompletedProcess对象
                output = result.stdout.strip() if hasattr(result, 'stdout') else str(result).strip()
            
            self.progress_signal.emit(f"当前verity状态: {output}")
            return output
        except Exception as e:
            self.error_signal.emit(f"检查verity状态失败: {str(e)}")
            return None

    def _execute_verity_commands(self):
        """执行verity命令序列"""
        try:
            # 1. 执行adb enable-verity
            self.progress_signal.emit("正在执行adb enable-verity...")
            enable_result = self._execute_command("enable-verity")
            
            if enable_result is None:
                self.error_signal.emit("执行adb enable-verity失败")
                return False
            
            if self.connection_mode == 'u2':
                enable_output = str(enable_result)
            else:
                enable_output = enable_result.stdout.strip() if hasattr(enable_result, 'stdout') else str(enable_result)
            
            self.progress_signal.emit(f"adb enable-verity执行结果: {enable_output}")

            # 2. 先执行adb disable-verity
            self.progress_signal.emit("正在执行adb disable-verity...")
            disable_result = self._execute_command("disable-verity")

            if disable_result is None:
                self.error_signal.emit("执行adb disable-verity失败")
                return False

            if self.connection_mode == 'u2':
                disable_output = str(disable_result)
            else:
                disable_output = disable_result.stdout.strip() if hasattr(disable_result, 'stdout') else str(
                    disable_result)

            self.progress_signal.emit(f"adb disable-verity执行结果: {disable_output}")
            
            return True
        except Exception as e:
            self.error_signal.emit(f"执行verity命令失败: {str(e)}")
            return False

    def run(self):
        """线程主函数"""
        try:
            self.progress_signal.emit("开始执行verity命令序列...")
            
            # 检查当前状态
            current_status = self._check_verity_status()
            
            # 执行verity命令序列
            success = self._execute_verity_commands()
            
            if success:
                # 再次检查状态
                new_status = self._check_verity_status()
                
                if current_status is not None and new_status is not None:
                    self.result_signal.emit(f"verity命令执行完成！\n原状态: {current_status}\n新状态: {new_status}")
                else:
                    self.result_signal.emit("verity命令执行完成！")
            else:
                self.error_signal.emit("verity命令执行失败")
                
        except Exception as e:
            self.error_signal.emit(f"执行verity命令时发生错误: {str(e)}")


class ADBDisableVerityThread(QThread):
    """仅执行adb disable-verity命令的线程"""
    
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)

    def __init__(self, device_id, connection_mode='adb', u2_device=None):
        super(ADBDisableVerityThread, self).__init__()
        self.device_id = device_id
        self.connection_mode = connection_mode
        self.u2_device = u2_device

    def _execute_command(self, command):
        """执行命令"""
        try:
            if self.connection_mode == 'u2' and self.u2_device:
                result = self.u2_device.shell(command)
                return result
            else:
                result = adb_utils.run_adb_command(command, self.device_id)
                return result
        except Exception as e:
            self.error_signal.emit(f"执行命令失败: {str(e)}")
            return None

    def run(self):
        """线程主函数"""
        try:
            self.progress_signal.emit("正在执行adb disable-verity...")
            
            result = self._execute_command("disable-verity")
            
            if result is None:
                self.error_signal.emit("执行adb disable-verity失败")
                return
            
            if self.connection_mode == 'u2':
                output = str(result)
            else:
                output = result.stdout.strip() if hasattr(result, 'stdout') else str(result)
            
            self.result_signal.emit(f"adb disable-verity执行完成！\n执行结果: {output}")
            
        except Exception as e:
            self.error_signal.emit(f"执行adb disable-verity时发生错误: {str(e)}")


class ADBEnableVerityThread(QThread):
    """仅执行adb enable-verity命令的线程"""
    
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)

    def __init__(self, device_id, connection_mode='adb', u2_device=None):
        super(ADBEnableVerityThread, self).__init__()
        self.device_id = device_id
        self.connection_mode = connection_mode
        self.u2_device = u2_device

    def _execute_command(self, command):
        """执行命令"""
        try:
            if self.connection_mode == 'u2' and self.u2_device:
                result = self.u2_device.shell(command)
                return result
            else:
                result = adb_utils.run_adb_command(command, self.device_id)
                return result
        except Exception as e:
            self.error_signal.emit(f"执行命令失败: {str(e)}")
            return None

    def run(self):
        """线程主函数"""
        try:
            self.progress_signal.emit("正在执行adb enable-verity...")
            
            result = self._execute_command("enable-verity")
            
            if result is None:
                self.error_signal.emit("执行adb enable-verity失败")
                return
            
            if self.connection_mode == 'u2':
                output = str(result)
            else:
                output = result.stdout.strip() if hasattr(result, 'stdout') else str(result)
            
            self.result_signal.emit(f"adb enable-verity执行完成！\n执行结果: {output}")
            
        except Exception as e:
            self.error_signal.emit(f"执行adb enable-verity时发生错误: {str(e)}")