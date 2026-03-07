"""
公共 Fallback 类定义

当主模块导入失败时，提供备用实现。
集中定义避免代码重复，同时保持模块独立性。
"""

import subprocess
import os


class ADBUtilsFallback:
    """ADB工具类的备用实现"""
    
    @staticmethod
    def run_adb_command(command, device_id=None, **kwargs):
        adb_cmd = "adb"
        if device_id:
            full_command = f'{adb_cmd} -s {device_id} {command}'
        else:
            full_command = f'{adb_cmd} {command}'
        
        default_kwargs = {
            'shell': True,
            'capture_output': True,
            'text': True,
            'encoding': 'utf-8',
            'errors': 'ignore'
        }
        default_kwargs.update(kwargs)
        
        return subprocess.run(full_command, **default_kwargs)


class ConfigManagerFallback:
    """配置管理器的备用实现"""
    
    def get(self, key, default=None):
        if key == "batch_install.special_packages":
            return {
                "@com.saicmotor.voiceservice": {
                    "delete_before_push": False,
                    "description": "voiceservice包，只push不删除"
                },
                "@com.saicmotor.adapterservice": {
                    "delete_before_push": False,
                    "description": "adapterservice包，只push不删除"
                }
            }
        return default
    
    def save(self):
        pass


class MockResult:
    """模拟subprocess返回结果"""
    
    def __init__(self, stdout="", stderr="", returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
