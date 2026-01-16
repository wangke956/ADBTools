#!/usr/bin/env python3
"""增强版配置文件管理器 - 提供完整的配置文件修改功能"""

import os
import json
import sys
import copy
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

class EnhancedConfigManager:
    """增强版配置文件管理器"""
    
    DEFAULT_CONFIG = {
        # 版本配置 - 全局版本号定义
        "version": {
            "major": 1,
            "minor": 6,
            "patch": 2,
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
            "timeout": 30,  # ADB命令超时时间（秒）
            "retry_count": 3,  # ADB命令重试次数
        },
        "ui": {
            "theme": "dark",  # dark/light/auto
            "language": "zh_CN",  # zh_CN/en_US
            "font_size": 10,
            "font_family": "Microsoft YaHei",  # 字体
            "window_width": 1200,  # 窗口宽度
            "window_height": 800,  # 窗口高度
            "auto_save_layout": True,  # 自动保存窗口布局
            "show_tooltips": True,  # 显示工具提示
        },
        "devices": {
            "default_device": "",  # 默认设备
            "auto_refresh": True,  # 自动刷新设备列表
            "refresh_interval": 5,  # 刷新间隔(秒)
            "multithread_refresh": True,  # 多线程刷新
            "show_offline_devices": False,  # 显示离线设备
            "device_filter": "all",  # 设备过滤器: all/online/offline
        },
        "logging": {
            "level": "INFO",  # DEBUG/INFO/WARNING/ERROR
            "file": "adbtools.log",  # 日志文件
            "max_size": 10485760,  # 最大10MB
            "backup_count": 5,  # 备份文件数量
            "console_output": True,  # 控制台输出
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
            },
            "default_action": "install",  # 默认操作: install/uninstall/push
            "verify_after_install": True,  # 安装后验证
            "stop_before_install": True,  # 安装前停止应用
            "clear_cache_before_install": False,  # 安装前清除缓存
        },
        "network": {
            "proxy_enabled": False,  # 是否启用代理
            "proxy_host": "127.0.0.1",  # 代理主机
            "proxy_port": 8080,  # 代理端口
            "proxy_type": "http",  # 代理类型: http/socks5
            "timeout": 30,  # 网络超时时间
        },
        "performance": {
            "max_threads": 4,  # 最大线程数
            "thread_pool_size": 10,  # 线程池大小
            "cache_enabled": True,  # 启用缓存
            "cache_ttl": 300,  # 缓存生存时间（秒）
            "auto_cleanup": True,  # 自动清理资源
        },
        "backup": {
            "auto_backup": True,  # 自动备份配置
            "backup_count": 10,  # 备份文件数量
            "backup_path": "./backups",  # 备份路径
            "compress_backups": True,  # 压缩备份文件
        },
        "shortcuts": {
            "refresh_devices": "F5",
            "screenshot": "Ctrl+S",
            "install_apk": "Ctrl+I",
            "pull_log": "Ctrl+L",
            "reboot_device": "Ctrl+R",
        }
    }
    
    def __init__(self, config_file: str = "adbtools_config.json"):
        """
        初始化增强版配置管理器
        
        Args:
            config_file: 配置文件名
        """
        self.config_file = config_file
        self.config = copy.deepcopy(self.DEFAULT_CONFIG)
        self.backup_manager = ConfigBackupManager(self)
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
    
    def load_config(self) -> bool:
        """加载配置文件"""
        config_path = self.get_config_path()
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # 深度合并配置
                self._deep_merge(self.config, loaded_config)
                print(f"配置文件加载成功: {config_path}")
                
                # 创建备份
                if self.config.get("backup.auto_backup", True):
                    self.backup_manager.create_backup()
                
                return True
            except Exception as e:
                print(f"配置文件加载失败，使用默认配置: {e}")
                self._create_default_config()
                return False
        else:
            print(f"配置文件不存在，创建默认配置: {config_path}")
            self._create_default_config()
            return True
    
    def reload_config(self) -> bool:
        """重新加载配置文件"""
        print(f"重新加载配置文件...")
        # 重置为默认配置
        self.config = copy.deepcopy(self.DEFAULT_CONFIG)
        # 重新加载
        return self.load_config()
    
    def save_config(self) -> bool:
        """保存配置文件"""
        try:
            config_path = self.get_config_path()
            
            # 确保目录存在
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # 保存前备份
            if os.path.exists(config_path) and self.config.get("backup.auto_backup", True):
                self.backup_manager.create_backup()
            
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
    
    def set(self, key: str, value: Any, auto_save: bool = True) -> bool:
        """设置配置值
        
        Args:
            key: 配置键，支持点号分隔
            value: 配置值
            auto_save: 是否自动保存
            
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
            if auto_save:
                return self.save_config()
            return True
        except Exception as e:
            print(f"设置配置失败: {e}")
            return False
    
    def update(self, updates: Dict[str, Any], auto_save: bool = True) -> bool:
        """批量更新配置
        
        Args:
            updates: 更新字典，键为配置路径，值为配置值
            auto_save: 是否自动保存
            
        Returns:
            是否全部成功
        """
        success = True
        for key, value in updates.items():
            if not self.set(key, value, auto_save=False):
                success = False
        
        if auto_save and success:
            return self.save_config()
        
        return success
    
    def reset_to_default(self, key: str = None) -> bool:
        """重置配置到默认值
        
        Args:
            key: 要重置的配置键，如果为None则重置所有配置
            
        Returns:
            是否成功
        """
        if key is None:
            # 重置所有配置
            self.config = copy.deepcopy(self.DEFAULT_CONFIG)
            return self.save_config()
        else:
            # 重置指定配置
            keys = key.split('.')
            default_config = copy.deepcopy(self.DEFAULT_CONFIG)
            
            try:
                # 获取默认值
                value = default_config
                for k in keys:
                    value = value[k]
                
                # 设置默认值
                return self.set(key, value)
            except (KeyError, TypeError):
                print(f"配置键不存在: {key}")
                return False
    
    def export_config(self, export_path: str) -> bool:
        """导出配置文件
        
        Args:
            export_path: 导出路径
            
        Returns:
            是否成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(export_path), exist_ok=True)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            print(f"配置文件导出成功: {export_path}")
            return True
        except Exception as e:
            print(f"配置文件导出失败: {e}")
            return False
    
    def import_config(self, import_path: str, merge: bool = True) -> bool:
        """导入配置文件
        
        Args:
            import_path: 导入路径
            merge: 是否合并配置（True=合并，False=替换）
            
        Returns:
            是否成功
        """
        try:
            if not os.path.exists(import_path):
                print(f"导入文件不存在: {import_path}")
                return False
            
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            if merge:
                # 深度合并配置
                self._deep_merge(self.config, imported_config)
            else:
                # 替换配置
                self.config = imported_config
            
            return self.save_config()
        except Exception as e:
            print(f"配置文件导入失败: {e}")
            return False
    
    def validate_config(self) -> Dict[str, List[str]]:
        """验证配置的有效性
        
        Returns:
            验证结果字典，包含错误和警告列表
        """
        errors = []
        warnings = []
        
        # 验证ADB路径
        adb_paths = self.get("adb.search_paths", [])
        if not isinstance(adb_paths, list):
            errors.append("adb.search_paths 必须是列表")
        
        # 验证超时时间
        timeout = self.get("adb.timeout", 30)
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            errors.append("adb.timeout 必须是正数")
        
        # 验证字体大小
        font_size = self.get("ui.font_size", 10)
        if not isinstance(font_size, int) or font_size < 8 or font_size > 20:
            warnings.append("ui.font_size 应在8-20之间")
        
        # 验证刷新间隔
        refresh_interval = self.get("devices.refresh_interval", 5)
        if not isinstance(refresh_interval, int) or refresh_interval < 1 or refresh_interval > 60:
            warnings.append("devices.refresh_interval 应在1-60秒之间")
        
        return {
            "errors": errors,
            "warnings": warnings,
            "is_valid": len(errors) == 0
        }
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要信息
        
        Returns:
            配置摘要字典
        """
        return {
            "version": self.get_version(),
            "adb_paths_count": len(self.get("adb.search_paths", [])),
            "theme": self.get("ui.theme", "dark"),
            "language": self.get("ui.language", "zh_CN"),
            "auto_refresh": self.get("devices.auto_refresh", True),
            "special_packages_count": len(self.get("batch_install.special_packages", {})),
            "config_size": len(json.dumps(self.config, ensure_ascii=False)),
            "last_modified": datetime.now().isoformat()
        }
    
    # 便捷方法
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
        success = success and self.set("version.major", major, auto_save=False)
        success = success and self.set("version.minor", minor, auto_save=False)
        success = success and self.set("version.patch", patch, auto_save=False)
        success = success and self.set("version.build", build, auto_save=False)
        
        if success:
            return self.save_config()
        return False


class ConfigBackupManager:
    """配置备份管理器"""
    
    def __init__(self, config_manager: EnhancedConfigManager):
        self.config_manager = config_manager
        self.backup_path = config_manager.get("backup.backup_path", "./backups")
    
    def create_backup(self) -> bool:
        """创建配置备份"""
        try:
            # 确保备份目录存在
            os.makedirs(self.backup_path, exist_ok=True)
            
            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.backup_path, f"adbtools_config_backup_{timestamp}.json")
            
            # 保存备份
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_manager.config, f, ensure_ascii=False, indent=2)
            
            # 清理旧备份
            self._cleanup_old_backups()
            
            return True
        except Exception as e:
            print(f"创建备份失败: {e}")
            return False
    
    def _cleanup_old_backups(self) -> None:
        """清理旧备份文件"""
        try:
            backup_count = self.config_manager.get("backup.backup_count", 10)
            
            # 获取所有备份文件
            backup_files = []
            for file in os.listdir(self.backup_path):
                if file.startswith("adbtools_config_backup_") and file.endswith(".json"):
                    file_path = os.path.join(self.backup_path, file)
                    backup_files.append((file_path, os.path.getmtime(file_path)))
            
            # 按修改时间排序（从旧到新）
            backup_files.sort(key=lambda x: x[1])
            
            # 删除多余的备份文件
            while len(backup_files) > backup_count:
                old_file, _ = backup_files.pop(0)
                try:
                    os.remove(old_file)
                    print(f"删除旧备份文件: {old_file}")
                except Exception as e:
                    print(f"删除备份文件失败: {e}")
        except Exception as e:
            print(f"清理备份文件失败: {e}")
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份文件
        
        Returns:
            备份文件列表
        """
        backups = []
        try:
            if not os.path.exists(self.backup_path):
                return backups
            
            for file in os.listdir(self.backup_path):
                if file.startswith("adbtools_config_backup_") and file.endswith(".json"):
                    file_path = os.path.join(self.backup_path, file)
                    stat = os.stat(file_path)
                    backups.append({
                        "filename": file,
                        "path": file_path,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "timestamp": stat.st_mtime
                    })
            
            # 按修改时间排序（从新到旧）
            backups.sort(key=lambda x: x["timestamp"], reverse=True)
            return backups
        except Exception as e:
            print(f"列出备份文件失败: {e}")
            return []
    
    def restore_backup(self, backup_file: str) -> bool:
        """从备份恢复配置
        
        Args:
            backup_file: 备份文件路径
            
        Returns:
            是否成功
        """
        return self.config_manager.import_config(backup_file, merge=False)


# 全局增强版配置管理器实例
enhanced_config_manager = EnhancedConfigManager()

# 向后兼容的别名
config_manager = enhanced_config_manager