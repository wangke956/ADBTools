from PyQt5.QtCore import QThread, pyqtSignal
import subprocess


class SkipPowerLimitThread(QThread):
    """跳过电源挡位限制线程 - 支持U2和ADB两种模式"""
    
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)
    
    def __init__(self, device_id=None, connection_mode='adb', u2_device=None):
        """
        初始化线程
        
        Args:
            device_id: 设备ID（ADB模式使用）
            connection_mode: 连接模式 ('u2' 或 'adb')
            u2_device: U2设备对象（仅当connection_mode='u2'时使用）
        """
        super().__init__()
        self.device_id = device_id
        self.connection_mode = connection_mode
        self.u2_device = u2_device
    
    def run(self):
        """执行跳过电源挡位限制操作"""
        try:
            # 检查设备连接是否有效
            if self.connection_mode == 'u2':
                if not self.u2_device:
                    self.error_signal.emit("U2设备连接无效，无法跳过电源限制")
                    return
            elif self.connection_mode == 'adb':
                if not self.device_id:
                    self.error_signal.emit("设备ID无效，无法跳过电源限制")
                    return
            else:
                self.error_signal.emit(f"不支持的连接模式: {self.connection_mode}")
                return
            
            command = 'setprop persist.update.enable 1'
            
            if self.connection_mode == 'u2' and self.u2_device:
                # U2模式执行命令
                self._execute_u2(command)
            elif self.connection_mode == 'adb':
                # ADB模式执行命令
                self._execute_adb(command)
                
        except Exception as e:
            self.error_signal.emit(f'跳过电源限制失败：{str(e)}')
    
    def _execute_u2(self, command):
        """U2模式下执行命令"""
        try:
            self.progress_signal.emit(f"执行命令: u2 shell {command}")
            
            res = self.u2_device.shell(command)
            
            # 处理不同格式的返回值
            if hasattr(res, 'exit_code'):
                # uiautomator2 新版本返回对象
                exit_code = res.exit_code
                output = str(res.output).strip() if hasattr(res, 'output') else ""
            else:
                # 旧版本或其他情况
                exit_code = 0
                output = str(res).strip() if res else ""
            
            if exit_code == 0 or not output:
                success_msg = '跳过电源挡位限制成功！（U2模式）'
                self.result_signal.emit(success_msg)  # 只发送到result_signal，避免重复
            else:
                error_msg = f'命令执行失败: {output}'
                self.error_signal.emit(error_msg)
                
        except Exception as e:
            self.error_signal.emit(f'U2模式执行失败：{str(e)}')
    
    def _execute_adb(self, command):
        """ADB模式下执行命令"""
        try:
            adb_command = f'adb -s {self.device_id} shell {command}'
            self.progress_signal.emit(f"执行命令: {adb_command}")
            
            res = subprocess.run(
                adb_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if res.returncode == 0:
                success_msg = '跳过电源挡位限制成功！（ADB模式）'
                self.result_signal.emit(success_msg)  # 只发送到result_signal，避免重复
            else:
                error_msg = res.stderr.strip() if res.stderr else '未知错误'
                self.error_signal.emit(f'命令执行失败：{error_msg}')
                
        except subprocess.TimeoutExpired:
            self.error_signal.emit('命令执行超时')
        except Exception as e:
            self.error_signal.emit(f'ADB模式执行失败：{str(e)}')
