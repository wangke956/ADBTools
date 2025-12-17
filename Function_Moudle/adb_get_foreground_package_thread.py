from PyQt5.QtCore import QThread, pyqtSignal
import subprocess
import re

class ADBGetForegroundPackageThread(QThread):
    signal_package = pyqtSignal(str)

    def __init__(self, device_id):
        super().__init__()
        self.device_id = device_id

    def run(self):
        try:
            # 首先检查设备是否连接
            check_command = f"adb -s {self.device_id} shell echo 'connection_test'"
            check_result = subprocess.run(check_command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            if check_result.returncode != 0:
                if "device not found" in check_result.stderr.lower():
                    self.signal_package.emit(f"设备 {self.device_id} 未连接，请检查设备连接状态")
                elif "offline" in check_result.stderr.lower():
                    self.signal_package.emit(f"设备 {self.device_id} 处于离线状态，请重新连接")
                else:
                    self.signal_package.emit(f"ADB连接失败: {check_result.stderr}")
                return
            
            # 使用ADB命令获取当前前台应用
            command = f"adb -s {self.device_id} shell dumpsys activity activities | grep 'mCurrentFocus'"
            result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            if result.returncode != 0:
                # 如果命令执行失败，尝试更简单的方法
                simple_command = f"adb -s {self.device_id} shell dumpsys window windows | grep 'mCurrentFocus'"
                simple_result = subprocess.run(simple_command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                
                if simple_result.returncode == 0 and simple_result.stdout.strip():
                    focus_info = simple_result.stdout.strip()
                else:
                    self.signal_package.emit("无法获取前台应用信息，可能设备不支持或应用权限不足")
                    return
            else:
                focus_info = result.stdout.strip()
            
            # 解析包名和活动名
            if focus_info and 'mCurrentFocus' in focus_info:
                try:
                    # 使用正则表达式提取包名和活动名
                    package_match = re.search(r'\{([^}]+)\}', focus_info)
                    if package_match:
                        package_info = package_match.group(1)
                        parts = package_info.split('/')
                        package_name = parts[0]
                        activity_name = parts[1] if len(parts) > 1 else ""
                        self.signal_package.emit(f"包名: {package_name}, 活动名: {activity_name}")
                    else:
                        self.signal_package.emit("无法解析应用信息")
                except Exception:
                    self.signal_package.emit("解析应用信息失败")
            else:
                self.signal_package.emit("当前没有正在运行的应用")
                
        except subprocess.CalledProcessError as e:
            self.signal_package.emit(f"ADB命令执行失败: {str(e)}")
        except Exception as e:
            self.signal_package.emit(f"获取前台应用失败: {str(e)}")