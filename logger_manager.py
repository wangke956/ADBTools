#!/usr/bin/env python3
"""
日志管理器 - 为ADBTools提供详细的日志记录功能

功能特性：
1. 多级别日志记录 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
2. 文件日志轮转（按大小和数量）
3. 控制台输出（可配置）
4. 详细的操作记录（包括时间戳、线程ID、函数名等）
5. 异常堆栈跟踪
6. 操作历史记录
7. 性能监控
"""

import os
import sys
import logging
import logging.handlers
import json
import traceback
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from functools import wraps
from contextlib import contextmanager

# 导入配置管理器
try:
    from config_manager import config_manager
except ImportError:
    # 如果导入失败，创建简单的配置回退
    class ConfigManagerFallback:
        def get(self, key: str, default: Any = None) -> Any:
            defaults = {
                "logging.level": "INFO",
                "logging.file": "adbtools.log",
                "logging.max_size": 10485760,
                "logging.backup_count": 5,
                "logging.console_output": True,
                "logging.log_dir": "logs",
                "logging.enable_operation_history": True,
                "logging.enable_performance_monitoring": True,
                "logging.format": "detailed",
            }
            return defaults.get(key, default)
    
    config_manager = ConfigManagerFallback()


class OperationLogger:
    """操作日志记录器 - 记录用户操作历史"""
    
    def __init__(self, log_file: str = "operation_history.log"):
        self.log_file = log_file
        self.operations = []
        self._lock = threading.Lock()
    
    def log_operation(self, operation_type: str, details: Dict[str, Any], 
                     device_id: Optional[str] = None, result: str = "success"):
        """
        记录操作
        
        Args:
            operation_type: 操作类型（如：install_apk, uninstall_app, screenshot等）
            details: 操作详情（字典）
            device_id: 设备ID
            result: 操作结果（success/failed）
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        thread_id = threading.current_thread().ident
        thread_name = threading.current_thread().name
        
        operation = {
            "timestamp": timestamp,
            "operation_type": operation_type,
            "device_id": device_id,
            "details": details,
            "result": result,
            "thread_id": thread_id,
            "thread_name": thread_name
        }
        
        with self._lock:
            self.operations.append(operation)
            # 保存到文件
            self._save_to_file(operation)
    
    def _save_to_file(self, operation: Dict[str, Any]):
        """保存操作到文件"""
        try:
            log_dir = Path(self.log_file).parent
            log_dir.mkdir(parents=True, exist_ok=True)
            
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(operation, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"保存操作日志失败: {e}")
    
    def get_recent_operations(self, count: int = 10) -> list:
        """获取最近的操作记录"""
        with self._lock:
            return self.operations[-count:] if len(self.operations) > count else self.operations.copy()
    
    def clear_history(self):
        """清空操作历史"""
        with self._lock:
            self.operations = []
            try:
                if os.path.exists(self.log_file):
                    os.remove(self.log_file)
            except Exception as e:
                print(f"清空操作历史失败: {e}")


class PerformanceMonitor:
    """性能监控器 - 记录操作耗时"""
    
    def __init__(self, log_file: str = "performance.log"):
        self.log_file = log_file
        self.metrics = {}
        self._lock = threading.Lock()
    
    @contextmanager
    def measure(self, operation_name: str, device_id: Optional[str] = None):
        """
        测量操作耗时
        
        Args:
            operation_name: 操作名称
            device_id: 设备ID
        """
        start_time = time.time()
        try:
            yield
        finally:
            elapsed_time = time.time() - start_time
            self._record_metric(operation_name, elapsed_time, device_id)
    
    def _record_metric(self, operation_name: str, elapsed_time: float, 
                      device_id: Optional[str] = None):
        """记录性能指标"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        metric = {
            "timestamp": timestamp,
            "operation": operation_name,
            "device_id": device_id,
            "elapsed_time": elapsed_time,
            "thread_id": threading.current_thread().ident
        }
        
        with self._lock:
            # 更新统计信息
            if operation_name not in self.metrics:
                self.metrics[operation_name] = {
                    "count": 0,
                    "total_time": 0,
                    "min_time": float('inf'),
                    "max_time": 0,
                    "avg_time": 0
                }
            
            stats = self.metrics[operation_name]
            stats["count"] += 1
            stats["total_time"] += elapsed_time
            stats["min_time"] = min(stats["min_time"], elapsed_time)
            stats["max_time"] = max(stats["max_time"], elapsed_time)
            stats["avg_time"] = stats["total_time"] / stats["count"]
            
            # 保存到文件
            self._save_to_file(metric)
    
    def _save_to_file(self, metric: Dict[str, Any]):
        """保存性能指标到文件"""
        try:
            log_dir = Path(self.log_file).parent
            log_dir.mkdir(parents=True, exist_ok=True)
            
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(metric, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"保存性能日志失败: {e}")
    
    def get_statistics(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """获取性能统计信息"""
        with self._lock:
            if operation_name:
                return self.metrics.get(operation_name, {})
            return self.metrics.copy()


class LoggerManager:
    """日志管理器 - 统一管理所有日志"""
    
    # 日志级别映射
    LOG_LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    # 日志格式
    LOG_FORMATS = {
        'simple': '%(asctime)s - %(levelname)s - %(message)s',
        'detailed': '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - [%(funcName)s] - %(message)s',
        'verbose': '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - [%(funcName)s] - [Thread-%(thread)d] - %(message)s'
    }
    
    # 日志目录最大大小限制（100MB）
    MAX_LOG_DIR_SIZE = 100 * 1024 * 1024  # 100MB
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(LoggerManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化日志管理器"""
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._initialized = True
        self.loggers = {}
        self.operation_logger = None
        self.performance_monitor = None
        
        # 加载配置
        self._load_config()
        
        # 初始化日志目录
        self._init_log_dir()
        
        # 检查并清理旧日志（控制日志目录大小）
        self._cleanup_old_logs()
        
        # 初始化操作日志和性能监控
        self._init_special_loggers()
    
    def _load_config(self):
        """加载日志配置"""
        self.log_level = config_manager.get("logging.level", "INFO")
        self.log_file = config_manager.get("logging.file", "adbtools.log")
        self.max_size = config_manager.get("logging.max_size", 10485760)  # 10MB
        self.backup_count = config_manager.get("logging.backup_count", 5)
        self.console_output = config_manager.get("logging.console_output", True)
        self.log_dir = config_manager.get("logging.log_dir", "logs")
        self.enable_operation_history = config_manager.get("logging.enable_operation_history", True)
        self.enable_performance_monitoring = config_manager.get("logging.enable_performance_monitoring", True)
        self.log_format = config_manager.get("logging.format", "detailed")
    
    def _init_log_dir(self):
        """初始化日志目录"""
        try:
            # 确定日志目录路径
            if getattr(sys, 'frozen', False):
                # PyInstaller打包后的路径
                base_dir = os.path.dirname(sys.executable)
            else:
                # 开发环境路径
                base_dir = os.path.dirname(os.path.abspath(__file__))
            
            self.log_dir = os.path.join(base_dir, self.log_dir)
            os.makedirs(self.log_dir, exist_ok=True)
            
            print(f"日志目录: {self.log_dir}")
        except Exception as e:
            print(f"初始化日志目录失败: {e}")
            self.log_dir = "."
    
    def _cleanup_old_logs(self):
        """清理旧日志文件，控制日志目录大小"""
        try:
            if not os.path.exists(self.log_dir):
                return
            
            # 计算日志目录总大小
            total_size = 0
            log_files = []
            
            for file_name in os.listdir(self.log_dir):
                file_path = os.path.join(self.log_dir, file_name)
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
                    log_files.append((file_path, file_size, os.path.getmtime(file_path)))
            
            # 如果超过限制，删除最早的日志文件
            if total_size > self.MAX_LOG_DIR_SIZE:
                # 按修改时间排序，最早的在前
                log_files.sort(key=lambda x: x[2])
                
                # 删除最早的日志文件，直到总大小小于限制的80%
                target_size = self.MAX_LOG_DIR_SIZE * 0.8
                for file_path, file_size, _ in log_files:
                    if total_size <= target_size:
                        break
                    try:
                        os.remove(file_path)
                        total_size -= file_size
                        print(f"删除旧日志文件: {os.path.basename(file_path)}")
                    except Exception as e:
                        print(f"删除日志文件失败 {file_path}: {e}")
                
                print(f"日志清理完成，当前大小: {total_size / 1024 / 1024:.2f} MB")
        except Exception as e:
            print(f"清理旧日志失败: {e}")
    
    def _init_special_loggers(self):
        """初始化特殊的日志记录器"""
        try:
            if self.enable_operation_history:
                # 按时间命名操作历史日志文件
                operation_log_file = os.path.join(self.log_dir, f"operation_history_{datetime.now().strftime('%Y%m%d')}.log")
                self.operation_logger = OperationLogger(operation_log_file)
            
            if self.enable_performance_monitoring:
                # 按时间命名性能监控日志文件
                performance_log_file = os.path.join(self.log_dir, f"performance_{datetime.now().strftime('%Y%m%d')}.log")
                self.performance_monitor = PerformanceMonitor(performance_log_file)
        except Exception as e:
            print(f"初始化特殊日志记录器失败: {e}")
    
    def get_logger(self, name: str = "ADBTools") -> logging.Logger:
        """
        获取日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            logging.Logger对象
        """
        # 首先从缓存中获取
        if name in self.loggers:
            return self.loggers[name]
        
        # 创建或获取日志记录器
        logger = logging.getLogger(name)
        
        # 如果已经存在处理器，说明已经被其他地方初始化过了
        if logger.handlers:
            # 清除所有处理器，避免重复
            logger.handlers.clear()
        
        logger.setLevel(self.LOG_LEVELS.get(self.log_level, logging.INFO))
        
        # 防止日志传播到根记录器（避免重复）
        logger.propagate = False
        
        # 设置日志格式
        formatter = logging.Formatter(
            self.LOG_FORMATS.get(self.log_format, self.LOG_FORMATS['detailed']),
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 添加文件处理器（按时间命名）
        try:
            # 使用按时间命名的日志文件
            log_file_name = f"{self.log_file.replace('.log', '')}_{datetime.now().strftime('%Y%m%d')}.log"
            log_file_path = os.path.join(self.log_dir, log_file_name)
            file_handler = logging.handlers.RotatingFileHandler(
                log_file_path,
                maxBytes=self.max_size,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"添加文件日志处理器失败: {e}")
        
        # 添加控制台处理器（如果启用）
        if self.console_output:
            try:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(self.LOG_LEVELS.get(self.log_level, logging.INFO))
                console_handler.setFormatter(formatter)
                logger.addHandler(console_handler)
            except Exception as e:
                print(f"添加控制台日志处理器失败: {e}")
        
        # 缓存日志记录器
        self.loggers[name] = logger
        
        return logger
    
    def log_operation(self, operation_type: str, details: Dict[str, Any], 
                     device_id: Optional[str] = None, result: str = "success"):
        """
        记录操作历史
        
        Args:
            operation_type: 操作类型
            details: 操作详情
            device_id: 设备ID
            result: 操作结果
        """
        if self.operation_logger:
            self.operation_logger.log_operation(operation_type, details, device_id, result)
    
    def get_recent_operations(self, count: int = 10) -> list:
        """获取最近的操作记录"""
        if self.operation_logger:
            return self.operation_logger.get_recent_operations(count)
        return []
    
    def measure_performance(self, operation_name: str, device_id: Optional[str] = None):
        """
        测量操作性能
        
        Args:
            operation_name: 操作名称
            device_id: 设备ID
            
        Returns:
            上下文管理器
        """
        if self.performance_monitor:
            return self.performance_monitor.measure(operation_name, device_id)
        
        # 如果性能监控未启用，返回空上下文管理器
        from contextlib import nullcontext
        return nullcontext()
    
    def get_performance_statistics(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """获取性能统计信息"""
        if self.performance_monitor:
            return self.performance_monitor.get_statistics(operation_name)
        return {}
    
    def reload_config(self):
        """重新加载配置"""
        self._load_config()
        # 重新初始化所有日志记录器
        for logger_name in list(self.loggers.keys()):
            del self.loggers[logger_name]
        self._init_special_loggers()


# 全局日志管理器实例
logger_manager = LoggerManager()

# 便捷函数
def get_logger(name: str = "ADBTools") -> logging.Logger:
    """获取日志记录器"""
    return logger_manager.get_logger(name)


def log_operation(operation_type: str, details: Dict[str, Any], 
                 device_id: Optional[str] = None, result: str = "success"):
    """记录操作历史"""
    logger_manager.log_operation(operation_type, details, device_id, result)


def measure_performance(operation_name: str, device_id: Optional[str] = None):
    """测量操作性能"""
    return logger_manager.measure_performance(operation_name, device_id)


def log_exception(logger: logging.Logger, operation: str, exc: Exception, 
                 device_id: Optional[str] = None):
    """
    记录异常信息
    
    Args:
        logger: 日志记录器
        operation: 操作名称
        exc: 异常对象
        device_id: 设备ID
    """
    logger.error(f"操作失败: {operation} | 设备: {device_id or 'N/A'} | 错误: {str(exc)}")
    logger.error(f"异常堆栈:\n{traceback.format_exc()}")


def log_function_call(logger: logging.Logger):
    """
    装饰器：记录函数调用
    
    Args:
        logger: 日志记录器
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            logger.debug(f"调用函数: {func_name} | 参数: args={args}, kwargs={kwargs}")
            
            try:
                result = func(*args, **kwargs)
                logger.debug(f"函数 {func_name} 执行成功")
                return result
            except Exception as e:
                logger.error(f"函数 {func_name} 执行失败: {str(e)}")
                logger.error(f"异常堆栈:\n{traceback.format_exc()}")
                raise
        
        return wrapper
    return decorator


# 创建默认日志记录器
default_logger = get_logger("ADBTools")


# ============================================
# 通用的日志辅助函数
# ============================================

def log_button_click(button_name: str, action: str, extra_info: str = ""):
    """统一的按钮点击日志记录"""
    import threading
    from datetime import datetime
    
    logger = get_logger("ADBTools.UI")
    
    # 获取当前线程信息
    thread_id = threading.current_thread().ident
    thread_name = threading.current_thread().name
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    # 构建详细日志消息
    message = f"[{timestamp}] [Thread-{thread_id}] 用户操作: 点击 {button_name} 按钮 -> {action}"
    if extra_info:
        message += f" ({extra_info})"
    logger.info(message)


def log_method_result(method_name: str, success: bool, result: str = "", device_id: str = None):
    """统一的方法调用结果日志记录"""
    import threading
    from datetime import datetime
    
    logger = get_logger("ADBTools.Method")
    
    # 获取当前线程信息
    thread_id = threading.current_thread().ident
    thread_name = threading.current_thread().name
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    # 构建详细日志消息
    if success:
        message = f"[{timestamp}] [Thread-{thread_id}] ✓ {method_name} 完成"
        if result:
            message += f": {result}"
        if device_id:
            message += f" | 设备: {device_id}"
        logger.info(message)
    else:
        message = f"[{timestamp}] [Thread-{thread_id}] ✗ {method_name} 失败"
        if result:
            message += f": {result}"
        if device_id:
            message += f" | 设备: {device_id}"
        logger.error(message)


def log_device_operation(operation_type: str, device_id: str, details: dict = None):
    """记录设备操作"""
    import threading
    from datetime import datetime
    
    logger = get_logger("ADBTools.Device")
    
    thread_id = threading.current_thread().ident
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    message = f"[{timestamp}] [Thread-{thread_id}] 设备操作: {operation_type} | 设备: {device_id}"
    if details:
        message += f" | 详情: {details}"
    logger.info(message)


def log_file_operation(operation_type: str, file_path: str, device_id: str = None, result: str = "success"):
    """记录文件操作"""
    import threading
    import os
    from datetime import datetime
    
    logger = get_logger("ADBTools.File")
    
    thread_id = threading.current_thread().ident
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    file_name = os.path.basename(file_path) if file_path else "N/A"
    
    message = f"[{timestamp}] [Thread-{thread_id}] 文件操作: {operation_type} | 文件: {file_name}"
    if device_id:
        message += f" | 设备: {device_id}"
    message += f" | 结果: {result}"
    
    if result == "success":
        logger.info(message)
    else:
        logger.error(message)


def log_thread_start(thread_name: str, details: dict = None):
    """记录线程启动"""
    import threading
    from datetime import datetime
    
    logger = get_logger("ADBTools.Thread")
    
    thread_id = threading.current_thread().ident
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    message = f"[{timestamp}] [Thread-{thread_id}] 线程启动: {thread_name}"
    if details:
        message += f" | 详情: {details}"
    logger.info(message)


def log_thread_complete(thread_name: str, result: str = "success", details: dict = None):
    """记录线程完成"""
    import threading
    from datetime import datetime
    
    logger = get_logger("ADBTools.Thread")
    
    thread_id = threading.current_thread().ident
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    message = f"[{timestamp}] [Thread-{thread_id}] 线程完成: {thread_name} | 结果: {result}"
    if details:
        message += f" | 详情: {details}"
    
    if result == "success":
        logger.info(message)
    else:
        logger.error(message)