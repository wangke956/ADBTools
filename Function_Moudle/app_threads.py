from PyQt5.QtCore import pyqtSignal
from .base_thread import BaseThread, DeviceBaseThread
from logger_manager import log_operation, measure_performance, log_exception
import subprocess
import os


class InstallFileThread(DeviceBaseThread):
    """安装文件线程"""
    
    signal_status = pyqtSignal(str)
    
    def __init__(self, device_id, package_path):
        super().__init__(device_id, "InstallFileThread")
        self.package_path = package_path
        
    def _run_implementation(self):
        """执行应用安装操作"""
        self.progress_signal.emit("开始安装应用...")
        
        try:
            from adb_utils import ADBUtils
            
            # 构建安装命令
            result = ADBUtils.run_adb_command_realtime(
                command=f"install -r \"{self.package_path}\"",
                device_id=self.device_id,
                output_callback=self.signal_status.emit
            )
            
            if result.returncode == 0:
                self.success_signal.emit("应用安装成功")
            else:
                self.error_signal.emit(f"应用安装失败: {result.stderr}")
                
        except Exception as e:
            self.error_signal.emit(f"安装应用时发生错误: {str(e)}")


class UninstallAppThread(DeviceBaseThread):
    """卸载应用线程"""
    
    def __init__(self, device_id, package_name):
        super().__init__(device_id, "UninstallAppThread")
        self.package_name = package_name
        
    def _run_implementation(self):
        """执行应用卸载操作"""
        self.progress_signal.emit(f"正在卸载应用: {self.package_name}")
        
        try:
            from adb_utils import ADBUtils
            
            result = ADBUtils.run_adb_command(
                command=f"uninstall {self.package_name}",
                device_id=self.device_id,
                timeout=30
            )
            
            if result.returncode == 0:
                self.progress_signal.emit(f"应用 {self.package_name} 卸载成功")
                self.success_signal.emit("应用卸载成功")
            else:
                self.error_signal.emit(f"应用卸载失败: {result.stderr}")
                
        except Exception as e:
            self.error_signal.emit(f"卸载应用时发生错误: {str(e)}")


class ForceStopAppThread(DeviceBaseThread):
    """强制停止应用线程"""
    
    def __init__(self, device_id, package_name):
        super().__init__(device_id, "ForceStopAppThread")
        self.package_name = package_name
        
    def _run_implementation(self):
        """执行强制停止应用操作"""
        self.progress_signal.emit(f"正在强制停止应用: {self.package_name}")
        
        try:
            from adb_utils import ADBUtils
            
            result = ADBUtils.run_adb_command(
                command=f"shell am force-stop {self.package_name}",
                device_id=self.device_id,
                timeout=10
            )
            
            if result.returncode == 0:
                self.progress_signal.emit(f"应用 {self.package_name} 已强制停止")
                self.success_signal.emit("应用已强制停止")
            else:
                self.error_signal.emit(f"强制停止应用失败: {result.stderr}")
                
        except Exception as e:
            self.error_signal.emit(f"强制停止应用时发生错误: {str(e)}")


class ClearAppCacheThread(DeviceBaseThread):
    """清除应用缓存线程"""
    
    def __init__(self, device_id, package_name):
        super().__init__(device_id, "ClearAppCacheThread")
        self.package_name = package_name
        
    def _run_implementation(self):
        """执行清除应用缓存操作"""
        self.progress_signal.emit(f"正在清除应用缓存: {self.package_name}")
        
        try:
            from adb_utils import ADBUtils
            
            result = ADBUtils.run_adb_command(
                command=f"shell pm clear {self.package_name}",
                device_id=self.device_id,
                timeout=15
            )
            
            if result.returncode == 0:
                self.progress_signal.emit(f"应用 {self.package_name} 缓存已清除")
                self.success_signal.emit("应用缓存已清除")
            else:
                self.error_signal.emit(f"清除应用缓存失败: {result.stderr}")
                
        except Exception as e:
            self.error_signal.emit(f"清除应用缓存时发生错误: {str(e)}")


