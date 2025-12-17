import functools
import traceback
from enum import Enum
from typing import Optional, Type, Union, Callable
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt


class ErrorLevel(Enum):
    """错误级别枚举"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ADBToolsException(Exception):
    """ADB工具自定义异常基类"""
    def __init__(self, message: str, level: ErrorLevel = ErrorLevel.ERROR):
        self.message = message
        self.level = level
        super().__init__(self.message)


class DeviceNotConnectedException(ADBToolsException):
    """设备未连接异常"""
    def __init__(self, message: str = "设备未连接"):
        super().__init__(message, ErrorLevel.ERROR)


class CommandExecutionException(ADBToolsException):
    """命令执行异常"""
    def __init__(self, message: str, command: str):
        super().__init__(f"命令执行失败: {command}\n错误信息: {message}", ErrorLevel.ERROR)


class FileOperationException(ADBToolsException):
    """文件操作异常"""
    def __init__(self, message: str, operation: str):
        super().__init__(f"文件操作失败: {operation}\n错误信息: {message}", ErrorLevel.ERROR)


class ExceptionManager:
    """异常管理类"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self._error_handlers = {
            DeviceNotConnectedException: self._handle_device_not_connected,
            CommandExecutionException: self._handle_command_execution,
            FileOperationException: self._handle_file_operation,
            Exception: self._handle_unknown_error
        }

        self._dialog_icons = {
            ErrorLevel.INFO: QMessageBox.Information,
            ErrorLevel.WARNING: QMessageBox.Warning,
            ErrorLevel.ERROR: QMessageBox.Critical,
            ErrorLevel.CRITICAL: QMessageBox.Critical
        }

        self._dialog_titles = {
            ErrorLevel.INFO: "提示",
            ErrorLevel.WARNING: "警告",
            ErrorLevel.ERROR: "错误",
            ErrorLevel.CRITICAL: "严重错误"
        }

    def set_parent(self, parent):
        """设置父窗口，用于显示弹窗"""
        self.parent = parent

    def handle_exception(self, exc: Exception, show_traceback: bool = False) -> str:
        """处理异常"""
        handler = self._error_handlers.get(type(exc), self._handle_unknown_error)
        error_message = handler(exc)
        
        if show_traceback:
            error_message += f"\n\n调用栈信息:\n{traceback.format_exc()}"
        
        # 显示错误弹窗
        self._show_error_dialog(error_message, getattr(exc, 'level', ErrorLevel.ERROR))
        
        return error_message

    def _show_error_dialog(self, message: str, level: ErrorLevel):
        """显示错误弹窗"""
        dialog = QMessageBox(self.parent)
        dialog.setIcon(self._dialog_icons.get(level, QMessageBox.Critical))
        dialog.setWindowTitle(self._dialog_titles.get(level, "错误"))
        dialog.setText(message)
        dialog.setStandardButtons(QMessageBox.Ok)
        
        # 设置弹窗样式
        dialog.setStyleSheet("""
            QMessageBox {
                background-color: #2b2b2b;
                color: #ffffff;
                min-width: 400px;
            }
            QMessageBox QLabel {
                color: #ffffff;
                font-size: 12px;
                padding: 10px;
            }
            QPushButton {
                background-color: #3b3b3b;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 5px 15px;
                border-radius: 3px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #4b4b4b;
            }
            QPushButton:pressed {
                background-color: #2b2b2b;
            }
        """)
        
        dialog.exec_()

    def _handle_device_not_connected(self, exc: DeviceNotConnectedException) -> str:
        return f"设备连接错误: {exc.message}\n\n请检查:\n1. USB连接是否正常\n2. 设备是否已授权\n3. ADB服务是否正常运行"

    def _handle_command_execution(self, exc: CommandExecutionException) -> str:
        return str(exc)

    def _handle_file_operation(self, exc: FileOperationException) -> str:
        return str(exc)

    def _handle_unknown_error(self, exc: Exception) -> str:
        return f"未知错误: {str(exc)}"


# 创建全局异常管理器实例
exception_manager = ExceptionManager()


def exception_handler(show_traceback: bool = False, 
                     expected_exceptions: tuple = (Exception,),
                     error_message: str = None):
    """
    异常处理装饰器
    
    Args:
        show_traceback: 是否显示调用栈信息
        expected_exceptions: 需要捕获的异常类型
        error_message: 自定义错误信息
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except expected_exceptions as e:
                custom_message = error_message or str(e)
                if isinstance(e, ADBToolsException):
                    exception_manager.handle_exception(e, show_traceback)
                else:
                    new_exception = ADBToolsException(custom_message)
                    exception_manager.handle_exception(new_exception, show_traceback)
                return None
        return wrapper
    return decorator 