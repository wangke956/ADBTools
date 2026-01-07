from PyQt5.QtCore import QThread, pyqtSignal
import requests
import json
import re
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class CheckUpdateThread(QThread):
    """检查GitHub更新的线程"""
    
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    update_available_signal = pyqtSignal(dict)  # 发送更新信息
    no_update_signal = pyqtSignal(str)  # 发送无更新信息
    check_failed_signal = pyqtSignal(str)  # 发送检查失败信息

    def __init__(self, current_version="1.0"):
        """
        初始化线程
        
        Args:
            current_version: 当前版本号
        """
        super(CheckUpdateThread, self).__init__()
        self.current_version = current_version
        self.github_api_url = "https://api.github.com/repos/wangke956/ADBTools/releases/latest"
        self.github_repo_url = "https://github.com/wangke956/ADBTools"

    def _get_latest_version_from_github(self):
        """从GitHub API获取最新版本信息"""
        try:
            self.progress_signal.emit("正在连接GitHub服务器...")
            
            # 设置请求头，避免被GitHub限制
            headers = {
                'User-Agent': 'ADBTools-Update-Checker/1.0',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # 发送请求获取最新release
            response = requests.get(self.github_api_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # 提取版本信息
                latest_version = data.get('tag_name', '')
                release_name = data.get('name', '')
                release_body = data.get('body', '')
                html_url = data.get('html_url', self.github_repo_url)
                published_at = data.get('published_at', '')
                prerelease = data.get('prerelease', False)
                assets = data.get('assets', [])
                
                # 清理版本号（移除可能的'v'前缀）
                if latest_version.startswith('v') or latest_version.startswith('V'):
                    latest_version = latest_version[1:]
                
                self.progress_signal.emit(f"成功获取GitHub版本信息: {latest_version}")
                
                # 查找安装文件
                setup_file_info = self._find_setup_file_in_assets(assets)
                
                return {
                    'success': True,
                    'latest_version': latest_version,
                    'release_name': release_name,
                    'release_body': release_body,
                    'html_url': html_url,
                    'published_at': published_at,
                    'prerelease': prerelease,
                    'assets': assets,
                    'setup_file': setup_file_info
                }
            elif response.status_code == 404:
                # 如果没有releases，尝试获取仓库信息作为备用
                self.progress_signal.emit("未找到发布版本，尝试获取仓库信息...")
                return self._get_repository_info_as_fallback()
            else:
                error_msg = f"GitHub API请求失败: HTTP {response.status_code}"
                if response.status_code == 403:
                    error_msg += " - API限制，请稍后重试"
                
                self.error_signal.emit(error_msg)
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except requests.exceptions.Timeout:
            error_msg = "连接GitHub服务器超时，请检查网络连接"
            self.error_signal.emit(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        except requests.exceptions.ConnectionError:
            error_msg = "无法连接到GitHub服务器，请检查网络连接"
            self.error_signal.emit(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求错误: {str(e)}"
            self.error_signal.emit(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        except json.JSONDecodeError:
            error_msg = "GitHub API响应格式错误"
            self.error_signal.emit(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"获取GitHub版本信息时发生未知错误: {str(e)}"
            self.error_signal.emit(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    def _find_setup_file_in_assets(self, assets):
        """在assets中查找安装文件
        
        Args:
            assets: GitHub Release的assets列表
            
        Returns:
            dict: 安装文件信息，包含name、browser_download_url、size等
        """
        if not assets:
            return None
            
        # 优先查找的文件名模式（按优先级排序）
        setup_patterns = [
            r'.*setup.*\.exe$',
            r'.*install.*\.exe$',
            r'.*ADBTools.*\.exe$',
            r'.*\.msi$',
            r'.*\.exe$',
            r'.*\.zip$',
            r'.*\.7z$',
            r'.*\.rar$'
        ]
        
        for pattern in setup_patterns:
            import re
            for asset in assets:
                asset_name = asset.get('name', '')
                if re.match(pattern, asset_name, re.IGNORECASE):
                    return {
                        'name': asset_name,
                        'browser_download_url': asset.get('browser_download_url', ''),
                        'size': asset.get('size', 0),
                        'content_type': asset.get('content_type', ''),
                        'download_count': asset.get('download_count', 0)
                    }
                    
        return None

    def _get_repository_info_as_fallback(self):
        """获取仓库信息作为备用（当没有releases时）"""
        try:
            # 获取仓库信息
            repo_api_url = "https://api.github.com/repos/wangke956/ADBTools"
            headers = {
                'User-Agent': 'ADBTools-Update-Checker/1.0',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(repo_api_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                repo_data = response.json()
                
                # 使用默认版本号
                latest_version = "1.0"  # 默认版本
                repo_name = repo_data.get('name', 'ADBTools')
                description = repo_data.get('description', '一个功能强大的ADB调试工具')
                html_url = repo_data.get('html_url', self.github_repo_url)
                updated_at = repo_data.get('updated_at', '')
                
                self.progress_signal.emit("成功获取仓库信息")
                
                return {
                    'success': True,
                    'latest_version': latest_version,
                    'release_name': f"{repo_name} 仓库",
                    'release_body': f"仓库描述: {description}\n\n注意：此仓库尚未创建发布版本。",
                    'html_url': html_url,
                    'published_at': updated_at,
                    'prerelease': False,
                    'is_fallback': True,  # 标记为备用信息
                    'assets': [],
                    'setup_file': None
                }
            else:
                error_msg = f"获取仓库信息失败: HTTP {response.status_code}"
                self.error_signal.emit(error_msg)
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            error_msg = f"获取仓库信息时发生错误: {str(e)}"
            self.error_signal.emit(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    def _compare_versions(self, current_version, latest_version):
        """比较版本号
        
        Args:
            current_version: 当前版本号 (如: "1.0.0")
            latest_version: 最新版本号 (如: "1.1.0")
            
        Returns:
            int: -1 if current < latest, 0 if equal, 1 if current > latest
        """
        try:
            # 清理版本号
            current = self._normalize_version(current_version)
            latest = self._normalize_version(latest_version)
            
            # 分割版本号
            current_parts = current.split('.')
            latest_parts = latest.split('.')
            
            # 确保两个版本号有相同数量的部分
            max_length = max(len(current_parts), len(latest_parts))
            current_parts = current_parts + ['0'] * (max_length - len(current_parts))
            latest_parts = latest_parts + ['0'] * (max_length - len(latest_parts))
            
            # 比较每个部分
            for i in range(max_length):
                current_num = self._parse_version_part(current_parts[i])
                latest_num = self._parse_version_part(latest_parts[i])
                
                if current_num < latest_num:
                    return -1  # 当前版本较旧
                elif current_num > latest_num:
                    return 1   # 当前版本较新
            
            return 0  # 版本相同
            
        except Exception as e:
            self.error_signal.emit(f"比较版本号时出错: {str(e)}")
            # 如果比较失败，使用简单的字符串比较
            if current_version < latest_version:
                return -1
            elif current_version > latest_version:
                return 1
            else:
                return 0

    def _normalize_version(self, version):
        """规范化版本号字符串"""
        if not version:
            return "0.0.0"
        
        # 移除非数字和点的字符，但保留数字和点
        version = re.sub(r'[^0-9.]', '', version)
        
        # 确保至少有一个点
        if '.' not in version:
            version = version + '.0'
        
        return version

    def _parse_version_part(self, part):
        """解析版本号部分为整数"""
        try:
            # 尝试转换为整数
            return int(part)
        except ValueError:
            # 如果不是纯数字，尝试提取数字部分
            match = re.search(r'\d+', part)
            if match:
                return int(match.group())
            return 0

    def run(self):
        """线程主函数"""
        try:
            self.progress_signal.emit("开始检查更新...")
            
            # 获取GitHub最新版本
            github_result = self._get_latest_version_from_github()
            
            if not github_result['success']:
                self.check_failed_signal.emit(github_result['error'])
                return
            
            latest_version = github_result['latest_version']
            is_fallback = github_result.get('is_fallback', False)
            
            if not latest_version:
                self.check_failed_signal.emit("无法从GitHub获取有效的版本号")
                return
            
            # 比较版本
            comparison = self._compare_versions(self.current_version, latest_version)
            
            if is_fallback:
                # 使用的是备用信息（没有releases）
                update_info = {
                    'current_version': self.current_version,
                    'latest_version': latest_version,
                    'release_name': github_result['release_name'],
                    'release_body': github_result['release_body'],
                    'html_url': github_result['html_url'],
                    'published_at': github_result['published_at'],
                    'prerelease': github_result['prerelease'],
                    'assets': github_result.get('assets', []),
                    'setup_file': github_result.get('setup_file'),
                    'is_fallback': True
                }
                self.update_available_signal.emit(update_info)
            elif comparison < 0:
                # 有更新可用
                update_info = {
                    'current_version': self.current_version,
                    'latest_version': latest_version,
                    'release_name': github_result['release_name'],
                    'release_body': github_result['release_body'],
                    'html_url': github_result['html_url'],
                    'published_at': github_result['published_at'],
                    'prerelease': github_result['prerelease'],
                    'assets': github_result.get('assets', []),
                    'setup_file': github_result.get('setup_file')
                }
                self.update_available_signal.emit(update_info)
            elif comparison == 0:
                # 已经是最新版本
                self.no_update_signal.emit(f"您已经使用的是最新版本 v{self.current_version}")
            else:
                # 当前版本比GitHub上的版本还新（可能是开发版）
                self.no_update_signal.emit(f"当前版本 v{self.current_version} 比GitHub上的版本 v{latest_version} 更新")
                
        except Exception as e:
            error_msg = f"检查更新过程中发生错误: {str(e)}"
            self.error_signal.emit(error_msg)
            self.check_failed_signal.emit(error_msg)