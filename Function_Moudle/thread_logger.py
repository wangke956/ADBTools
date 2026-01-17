#!/usr/bin/env python3
"""
线程日志工具 - 为所有线程提供统一的日志记录功能

使用方法：
1. 在线程文件中导入：from thread_logger import ThreadLogger, log_thread_operation
2. 创建日志记录器：logger = ThreadLogger.get_logger("YourThreadName")
3. 在 run 方法中使用装饰器或手动记录日志
"""

import sys
import os
from functools import wraps
from typing import Optional, Dict, Any, Callable

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入日志管理器
from logger_manager import get_logger, log_operation, measure_performance, log_exception


class ThreadLogger:
    """线程日志记录器"""
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name: str):
        """
        获取线程日志记录器
        
        Args:
            name: 日志记录器名称（通常使用线程类名）
            
        Returns:
            logging.Logger对象
        """
        if name not in cls._loggers:
            logger = get_logger(f"ADBTools.{name}")
            # 确保不会传播到父记录器
            logger.propagate = False
            cls._loggers[name] = logger
        return cls._loggers[name]


def log_thread_operation(operation_name: str, device_id: Optional[str] = None):
    """
    装饰器：记录线程操作
    
    Args:
        operation_name: 操作名称
        device_id: 设备ID（可选）
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # 获取日志记录器
            logger_name = self.__class__.__name__
            logger = ThreadLogger.get_logger(logger_name)
            
            # 记录操作开始
            logger.info(f"开始执行: {operation_name}")
            log_operation(operation_name, {
                "thread": logger_name,
                "device_id": device_id or getattr(self, 'device_id', None),
                "args": str(args),
                "kwargs": str(kwargs)
            }, device_id)
            
            # 使用性能监控
            with measure_performance(operation_name, device_id):
                try:
                    result = func(self, *args, **kwargs)
                    logger.info(f"执行成功: {operation_name}")
                    return result
                except Exception as e:
                    logger.error(f"执行失败: {operation_name} | 错误: {str(e)}")
                    log_exception(logger, operation_name, e, device_id)
                    raise
        
        return wrapper
    return decorator


def log_thread_signal(logger, signal_type: str, message: str):
    """
    记录线程信号发送
    
    Args:
        logger: 日志记录器
        signal_type: 信号类型（如：progress, error, status等）
        message: 信号消息
    """
    logger.debug(f"发送信号 [{signal_type}]: {message}")


def log_thread_start(logger, thread_name: str):
    """
    记录线程启动
    
    Args:
        logger: 日志记录器
        thread_name: 线程名称
    """
    logger.info(f"线程启动: {thread_name}")


def log_thread_finish(logger, thread_name: str, success: bool = True):
    """
    记录线程结束
    
    Args:
        logger: 日志记录器
        thread_name: 线程名称
        success: 是否成功
    """
    status = "成功" if success else "失败"
    logger.info(f"线程结束: {thread_name} - {status}")


def log_thread_error(logger, thread_name: str, error: Exception):
    """
    记录线程错误
    
    Args:
        logger: 日志记录器
        thread_name: 线程名称
        error: 异常对象
    """
    logger.error(f"线程错误: {thread_name} | {str(error)}")
    log_exception(logger, thread_name, error)


# 便捷函数
def get_thread_logger(thread_class_name: str):
    """获取线程日志记录器（便捷函数）"""
    return ThreadLogger.get_logger(thread_class_name)


# 使用示例：
# 
# class MyThread(QThread):
#     def __init__(self, device_id):
#         super().__init__()
#         self.device_id = device_id
#         self.logger = get_thread_logger("MyThread")
#         self.logger.info(f"线程初始化: {device_id}")
#     
#     @log_thread_operation("my_operation", device_id=None)
#     def run(self):
#         # 线程主要逻辑
#         pass