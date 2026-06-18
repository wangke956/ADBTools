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

    def _get_proxy_u2(self):
        """U2模式下获取代理"""
        try:
            d = self.u2_device
            result = d.shell("settings get global http_proxy")
            proxy_info = result.output.strip() if hasattr(result, 'output') else str(result).strip()
            
            if proxy_info and proxy_info != ":0":
                self.result_signal.emit(f"当前代理: {proxy_info}")
            else:
                self.result_signal.emit("当前未设置代理")
                
        except Exception as e:
            self.error_signal.emit(f"U2模式获取代理失败: {str(e)}")

    def _get_proxy_adb(self):
        """ADB模式下获取代理"""
        try:
            result = adb_utils.run_adb_command(
                command="shell settings get global http_proxy",
                device_id=self.device_id
            )
            
            if result.returncode == 0:
                proxy_info = result.stdout.strip()
                if proxy_info and proxy_info != ":0":
                    self.result_signal.emit(f"当前代理: {proxy_info}")
                else:
                    self.result_signal.emit("当前未设置代理")
            else:
                self.error_signal.emit(f"获取代理失败: {result.stderr}")
                
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
            d = self.u2_device
            result = d.shell(f"settings put global http_proxy {proxy_string}")
            output = result.output.strip() if hasattr(result, 'output') else str(result).strip()
            
            # settings put命令成功时通常没有输出
            if result.exit_code == 0 or not output:
                self.result_signal.emit(f"代理设置成功: {proxy_string}")
            else:
                self.error_signal.emit(f"设置代理失败: {output}")
                
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
                self.error_signal.emit(f"设置代理失败: {result.stderr}")
                
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
            output = result.output.strip() if hasattr(result, 'output') else str(result).strip()
            
            # settings put命令成功时通常没有输出
            if result.exit_code == 0 or not output:
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
                self.error_signal.emit(f"清除代理失败: {result.stderr}")
                
        except Exception as e:
            self.error_signal.emit(f"ADB模式清除代理失败: {str(e)}")
