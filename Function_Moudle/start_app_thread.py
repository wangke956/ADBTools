#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动应用线程 - 支持U2和ADB两种模式
"""

from PyQt5.QtCore import QThread, pyqtSignal
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from adb_utils import adb_utils
except ImportError:
    from fallbacks import ADBUtilsFallback
    adb_utils = ADBUtilsFallback()


class StartAppThread(QThread):
    """启动应用线程 - 支持U2和ADB模式"""
    
    progress_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, device_id, app_name, connection_mode='adb', u2_device=None):
        """
        初始化线程
        
        Args:
            device_id: 设备ID
            app_name: 应用包名或完整的Activity路径 (如: com.example.app 或 com.example.app/.MainActivity)
            connection_mode: 连接模式 ('u2' 或 'adb')
            u2_device: U2设备对象（仅当connection_mode='u2'时使用）
        """
        super().__init__()
        self.device_id = device_id
        self.app_name = app_name
        self.connection_mode = connection_mode
        self.u2_device = u2_device
        
        # 解析包名和Activity
        if '/' in app_name and not app_name.startswith('@'):
            # 完整格式: package/activity
            parts = app_name.split('/', 1)
            self.package_name = parts[0]
            self.activity_name = parts[1] if len(parts) > 1 else None
        else:
            # 只是包名
            self.package_name = app_name
            self.activity_name = None

    def run(self):
        """执行启动应用操作"""
        try:
            self.progress_signal.emit(f"正在启动应用: {self.app_name}...")
            
            if self.connection_mode == 'u2' and self.u2_device:
                # U2模式启动
                self._start_app_u2()
            elif self.connection_mode == 'adb':
                # ADB模式启动
                self._start_app_adb()
            else:
                self.error_signal.emit("设备未连接或连接模式无效")
                
        except Exception as e:
            self.error_signal.emit(f"启动应用失败: {str(e)}")

    def _start_app_u2(self):
        """U2模式下启动应用 - 最快速度启动"""
        import re
        
        try:
            d = self.u2_device
            
            # 方法1: 如果有指定的Activity，使用app_start(package, activity) - 最快
            if self.activity_name:
                self.progress_signal.emit(f"[U2] 正在启动应用...")
                d.app_start(self.package_name, self.activity_name)
                self.result_signal.emit(f"已启动应用: {self.app_name}")
            else:
                # 方法2: 只有包名，直接使用app_start - 同样快
                self.progress_signal.emit(f"[U2] 正在启动应用...")
                d.app_start(self.package_name)
                self.result_signal.emit(f"已启动应用: {self.app_name}")
                
        except Exception as e:
            # 方法3: 如果app_start失败，才尝试其他方式
            try:
                self.progress_signal.emit("[U2] 启动失败，尝试备用方案...")
                main_activity = self._get_main_activity_u2()
                
                if main_activity:
                    result = d.shell(f"am start -n {main_activity}")
                    self.result_signal.emit(f"已启动应用: {self.app_name}")
                else:
                    monkey_result = d.shell(f"monkey -p {self.package_name} -c android.intent.category.LAUNCHER 1")
                    
                    if hasattr(monkey_result, 'output'):
                        output = monkey_result.output
                    else:
                        output = str(monkey_result)
                    
                    if "No activities found" in output or "Error" in output:
                        self.error_signal.emit(f"U2模式启动失败: 无法找到应用的Activity")
                    else:
                        self.result_signal.emit(f"已启动应用: {self.app_name}")
            except Exception as e2:
                self.error_signal.emit(f"U2模式启动失败: {str(e2)}")

    def _parse_main_activity(self, output, package_name):
        """从pm dump输出中解析主Activity（通用方法）"""
        import re
        
        if not output or not isinstance(output, str):
            return None
        
        # 查找包含MAIN intent的Activity
        for line in output.split('\n'):
            if 'android.intent.action.MAIN' in line and 'cmp=' in line:
                match = re.search(r'cmp=([^\s}]+)', line)
                if match:
                    cmp_value = match.group(1)
                    if cmp_value.startswith(package_name + '/'):
                        return cmp_value
        
        # 备选：查找第一个匹配的Activity
        pattern = r'cmp=' + re.escape(package_name) + r'/([^\s}]+)'
        matches = re.findall(pattern, output)
        cleaned_matches = [match.strip() for match in matches if match.strip()]
        if cleaned_matches:
            return f"{package_name}/{cleaned_matches[0]}"
        
        return None

    def _get_main_activity_u2(self):
        """在U2模式下获取应用的主Activity"""
        try:
            d = self.u2_device
            result = d.shell(f"pm dump {self.package_name}")
            output = result.output if hasattr(result, 'output') else str(result)
            return self._parse_main_activity(output, self.package_name)
        except Exception as e:
            self.progress_signal.emit(f"[U2] 查询主Activity失败: {str(e)}")
            return None

    def _start_app_adb(self):
        """ADB模式下启动应用 - 最快速度启动"""
        try:
            # 如果有指定的Activity，直接启动 - 最快
            if self.activity_name:
                self.progress_signal.emit("[ADB] 正在启动应用...")
                result = adb_utils.run_adb_command(
                    f"shell am start -n {self.app_name}", 
                    self.device_id, 
                    check=True
                )
                
                if result.returncode == 0:
                    self.result_signal.emit(f"已启动应用: {self.app_name}")
                else:
                    self.error_signal.emit(f"[ADB] 应用启动失败: {result.stderr}")
            else:
                # 没有指定Activity，查询主Activity后启动
                main_activity = self._get_main_activity_adb()
                
                if main_activity:
                    result = adb_utils.run_adb_command(
                        f"shell am start -n {main_activity}", 
                        self.device_id, 
                        check=True
                    )
                    
                    if result.returncode == 0:
                        self.result_signal.emit(f"已启动应用: {self.package_name}")
                    else:
                        self.error_signal.emit(f"[ADB] 应用启动失败: {result.stderr}")
                else:
                    # 如果没有找到Activity，尝试直接使用包名启动
                    result = adb_utils.run_adb_command(
                        f"shell am start -n {self.package_name}", 
                        self.device_id, 
                        check=True
                    )
                    
                    if result.returncode == 0:
                        self.result_signal.emit(f"已启动应用: {self.package_name}")
                    else:
                        self.error_signal.emit(f"[ADB] 应用启动失败: {result.stderr}")
                    
        except Exception as e:
            self.error_signal.emit(f"[ADB] 应用启动失败: {str(e)}")

    def _get_main_activity_adb(self):
        """在ADB模式下获取应用的主Activity"""
        try:
            # 先检查应用是否安装
            result = adb_utils.run_adb_command(
                f"shell pm list packages {self.package_name}", 
                self.device_id
            )
            
            stdout = result.stdout
            if not isinstance(stdout, str):
                stdout = str(stdout) if stdout is not None else ""
            
            if self.package_name not in stdout:
                self.error_signal.emit(f"应用 {self.package_name} 未安装")
                return None
            
            # 查询应用信息并解析Activity
            result = adb_utils.run_adb_command(
                f"shell pm dump {self.package_name}", 
                self.device_id
            )
            
            if result.returncode != 0:
                return None
            
            output = result.stdout
            if not isinstance(output, str):
                output = str(output) if output is not None else ""
            
            return self._parse_main_activity(output, self.package_name)
            
        except Exception as e:
            self.progress_signal.emit(f"[ADB] 查询Activity失败: {str(e)}")
            return None
