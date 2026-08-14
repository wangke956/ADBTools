from PyQt6.QtCore import pyqtSignal
from .base_thread import BaseThread
from logger_manager import log_operation, measure_performance, log_exception
import requests
import os
import json
import socket

# 全局socket超时，防止github握手卡死
socket.setdefaulttimeout(8)


class CheckUpdateThread(BaseThread):
    """检查更新线程"""

    update_available_signal = pyqtSignal(dict)  # 发送更新信息
    no_update_signal = pyqtSignal(str)
    check_failed_signal = pyqtSignal(str)

    def __init__(self, current_version):
        super().__init__("CheckUpdateThread")
        self.current_version = current_version
        self._stop_flag = False

    def stop(self):
        """外部调用终止线程"""
        self._stop_flag = True
        self.quit()

    def _run_implementation(self):
        self.progress_signal.emit("正在检查更新...")
        # 双备用接口，防止github无法访问
        api_list = [
            "https://api.github.com/repos/wangke956/ADBTools/releases/latest",
            "https://cdn.jsdelivr.net/gh/wangke956/ADBTools@main/latest.json"
        ]
        resp = None
        used_url = ""
        try:
            for url in api_list:
                if self._stop_flag:
                    return
                try:
                    resp = requests.get(url, timeout=8)
                    if resp.status_code == 200:
                        used_url = url
                        break
                except Exception:
                    continue

            if resp is None or resp.status_code != 200:
                raise ConnectionError("所有更新接口均无法访问")

            release_info = resp.json()
            if used_url.endswith(".json"):
                # 适配备用json格式
                latest_version = release_info.get("latest", "0.0.0").lstrip("v")
            else:
                latest_version = release_info.get('tag_name', 'v0.0.0').lstrip('v')

            # 版本对比
            if self._is_version_newer(latest_version, self.current_version):
                update_info = {
                    'current_version': self.current_version,
                    'latest_version': latest_version,
                    'release_name': release_info.get('name', ''),
                    'release_body': release_info.get('body', ''),
                    'html_url': release_info.get('html_url', ''),
                    'is_fallback': False
                }
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

        except requests.exceptions.RequestException as e:
            err = f"网络连接失败: {str(e)}"
            self.check_failed_signal.emit(err)
            self.error_signal.emit(f"检查更新失败: {str(e)}")
            log_exception()
        except Exception as e:
            err = f"检查更新时发生错误: {str(e)}"
            self.check_failed_signal.emit(err)
            self.error_signal.emit(err)
            log_exception()

    def _is_version_newer(self, latest, current):
        try:
            # 剔除版本后缀 1.1.0-alpha → 1.1.0
            def clean_ver(v):
                return v.split("-")[0]
            latest_parts = list(map(int, clean_ver(latest).split('.')))
            current_parts = list(map(int, clean_ver(current).split('.')))
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts += [0] * (max_len - len(latest_parts))
            current_parts += [0] * (max_len - len(current_parts))
            return latest_parts > current_parts
        except Exception:
            log_exception()
            return False


class DownloadUpdateThread(BaseThread):
    """下载更新线程"""
    progress_signal = pyqtSignal(int)
    download_complete_signal = pyqtSignal(str)

    def __init__(self, download_url, save_path):
        super().__init__("DownloadUpdateThread")
        self.download_url = download_url
        self.save_path = save_path
        self._stop_flag = False

    def stop(self):
        self._stop_flag = True
        self.quit()

    def _run_implementation(self):
        self.progress_signal.emit(0)
        self.progress_signal.emit("开始下载更新...")
        try:
            os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
            response = requests.get(self.download_url, stream=True, timeout=300)
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            with open(self.save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    # 收到停止信号立刻终止写入
                    if self._stop_flag:
                        response.close()
                        os.remove(self.save_path)
                        self.error_signal.emit("下载已取消")
                        return
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
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
            log_exception()
