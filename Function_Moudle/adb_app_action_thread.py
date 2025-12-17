from PyQt5.QtCore import QThread, pyqtSignal
import subprocess
import re
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

class ADBAppActionThread(QThread):
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, device_id, package_name):
        super(ADBAppActionThread, self).__init__()
        self.device_id = device_id
        self.package_name = package_name

    def _check_app_installed(self):
        """检查应用是否已安装"""
        try:
            result = adb_utils.run_adb_command(f"shell pm list packages {self.package_name}", self.device_id)
            
            # 确保stdout是字符串类型
            stdout = result.stdout
            if not isinstance(stdout, str):
                stdout = str(stdout) if stdout is not None else ""
            
            return self.package_name in stdout
        except Exception:
            return False

    def _get_main_activity(self):
        """查询应用的默认主Activity"""
        try:
            # 先检查应用是否安装
            if not self._check_app_installed():
                self.error_signal.emit(f"应用 {self.package_name} 未安装")
                return None
            
            # 执行adb shell pm dump命令查询应用信息
            result = adb_utils.run_adb_command(f"shell pm dump {self.package_name}", self.device_id)
            
            if result.returncode != 0:
                return None
            
            # 解析输出，查找主Activity
            output = result.stdout
            
            # 确保output是字符串类型
            if not isinstance(output, str):
                output = str(output) if output is not None else ""
            
            # 如果输出为空，直接返回None
            if not output:
                return None
            
            # 查找包含MAIN intent的Activity
            # 使用正则表达式匹配 cmp=包名/Activity 格式
            pattern = r'cmp=' + re.escape(self.package_name) + r'/([^\s}]+)'
            matches = re.findall(pattern, output)
            
            # 清理匹配结果，去除空格
            cleaned_matches = [match.strip() for match in matches if match.strip()]
            
            # 查找包含android.intent.action.MAIN的Activity
            for line in output.split('\n'):
                if 'android.intent.action.MAIN' in line and 'cmp=' in line:
                    # 提取cmp=后面的内容
                    match = re.search(r'cmp=([^\s}]+)', line)
                    if match:
                        cmp_value = match.group(1)
                        if cmp_value.startswith(self.package_name + '/'):
                            return cmp_value
            
            # 如果没有找到明确的MAIN Activity，使用第一个匹配的Activity
            if cleaned_matches:
                return f"{self.package_name}/{cleaned_matches[0]}"
            
            return None
            
        except subprocess.CalledProcessError as e:
            self.error_signal.emit(f"查询Activity失败: {str(e)}")
            return None
        except Exception as e:
            self.error_signal.emit(f"查询Activity失败: {str(e)}")
            return None

    def run(self):
        try:
            self.progress_signal.emit("正在查询应用主Activity...")
            
            # 先查询主Activity
            main_activity = self._get_main_activity()
            
            if main_activity:
                self.progress_signal.emit(f"找到主Activity: {main_activity}")
                self.progress_signal.emit("正在启动应用程序...")
                
                # 使用完整的包名/Activity启动应用
                result = adb_utils.run_adb_command(f"shell am start -n {main_activity}", self.device_id, check=True)
                
                if result.returncode == 0:
                    self.progress_signal.emit("应用启动成功")
                    if result.stdout:
                        self.progress_signal.emit(result.stdout.strip())
                else:
                    self.error_signal.emit(f"应用启动失败: {result.stderr}")
            else:
                # 如果没有找到Activity，尝试直接使用包名启动
                self.progress_signal.emit("未找到主Activity，尝试直接启动...")
                result = adb_utils.run_adb_command(f"shell am start -n {self.package_name}", self.device_id, check=True)
                
                if result.returncode == 0:
                    self.progress_signal.emit("应用启动成功")
                else:
                    self.error_signal.emit(f"应用启动失败: {result.stderr}")
                    
        except subprocess.CalledProcessError as e:
            self.error_signal.emit(f"应用启动失败: {str(e)}")
        except Exception as e:
            self.error_signal.emit(f"应用启动失败: {str(e)}")