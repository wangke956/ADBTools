from PyQt5.QtCore import QThread, QMutex, QWaitCondition, pyqtSignal, QObject
import time
from enum import Enum
from typing import Dict, List, Optional, Callable, Any


class ThreadStatus(Enum):
    """线程状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ThreadPoolManager(QObject):
    """线程池管理器"""
    
    thread_started_signal = pyqtSignal(str, str)  # thread_id, thread_name
    thread_completed_signal = pyqtSignal(str, str)  # thread_id, thread_name
    thread_failed_signal = pyqtSignal(str, str, str)  # thread_id, thread_name, error_message
    thread_cancelled_signal = pyqtSignal(str, str)  # thread_id, thread_name
    pool_status_signal = pyqtSignal(dict)  # 线程池状态信息
    
    def __init__(self, max_workers: int = 4):
        super().__init__()
        self.max_workers = max_workers
        self.active_threads: Dict[str, QThread] = {}
        self.thread_status: Dict[str, ThreadStatus] = {}
        self.thread_names: Dict[str, str] = {}
        self.thread_results: Dict[str, Any] = {}
        self.thread_errors: Dict[str, Exception] = {}
        
        # 线程安全机制
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()
        
        # 统计信息
        self.total_threads = 0
        self.completed_threads = 0
        self.failed_threads = 0
        
    def add_thread(self, thread: QThread, thread_name: str) -> str:
        """添加线程到线程池"""
        thread_id = f"thread_{int(time.time() * 1000)}_{self.total_threads}"
        
        with QMutexLocker(self.mutex):
            self.active_threads[thread_id] = thread
            self.thread_status[thread_id] = ThreadStatus.IDLE
            self.thread_names[thread_id] = thread_name
            self.total_threads += 1
            
            # 连接信号
            thread.started.connect(lambda: self._on_thread_started(thread_id))
            thread.finished.connect(lambda: self._on_thread_finished(thread_id))
            
            # 检查是否需要等待
            if len(self.active_threads) > self.max_workers:
                self.wait_condition.wait(self.mutex)
        
        return thread_id
    
    def start_thread(self, thread_id: str) -> bool:
        """启动指定线程"""
        with QMutexLocker(self.mutex):
            if thread_id not in self.active_threads:
                return False
                
            thread = self.active_threads[thread_id]
            if self.thread_status[thread_id] == ThreadStatus.IDLE:
                self.thread_status[thread_id] = ThreadStatus.RUNNING
                thread.start()
                return True
        return False
    
    def cancel_thread(self, thread_id: str) -> bool:
        """取消指定线程"""
        with QMutexLocker(self.mutex):
            if thread_id not in self.active_threads:
                return False
                
            thread = self.active_threads[thread_id]
            if self.thread_status[thread_id] == ThreadStatus.RUNNING:
                self.thread_status[thread_id] = ThreadStatus.CANCELLED
                thread.requestInterruption()
                return True
        return False
    
    def wait_for_thread(self, thread_id: str, timeout: Optional[int] = None) -> bool:
        """等待线程完成"""
        with QMutexLocker(self.mutex):
            if thread_id not in self.active_threads:
                return False
                
            start_time = time.time()
            while self.thread_status[thread_id] in [ThreadStatus.RUNNING, ThreadStatus.IDLE]:
                if timeout is not None and (time.time() - start_time) > timeout:
                    return False
                self.wait_condition.wait(self.mutex, 100)  # 100ms超时
        
        return True
    
    def get_thread_status(self, thread_id: str) -> Optional[ThreadStatus]:
        """获取线程状态"""
        with QMutexLocker(self.mutex):
            return self.thread_status.get(thread_id)
    
    def get_thread_result(self, thread_id: str) -> Optional[Any]:
        """获取线程执行结果"""
        with QMutexLocker(self.mutex):
            return self.thread_results.get(thread_id)
    
    def get_thread_error(self, thread_id: str) -> Optional[Exception]:
        """获取线程错误信息"""
        with QMutexLocker(self.mutex):
            return self.thread_errors.get(thread_id)
    
    def get_pool_status(self) -> Dict[str, Any]:
        """获取线程池状态信息"""
        with QMutexLocker(self.mutex):
            status_counts = {}
            for status in ThreadStatus:
                status_counts[status.value] = sum(1 for s in self.thread_status.values() if s == status)
            
            return {
                'total_threads': self.total_threads,
                'active_threads': len(self.active_threads),
                'completed_threads': self.completed_threads,
                'failed_threads': self.failed_threads,
                'status_counts': status_counts,
                'max_workers': self.max_workers
            }
    
    def clear_completed_threads(self) -> None:
        """清理已完成的线程"""
        with QMutexLocker(self.mutex):
            completed_threads = [tid for tid, status in self.thread_status.items() 
                                if status in [ThreadStatus.COMPLETED, ThreadStatus.FAILED, ThreadStatus.CANCELLED]]
            
            for thread_id in completed_threads:
                thread = self.active_threads.pop(thread_id)
                thread.deleteLater()
                self.thread_status.pop(thread_id)
                self.thread_names.pop(thread_id)
                self.thread_results.pop(thread_id, None)
                self.thread_errors.pop(thread_id, None)
    
    def shutdown(self, wait: bool = True) -> None:
        """关闭线程池"""
        with QMutexLocker(self.mutex):
            # 取消所有运行中的线程
            for thread_id, status in self.thread_status.items():
                if status == ThreadStatus.RUNNING:
                    self.cancel_thread(thread_id)
            
            if wait:
                # 等待所有线程完成
                while self.active_threads:
                    self.wait_condition.wait(self.mutex, 100)
            
            # 清理所有线程
            for thread in self.active_threads.values():
                thread.deleteLater()
            
            self.active_threads.clear()
            self.thread_status.clear()
            self.thread_names.clear()
            self.thread_results.clear()
            self.thread_errors.clear()
    
    def _on_thread_started(self, thread_id: str) -> None:
        """线程启动回调"""
        with QMutexLocker(self.mutex):
            if thread_id in self.thread_status:
                self.thread_status[thread_id] = ThreadStatus.RUNNING
        
        thread_name = self.thread_names.get(thread_id, "Unknown")
        self.thread_started_signal.emit(thread_id, thread_name)
        self._update_pool_status()
    
    def _on_thread_finished(self, thread_id: str) -> None:
        """线程完成回调"""
        with QMutexLocker(self.mutex):
            if thread_id in self.thread_status:
                current_status = self.thread_status[thread_id]
                
                if current_status == ThreadStatus.CANCELLED:
                    self.thread_status[thread_id] = ThreadStatus.CANCELLED
                else:
                    self.thread_status[thread_id] = ThreadStatus.COMPLETED
                    self.completed_threads += 1
                
                # 通知等待的线程
                self.wait_condition.wakeAll()
        
        thread_name = self.thread_names.get(thread_id, "Unknown")
        
        if self.thread_status.get(thread_id) == ThreadStatus.COMPLETED:
            self.thread_completed_signal.emit(thread_id, thread_name)
        elif self.thread_status.get(thread_id) == ThreadStatus.CANCELLED:
            self.thread_cancelled_signal.emit(thread_id, thread_name)
        
        self._update_pool_status()
    
    def _update_pool_status(self) -> None:
        """更新线程池状态并发送信号"""
        status = self.get_pool_status()
        self.pool_status_signal.emit(status)


class QMutexLocker:
    """QMutex的自动锁管理"""
    
    def __init__(self, mutex: QMutex):
        self.mutex = mutex
        self.mutex.lock()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.mutex.unlock()
