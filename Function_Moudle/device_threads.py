from PyQt5.QtCore import pyqtSignal
from .base_thread import BaseThread, DeviceBaseThread
from logger_manager import log_device_operation, log_operation, measure_performance
import subprocess
import time
import uiautomator2 as u2

# 确保 Nuitka 兼容性
from nuitka_compat import ensure_nuitka_compatibility
ensure_nuitka_compatibility()


class RefreshDevicesThread(BaseThread):
    """刷新设备列表线程"""
    
    devices_signal = pyqtSignal(list)  # 发送设备列表
    
    def __init__(self):
        super().__init__("RefreshDevicesThread")
        
    def _run_implementation(self):
        """执行刷新设备列表操作"""
        self.progress_signal.emit("开始刷新设备列表...")
        
        from adb_utils import ADBUtils
        
        try:
            # 使用性能监控
            with measure_performance("refresh_devices"):
                # 执行 ADB 命令获取设备列表
                result = ADBUtils.run_adb_command(
                    command="devices",
                    timeout=10
                )
                
                if result.returncode != 0:
                    error_msg = f"ADB命令执行失败: {result.stderr}"
                    self.error_signal.emit(error_msg)
                    self.devices_signal.emit([])
                    return
                
                # 解析设备列表
                output = result.stdout.strip()
                if not output:
                    self.progress_signal.emit("ADB命令返回空结果")
                    self.devices_signal.emit([])
                    return
                
                lines = output.split('\n')
                device_ids = []
                
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith("List of devices"):
                        parts = line.split()
                        if len(parts) >= 2 and parts[1] in ["device", "offline"]:
                            device_ids.append(parts[0])
                            self.logger.info(f"发现设备: {parts[0]} (状态: {parts[1]})")
                
                if device_ids:
                    self.progress_signal.emit(f"找到 {len(device_ids)} 个设备")
                    self.devices_signal.emit(device_ids)
                else:
                    self.progress_signal.emit("未检测到任何设备")
                    self.devices_signal.emit([])
                    
        except subprocess.TimeoutExpired:
            self.error_signal.emit("刷新设备列表超时，请检查ADB连接")
            self.devices_signal.emit([])
        except Exception as e:
            self.error_signal.emit(f"刷新设备列表时发生错误: {str(e)}")
            self.devices_signal.emit([])


class U2ConnectThread(DeviceBaseThread):
    """U2连接线程"""
    
    connected_signal = pyqtSignal(object, str)  # 发送连接成功的u2设备对象和设备ID
    
    def __init__(self, device_id):
        super().__init__(device_id, "U2ConnectThread")
        
    def _run_implementation(self):
        """尝试U2连接"""
        start_time = time.time()
        self.progress_signal.emit(f"正在连接到设备: {self.device_id}")
        
        try:
            # 直接尝试U2连接
            d = u2.connect(self.device_id)
            
            if d:
                # 获取设备详细信息
                try:
                    info = d.info
                    device_info = {
                        'serial': self.device_id,
                        'model': info.get('model', 'Unknown'),
                        'brand': info.get('brand', 'Unknown'),
                        'version': info.get('version', 'Unknown'),
                        'sdk': info.get('sdk', 'Unknown'),
                        'manufacturer': info.get('manufacturer', 'Unknown')
                    }
                    
                    elapsed_time = time.time() - start_time
                    self.progress_signal.emit(f"U2连接成功: {self.device_id}")
                    self.progress_signal.emit(f"设备型号: {device_info['brand']} {device_info['model']}")
                    self.progress_signal.emit(f"Android版本: {device_info['version']}")
                    self.progress_signal.emit(f"SDK版本: {device_info['sdk']}")
                    
                    self.connected_signal.emit(d, self.device_id)
                    
                except Exception as info_error:
                    # 如果获取设备信息失败，降级到ADB模式
                    self.progress_signal.emit(f"U2连接无法获取设备信息，降级到ADB模式: {self.device_id}")
                    self.progress_signal.emit(f"原因: {str(info_error)}")
                    self.connected_signal.emit(None, self.device_id)
            else:
                error_msg = f"U2连接失败: 无法连接到设备 {self.device_id}"
                self.error_signal.emit(error_msg)
                self.connected_signal.emit(None, self.device_id)
                
        except Exception as e:
            error_msg = f"U2连接异常: {str(e)}"
            self.error_signal.emit(error_msg)
            self.connected_signal.emit(None, self.device_id)


