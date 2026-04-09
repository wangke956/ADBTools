from PyQt5.QtCore import pyqtSignal
from .base_thread import DeviceBaseThread
from logger_manager import log_operation, log_device_operation
import os


class DatongBatchInstallThread(DeviceBaseThread):
    """大通批量安装线程"""
    
    install_signal = pyqtSignal(str)
    
    def __init__(self, device_id, apk_folder):
        super().__init__(device_id, "DatongBatchInstallThread")
        self.apk_folder = apk_folder
        
    def _run_implementation(self):
        """执行批量安装操作"""
        self.progress_signal.emit("开始批量安装APK文件...")
        
        try:
            from adb_utils import ADBUtils
            
            # 获取所有APK文件
            apk_files = []
            for file in os.listdir(self.apk_folder):
                if file.lower().endswith('.apk'):
                    apk_files.append(os.path.join(self.apk_folder, file))
            
            if not apk_files:
                self.error_signal.emit("未找到APK文件")
                return
                
            success_count = 0
            total_count = len(apk_files)
            
            self.progress_signal.emit(f"找到 {total_count} 个APK文件")
            
            for apk_file in apk_files:
                apk_name = os.path.basename(apk_file)
                self.progress_signal.emit(f"正在安装: {apk_name}")
                
                result = ADBUtils.run_adb_command_realtime(
                    command=f"install -r \"{apk_file}\"",
                    device_id=self.device_id,
                    output_callback=self.install_signal.emit
                )
                
                if result.returncode == 0:
                    success_count += 1
                    self.progress_signal.emit(f"✓ {apk_name} 安装成功")
                else:
                    self.progress_signal.emit(f"✗ {apk_name} 安装失败")
            
            self.progress_signal.emit(f"批量安装完成: {success_count}/{total_count} 成功")
            self.success_signal.emit(f"批量安装完成: {success_count}/{total_count} 成功")
            
        except Exception as e:
            self.error_signal.emit(f"批量安装时发生错误: {str(e)}")


class DatongBatchVerifyVersionThread(DeviceBaseThread):
    """大通批量验证版本线程"""
    
    verify_signal = pyqtSignal(str)
    
    def __init__(self, device_id, apk_folder):
        super().__init__(device_id, "DatongBatchVerifyVersionThread")
        self.apk_folder = apk_folder
        
    def _run_implementation(self):
        """执行批量验证版本操作"""
        self.progress_signal.emit("开始验证APK版本...")
        
        try:
            from adb_utils import ADBUtils
            
            # 获取所有APK文件
            apk_files = []
            for file in os.listdir(self.apk_folder):
                if file.lower().endswith('.apk'):
                    apk_files.append(os.path.join(self.apk_folder, file))
            
            if not apk_files:
                self.error_signal.emit("未找到APK文件")
                return
                
            self.progress_signal.emit(f"找到 {len(apk_files)} 个APK文件")
            
            for apk_file in apk_files:
                apk_name = os.path.basename(apk_file)
                
                # 使用aapt获取包名
                from adb_utils import ADBUtils
                package_name = ADBUtils.aapt_get_package_name(apk_file)
                
                if package_name and "失败" not in package_name:
                    # 检查设备上的版本
                    success, version = ADBUtils.get_app_version(self.device_id, package_name)
                    
                    if success:
                        self.progress_signal.emit(f"{package_name}: {version}")
                        self.verify_signal.emit(f"{package_name}: {version}")
                    else:
                        self.progress_signal.emit(f"{package_name}: 未安装")
                        self.verify_signal.emit(f"{package_name}: 未安装")
                else:
                    self.progress_signal.emit(f"{apk_name}: 获取包名失败")
                    self.verify_signal.emit(f"{apk_name}: 获取包名失败")
            
            self.progress_signal.emit("版本验证完成")
            self.success_signal.emit("版本验证完成")
            
        except Exception as e:
            self.error_signal.emit(f"验证版本时发生错误: {str(e)}")


class DatongInputPasswordThread(DeviceBaseThread):
    """大通输入密码线程"""
    
    def __init__(self, device_id, password):
        super().__init__(device_id, "DatongInputPasswordThread")
        self.password = password
        
    def _run_implementation(self):
        """执行输入密码操作"""
        self.progress_signal.emit("正在输入密码...")
        
        try:
            from adb_utils import ADBUtils
            
            # 处理特殊字符
            import urllib.parse
            encoded_password = urllib.parse.quote(self.password)
            
            result = ADBUtils.run_adb_command(
                command=f"shell input text {encoded_password}",
                device_id=self.device_id,
                timeout=10
            )
            
            if result.returncode == 0:
                self.progress_signal.emit("密码输入成功")
                self.success_signal.emit("密码输入成功")
            else:
                self.error_signal.emit(f"密码输入失败: {result.stderr}")
                
        except Exception as e:
            self.error_signal.emit(f"输入密码时发生错误: {str(e)}")


class DatongSetDatetimeThread(DeviceBaseThread):
    """大通设置日期时间线程"""
    
    def __init__(self, device_id, datetime_str):
        super().__init__(device_id, "DatongSetDatetimeThread")
        self.datetime_str = datetime_str
        
    def _run_implementation(self):
        """执行设置日期时间操作"""
        self.progress_signal.emit(f"正在设置日期时间: {self.datetime_str}")
        
        try:
            from adb_utils import ADBUtils
            
            # 设置系统日期时间
            result = ADBUtils.run_adb_command(
                command=f"shell date -s \"{self.datetime_str}\"",
                device_id=self.device_id,
                timeout=10
            )
            
            if result.returncode == 0:
                self.progress_signal.emit("日期时间设置成功")
                self.success_signal.emit("日期时间设置成功")
            else:
                self.error_signal.emit(f"日期时间设置失败: {result.stderr}")
                
        except Exception as e:
            self.error_signal.emit(f"设置日期时间时发生错误: {str(e)}")


class DatongOpenTelenavEngineeringThread(DeviceBaseThread):
    """大通打开泰维地图工程模式线程"""
    
    def __init__(self, device_id):
        super().__init__(device_id, "DatongOpenTelenavEngineeringThread")
        
    def _run_implementation(self):
        """执行打开泰维地图工程模式操作"""
        self.progress_signal.emit("正在打开泰维地图工程模式...")
        
        try:
            from adb_utils import ADBUtils
            
            # 启动泰维地图工程模式
            result = ADBUtils.run_adb_command(
                command="shell am start -n com.telenav/.ui.activity.MainActivity --es engineeringMode true",
                device_id=self.device_id,
                timeout=15
            )
            
            if result.returncode == 0:
                self.progress_signal.emit("泰维地图工程模式已打开")
                self.success_signal.emit("泰维地图工程模式已打开")
            else:
                self.error_signal.emit(f"打开泰维地图工程模式失败: {result.stderr}")
                
        except Exception as e:
            self.error_signal.emit(f"打开泰维地图工程模式时发生错误: {str(e)}")