class ListPackageThread(DeviceBaseThread):
    """列出应用包线程"""
    
    packages_signal = pyqtSignal(list)
    
    def __init__(self, device_id):
        super().__init__(device_id, "ListPackageThread")
        
    def _run_implementation(self):
        """执行列出应用包操作"""
        self.progress_signal.emit("正在获取应用包列表...")
        
        try:
            from adb_utils import ADBUtils
            
            result = ADBUtils.run_adb_command(
                command="shell pm list packages",
                device_id=self.device_id,
                timeout=30
            )
            
            if result.returncode == 0:
                packages = []
                for line in result.stdout.strip().split('\n'):
                    if line.startswith("package:"):
                        package_name = line.replace("package:", "").strip()
                        packages.append(package_name)
                
                self.progress_signal.emit(f"找到 {len(packages)} 个应用包")
                self.packages_signal.emit(packages)
            else:
                self.error_signal.emit(f"获取应用包列表失败: {result.stderr}")
                self.packages_signal.emit([])
                
        except Exception as e:
            self.error_signal.emit(f"获取应用包列表时发生错误: {str(e)}")
            self.packages_signal.emit([])


class GetForegroundPackageThread(DeviceBaseThread):
    """获取前台应用包线程"""
    
    package_signal = pyqtSignal(str)
    
    def __init__(self, device_id):
        super().__init__(device_id, "GetForegroundPackageThread")
        
    def _run_implementation(self):
        """执行获取前台应用包操作"""
        self.progress_signal.emit("正在获取前台应用包...")
        
        try:
            from adb_utils import ADBUtils
            
            result = ADBUtils.run_adb_command(
                command="shell dumpsys window | findstr mCurrentFocus",
                device_id=self.device_id,
                timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                if output:
                    # 解析输出获取包名
                    import re
                    match = re.search(r'([^/]+)/', output)
                    if match:
                        package_name = match.group(1)
                        self.progress_signal.emit(f"前台应用包: {package_name}")
                        self.package_signal.emit(package_name)
                    else:
                        self.error_signal.emit("无法解析前台应用包信息")
                        self.package_signal.emit("")
                else:
                    self.error_signal.emit("未获取到前台应用信息")
                    self.package_signal.emit("")
            else:
                self.error_signal.emit(f"获取前台应用包失败: {result.stderr}")
                self.package_signal.emit("")
                
        except Exception as e:
            self.error_signal.emit(f"获取前台应用包时发生错误: {str(e)}")
            self.package_signal.emit("")


class GetRunningAppInfoThread(DeviceBaseThread):
    """获取运行应用信息线程"""
    
    app_info_signal = pyqtSignal(dict)
    
    def __init__(self, device_id):
        super().__init__(device_id, "GetRunningAppInfoThread")
        
    def _run_implementation(self):
        """执行获取运行应用信息操作"""
        self.progress_signal.emit("正在获取运行应用信息...")
        
        try:
            from adb_utils import ADBUtils
            
            result = ADBUtils.run_adb_command(
                command="shell ps",
                device_id=self.device_id,
                timeout=15
            )
            
            if result.returncode == 0:
                app_info = []
                lines = result.stdout.strip().split('\n')
                
                for line in lines[1:]:  # 跳过标题行
                    parts = line.split()
                    if len(parts) >= 9:
                        pid = parts[1]
                        name = parts[-1]
                        app_info.append({
                            'pid': pid,
                            'name': name
                        })
                
                self.progress_signal.emit(f"找到 {len(app_info)} 个运行中的应用")
                self.app_info_signal.emit(app_info)
            else:
                self.error_signal.emit(f"获取运行应用信息失败: {result.stderr}")
                self.app_info_signal.emit([])
                
        except Exception as e:
            self.error_signal.emit(f"获取运行应用信息时发生错误: {str(e)}")
            self.app_info_signal.emit([])


class InputTextThread(DeviceBaseThread):
    """输入文本线程"""
    
    def __init__(self, device_id, text):
        super().__init__(device_id, "InputTextThread")
        self.text = text
        
    def _run_implementation(self):
        """执行输入文本操作"""
        self.progress_signal.emit(f"正在输入文本: {self.text}")
        
        try:
            from adb_utils import ADBUtils
            
            # 处理特殊字符
            import urllib.parse
            encoded_text = urllib.parse.quote(self.text)
            
            result = ADBUtils.run_adb_command(
                command=f"shell input text {encoded_text}",
                device_id=self.device_id,
                timeout=10
            )
            
            if result.returncode == 0:
                self.progress_signal.emit("文本输入成功")
                self.success_signal.emit("文本输入成功")
            else:
                self.error_signal.emit(f"文本输入失败: {result.stderr}")
                
        except Exception as e:
            self.error_signal.emit(f"文本输入时发生错误: {str(e)}")
