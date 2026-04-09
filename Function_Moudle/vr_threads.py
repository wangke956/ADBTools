from PyQt5.QtCore import pyqtSignal
from .base_thread import DeviceBaseThread
from logger_manager import log_operation, log_device_operation
import subprocess


class SwitchVREnvThread(DeviceBaseThread):
    """切换VR环境线程"""
    
    def __init__(self, device_id, env_type):
        super().__init__(device_id, "SwitchVREnvThread")
        self.env_type = env_type
        
    def _run_implementation(self):
        """执行切换VR环境操作"""
        self.progress_signal.emit(f"正在切换到{self.env_type}环境...")
        
        try:
            from adb_utils import ADBUtils
            
            # 根据环境类型执行不同的命令
            if self.env_type == "开发环境":
                command = "shell setprop vr.debug.mode 1"
            elif self.env_type == "测试环境":
                command = "shell setprop vr.debug.mode 2"
            elif self.env_type == "生产环境":
                command = "shell setprop vr.debug.mode 0"
            else:
                self.error_signal.emit(f"未知的VR环境类型: {self.env_type}")
                return
                
            result = ADBUtils.run_adb_command(
                command=command,
                device_id=self.device_id,
                timeout=10
            )
            
            if result.returncode == 0:
                self.progress_signal.emit(f"已切换到{self.env_type}")
                self.success_signal.emit("VR环境切换成功")
            else:
                self.error_signal.emit(f"切换VR环境失败: {result.stderr}")
                
        except Exception as e:
            self.error_signal.emit(f"切换VR环境时发生错误: {str(e)}")


class CheckVRNetworkThread(DeviceBaseThread):
    """检查VR网络线程"""
    
    network_signal = pyqtSignal(dict)
    
    def __init__(self, device_id):
        super().__init__(device_id, "CheckVRNetworkThread")
        
    def _run_implementation(self):
        """执行检查VR网络操作"""
        self.progress_signal.emit("正在检查VR网络状态...")
        
        try:
            from adb_utils import ADBUtils
            
            # 检查网络连接状态
            result = ADBUtils.run_adb_command(
                command="shell ping -c 3 8.8.8.8",
                device_id=self.device_id,
                timeout=15
            )
            
            network_info = {
                'status': 'success' if result.returncode == 0 else 'failed',
                'output': result.stdout,
                'error': result.stderr
            }
            
            if result.returncode == 0:
                self.progress_signal.emit("VR网络连接正常")
            else:
                self.progress_signal.emit("VR网络连接异常")
                
            self.network_signal.emit(network_info)
            self.success_signal.emit("VR网络检查完成")
            
        except Exception as e:
            self.error_signal.emit(f"检查VR网络时发生错误: {str(e)}")
            self.network_signal.emit({'status': 'error', 'error': str(e)})


class ActivateVRThread(DeviceBaseThread):
    """激活VR线程"""
    
    def __init__(self, device_id):
        super().__init__(device_id, "ActivateVRThread")
        
    def _run_implementation(self):
        """执行激活VR操作"""
        self.progress_signal.emit("正在激活VR功能...")
        
        try:
            from adb_utils import ADBUtils
            
            # 执行激活VR命令
            result = ADBUtils.run_adb_command(
                command="shell am start -n com.htc.vr/.VREnterActivity",
                device_id=self.device_id,
                timeout=15
            )
            
            if result.returncode == 0:
                self.progress_signal.emit("VR功能已激活")
                self.success_signal.emit("VR激活成功")
            else:
                self.error_signal.emit(f"激活VR失败: {result.stderr}")
                
        except Exception as e:
            self.error_signal.emit(f"激活VR时发生错误: {str(e)}")


class SetVRTimeoutThread(DeviceBaseThread):
    """设置VR超时线程"""
    
    def __init__(self, device_id, timeout_seconds):
        super().__init__(device_id, "SetVRTimeoutThread")
        self.timeout_seconds = timeout_seconds
        
    def _run_implementation(self):
        """执行设置VR超时操作"""
        self.progress_signal.emit(f"正在设置VR超时时间为 {self.timeout_seconds} 秒...")
        
        try:
            from adb_utils import ADBUtils
            
            # 设置VR超时时间
            result = ADBUtils.run_adb_command(
                command=f"shell setprop vr.timeout {self.timeout_seconds}",
                device_id=self.device_id,
                timeout=10
            )
            
            if result.returncode == 0:
                self.progress_signal.emit(f"VR超时时间已设置为 {self.timeout_seconds} 秒")
                self.success_signal.emit("VR超时设置成功")
            else:
                self.error_signal.emit(f"设置VR超时失败: {result.stderr}")
                
        except Exception as e:
            self.error_signal.emit(f"设置VR超时时间时发生错误: {str(e)}")


class SkipPowerLimitThread(DeviceBaseThread):
    """跳过电源限制线程"""
    
    def __init__(self, device_id):
        super().__init__(device_id, "SkipPowerLimitThread")
        
    def _run_implementation(self):
        """执行跳过电源限制操作"""
        self.progress_signal.emit("正在跳过电源挡位限制...")
        
        try:
            from adb_utils import ADBUtils
            
            # 执行跳过电源限制命令
            result = ADBUtils.run_adb_command(
                command="shell setprop vr.power.limit.skip 1",
                device_id=self.device_id,
                timeout=10
            )
            
            if result.returncode == 0:
                self.progress_signal.emit("电源挡位限制已跳过")
                self.success_signal.emit("跳过电源限制成功")
            else:
                self.error_signal.emit(f"跳过电源限制失败: {result.stderr}")
                
        except Exception as e:
            self.error_signal.emit(f"跳过电源限制时发生错误: {str(e)}")