class RebootDeviceThread(DeviceBaseThread):
    """重启设备线程"""
    
    def __init__(self, device_id):
        super().__init__(device_id, "RebootDeviceThread")
        
    def _run_implementation(self):
        """执行设备重启操作"""
        from adb_utils import ADBUtils
        
        self.progress_signal.emit(f"正在重启设备: {self.device_id}")
        
        try:
            # 执行重启命令
            result = ADBUtils.run_adb_command(
                command="reboot",
                device_id=self.device_id,
                timeout=30
            )
            
            if result.returncode == 0:
                self.progress_signal.emit(f"设备 {self.device_id} 重启命令已发送")
                self.progress_signal.emit("设备正在重启，请等待...")
                self.success_signal.emit("设备重启成功")
            else:
                error_msg = f"重启设备失败: {result.stderr}"
                self.error_signal.emit(error_msg)
                
        except Exception as e:
            self.error_signal.emit(f"重启设备时发生错误: {str(e)}")


class U2ReinitThread(DeviceBaseThread):
    """重新初始化U2服务线程"""
    
    success_signal = pyqtSignal(str)
    
    def __init__(self, device_id, u2_device=None):
        super().__init__(device_id, "U2ReinitThread")
        self.u2_device = u2_device
        
    def _run_implementation(self):
        """重新初始化U2服务"""
        from adb_utils import ADBUtils
        
        self.progress_signal.emit(f"开始重新初始化设备 {self.device_id} 的U2服务...")
        
        try:
            # 停止U2服务
            self.progress_signal.emit("停止U2服务...")
            ADBUtils.run_adb_command(
                command="shell am force-stop com.github.uiautomator",
                device_id=self.device_id
            )
            
            # 清理相关进程
            self.progress_signal.emit("清理U2相关进程...")
            ADBUtils.run_adb_command(
                command="shell pkill -f uiautomator",
                device_id=self.device_id
            )
            
            # 重新安装U2
            self.progress_signal.emit("重新安装U2服务...")
            u2.install(self.device_id)
            
            # 等待服务启动
            self.progress_signal.emit("等待U2服务启动...")
            time.sleep(3)
            
            # 重新连接测试
            self.progress_signal.emit("测试U2连接...")
            d = u2.connect(self.device_id)
            
            if d:
                self.progress_signal.emit("U2服务重新初始化成功")
                self.success_signal.emit("U2服务重新初始化成功")
            else:
                self.error_signal.emit("U2服务重新初始化失败")
                
        except Exception as e:
            self.error_signal.emit(f"重新初始化U2服务时发生错误: {str(e)}")


class AdbRootThread(DeviceBaseThread):
    """获取Root权限线程"""
    
    def __init__(self, device_id):
        super().__init__(device_id, "AdbRootThread")
        
    def _run_implementation(self):
        """执行获取Root权限操作"""
        from adb_utils import ADBUtils
        
        self.progress_signal.emit("正在尝试获取Root权限...")
        
        try:
            # 执行root命令
            result = ADBUtils.run_adb_command(
                command="root",
                device_id=self.device_id,
                timeout=10
            )
            
            # 等待设备重启ADB服务
            time.sleep(3)
            
            if result.returncode == 0:
                self.progress_signal.emit(f"获取Root权限成功: {result.stdout.strip()}")
                self.success_signal.emit("获取Root权限成功")
            else:
                self.error_signal.emit(f"获取Root权限失败: {result.stderr.strip()}")
                
        except subprocess.TimeoutExpired:
            self.error_signal.emit("获取Root权限超时")
        except Exception as e:
            self.error_signal.emit(f"获取Root权限时发生错误: {str(e)}")
