#!/usr/bin/env python3
"""ADB工具类，解决PyInstaller打包后的ADB路径问题"""

import os
import subprocess
import sys
import time
from pathlib import Path

# 导入日志管理器
from logger_manager import get_logger, log_operation, measure_performance, log_exception

# 创建日志记录器
logger = get_logger("ADBTools.ADB_Utils")

# 导入命令日志记录器
try:
    from Function_Moudle.command_logger import log_command_execution
except ImportError:
    # 如果导入失败，创建一个空函数
    def log_command_execution(*args, **kwargs):
        pass

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
            logger.debug(f"使用缓存的ADB路径: {cls._adb_path}")
            return cls._adb_path
        
        logger.info("开始查找ADB可执行文件...")
        
        # 从配置文件中获取搜索路径
        possible_paths = config_manager.get_adb_search_paths()
        logger.debug(f"ADB搜索路径: {possible_paths}")
        
        # 尝试查找ADB
        for path in possible_paths:
            try:
                # 检查是否是绝对路径且文件存在
                if os.path.isabs(path) and os.path.isfile(path):
                    cls._adb_path = path
                    logger.info(f"找到ADB (绝对路径): {path}")
                    return path
                
                # 检查相对路径（相对于当前工作目录）
                if os.path.isfile(path):
                    cls._adb_path = os.path.abspath(path)
                    logger.info(f"找到ADB (相对路径): {cls._adb_path}")
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
                        logger.info(f"找到ADB (系统PATH): {found_path}")
                        return found_path
            except Exception as e:
                logger.debug(f"检查路径 {path} 时出错: {e}")
                continue
        
        # 如果都没找到，记录错误并返回"adb"（依赖系统PATH）
        logger.warning("未找到ADB可执行文件，将尝试使用系统PATH中的adb")
        print("警告: 未找到ADB可执行文件，将尝试使用系统PATH中的adb")
        cls._adb_path = "adb"
        return "adb"
    
    @classmethod
    def run_adb_command(cls, command, device_id=None, **kwargs):
        """执行ADB命令"""
        import threading
        from datetime import datetime
        
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
        
        # 获取线程和时间信息
        thread_id = threading.current_thread().ident
        thread_name = threading.current_thread().name
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # 记录命令执行（只记录关键信息）
        if device_id:
            logger.debug(f"[{timestamp}] [Thread-{thread_id}] 执行ADB命令 [{device_id}]: {command}")
        else:
            logger.debug(f"[{timestamp}] [Thread-{thread_id}] 执行ADB命令 [全局]: {command}")
        
        try:
            import time
            start_time = time.time()
            result = subprocess.run(full_command, **default_kwargs)
            elapsed_time = time.time() - start_time
            
            # 只在失败时记录详细信息
            if result.returncode != 0:
                logger.error(f"[{timestamp}] [Thread-{thread_id}] ADB命令执行失败: {command}")
                logger.error(f"返回码: {result.returncode}")
                if result.stderr:
                    logger.error(f"错误输出: {result.stderr.strip()}")
            else:
                # 成功时记录简要信息
                if device_id:
                    logger.debug(f"[{timestamp}] [Thread-{thread_id}] ADB命令执行成功 [{device_id}]: {command} (耗时: {elapsed_time:.3f}s)")
                else:
                    logger.debug(f"[{timestamp}] [Thread-{thread_id}] ADB命令执行成功 [全局]: {command} (耗时: {elapsed_time:.3f}s)")
            
            # 记录到命令历史（不记录到主日志）
            log_command_execution(
                command=command,
                device_id=device_id,
                full_command=full_command,
                adb_path=adb_path,
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time=elapsed_time,
                result="success" if result.returncode == 0 else "failed",
                thread_id=thread_id,
                thread_name=thread_name,
                timestamp=timestamp
            )
            
            return result
        except Exception as e:
            logger.error(f"[{timestamp}] [Thread-{thread_id}] ADB命令执行异常: {command} | 错误: {str(e)}")
            # 创建模拟的subprocess结果对象
            class MockResult:
                def __init__(self):
                    self.returncode = 1
                    self.stdout = ""
                    self.stderr = str(e)
            
            return MockResult()
    
    @classmethod
    def run_adb_command_realtime(cls, command, device_id=None, output_callback=None, **kwargs):
        """
        执行ADB命令并实时输出
        
        Args:
            command: ADB命令
            device_id: 设备ID
            output_callback: 输出回调函数，接收字符串参数
            **kwargs: 其他subprocess参数
        
        Returns:
            subprocess.CompletedProcess对象
        """
        adb_path = cls.get_adb_path()
        
        # 构建完整命令
        if device_id:
            full_command = f'"{adb_path}" -s {device_id} {command}'
        else:
            full_command = f'"{adb_path}" {command}'
        
        logger.info(f"========== 开始执行ADB实时命令 ==========")
        logger.info(f"设备ID: {device_id if device_id else '无'}")
        logger.info(f"命令: {command}")
        logger.info(f"完整命令: {full_command}")
        logger.info(f"模式: 实时输出")
        
        # 记录操作历史
        log_operation("adb_command_realtime", {
            "command": command,
            "full_command": full_command,
            "device_id": device_id,
            "mode": "realtime"
        }, device_id)
        
        # 设置默认参数
        default_kwargs = {
            'shell': True,
            'stdout': subprocess.PIPE,
            'stderr': subprocess.STDOUT,  # 将stderr合并到stdout
            'text': True,
            'encoding': 'utf-8',
            'errors': 'ignore',
            'bufsize': 1,  # 行缓冲
            'universal_newlines': True
        }
        default_kwargs.update(kwargs)
        
        try:
            if output_callback:
                # 实时输出模式
                logger.info(f"启动实时输出进程...")
                process = subprocess.Popen(
                    full_command,
                    **{k: v for k, v in default_kwargs.items() if k not in ['capture_output']}
                )
                
                logger.info(f"========== 实时输出开始 ==========")
                
                # 实时读取输出
                output_lines = []
                line_count = 0
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        line = line.rstrip('\n')
                        output_lines.append(line)
                        line_count += 1
                        logger.info(f"  [行 {line_count}] {line}")
                        output_callback(line)
                
                # 等待进程结束
                returncode = process.wait()
                
                logger.info(f"========== 实时输出结束 ==========")
                logger.info(f"总行数: {line_count}")
                logger.info(f"========== 命令执行结果 ==========")
                logger.info(f"返回码: {returncode}")
                
                if returncode == 0:
                    logger.info(f"✓ 实时命令执行成功: {command}")
                    log_operation("adb_command_realtime_success", {
                        "command": command,
                        "device_id": device_id,
                        "returncode": returncode,
                        "output_lines": line_count
                    }, device_id, "success")
                else:
                    logger.error(f"✗ 实时命令执行失败 [返回码: {returncode}]: {command}")
                    log_operation("adb_command_realtime_failed", {
                        "command": command,
                        "device_id": device_id,
                        "returncode": returncode,
                        "output_lines": line_count
                    }, device_id, "failed")
                
                logger.info(f"========== 命令执行结束 ==========")
                
                # 创建结果对象
                class RealtimeResult:
                    def __init__(self):
                        self.returncode = returncode
                        self.stdout = '\n'.join(output_lines)
                        self.stderr = ""
                
                return RealtimeResult()
            else:
                # 非实时模式，使用原来的方法
                logger.info(f"切换到非实时模式")
                return cls.run_adb_command(command, device_id, **kwargs)
                
        except Exception as e:
            logger.error(f"========== 命令执行异常 ==========")
            logger.error(f"命令: {command}")
            logger.error(f"异常类型: {type(e).__name__}")
            logger.error(f"异常信息: {str(e)}")
            logger.error(f"========== 命令执行结束 ==========")
            
            log_exception(logger, f"run_adb_command_realtime: {command}", e)
            log_operation("adb_command_realtime_error", {
                "command": command,
                "device_id": device_id,
                "error_type": type(e).__name__,
                "error_message": str(e)
            }, device_id, "error")
            
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