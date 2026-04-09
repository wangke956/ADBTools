from PyQt5.QtCore import pyqtSignal
from .base_thread import BaseThread
from logger_manager import log_operation, measure_performance, log_exception
import requests
import os
import json


class CheckUpdateThread(BaseThread):
    """检查更新线程"""
    
    update_available_signal = pyqtSignal(dict)  # 发送更新信息
    no_update_signal = pyqtSignal(str)
    check_failed_signal = pyqtSignal(str)
    
    def __init__(self, current_version):
        super().__init__("CheckUpdateThread")
        self.current_version = current_version
        
    def _run_implementation(self):
        """执行检查更新操作"""
        self.progress_signal.emit("正在检查更新...")
        
        try:
            # GitHub API URL
            api_url = "https://api.github.com/repos/wangke956/ADBTools/releases/latest"
            
            # 发送请求
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 200:
                release_info = response.json()
                
                # 获取最新版本号
                latest_version = release_info.get('tag_name', 'v0.0.0').lstrip('v')
                
                # 比较版本
                if self._is_version_newer(latest_version, self.current_version):
                    # 准备更新信息
                    update_info = {
                        'current_version': self.current_version,
                        'latest_version': latest_version,
                        'release_name': release_info.get('name', ''),
                        'release_body': release_info.get('body', ''),
                        'html_url': release_info.get('html_url', ''),
                        'is_fallback': False
                    }
                    
                    # 获取安装文件信息
                    assets = release_info.get('assets', [])
                    for asset in assets:
                        if asset.get('name', '').endswith('.exe'):
                            update_info['setup_file'] = {
                                'name': asset.get('name'),
                                'size': asset.get('size'),
                                'download_url': asset.get('browser_download_url')
                            }
                            break
                    
                    self.update_available_signal.emit(update_info)
                    self.progress_signal.emit(f"发现新版本: v{latest_version}")
                else:
                    self.no_update_signal.emit("当前已是最新版本")
                    self.progress_signal.emit("当前已是最新版本")
            else:
                # 如果GitHub API失败，使用备用信息
                self.progress_signal.emit("GitHub API访问失败，使用备用信息")
                update_info = {
                    'current_version': self.current_version,
                    'latest_version': self.current_version,
                    'is_fallback': True,
                    'html_url': "https://github.com/wangke956/ADBTools"
                }
                self.update_available_signal.emit(update_info)
                
        except requests.exceptions.RequestException as e:
            self.check_failed_signal.emit(f"网络连接失败: {str(e)}")
            self.error_signal.emit(f"检查更新失败: {str(e)}")
        except Exception as e:
            self.check_failed_signal.emit(f"检查更新时发生错误: {str(e)}")
            self.error_signal.emit(f"检查更新失败: {str(e)}")
    
    def _is_version_newer(self, latest, current):
        """比较版本号是否更新"""
        try:
            latest_parts = list(map(int, latest.split('.')))
            current_parts = list(map(int, current.split('.')))
            
            # 补齐版本号长度
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts += [0] * (max_len - len(latest_parts))
            current_parts += [0] * (max_len - len(current_parts))
            
            return latest_parts > current_parts
        except:
            return False


class DownloadUpdateThread(BaseThread):
    """下载更新线程"""
    
    progress_signal = pyqtSignal(int)  # 进度百分比
    download_complete_signal = pyqtSignal(str)
    
    def __init__(self, download_url, save_path):
        super().__init__("DownloadUpdateThread")
        self.download_url = download_url
        self.save_path = save_path
        
    def _run_implementation(self):
        """执行下载更新操作"""
        self.progress_signal.emit(0)
        self.progress_signal.emit("开始下载更新...")
        
        try:
            # 确保保存目录存在
            os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
            
            # 发送请求并下载
            response = requests.get(self.download_url, stream=True, timeout=300)
            total_size = int(response.headers.get('content-length', 0))
            
            downloaded_size = 0
            with open(self.save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # 计算进度
                        if total_size > 0:
                            progress = int((downloaded_size / total_size) * 100)
                            self.progress_signal.emit(progress)
            
            self.progress_signal.emit(100)
            self.progress_signal.emit("下载完成")
            self.download_complete_signal.emit(self.save_path)
            self.success_signal.emit("更新包下载成功")
            
        except requests.exceptions.RequestException as e:
            self.error_signal.emit(f"下载失败: {str(e)}")
        except Exception as e:
            self.error_signal.emit(f"下载更新时发生错误: {str(e)}")
