#!/usr/bin/env python3
"""
Fallbacks module - 提供模拟对象用于测试和兼容性处理
"""

import subprocess


class MockResult:
    """
    模拟 subprocess.CompletedProcess 对象
    
    用于在没有实际执行命令的情况下返回模拟结果，
    主要用于测试模式或当真实命令无法执行时的回退方案。
    """
    
    def __init__(self, stdout="", stderr="", returncode=0):
        """
        初始化模拟结果
        
        Args:
            stdout (str): 标准输出内容
            stderr (str): 标准错误内容
            returncode (int): 返回码，0表示成功，非0表示失败
        """
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
    
    def __str__(self):
        """字符串表示"""
        if self.returncode == 0:
            return f"MockResult(success=True, stdout='{self.stdout}')"
        else:
            return f"MockResult(success=False, stderr='{self.stderr}', returncode={self.returncode})"
    
    def __repr__(self):
        """详细字符串表示"""
        return (f"MockResult(stdout={self.stdout!r}, "
                f"stderr={self.stderr!r}, "
                f"returncode={self.returncode})")


class ADBUtilsFallback:
    """
    ADBUtils 的回退实现
    
    当真实的 adb_utils 模块不可用时使用此回退类
    """
    
    @staticmethod
    def run_adb_command(command, device_id=None, **kwargs):
        """模拟运行ADB命令"""
        return MockResult("", f"Fallback: Command not executed: {command}", 1)
    
    @staticmethod
    def get_adb_path():
        """获取ADB路径的默认值"""
        return "adb"
    
    @staticmethod
    def check_adb_available():
        """检查ADB是否可用（总是返回False）"""
        return False
    
    @staticmethod
    def get_devices():
        """获取设备列表（返回空列表）"""
        return []


class ConfigManagerFallback:
    """
    配置管理器的回退实现
    
    当真实的 config_manager 模块不可用时使用此回退类
    """
    
    def __init__(self):
        self._config = {}
    
    def get(self, key, default=None):
        """获取配置项"""
        return self._config.get(key, default)
    
    def set(self, key, value):
        """设置配置项"""
        self._config[key] = value
    
    def save(self):
        """保存配置（空操作）"""
        pass
    
    def load(self):
        """加载配置（空操作）"""
        pass


# 导出所有回退类
__all__ = [
    'MockResult',
    'ADBUtilsFallback', 
    'ConfigManagerFallback'
]
