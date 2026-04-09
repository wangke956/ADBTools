from PyQt5.QtCore import QObject, pyqtSignal, QMutex, QWaitCondition, QTimer
from enum import Enum, auto
from typing import Dict, List, Optional, Callable, Any
import time
from concurrent.futures import ThreadPoolExecutor
from .exception_handler import *


class OperationStatus(Enum):
    """操作状态枚举"""
    QUEUED = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()
    PAUSED = auto()


class OperationPriority(Enum):
    """操作优先级枚举"""
    LOW = auto()
    NORMAL = auto()
    HIGH = auto()
    URGENT = auto()


class Operation:
    """操作类"""
    
    def __init__(self, 
                 operation_id: str,
                 operation_type: str,
                 callback: Callable,
                 priority: OperationPriority = OperationPriority.NORMAL,
                 dependencies: Optional[List[str]] = None,
                 timeout: Optional[int] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.operation_id = operation_id
        self.operation_type = operation_type
        self.callback = callback
        self.priority = priority
        self.dependencies = dependencies or []
        self.timeout = timeout
        self.metadata = metadata or {}
        
        # 状态管理
        self.status = OperationStatus.QUEUED
        self.start_time = None
        self.completion_time = None
        self.result = None
        self.error = None
        self.progress = 0.0
    
    def __lt__(self, other):
        """优先级排序"""
        return self.priority.value > other.priority.value


class OperationQueueManager(QObject):
    """操作队列管理器"""
    
    # 信号定义
    operation_queued_signal = pyqtSignal(str, str)  # operation_id, operation_type
    operation_started_signal = pyqtSignal(str, str)  # operation_id, operation_type
    operation_completed_signal = pyqtSignal(str, str, object)  # operation_id, operation_type, result
    operation_failed_signal = pyqtSignal(str, str, str)  # operation_id, operation_type, error_message
    operation_cancelled_signal = pyqtSignal(str, str)  # operation_id, operation_type
    operation_progress_signal = pyqtSignal(str, str, float)  # operation_id, operation_type, progress
    queue_status_signal = pyqtSignal(dict)  # 队列状态信息
    
    def __init__(self, max_concurrent_operations: int = 2):
        super().__init__()
        self.max_concurrent_operations = max_concurrent_operations
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_operations)
        
        # 队列和操作管理
        self.operation_queue: List[Operation] = []
        self.running_operations: Dict[str, Operation] = {}
        self.completed_operations: Dict[str, Operation] = {}
        self.operation_futures: Dict[str, Any] = {}
        
        # 线程安全机制
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()
        
        # 设备锁定机制（避免同一设备并发操作）
        self.locked_devices: Dict[str, str] = {}  # device_id -> operation_id
        
        # 调度定时器
        self.scheduler_timer = QTimer()
        self.scheduler_timer.timeout.connect(self._schedule_operations)
        self.scheduler_timer.start(100)  # 每100ms调度一次
    
    def add_operation(self, operation: Operation) -> bool:
        """添加操作到队列"""
        with QMutexLocker(self.mutex):
            # 检查操作ID是否已存在
            if operation.operation_id in self.running_operations or \
               operation.operation_id in self.completed_operations:
                return False
            
            # 检查依赖关系
            if not self._check_dependencies(operation):
                return False
            
            # 检查设备锁定
            device_id = operation.metadata.get('device_id')
            if device_id and device_id in self.locked_devices:
                self._log_operation(operation, f"设备 {device_id} 被锁定，操作加入队列")
            
            # 添加到队列
            self.operation_queue.append(operation)
            self._sort_queue()
            
            # 发送信号
            self.operation_queued_signal.emit(operation.operation_id, operation.operation_type)
            
            # 更新队列状态
            self._update_queue_status()
            
            return True
    
    def cancel_operation(self, operation_id: str) -> bool:
        """取消操作"""
        with QMutexLocker(self.mutex):
            # 检查是否在运行中
            if operation_id in self.running_operations:
                operation = self.running_operations[operation_id]
                operation.status = OperationStatus.CANCELLED
                
                # 取消线程
                if operation_id in self.operation_futures:
                    future = self.operation_futures[operation_id]
                    future.cancel()
                
                # 释放设备锁定
                device_id = operation.metadata.get('device_id')
                if device_id and self.locked_devices.get(device_id) == operation_id:
                    del self.locked_devices[device_id]
                
                # 发送信号
                self.operation_cancelled_signal.emit(operation_id, operation.operation_type)
                return True
            
            # 检查是否在队列中
            for i, operation in enumerate(self.operation_queue):
                if operation.operation_id == operation_id:
                    operation.status = OperationStatus.CANCELLED
                    self.operation_queue.pop(i)
                    self.operation_cancelled_signal.emit(operation_id, operation.operation_type)
                    return True
            
            return False
    
    def pause_operation(self, operation_id: str) -> bool:
        """暂停操作"""
        with QMutexLocker(self.mutex):
            if operation_id in self.running_operations:
                operation = self.running_operations[operation_id]
                operation.status = OperationStatus.PAUSED
                return True
            return False
    
    def resume_operation(self, operation_id: str) -> bool:
        """恢复操作"""
        with QMutexLocker(self.mutex):
            if operation_id in self.running_operations:
                operation = self.running_operations[operation_id]
                operation.status = OperationStatus.RUNNING
                return True
            return False
    
    def get_operation_status(self, operation_id: str) -> Optional[OperationStatus]:
        """获取操作状态"""
        with QMutexLocker(self.mutex):
            # 检查运行中的操作
            if operation_id in self.running_operations:
                return self.running_operations[operation_id].status
            
            # 检查队列中的操作
            for operation in self.operation_queue:
                if operation.operation_id == operation_id:
                    return operation.status
            
            # 检查已完成的操作
            if operation_id in self.completed_operations:
                return self.completed_operations[operation_id].status
            
            return None
    
    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态信息"""
        with QMutexLocker(self.mutex):
            status_counts = {}
            for status in OperationStatus:
                status_counts[status.name] = sum(1 for op in self.operation_queue if op.status == status)
            
            return {
                'queued_operations': len(self.operation_queue),
                'running_operations': len(self.running_operations),
                'completed_operations': len(self.completed_operations),
                'status_counts': status_counts,
                'locked_devices': len(self.locked_devices),
                'max_concurrent_operations': self.max_concurrent_operations
            }
    
    def clear_completed_operations(self) -> None:
        """清理已完成的操作"""
        with QMutexLocker(self.mutex):
            self.completed_operations.clear()
    
    def shutdown(self, wait: bool = True) -> None:
        """关闭队列管理器"""
        with QMutexLocker(self.mutex):
            # 取消所有操作
            for operation_id in list(self.running_operations.keys()):
                self.cancel_operation(operation_id)
            
            # 清空队列
            self.operation_queue.clear()
            
            # 关闭调度器
            self.scheduler_timer.stop()
            
            # 关闭线程池
            self.executor.shutdown(wait=wait)
    
    def _schedule_operations(self):
        """调度操作执行"""
        with QMutexLocker(self.mutex):
            # 检查是否有可用的执行槽位
            if len(self.running_operations) >= self.max_concurrent_operations:
                return
            
            # 遍历队列，找到可以执行的操作
            executable_operations = []
            
            for i, operation in enumerate(self.operation_queue):
                # 检查操作是否已取消
                if operation.status == OperationStatus.CANCELLED:
                    self.operation_queue.pop(i)
                    continue
                
                # 检查依赖是否已完成
                if not self._check_dependencies_completed(operation):
                    continue
                
                # 检查设备锁定
                device_id = operation.metadata.get('device_id')
                if device_id and device_id in self.locked_devices:
                    continue
                
                # 可以执行此操作
                executable_operations.append((i, operation))
            
            # 按优先级排序
            executable_operations.sort(key=lambda x: x[1])
            
            # 执行操作
            for i, operation in executable_operations:
                if len(self.running_operations) >= self.max_concurrent_operations:
                    break
                
                # 从队列中移除
                self.operation_queue.pop(i)
                
                # 添加到运行中
                self.running_operations[operation.operation_id] = operation
                
                # 锁定设备
                device_id = operation.metadata.get('device_id')
                if device_id:
                    self.locked_devices[device_id] = operation.operation_id
                
                # 更新状态
                operation.status = OperationStatus.RUNNING
                operation.start_time = time.time()
                
                # 发送信号
                self.operation_started_signal.emit(operation.operation_id, operation.operation_type)
                
                # 提交到线程池
                future = self.executor.submit(self._execute_operation, operation)
                self.operation_futures[operation.operation_id] = future
                
                # 更新队列状态
                self._update_queue_status()
    
    def _execute_operation(self, operation: Operation):
        """执行操作"""
        try:
            # 设置进度回调
            def progress_callback(progress: float):
                operation.progress = progress
                self.operation_progress_signal.emit(
                    operation.operation_id, 
                    operation.operation_type, 
                    progress
                )
            
            # 执行回调
            operation.result = operation.callback(progress_callback=progress_callback)
            
            # 更新状态
            with QMutexLocker(self.mutex):
                operation.status = OperationStatus.COMPLETED
                operation.completion_time = time.time()
                
                # 移除运行中状态
                del self.running_operations[operation.operation_id]
                del self.operation_futures[operation.operation_id]
                
                # 释放设备锁定
                device_id = operation.metadata.get('device_id')
                if device_id and self.locked_devices.get(device_id) == operation.operation_id:
                    del self.locked_devices[device_id]
                
                # 添加到已完成
                self.completed_operations[operation.operation_id] = operation
            
            # 发送完成信号
            self.operation_completed_signal.emit(
                operation.operation_id, 
                operation.operation_type, 
                operation.result
            )
            
        except Exception as e:
            # 更新状态
            with QMutexLocker(self.mutex):
                operation.status = OperationStatus.FAILED
                operation.error = str(e)
                operation.completion_time = time.time()
                
                # 移除运行中状态
                del self.running_operations[operation.operation_id]
                del self.operation_futures[operation.operation_id]
                
                # 释放设备锁定
                device_id = operation.metadata.get('device_id')
                if device_id and self.locked_devices.get(device_id) == operation.operation_id:
                    del self.locked_devices[device_id]
                
                # 添加到已完成
                self.completed_operations[operation.operation_id] = operation
            
            # 发送失败信号
            self.operation_failed_signal.emit(
                operation.operation_id, 
                operation.operation_type, 
                str(e)
            )
        
        finally:
            # 更新队列状态
            self._update_queue_status()
    
    def _check_dependencies(self, operation: Operation) -> bool:
        """检查依赖关系是否满足"""
        for dep_id in operation.dependencies:
            if dep_id not in self.completed_operations:
                return False
        return True
    
    def _check_dependencies_completed(self, operation: Operation) -> bool:
        """检查依赖是否已完成"""
        for dep_id in operation.dependencies:
            if dep_id not in self.completed_operations:
                return False
        return True
    
    def _sort_queue(self):
        """按优先级排序队列"""
        self.operation_queue.sort()
    
    def _update_queue_status(self):
        """更新队列状态并发送信号"""
        status = self.get_queue_status()
        self.queue_status_signal.emit(status)
    
    def _log_operation(self, operation: Operation, message: str):
        """记录操作日志"""
        print(f"[OperationQueue] {operation.operation_type} ({operation.operation_id}): {message}")


class QMutexLocker:
    """QMutex的自动锁管理"""
    
    def __init__(self, mutex: QMutex):
        self.mutex = mutex
        self.mutex.lock()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.mutex.unlock()
