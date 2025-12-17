from PyQt5.QtCore import QThread, pyqtSignal
import subprocess
import re

class ADBAppActionThread(QThread):
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, device_id, package_name):
        super(ADBAppActionThread, self).__init__()
        self.device_id = device_id
        self.package_name = package_name

    def _get_main_activity(self):
        """查询应用的默认主Activity"""
        try:
            # 执行adb shell pm dump命令查询应用信息
            command = f"adb -s {self.device_id} shell pm dump {self.package_name}"
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                return None
            
            # 解析输出，查找主Activity
            output = result.stdout
            
            # 查找包含MAIN intent的Activity
            # 使用正则表达式匹配 cmp=包名/Activity 格式
            pattern = r'cmp=' + re.escape(self.package_name) + r'/([^\s}]+)'
            matches = re.findall(pattern, output)
            
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
            if matches:
                return f"{self.package_name}/{matches[0]}"
            
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
                command = f"adb -s {self.device_id} shell am start -n {main_activity}"
                result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.progress_signal.emit("应用启动成功")
                    if result.stdout:
                        self.progress_signal.emit(result.stdout.strip())
                else:
                    self.error_signal.emit(f"应用启动失败: {result.stderr}")
            else:
                # 如果没有找到Activity，尝试直接使用包名启动
                self.progress_signal.emit("未找到主Activity，尝试直接启动...")
                command = f"adb -s {self.device_id} shell am start -n {self.package_name}"
                result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.progress_signal.emit("应用启动成功")
                else:
                    self.error_signal.emit(f"应用启动失败: {result.stderr}")
                    
        except subprocess.CalledProcessError as e:
            self.error_signal.emit(f"应用启动失败: {str(e)}")
        except Exception as e:
            self.error_signal.emit(f"应用启动失败: {str(e)}")