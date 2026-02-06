#!/usr/bin/env python3
"""大通页面设置设备日期时间线程类"""

import threading
import time
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal

# 导入ADB工具类
import sys
import os
# 添加主目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入日志管理器
from logger_manager import get_logger, log_operation, log_method_result, log_exception

# 创建日志记录器
logger = get_logger("ADBTools.DatongSetDatetimeThread")


class DatongSetDatetimeThread(QThread):
    """大通页面设置设备日期时间线程类"""
    
    # 定义信号
    progress_signal = pyqtSignal(str)  # 进度信息信号
    error_signal = pyqtSignal(str)  # 错误信息信号
    result_signal = pyqtSignal(str)  # 结果信息信号
    
    def __init__(self, device_id, connection_mode='adb', u2_device=None):
        """
        初始化线程
        
        Args:
            device_id (str): 设备ID
            connection_mode (str): 连接模式 ('adb' 或 'u2')
            u2_device: uiautomator2设备对象（如果使用u2模式）
        """
        super().__init__()
        self.device_id = device_id
        self.connection_mode = connection_mode
        self.u2_device = u2_device
        self.is_stopped = False
    
    def stop(self):
        """停止线程"""
        self.is_stopped = True
        logger.info("用户请求停止设置日期时间线程")
    
    def run(self):
        """执行设置日期时间操作"""
        try:
            logger.info(f"开始设置设备 {self.device_id} 的日期时间")
            self.progress_signal.emit(f"开始设置设备 {self.device_id} 的日期时间...")
            
            # 检查设备连接状态
            if not self.device_id:
                error_msg = "设备未连接或未选择设备"
                self.error_signal.emit(error_msg)
                log_method_result("DatongSetDatetimeThread.run", False, error_msg)
                return
            
            # 获取当前时间并格式化为adb shell date命令需要的格式
            current_time = datetime.now()
            # 格式: MMDDhhmmYYYY.ss (月日时分年.秒)
            date_command = current_time.strftime("%m%d%H%M%Y.%S")
            
            self.progress_signal.emit(f"当前时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            self.progress_signal.emit(f"准备执行命令: adb -s {self.device_id} shell date {date_command}")
            
            # 执行ADB命令设置日期时间
            if self.connection_mode == 'adb':
                result = self._set_datetime_adb(date_command)
            elif self.connection_mode == 'u2' and self.u2_device:
                result = self._set_datetime_u2(date_command)
            else:
                error_msg = "不支持的连接模式或设备未连接"
                self.error_signal.emit(error_msg)
                log_method_result("DatongSetDatetimeThread.run", False, error_msg)
                return
            
            # 处理执行结果
            if result.returncode == 0:
                success_msg = f"✓ 日期时间设置成功！\n"
                success_msg += f"  设备: {self.device_id}\n"
                success_msg += f"  新时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                success_msg += f"  命令: adb -s {self.device_id} shell date {date_command}"
                self.result_signal.emit(success_msg)
                logger.info(f"日期时间设置成功: {success_msg}")
                log_method_result("DatongSetDatetimeThread.run", True, "日期时间设置成功")
            else:
                error_msg = f"✗ 日期时间设置失败！\n"
                error_msg += f"  设备: {self.device_id}\n"
                error_msg += f"  命令: adb -s {self.device_id} shell date {date_command}\n"
                if result.stderr:
                    error_msg += f"  错误信息: {result.stderr.strip()}"
                self.error_signal.emit(error_msg)
                logger.error(f"日期时间设置失败: {error_msg}")
                log_method_result("DatongSetDatetimeThread.run", False, f"设置失败: {result.stderr}")
                
        except Exception as e:
            error_msg = f"设置日期时间时发生异常: {str(e)}"
            self.error_signal.emit(error_msg)
            log_exception(logger, "DatongSetDatetimeThread.run", e)
            log_method_result("DatongSetDatetimeThread.run", False, str(e))
    
    def _set_datetime_adb(self, date_command):
        """使用ADB模式设置日期时间"""
        try:
            # 导入adb_utils实例
            from adb_utils import adb_utils
            
            # 构建命令
            command = f"shell date {date_command}"
            self.progress_signal.emit(f"执行ADB命令: {command}")
            
            # 执行命令 - 通过adb_utils实例调用run_adb_command方法
            result = adb_utils.run_adb_command(command, device_id=self.device_id)
            return result
        except Exception as e:
            logger.error(f"使用ADB模式设置日期时间时出错: {e}")
            raise
    
    def _set_datetime_u2(self, date_command):
        """使用u2模式设置日期时间"""
        try:
            # 使用uiautomator2的shell方法执行命令
            self.progress_signal.emit(f"使用u2模式执行命令: date {date_command}")
            
            # uiautomator2的shell方法返回的是ShellResponse对象
            result = self.u2_device.shell(f"date {date_command}")
            
            # 构造一个模拟的subprocess结果对象
            class MockResult:
                def __init__(self, stdout, stderr, returncode):
                    self.stdout = stdout
                    self.stderr = stderr
                    self.returncode = returncode
            
            # 处理ShellResponse对象
            if hasattr(result, 'error'):
                # 如果有错误信息
                error_msg = str(result.error) if result.error else ""
                return MockResult("", error_msg, 1)
            elif hasattr(result, 'output'):
                # 如果有输出信息
                output = str(result.output) if result.output else ""
                # 检查是否包含错误信息
                if result.output and "error" in str(result.output).lower():
                    return MockResult("", str(result.output), 1)
                else:
                    return MockResult(output, "", 0)
            else:
                # 通用处理方式
                result_str = str(result)
                if "error" in result_str.lower():
                    return MockResult("", result_str, 1)
                else:
                    return MockResult(result_str, "", 0)
        except Exception as e:
            logger.error(f"使用u2模式设置日期时间时出错: {e}")
            raise