from PyQt5.QtCore import QThread, pyqtSignal
import subprocess
import sys
import os

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class GetRunningAppInfoThread(QThread):
    progress_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, d):
        super().__init__()
        self.d = d
        self.current_app = None
        self.package_name = None

    def run(self):
        try:
            self.progress_signal.emit("正在获取应用信息...")
            self.current_app = self.d.app_current()
            self.progress_signal.emit("正在获取包名...")
            self.package_name = self.current_app['package']
            self.progress_signal.emit("正在获取应用版本信息...")
            
            # 先尝试使用 u2 的 app_info 方法
            try:
                app_info = self.d.app_info(self.package_name)
                if app_info and 'versionName' in app_info:
                    version_name = app_info.get('versionName', '未知版本')
                    self.result_signal.emit(f"应用 {self.package_name} 版本号: {version_name}")
                    return
            except Exception as e:
                # 如果 u2 的 app_info 失败，使用 aapt 命令
                self.progress_signal.emit(f"u2获取版本失败，尝试使用aapt命令...")
            
            # 使用 aapt 命令获取版本信息
            try:
                # 获取 APK 路径
                apk_path = self._get_apk_path()
                if not apk_path:
                    self.error_signal.emit(f"无法获取应用 {self.package_name} 的APK路径")
                    return
                
                # 使用 aapt 获取版本信息
                version_name = self._get_version_by_aapt(apk_path)
                if version_name:
                    self.result_signal.emit(f"应用 {self.package_name} 版本号: {version_name}")
                else:
                    self.error_signal.emit(f"无法获取应用 {self.package_name} 的版本信息")
                    
            except Exception as e:
                self.error_signal.emit(f"获取版本信息失败: {str(e)}")
                
        except Exception as e:
            self.error_signal.emit(str(e))
    
    def _get_apk_path(self):
        """获取应用的主APK路径"""
        try:
            # 使用 adb shell pm path 命令获取 APK 路径
            from adb_utils import ADBUtils
            adb_utils = ADBUtils()
            adb_path = adb_utils.get_adb_path()
            
            device_id = self.d.serial
            cmd = f'"{adb_path}" -s {device_id} shell pm path {self.package_name}'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout:
                # 解析输出，获取主 APK 路径
                for line in result.stdout.strip().split('\n'):
                    if line.startswith('package:'):
                        apk_path = line.replace('package:', '').strip()
                        # 只返回 base.apk，避免 split APK 的问题
                        if 'base.apk' in apk_path:
                            return apk_path
                        return apk_path
            
            return None
        except Exception as e:
            print(f"获取APK路径失败: {e}")
            return None
    
    def _get_version_by_aapt(self, apk_path):
        """使用 aapt 命令获取版本信息"""
        try:
            # 先将 APK 拉取到本地临时目录
            import tempfile
            temp_dir = tempfile.mkdtemp()
            local_apk_path = os.path.join(temp_dir, os.path.basename(apk_path))
            
            # 使用 adb pull 拉取 APK
            from adb_utils import ADBUtils
            adb_utils = ADBUtils()
            adb_path = adb_utils.get_adb_path()
            device_id = self.d.serial
            
            pull_cmd = f'"{adb_path}" -s {device_id} pull "{apk_path}" "{local_apk_path}"'
            result = subprocess.run(pull_cmd, shell=True, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                # 清理临时文件
                if os.path.exists(local_apk_path):
                    os.remove(local_apk_path)
                os.rmdir(temp_dir)
                return None
            
            # 使用 aapt 获取版本信息
            aapt_cmd = f'aapt dump badging "{local_apk_path}" | findstr "versionName"'
            result = subprocess.run(aapt_cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            # 清理临时文件
            if os.path.exists(local_apk_path):
                os.remove(local_apk_path)
            os.rmdir(temp_dir)
            
            if result.returncode == 0 and result.stdout:
                # 解析版本号
                for line in result.stdout.strip().split('\n'):
                    if 'versionName' in line:
                        version_name = line.split('=')[1].strip().strip("'").strip('"')
                        return version_name
            
            return None
        except Exception as e:
            print(f"aapt获取版本失败: {e}")
            return None