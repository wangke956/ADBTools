from enum import Enum, auto
from typing import Optional, Dict, Any
import traceback


class ErrorType(Enum):
    """错误类型枚举"""
    # 网络错误
    NETWORK_ERROR = auto()
    CONNECTION_ERROR = auto()
    TIMEOUT_ERROR = auto()
    
    # 设备错误
    DEVICE_NOT_FOUND = auto()
    DEVICE_DISCONNECTED = auto()
    DEVICE_PERMISSION_DENIED = auto()
    DEVICE_BUSY = auto()
    
    # 权限错误
    PERMISSION_DENIED = auto()
    ACCESS_DENIED = auto()
    
    # 文件错误
    FILE_NOT_FOUND = auto()
    FILE_PERMISSION_DENIED = auto()
    FILE_IO_ERROR = auto()
    
    # 应用错误
    APP_NOT_INSTALLED = auto()
    APP_START_FAILED = auto()
    APP_CRASHED = auto()
    
    # 命令错误
    COMMAND_NOT_FOUND = auto()
    COMMAND_EXECUTION_FAILED = auto()
    
    # 配置错误
    CONFIG_ERROR = auto()
    INVALID_PARAMETER = auto()
    
    # 系统错误
    SYSTEM_ERROR = auto()
    OUT_OF_MEMORY = auto()
    
    # 未知错误
    UNKNOWN_ERROR = auto()


class ErrorSeverity(Enum):
    """错误严重程度"""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


class BaseAppException(Exception):
    """应用异常基类"""
    
    def __init__(self, message: str, error_type: ErrorType, severity: ErrorSeverity = ErrorSeverity.ERROR):
        super().__init__(message)
        self.error_type = error_type
        self.severity = severity
        self.timestamp = None  # 将在异常处理时设置
        self.stack_trace = traceback.format_exc()
    
    def get_error_info(self) -> Dict[str, Any]:
        """获取错误信息字典"""
        return {
            'message': str(self),
            'error_type': self.error_type.name,
            'severity': self.severity.name,
            'timestamp': self.timestamp,
            'stack_trace': self.stack_trace
        }


# 网络异常类
class NetworkException(BaseAppException):
    """网络异常基类"""
    
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.ERROR):
        super().__init__(message, ErrorType.NETWORK_ERROR, severity)


class ConnectionException(NetworkException):
    """连接异常"""
    
    def __init__(self, message: str):
        super().__init__(message)
        self.error_type = ErrorType.CONNECTION_ERROR


class TimeoutException(NetworkException):
    """超时异常"""
    
    def __init__(self, message: str):
        super().__init__(message)
        self.error_type = ErrorType.TIMEOUT_ERROR


# 设备异常类
class DeviceException(BaseAppException):
    """设备异常基类"""
    
    def __init__(self, message: str, device_id: Optional[str] = None, severity: ErrorSeverity = ErrorSeverity.ERROR):
        super().__init__(message, ErrorType.DEVICE_NOT_FOUND, severity)
        self.device_id = device_id


class DeviceNotFoundException(DeviceException):
    """设备未找到异常"""
    
    def __init__(self, device_id: str):
        message = f"设备 {device_id} 未找到"
        super().__init__(message, device_id)
        self.error_type = ErrorType.DEVICE_NOT_FOUND


class DeviceDisconnectedException(DeviceException):
    """设备断开连接异常"""
    
    def __init__(self, device_id: str):
        message = f"设备 {device_id} 已断开连接"
        super().__init__(message, device_id)
        self.error_type = ErrorType.DEVICE_DISCONNECTED


class DevicePermissionDeniedException(DeviceException):
    """设备权限拒绝异常"""
    
    def __init__(self, device_id: str):
        message = f"设备 {device_id} 权限被拒绝"
        super().__init__(message, device_id)
        self.error_type = ErrorType.DEVICE_PERMISSION_DENIED


class DeviceBusyException(DeviceException):
    """设备忙异常"""
    
    def __init__(self, device_id: str):
        message = f"设备 {device_id} 正在处理其他任务"
        super().__init__(message, device_id)
        self.error_type = ErrorType.DEVICE_BUSY


# 权限异常类
class PermissionException(BaseAppException):
    """权限异常基类"""
    
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.ERROR):
        super().__init__(message, ErrorType.PERMISSION_DENIED, severity)


