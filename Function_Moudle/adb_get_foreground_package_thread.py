from PyQt5.QtCore import QThread, pyqtSignal
import subprocess
import re

class ADBGetForegroundPackageThread(QThread):
    """ADB模式下获取前台应用包名的线程"""
    progress_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, device_id):
        super().__init__()
        self.device_id = device_id

    def run(self):
        try:
            self.progress_signal.emit("正在获取前台应用...")
            
            # 方法1: 使用 dumpsys activity top (更可靠)
            command = f"adb -s {self.device_id} shell dumpsys activity top"
            result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=30)
            
            focus_info = None
            if result.returncode == 0 and result.stdout:
                # 在 Python 中过滤包含 ACTIVITY 的行
                for line in result.stdout.split('\n'):
                    if 'ACTIVITY' in line:
                        focus_info = line.strip()
                        break
            
            # 方法2: 如果方法1失败，尝试 dumpsys window
            if not focus_info:
                command2 = f"adb -s {self.device_id} shell dumpsys window windows"
                result2 = subprocess.run(command2, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=30)
                
                if result2.returncode == 0 and result2.stdout:
                    for line in result2.stdout.split('\n'):
                        if 'mCurrentFocus' in line or 'mFocusedApp' in line:
                            focus_info = line.strip()
                            break
            
            if not focus_info:
                self.error_signal.emit("无法获取前台应用信息")
                return
            
            # 解析包名和活动名
            # 格式示例: ACTIVITY com.android.settings/.SubSettings
            # 或: mCurrentFocus=Window{abc xyz u0 com.android.settings/com.android.settings.SubSettings}
            package_name = None
            activity_name = None
            
            # 尝试匹配 ACTIVITY 格式
            activity_match = re.search(r'ACTIVITY\s+(\S+)', focus_info)
            if activity_match:
                full_name = activity_match.group(1)
                if '/' in full_name:
                    parts = full_name.split('/')
                    package_name = parts[0]
                    activity_name = parts[1] if len(parts) > 1 else ""
                else:
                    package_name = full_name
            
            # 尝试匹配 mCurrentFocus 格式
            if not package_name:
                focus_match = re.search(r'\{[^}]*\s+(\S+)/(\S*)\}', focus_info)
                if focus_match:
                    package_name = focus_match.group(1)
                    activity_name = focus_match.group(2) if focus_match.group(2) else ""
            
            if package_name:
                if activity_name:
                    self.result_signal.emit(f"包名: {package_name}, 活动名: {activity_name}")
                else:
                    self.result_signal.emit(f"包名: {package_name}")
            else:
                self.error_signal.emit("无法解析应用信息")
                
        except subprocess.TimeoutExpired:
            self.error_signal.emit("ADB命令执行超时")
        except Exception as e:
            self.error_signal.emit(f"获取前台应用失败: {str(e)}")