from PyQt5.QtCore import QThread, pyqtSignal
import subprocess
import re

class ADBListPackageThread(QThread):
    progress_signal = pyqtSignal(str)
    result_signal = pyqtSignal(list)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, device_id, findstr=''):
        super(ADBListPackageThread, self).__init__()
        self.device_id = device_id
        self.findstr = findstr

    def run(self):
        try:
            self.progress_signal.emit("正在获取应用列表...")
            
            # 首先检查设备连接
            from Function_Moudle.adb_utils import check_device_connection
            is_connected, error_msg = check_device_connection(self.device_id)
            if not is_connected:
                self.error_signal.emit(error_msg)
                return
            
            # 使用ADB命令列出所有包名
            command = f"adb -s {self.device_id} shell pm list packages"
            result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            if result.returncode != 0:
                self.error_signal.emit(f"获取应用列表失败: {result.stderr}")
                return
            
            # 解析包名列表
            packages = []
            for line in result.stdout.split('\n'):
                if line.startswith('package:'):
                    package_name = line.replace('package:', '').strip()
                    if self.findstr:
                        if self.findstr.lower() in package_name.lower():
                            packages.append(package_name)
                    else:
                        packages.append(package_name)
            
            total_apps = len(packages)
            if self.findstr:
                self.progress_signal.emit(f"设备上共有 {total_apps} 个应用，包含关键字 {self.findstr}")
            else:
                self.progress_signal.emit(f"设备上共有 {total_apps} 个应用")
            
            # 批量发送结果
            batch_size = 50
            for i in range(0, len(packages), batch_size):
                batch = packages[i:i + batch_size]
                # 为每个包添加版本信息
                batch_with_version = []
                for package in batch:
                    try:
                        version_command = f"adb -s {self.device_id} shell dumpsys package {package}"
                        version_result = subprocess.run(version_command, shell=True, check=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                        
                        # 提取版本信息
                        version_match = re.search(r'versionName=(\S+)', version_result.stdout)
                        if version_match:
                            version = version_match.group(1)
                        else:
                            version = '未知版本'
                        
                        batch_with_version.append(f"{package}, 版本号: {version}")
                    except Exception:
                        batch_with_version.append(f"{package}, 版本号: 获取失败")
                
                self.result_signal.emit(batch_with_version)
                
                # 更新进度
                progress = min((i + len(batch)) / total_apps * 100, 100)
                self.progress_signal.emit(f"处理进度: {progress:.1f}% ({min(i + len(batch), total_apps)}/{total_apps})")
            
            self.finished_signal.emit(f"\n完成! 共处理 {total_apps} 个应用")
            
        except subprocess.CalledProcessError as e:
            self.error_signal.emit(f"获取应用列表失败: {e}")
        except Exception as e:
            self.error_signal.emit(f"获取应用列表失败: {e}")