class AccessDeniedException(PermissionException):
    """访问拒绝异常"""
    
    def __init__(self, resource: str):
        message = f"访问资源 {resource} 被拒绝"
        super().__init__(message)
        self.error_type = ErrorType.ACCESS_DENIED


# 文件异常类
class FileException(BaseAppException):
    """文件异常基类"""
    
    def __init__(self, message: str, file_path: Optional[str] = None, severity: ErrorSeverity = ErrorSeverity.ERROR):
        super().__init__(message, ErrorType.FILE_NOT_FOUND, severity)
        self.file_path = file_path


class FileNotFoundException(FileException):
    """文件未找到异常"""
    
    def __init__(self, file_path: str):
        message = f"文件 {file_path} 未找到"
        super().__init__(message, file_path)
        self.error_type = ErrorType.FILE_NOT_FOUND


class FilePermissionDeniedException(FileException):
    """文件权限拒绝异常"""
    
    def __init__(self, file_path: str):
        message = f"没有权限访问文件 {file_path}"
        super().__init__(message, file_path)
        self.error_type = ErrorType.FILE_PERMISSION_DENIED


class FileIOException(FileException):
    """文件IO异常"""
    
    def __init__(self, file_path: str, operation: str):
        message = f"文件 {file_path} {operation} 失败"
        super().__init__(message, file_path)
        self.error_type = ErrorType.FILE_IO_ERROR
        self.operation = operation


# 应用异常类
class AppException(BaseAppException):
    """应用异常基类"""
    
    def __init__(self, message: str, app_package: Optional[str] = None, severity: ErrorSeverity = ErrorSeverity.ERROR):
        super().__init__(message, ErrorType.APP_NOT_INSTALLED, severity)
        self.app_package = app_package


class AppNotInstalledException(AppException):
    """应用未安装异常"""
    
    def __init__(self, app_package: str):
        message = f"应用 {app_package} 未安装"
        super().__init__(message, app_package)
        self.error_type = ErrorType.APP_NOT_INSTALLED


class AppStartFailedException(AppException):
    """应用启动失败异常"""
    
    def __init__(self, app_package: str):
        message = f"应用 {app_package} 启动失败"
        super().__init__(message, app_package)
        self.error_type = ErrorType.APP_START_FAILED


class AppCrashedException(AppException):
    """应用崩溃异常"""
    
    def __init__(self, app_package: str):
        message = f"应用 {app_package} 崩溃"
        super().__init__(message, app_package)
        self.error_type = ErrorType.APP_CRASHED


# 命令异常类
class CommandException(BaseAppException):
    """命令异常基类"""
    
    def __init__(self, message: str, command: Optional[str] = None, severity: ErrorSeverity = ErrorSeverity.ERROR):
        super().__init__(message, ErrorType.COMMAND_NOT_FOUND, severity)
        self.command = command


class CommandNotFoundException(CommandException):
    """命令未找到异常"""
    
    def __init__(self, command: str):
        message = f"命令 {command} 未找到"
        super().__init__(message, command)
        self.error_type = ErrorType.COMMAND_NOT_FOUND


class CommandExecutionFailedException(CommandException):
    """命令执行失败异常"""
    
    def __init__(self, command: str, error: str):
        message = f"命令 {command} 执行失败: {error}"
        super().__init__(message, command)
        self.error_type = ErrorType.COMMAND_EXECUTION_FAILED
        self.execution_error = error


# 配置异常类
class ConfigException(BaseAppException):
    """配置异常基类"""
    
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.ERROR):
        super().__init__(message, ErrorType.CONFIG_ERROR, severity)


class InvalidParameterException(ConfigException):
    """无效参数异常"""
    
    def __init__(self, parameter: str, value: Any):
        message = f"参数 {parameter} 的值 {value} 无效"
        super().__init__(message)
        self.error_type = ErrorType.INVALID_PARAMETER
        self.parameter = parameter
        self.value = value


# 系统异常类
class SystemException(BaseAppException):
    """系统异常基类"""
    
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.CRITICAL):
        super().__init__(message, ErrorType.SYSTEM_ERROR, severity)


class OutOfMemoryException(SystemException):
    """内存不足异常"""
    
    def __init__(self):
        message = "系统内存不足"
        super().__init__(message)
        self.error_type = ErrorType.OUT_OF_MEMORY


# 未知异常类
class UnknownException(BaseAppException):
    """未知异常"""
    
    def __init__(self, message: str):
        super().__init__(message, ErrorType.UNKNOWN_ERROR)
