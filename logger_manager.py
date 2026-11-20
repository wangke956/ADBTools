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

# 导入应用路径工具（获取真实安装目录，兼容 Nuitka onefile 临时解压目录问题）
from app_paths import get_app_dir, is_frozen, is_dir_writable, get_fallback_log_dirs

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
        self.log_dir = "."  # 默认值，防止初始化失败时属性不存在
        self._init_error = None  # 记录初始化错误
        self._log_dir_diagnostics = []  # 日志目录选择过程诊断（供崩溃日志输出）
        self._log_dir_warning = None  # 安装目录不可写回退时的可见提醒文本
        
        try:
            # 加载配置
            self._load_config()
            
            # 初始化日志目录
            self._init_log_dir()
            
            # 检查并清理旧日志（控制日志目录大小）
            self._cleanup_old_logs()
            
            # 初始化操作日志和性能监控
            self._init_special_loggers()
        except Exception as e:
            self._init_error = str(e)
            print(f"日志管理器初始化警告: {e}")
            # 使用默认值确保程序能继续运行
            if not hasattr(self, 'log_dir') or not self.log_dir:
                self.log_dir = "."
    
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
        """初始化日志目录

        优先安装目录/logs；若不可写（如 Program Files 下 Users 组无写权限），
        回退到 %LOCALAPPDATA%\\ADBTools\\logs 等候选目录。
        所有尝试与失败原因写入 self._log_dir_diagnostics，供上层输出到崩溃日志。
        """
        self._log_dir_diagnostics = []
        try:
            # 确定日志目录路径：优先使用程序真实所在目录（安装目录）
            # 注意：Nuitka onefile 模式下 sys.executable 指向临时解压目录（退出即删除），
            # get_app_dir() 基于 __compiled__.containing_dir 返回原始 exe 目录，不依赖C盘用户目录权限
            base_dir = get_app_dir()
            if is_frozen():
                self._log_dir_diagnostics.append(f"运行模式: frozen, 安装目录: {base_dir}")
            else:
                self._log_dir_diagnostics.append(f"运行模式: dev, 项目目录: {base_dir}")

            # 候选目录：安装目录/logs 优先，后接 %LOCALAPPDATA%\\ADBTools\\logs 等兜底
            rel_log_dir = self.log_dir if isinstance(self.log_dir, str) and self.log_dir else "logs"
            primary = rel_log_dir if os.path.isabs(rel_log_dir) else os.path.join(base_dir, rel_log_dir)
            candidates = [primary] + get_fallback_log_dirs()

            chosen = None
            for cand in candidates:
                ok, reason = is_dir_writable(cand)
                self._log_dir_diagnostics.append(f"候选 {cand} → {'可写' if ok else '不可写'} ({reason})")
                if ok:
                    chosen = cand
                    break

            if chosen is None:
                # 全部候选不可写，最后的兜底：当前工作目录
                chosen = os.path.abspath(".")
                self._log_dir_diagnostics.append(f"全部候选不可写，回退到当前工作目录: {chosen}")
                try:
                    os.makedirs(chosen, exist_ok=True)
                except Exception:
                    pass

            self.log_dir = chosen
            if chosen != primary:
                # 安装目录不可写，需要可见提醒（不依赖 print，因为 GUI 模式禁用了控制台）
                msg = (f"安装目录日志不可写，已回退到: {chosen}\n"
                       f"原因: {primary} 无写入权限\n"
                       f"建议: 卸载后重装到 %LOCALAPPDATA%\\Programs\\ADBTools，"
                       f"或给 {primary} 授予 Users 组修改权限")
                self._log_dir_diagnostics.append(msg)
                self._log_dir_warning = msg
            else:
                self._log_dir_warning = None
        except Exception as e:
            self._log_dir_diagnostics.append(f"_init_log_dir 异常: {type(e).__name__}: {e}")
            self.log_dir = "."
            self._log_dir_warning = None
    
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
        # 防御：即使 _init_log_dir 选定了可写目录，也可能在后续时刻因权限变化/磁盘满等原因失败，
        # 失败时逐个尝试兜底目录，避免因单个路径报错导致日志静默丢失
        log_file_name = f"{self.log_file.replace('.log', '')}_{datetime.now().strftime('%Y%m%d')}.log"
        handler_paths = [os.path.join(self.log_dir, log_file_name)]
        for cand in get_fallback_log_dirs():
            p = os.path.join(cand, log_file_name)
            if p not in handler_paths:
                handler_paths.append(p)

        file_handler = None
        last_err = None
        for log_file_path in handler_paths:
            try:
                os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
                file_handler = logging.handlers.RotatingFileHandler(
                    log_file_path,
                    maxBytes=self.max_size,
                    backupCount=self.backup_count,
                    encoding='utf-8'
                )
                # 如果实际使用的目录与 self.log_dir 不一致，同步更新，供其他日志（operation/performance）使用
                actual_dir = os.path.dirname(log_file_path)
                if actual_dir != self.log_dir:
                    self.log_dir = actual_dir
                    self._log_dir_diagnostics.append(
                        f"get_logger 中主目录不可用，回退到: {actual_dir}")
                break
            except Exception as e:
                last_err = e
                self._log_dir_diagnostics.append(
                    f"RotatingFileHandler 失败 {log_file_path}: {type(e).__name__}: {e}")
                continue

        if file_handler is not None:
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        else:
            # 所有候选均失败，日志仅能走控制台（GUI 打包下不可见），至少记录错误供诊断
            self._log_dir_diagnostics.append(f"所有文件日志处理器候选均失败，最后错误: {last_err}")
        
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


# 全局日志管理器实例（延迟初始化）
_logger_manager_instance = None
_logger_manager_lock = threading.Lock()


def _get_logger_manager():
    """获取日志管理器实例（延迟初始化）"""
    global _logger_manager_instance
    if _logger_manager_instance is None:
        with _logger_manager_lock:
            if _logger_manager_instance is None:
                try:
                    _logger_manager_instance = LoggerManager()
                except Exception as e:
                    print(f"创建日志管理器失败: {e}")
                    # 创建一个最小化的回退实例
                    _logger_manager_instance = LoggerManager.__new__(LoggerManager)
                    _logger_manager_instance._initialized = True
                    _logger_manager_instance.loggers = {}
                    _logger_manager_instance.operation_logger = None
                    _logger_manager_instance.performance_monitor = None
                    _logger_manager_instance.log_dir = "."
                    _logger_manager_instance._init_error = str(e)
    return _logger_manager_instance


# 兼容性属性访问
class LoggerManagerProxy:
    """日志管理器代理类，支持延迟初始化和属性访问"""
    
    def __getattr__(self, name):
        return getattr(_get_logger_manager(), name)


logger_manager = LoggerManagerProxy()


# 便捷函数
def get_logger(name: str = "ADBTools") -> logging.Logger:
    """获取日志记录器"""
    try:
        return logger_manager.get_logger(name)
    except Exception as e:
        # 如果日志管理器完全无法工作，返回一个基本的控制台logger
        print(f"获取日志记录器失败: {e}")
        fallback_logger = logging.getLogger(name)
        if not fallback_logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            fallback_logger.addHandler(handler)
            fallback_logger.setLevel(logging.INFO)
        return fallback_logger


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