#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络代理管理线程 - 支持U2和ADB两种模式
提供获取、设置和清除网络代理功能
"""

from PyQt5.QtCore import QThread, pyqtSignal
import sys
import os
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from adb_utils import adb_utils
except ImportError:
    from fallbacks import ADBUtilsFallback
    adb_utils = ADBUtilsFallback()


class GetProxyThread(QThread):
    """获取网络代理信息线程 - 支持U2和ADB模式"""

    progress_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    def __init__(self, device_id, connection_mode='adb', u2_device=None):
        """
        初始化线程

        Args:
            device_id: 设备ID
            connection_mode: 连接模式 ('u2' 或 'adb')
            u2_device: U2设备对象（仅当connection_mode='u2'时使用）
        """
        super().__init__()
        self.device_id = device_id
        self.connection_mode = connection_mode
        self.u2_device = u2_device


    def _get_proxy_u2(self):
        """U2模式下获取代理"""
        try:
            d = self.u2_device
            result = d.shell("settings get global http_proxy")
            # 处理不同格式的返回值
            if hasattr(result, 'output'):
                # uiautomator2 新版本返回对象
                proxy_info = str(result.output).strip()
            elif hasattr(result, '__str__'):
                # 可能是字符串或其他类型
                proxy_info = str(result).strip()
            else:
                proxy_info = ""

            # 清理可能的空值和特殊值
            if not proxy_info or proxy_info == "" or proxy_info == ":0":
                self.result_signal.emit("当前未设置代理")
            else:
                self.result_signal.emit(f"当前代理: {proxy_info}")

        except Exception as e:
            self.error_signal.emit(f"U2模式获取代理失败: {str(e)}")

    def run(self):
        """执行获取代理操作"""
        try:
            self.progress_signal.emit("正在获取网络代理信息...")

            if self.connection_mode == 'u2' and self.u2_device:
                # U2模式获取代理
                self._get_proxy_u2()
            elif self.connection_mode == 'adb':
                # ADB模式获取代理
                self._get_proxy_adb()
            else:
                self.error_signal.emit("设备未连接或连接模式无效")

        except Exception as e:
            self.error_signal.emit(f"获取代理失败: {str(e)}")

    def _get_proxy_adb(self):
        """ADB模式下获取代理"""
        try:
            result = adb_utils.run_adb_command(
                command="shell settings get global http_proxy",
                device_id=self.device_id
            )

            if result.returncode == 0:
                proxy_info = result.stdout.strip() if result.stdout else ""

                # 清理可能的空值和特殊值
                if not proxy_info or proxy_info == "" or proxy_info == ":0":
                    self.result_signal.emit("当前未设置代理")
                else:
                    self.result_signal.emit(f"当前代理: {proxy_info}")
            else:
                error_msg = result.stderr.strip() if result.stderr else "未知错误"
                self.error_signal.emit(f"获取代理失败: {error_msg}")

        except Exception as e:
            self.error_signal.emit(f"ADB模式获取代理失败: {str(e)}")



class SetProxyThread(QThread):
    """设置网络代理线程 - 支持U2和ADB模式"""

    progress_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, device_id, proxy_address, proxy_port, connection_mode='adb', u2_device=None):
        """
        初始化线程

        Args:
            device_id: 设备ID
            proxy_address: 代理服务器地址 (如: 192.168.137.1)
            proxy_port: 代理服务器端口 (如: 7897)
            connection_mode: 连接模式 ('u2' 或 'adb')
            u2_device: U2设备对象（仅当connection_mode='u2'时使用）
        """
        super().__init__()
        self.device_id = device_id
        self.proxy_address = proxy_address
        self.proxy_port = proxy_port
        self.connection_mode = connection_mode
        self.u2_device = u2_device

    def run(self):
        """执行设置代理操作"""
        try:
            proxy_string = f"{self.proxy_address}:{self.proxy_port}"
            self.progress_signal.emit(f"正在设置网络代理: {proxy_string}...")

            if self.connection_mode == 'u2' and self.u2_device:
                # U2模式设置代理
                self._set_proxy_u2(proxy_string)
            elif self.connection_mode == 'adb':
                # ADB模式设置代理
                self._set_proxy_adb(proxy_string)
            else:
                self.error_signal.emit("设备未连接或连接模式无效")

        except Exception as e:
            self.error_signal.emit(f"设置代理失败: {str(e)}")

    def _set_proxy_u2(self, proxy_string):
        """U2模式下设置代理"""
        try:
            # 检查u2设备是否有效
            if not self.u2_device:
                self.error_signal.emit("U2设备对象无效")
                return

            d = self.u2_device
            result = d.shell(f"settings put global http_proxy {proxy_string}")

            # 处理不同格式的返回值
            if hasattr(result, 'exit_code'):
                # uiautomator2 新版本返回对象
                exit_code = result.exit_code
                output = str(result.output).strip() if hasattr(result, 'output') else ""
            else:
                # 旧版本或其他情况，假设成功
                exit_code = 0
                output = str(result).strip() if result else ""

            # settings put命令成功时通常没有输出或exit_code为0
            if exit_code == 0 or not output:
                self.result_signal.emit(f"代理设置成功: {proxy_string}")
            else:
                self.error_signal.emit(f"设置代理失败: {output}")

        except AttributeError as e:
            self.error_signal.emit(f"U2设备连接异常: {str(e)}")
        except Exception as e:
            self.error_signal.emit(f"U2模式设置代理失败: {str(e)}")

    def _set_proxy_adb(self, proxy_string):
        """ADB模式下设置代理"""
        try:
            result = adb_utils.run_adb_command(
                command=f"shell settings put global http_proxy {proxy_string}",
                device_id=self.device_id
            )

            if result.returncode == 0:
                self.result_signal.emit(f"代理设置成功: {proxy_string}")
            else:
                error_msg = result.stderr.strip() if result.stderr else "未知错误"
                self.error_signal.emit(f"设置代理失败: {error_msg}")

        except Exception as e:
            self.error_signal.emit(f"ADB模式设置代理失败: {str(e)}")


class ClearProxyThread(QThread):
    """清除网络代理线程 - 支持U2和ADB模式"""

    progress_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, device_id, connection_mode='adb', u2_device=None):
        """
        初始化线程

        Args:
            device_id: 设备ID
            connection_mode: 连接模式 ('u2' 或 'adb')
            u2_device: U2设备对象（仅当connection_mode='u2'时使用）
        """
        super().__init__()
        self.device_id = device_id
        self.connection_mode = connection_mode
        self.u2_device = u2_device

    def run(self):
        """执行清除代理操作"""
        try:
            self.progress_signal.emit("正在清除网络代理...")

            if self.connection_mode == 'u2' and self.u2_device:
                # U2模式清除代理
                self._clear_proxy_u2()
            elif self.connection_mode == 'adb':
                # ADB模式清除代理
                self._clear_proxy_adb()
            else:
                self.error_signal.emit("设备未连接或连接模式无效")

        except Exception as e:
            self.error_signal.emit(f"清除代理失败: {str(e)}")

    def _clear_proxy_u2(self):
        """U2模式下清除代理"""
        try:
            d = self.u2_device
            result = d.shell("settings put global http_proxy :0")

            # 处理不同格式的返回值
            if hasattr(result, 'exit_code'):
                # uiautomator2 新版本返回对象
                exit_code = result.exit_code
                output = str(result.output).strip() if hasattr(result, 'output') else ""
            else:
                # 旧版本或其他情况，假设成功
                exit_code = 0
                output = str(result).strip() if result else ""

            # settings put命令成功时通常没有输出或exit_code为0
            if exit_code == 0 or not output:
                self.result_signal.emit("代理已清除")
            else:
                self.error_signal.emit(f"清除代理失败: {output}")

        except Exception as e:
            self.error_signal.emit(f"U2模式清除代理失败: {str(e)}")

    def _clear_proxy_adb(self):
        """ADB模式下清除代理"""
        try:
            result = adb_utils.run_adb_command(
                command="shell settings put global http_proxy :0",
                device_id=self.device_id
            )

            if result.returncode == 0:
                self.result_signal.emit("代理已清除")
            else:
                error_msg = result.stderr.strip() if result.stderr else "未知错误"
                self.error_signal.emit(f"清除代理失败: {error_msg}")

        except Exception as e:
            self.error_signal.emit(f"ADB模式清除代理失败: {str(e)}")
