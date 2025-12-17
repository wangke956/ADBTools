#!/usr/bin/env python3
"""ADB工具类，解决PyInstaller打包后的ADB路径问题"""

import os
import subprocess
import sys
from pathlib import Path

# 导入配置管理器
try:
    from config_manager import config_manager
except ImportError:
    # 如果导入失败，创建简单的配置回退
    class ConfigManagerFallback:
        def get_adb_search_paths(self):
            # 默认搜索路径
            paths = []
            if sys.platform == "win32":
                paths.extend([
                    "adb.exe",
                    "adb",
                    os.path.join(os.environ.get("ANDROID_HOME", ""), "platform-tools", "adb.exe"),
                    os.path.join(os.environ.get("ANDROID_SDK_ROOT", ""), "platform-tools", "adb.exe"),
                    r"C:\Program Files (x86)\Android\android-sdk\platform-tools\adb.exe",
                    r"D:\work_tools\adb-1\adb.exe",
                ])
            else:
                paths.extend([
                    "adb",
                    os.path.join(os.environ.get("ANDROID_HOME", ""), "platform-tools", "adb"),
                    os.path.join(os.environ.get("ANDROID_SDK_ROOT", ""), "platform-tools", "adb"),
                    "/usr/bin/adb",
                    "/usr/local/bin/adb",
                ])
            
            # 如果是PyInstaller打包的exe，添加exe同目录路径
            if getattr(sys, 'frozen', False):
                exe_dir = os.path.dirname(sys.executable)
                if sys.platform == "win32":
                    paths.insert(0, os.path.join(exe_dir, "adb.exe"))
                    paths.insert(0, os.path.join(exe_dir, "tools", "adb.exe"))
                else:
                    paths.insert(0, os.path.join(exe_dir, "adb"))
                    paths.insert(0, os.path.join(exe_dir, "tools", "adb"))
            
            return paths
    
    config_manager = ConfigManagerFallback()

class ADBUtils:
    """ADB工具类，统一管理ADB命令执行"""
    
    # ADB路径缓存
    _adb_path = None
    
    @classmethod
    def get_adb_path(cls):
        """获取ADB可执行文件路径"""
        if cls._adb_path is not None:
            return cls._adb_path
        
        # 从配置文件中获取搜索路径
        possible_paths = config_manager.get_adb_search_paths()
        
        # 尝试查找ADB
        for path in possible_paths:
            try:
                # 检查是否是绝对路径且文件存在
                if os.path.isabs(path) and os.path.isfile(path):
                    cls._adb_path = path
                    return path
                
                # 检查相对路径（相对于当前工作目录）
                if os.path.isfile(path):
                    cls._adb_path = os.path.abspath(path)
                    return cls._adb_path
                
                # 尝试在系统PATH中查找
                if sys.platform == "win32":
                    result = subprocess.run(["where", path], capture_output=True, text=True)
                else:
                    result = subprocess.run(["which", path], capture_output=True, text=True)
                
                if result.returncode == 0:
                    found_path = result.stdout.strip().split('\n')[0]
                    if os.path.isfile(found_path):
                        cls._adb_path = found_path
                        return found_path
            except:
                continue
        
        # 如果都没找到，记录错误并返回"adb"（依赖系统PATH）
        print("警告: 未找到ADB可执行文件，将尝试使用系统PATH中的adb")
        cls._adb_path = "adb"
        return "adb"
    
    @classmethod
    def run_adb_command(cls, command, device_id=None, **kwargs):
        """执行ADB命令"""
        adb_path = cls.get_adb_path()
        
        # 构建完整命令
        if device_id:
            full_command = f'"{adb_path}" -s {device_id} {command}'
        else:
            full_command = f'"{adb_path}" {command}'
        
        # 设置默认参数
        default_kwargs = {
            'shell': True,
            'capture_output': True,
            'text': True,
            'encoding': 'utf-8',
            'errors': 'ignore'
        }
        default_kwargs.update(kwargs)
        
        try:
            result = subprocess.run(full_command, **default_kwargs)
            return result
        except Exception as e:
            # 创建模拟的subprocess结果对象
            class MockResult:
                def __init__(self):
                    self.returncode = 1
                    self.stdout = ""
                    self.stderr = str(e)
            
            return MockResult()
    
    @classmethod
    def check_adb_available(cls):
        """检查ADB是否可用"""
        try:
            result = cls.run_adb_command("version")
            return result.returncode == 0
        except:
            return False
    
    @classmethod
    def get_devices(cls):
        """获取设备列表"""
        result = cls.run_adb_command("devices")
        if result.returncode != 0:
            return []
        
        devices = []
        lines = result.stdout.strip().split('\n')[1:]  # 跳过第一行标题
        for line in lines:
            if line.strip():
                device_id = line.split('\t')[0]
                devices.append(device_id)
        
        return devices
    
    @classmethod
    def check_app_installed(cls, device_id, package_name):
        """检查应用是否已安装"""
        result = cls.run_adb_command(f"shell pm list packages {package_name}", device_id)
        if result.returncode != 0:
            return False
        
        stdout = result.stdout
        if not isinstance(stdout, str):
            stdout = str(stdout) if stdout is not None else ""
        
        return package_name in stdout
    
    @classmethod
    def get_app_version(cls, device_id, package_name):
        """获取应用版本信息"""
        result = cls.run_adb_command(f"shell dumpsys package {package_name} | grep versionName", device_id)
        if result.returncode != 0:
            return False, "获取版本信息失败"
        
        # 解析版本信息
        stdout = result.stdout
        for line in stdout.split('\n'):
            if 'versionName' in line:
                version = line.split('=')[-1].strip()
                return True, version
        
        return False, "未找到版本信息"


# 全局实例
adb_utils = ADBUtils()