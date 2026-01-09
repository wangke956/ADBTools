#!/usr/bin/env python3
"""配置文件管理器"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    """配置文件管理器"""
    
    DEFAULT_CONFIG = {
        # 版本配置 - 全局版本号定义
        "version": {
            "major": 1,
            "minor": 6,
            "patch": 0,
            "build": 0,
        },
        "adb": {
            "search_paths": [
                "adb",  # 系统PATH
                "adb.exe",
                "./adb.exe",  # 同目录
                "./tools/adb.exe",  # tools目录
                r"C:\Program Files (x86)\Android\android-sdk\platform-tools\adb.exe",
                r"D:\work_tools\adb-1\adb.exe",  # 默认路径
            ],
            "custom_path": "",  # 用户自定义路径
            "auto_detect": True,  # 是否自动检测
        },
        "ui": {
            "theme": "dark",  # dark/light
            "language": "zh_CN",  # zh_CN/en_US
            "font_size": 10,
        },
        "devices": {
            "default_device": "",  # 默认设备
            "auto_refresh": True,  # 自动刷新设备列表
            "refresh_interval": 5,  # 刷新间隔(秒)
        },
        "logging": {
            "level": "INFO",  # DEBUG/INFO/WARNING/ERROR
            "file": "adbtools.log",  # 日志文件
            "max_size": 10485760,  # 最大10MB
        },
        "batch_install": {
            "special_packages": {
                "@com.saicmotor.voiceservice": {
                    "delete_before_push": False,
                    "description": "voiceservice包，只push不删除"
                },
                "@com.saicmotor.adapterservice": {
                    "delete_before_push": True,
                    "description": "adapterservice包，先删除再push"
                }
            }
        }
    }
    
    def __init__(self, config_file: str = "adbtools_config.json"):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件名
        """
        self.config_file = config_file
        self.config = self.DEFAULT_CONFIG.copy()
        self.load_config()
    
    def get_config_path(self) -> str:
        """获取配置文件路径"""
        # 如果是PyInstaller打包的exe，配置文件放在exe同目录
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
            return os.path.join(exe_dir, self.config_file)
        
        # 否则放在项目根目录
        project_root = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(project_root, self.config_file)
    
    def load_config(self) -> None:
        """加载配置文件"""
        config_path = self.get_config_path()
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # 深度合并配置
                self._deep_merge(self.config, loaded_config)
                print(f"配置文件加载成功: {config_path}")
            except Exception as e:
                print(f"配置文件加载失败，使用默认配置: {e}")
                self._create_default_config()
        else:
            print(f"配置文件不存在，创建默认配置: {config_path}")
            self._create_default_config()
    
    def reload_config(self) -> None:
        """重新加载配置文件"""
        print(f"重新加载配置文件...")
        # 重置为默认配置
        self.config = self.DEFAULT_CONFIG.copy()
        # 重新加载
        self.load_config()
    
    def save_config(self) -> bool:
        """保存配置文件"""
        try:
            config_path = self.get_config_path()
            
            # 确保目录存在
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            print(f"配置文件保存成功: {config_path}")
            return True
        except Exception as e:
            print(f"配置文件保存失败: {e}")
            return False
    
    def _create_default_config(self) -> None:
        """创建默认配置文件"""
        self.save_config()
    
    def _deep_merge(self, target: Dict, source: Dict) -> None:
        """深度合并字典"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键，支持点号分隔，如 "adb.search_paths"
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """设置配置值
        
        Args:
            key: 配置键，支持点号分隔
            value: 配置值
            
        Returns:
            是否成功
        """
        keys = key.split('.')
        config = self.config
        
        try:
            # 遍历到最后一个键的父级
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # 设置值
            config[keys[-1]] = value
            
            # 自动保存
            self.save_config()
            return True
        except Exception as e:
            print(f"设置配置失败: {e}")
            return False
    
    def get_adb_search_paths(self) -> list:
        """获取ADB搜索路径列表"""
        paths = self.get("adb.search_paths", [])
        
        # 添加自定义路径（如果存在）
        custom_path = self.get("adb.custom_path", "")
        if custom_path and os.path.isfile(custom_path):
            paths.insert(0, custom_path)
        
        # 如果是PyInstaller打包的exe，添加exe同目录路径
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
            exe_paths = [
                os.path.join(exe_dir, "adb.exe"),
                os.path.join(exe_dir, "tools", "adb.exe"),
                os.path.join(exe_dir, "adb"),
            ]
            paths = exe_paths + paths
        
        return paths
    
    def set_adb_custom_path(self, path: str) -> bool:
        """设置ADB自定义路径"""
        if path and os.path.isfile(path):
            return self.set("adb.custom_path", path)
        return False
    
    def get_adb_custom_path(self) -> str:
        """获取ADB自定义路径"""
        return self.get("adb.custom_path", "")
    
    def is_auto_detect_adb(self) -> bool:
        """是否自动检测ADB"""
        return self.get("adb.auto_detect", True)
    
    # 版本号相关方法
    def get_version(self) -> str:
        """获取完整版本号 (格式: 主版本.次版本.修订号)"""
        major = self.get("version.major", 1)
        minor = self.get("version.minor", 0)
        patch = self.get("version.patch", 0)
        return f"{major}.{minor}.{patch}"
    
    def get_file_version(self) -> str:
        """获取文件版本号 (格式: 主版本.次版本.修订号.构建号)"""
        major = self.get("version.major", 1)
        minor = self.get("version.minor", 0)
        patch = self.get("version.patch", 0)
        build = self.get("version.build", 0)
        return f"{major}.{minor}.{patch}.{build}"
    
    def get_version_parts(self) -> dict:
        """获取版本号的各个部分"""
        return {
            "major": self.get("version.major", 1),
            "minor": self.get("version.minor", 0),
            "patch": self.get("version.patch", 0),
            "build": self.get("version.build", 0),
            "version": self.get_version(),
            "file_version": self.get_file_version()
        }
    
    def set_version(self, major: int, minor: int, patch: int, build: int = 0) -> bool:
        """设置版本号
        
        Args:
            major: 主版本号
            minor: 次版本号
            patch: 修订号
            build: 构建号 (可选)
            
        Returns:
            是否成功
        """
        success = True
        success = success and self.set("version.major", major)
        success = success and self.set("version.minor", minor)
        success = success and self.set("version.patch", patch)
        success = success and self.set("version.build", build)
        return success


# 全局配置管理器实例
config_manager = ConfigManager()