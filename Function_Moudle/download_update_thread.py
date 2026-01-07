from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker
import requests
import os
import tempfile
import sys
import time
import threading

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class DownloadUpdateThread(QThread):
    """下载更新文件的线程"""
    
    progress_signal = pyqtSignal(int, int, str)  # 当前大小, 总大小, 状态信息
    download_complete_signal = pyqtSignal(str)   # 下载完成的文件路径
    error_signal = pyqtSignal(str)               # 错误信息
    download_canceled_signal = pyqtSignal()      # 下载被取消

    def __init__(self, download_url, file_name=None):
        """
        初始化下载线程
        
        Args:
            download_url: 下载链接
            file_name: 保存的文件名（可选）
        """
        super(DownloadUpdateThread, self).__init__()
        self.download_url = download_url
        self.file_name = file_name
        self._canceled = False
        self._mutex = QMutex()  # 线程锁
        self.temp_dir = tempfile.gettempdir()
        self.save_path = None
        
    def cancel(self):
        """取消下载"""
        with QMutexLocker(self._mutex):
            self._canceled = True
            
    def is_canceled(self):
        """检查是否已取消"""
        with QMutexLocker(self._mutex):
            return self._canceled
        
    def _get_filename_from_url(self, url):
        """从URL中提取文件名"""
        if not url:
            return "update_setup.exe"
            
        # 从URL中提取文件名
        filename = os.path.basename(url)
        
        # 如果没有扩展名，添加默认扩展名
        if not os.path.splitext(filename)[1]:
            filename = "ADBTools_Setup.exe"
            
        return filename
        
    def _get_filename_from_content_disposition(self, headers):
        """从Content-Disposition头中提取文件名"""
        content_disposition = headers.get('content-disposition', '')
        if not content_disposition:
            return None
            
        # 查找filename=部分
        import re
        match = re.search(r'filename\*?=["\']?([^"\';]+)', content_disposition)
        if match:
            filename = match.group(1)
            # 处理URL编码
            import urllib.parse
            return urllib.parse.unquote(filename)
            
        return None
        
    def run(self):
        """线程主函数"""
        try:
            # 确定保存的文件名
            if not self.file_name:
                self.file_name = self._get_filename_from_url(self.download_url)
                
            # 完整的保存路径
            self.save_path = os.path.join(self.temp_dir, self.file_name)
            
            self.progress_signal.emit(0, 0, f"开始下载更新文件: {self.file_name}")
            
            # 检查是否已取消
            if self.is_canceled():
                self.progress_signal.emit(0, 0, "下载已取消")
                self.download_canceled_signal.emit()
                return
            
            # 设置请求头
            headers = {
                'User-Agent': 'ADBTools-Updater/1.0',
                'Accept': '*/*'
            }
            
            # 发送请求获取文件大小
            self.progress_signal.emit(0, 0, "正在获取文件信息...")
            
            try:
                response = requests.get(self.download_url, headers=headers, stream=True, timeout=30)
            except Exception as e:
                self.error_signal.emit(f"连接失败: {str(e)}")
                return
            
            if response.status_code != 200:
                error_msg = f"下载失败: HTTP {response.status_code}"
                self.error_signal.emit(error_msg)
                response.close()
                return
                
            try:
                # 获取文件总大小
                total_size = int(response.headers.get('content-length', 0))
                
                # 尝试从响应头获取更好的文件名
                content_filename = self._get_filename_from_content_disposition(response.headers)
                if content_filename:
                    self.file_name = content_filename
                    self.save_path = os.path.join(self.temp_dir, self.file_name)
                    
                self.progress_signal.emit(0, total_size, f"文件大小: {self._format_size(total_size)}")
                
                # 检查是否已取消
                if self.is_canceled():
                    response.close()
                    self.progress_signal.emit(0, 0, "下载已取消")
                    self.download_canceled_signal.emit()
                    return
                
                # 下载文件
                downloaded_size = 0
                start_time = time.time()
                
                with open(self.save_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        # 检查是否已取消
                        if self.is_canceled():
                            response.close()
                            self._cleanup_partial_file()
                            self.progress_signal.emit(downloaded_size, total_size, "下载已取消")
                            self.download_canceled_signal.emit()
                            return
                            
                        if chunk:
                            file.write(chunk)
                            downloaded_size += len(chunk)
                            
                            # 计算下载速度
                            elapsed_time = time.time() - start_time
                            if elapsed_time > 0:
                                speed = downloaded_size / elapsed_time
                                speed_str = self._format_size(speed) + "/s"
                            else:
                                speed_str = "计算中..."
                                
                            # 计算进度百分比
                            if total_size > 0:
                                percent = (downloaded_size / total_size) * 100
                                status = f"下载中: {percent:.1f}% ({self._format_size(downloaded_size)}/{self._format_size(total_size)}) - {speed_str}"
                            else:
                                status = f"下载中: {self._format_size(downloaded_size)} - {speed_str}"
                                
                            # 发送进度信号
                            self.progress_signal.emit(downloaded_size, total_size, status)
                
                response.close()
                            
                # 下载完成
                if os.path.exists(self.save_path) and os.path.getsize(self.save_path) > 0:
                    self.progress_signal.emit(downloaded_size, total_size, "下载完成！")
                    self.download_complete_signal.emit(self.save_path)
                else:
                    self.error_signal.emit("下载的文件为空或不存在")
                    
            except Exception as e:
                response.close()
                self._cleanup_partial_file()
                raise e
                    
        except requests.exceptions.Timeout:
            self.error_signal.emit("下载超时，请检查网络连接")
        except requests.exceptions.ConnectionError:
            self.error_signal.emit("网络连接错误，请检查网络设置")
        except requests.exceptions.RequestException as e:
            self.error_signal.emit(f"下载请求错误: {str(e)}")
        except IOError as e:
            self.error_signal.emit(f"文件保存错误: {str(e)}")
        except Exception as e:
            self.error_signal.emit(f"下载过程中发生未知错误: {str(e)}")
            
    def _cleanup_partial_file(self):
        """清理部分下载的文件"""
        try:
            if self.save_path and os.path.exists(self.save_path):
                os.remove(self.save_path)
        except Exception as e:
            # 忽略清理错误，避免影响主流程
            pass
            
    def _format_size(self, size_bytes):
        """格式化文件大小显示"""
        if size_bytes == 0:
            return "0 B"
            
        size_names = ("B", "KB", "MB", "GB", "TB")
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
            
        return f"{size_bytes:.2f} {size_names[i]}"


class GitHubReleaseDownloader(QThread):
    """专门用于下载GitHub Release文件的线程"""
    
    progress_signal = pyqtSignal(int, int, str)
    download_complete_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    release_info_signal = pyqtSignal(dict)  # 发布信息
    
    def __init__(self, repo_owner="wangke956", repo_name="ADBTools"):
        """
        初始化GitHub Release下载器
        
        Args:
            repo_owner: 仓库所有者
            repo_name: 仓库名称
        """
        super(GitHubReleaseDownloader, self).__init__()
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        self._canceled = False
        
    def cancel(self):
        """取消下载"""
        self._canceled = True
        
    def _find_setup_file(self, assets):
        """在发布资源中查找安装文件"""
        # 优先查找的文件名模式
        setup_patterns = [
            r'.*setup.*\.exe$',
            r'.*install.*\.exe$',
            r'.*ADBTools.*\.exe$',
            r'.*\.msi$',
            r'.*\.exe$'
        ]
        
        for asset in assets:
            asset_name = asset.get('name', '').lower()
            for pattern in setup_patterns:
                import re
                if re.match(pattern, asset_name, re.IGNORECASE):
                    return asset
                    
        return None
        
    def run(self):
        """线程主函数"""
        try:
            self.progress_signal.emit(0, 0, "正在获取GitHub发布信息...")
            
            # 获取最新发布信息
            headers = {
                'User-Agent': 'ADBTools-Updater/1.0',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(self.github_api_url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                self.error_signal.emit(f"获取发布信息失败: HTTP {response.status_code}")
                return
                
            release_data = response.json()
            
            # 提取发布信息
            release_info = {
                'tag_name': release_data.get('tag_name', ''),
                'name': release_data.get('name', ''),
                'body': release_data.get('body', ''),
                'published_at': release_data.get('published_at', ''),
                'prerelease': release_data.get('prerelease', False),
                'assets': release_data.get('assets', [])
            }
            
            # 发送发布信息
            self.release_info_signal.emit(release_info)
            
            # 查找安装文件
            setup_asset = self._find_setup_file(release_info['assets'])
            
            if not setup_asset:
                self.error_signal.emit("未找到安装文件")
                return
                
            # 获取下载链接和文件名
            download_url = setup_asset.get('browser_download_url', '')
            file_name = setup_asset.get('name', 'ADBTools_Setup.exe')
            file_size = setup_asset.get('size', 0)
            
            if not download_url:
                self.error_signal.emit("安装文件没有下载链接")
                return
                
            self.progress_signal.emit(0, file_size, f"找到安装文件: {file_name}")
            
            # 下载文件
            download_thread = DownloadUpdateThread(download_url, file_name)
            
            # 连接信号
            def on_progress(current, total, status):
                self.progress_signal.emit(current, total, status)
                
            def on_complete(file_path):
                self.download_complete_signal.emit(file_path)
                
            def on_error(error_msg):
                self.error_signal.emit(error_msg)
                
            download_thread.progress_signal.connect(on_progress)
            download_thread.download_complete_signal.connect(on_complete)
            download_thread.error_signal.connect(on_error)
            
            # 启动下载
            download_thread.start()
            download_thread.wait()
            
        except requests.exceptions.Timeout:
            self.error_signal.emit("连接GitHub超时")
        except requests.exceptions.ConnectionError:
            self.error_signal.emit("无法连接到GitHub")
        except Exception as e:
            self.error_signal.emit(f"获取发布信息时发生错误: {str(e)}")