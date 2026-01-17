#!/usr/bin/env python3
"""方法调用日志装饰器"""

import functools
import logging
from typing import Callable, Any, Optional

# 获取日志记录器
logger = logging.getLogger("ADBTools.LogDecorator")

def log_method_call(method_name: Optional[str] = None, 
                    result_message: str = "方法调用完成",
                    failure_message: str = "方法调用失败"):
    """
    方法调用日志装饰器
    
    Args:
        method_name: 方法名称（如果为None，则使用实际方法名）
        result_message: 成功时的消息
        failure_message: 失败时的消息
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            actual_method_name = method_name or func.__name__
            
            try:
                # 执行方法
                result = func(self, *args, **kwargs)
                
                # 记录成功日志
                logger.info("=" * 80)
                logger.info(f"{result_message}: {actual_method_name}")
                logger.info("=" * 80)
                
                return result
            except Exception as e:
                # 记录失败日志
                logger.error("=" * 80)
                logger.error(f"{failure_message}: {actual_method_name}")
                logger.error(f"错误信息: {e}")
                logger.error("=" * 80)
                
                # 重新抛出异常
                raise
        
        return wrapper
    return decorator


def log_method_call_with_result(method_name: Optional[str] = None):
    """
    方法调用日志装饰器（带结果记录）
    
    Args:
        method_name: 方法名称（如果为None，则使用实际方法名）
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            actual_method_name = method_name or func.__name__
            
            try:
                # 执行方法
                result = func(self, *args, **kwargs)
                
                # 记录成功日志（带结果）
                logger.info("=" * 80)
                logger.info(f"方法调用完成: {actual_method_name}")
                if result is not None:
                    logger.info(f"返回结果: {result}")
                logger.info("=" * 80)
                
                return result
            except Exception as e:
                # 记录失败日志
                logger.error("=" * 80)
                logger.error(f"方法调用失败: {actual_method_name}")
                logger.error(f"错误信息: {e}")
                logger.error("=" * 80)
                
                # 重新抛出异常
                raise
        
        return wrapper
    return decorator