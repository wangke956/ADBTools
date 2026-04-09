from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition
from logger_manager import get_logger, log_thread_start, log_thread_complete, log_exception
import time
from enum import Enum
from typing import Optional, Dict, Any, Callable


class ThreadStatus(Enum):
    """线程状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BaseThread(QThread):
    """线程基类，统一线程基本结构和信号定义"""
    
    # 基本信号
    progress_signal = pyqtSignal(str)    # 进度信号
    progress_percent_signal = pyqtSignal(int)  # 进度百分比信号
    error_signal = pyqtSignal(str)       # 错误信号
    success_signal = pyqtSignal(str)     # 成功信号
    finished_signal = pyqtSignal()       # 完成信号
    cancelled_signal = pyqtSignal()      # 取消信号
    status_changed_signal = pyqtSignal(str)  # 状态变化信号
    
    def __init__(self, thread_name=None, timeout: Optional[int] = None, max_retries: int = 0, retry_interval: int = 1):
        super().__init__()
        self.thread_name = thread_name or self.__class__.__name__
        self.logger = get_logger(f"ADBTools.{self.thread_name}")
        self.is_running = False
        self.status = ThreadStatus.IDLE
        self.timeout = timeout  # 超时时间（秒）
        self.max_retries = max_retries  # 最大重试次数
        self.retry_interval = retry_interval  # 重试间隔（秒）
        self.retry_count = 0
        
        # 线程安全机制
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()
        self._should_cancel = False
        
        # 执行结果
        self.result = None
        self.error = None
        
    def run(self):
        """线程执行入口，包含统一的日志记录、异常处理、超时和重试机制"""
        thread_id = self.currentThreadId()
        
        try:
            # 更新状态为运行中
            self._update_status(ThreadStatus.RUNNING)
            
            # 记录线程开始
            log_thread_start(self.thread_name, {"thread_id": thread_id})
            self.logger.info(f"线程开始执行: {self.thread_name}")
            
            # 执行带超时和重试的操作
            success = self._execute_with_timeout_and_retry()
            
            if success:
                # 记录线程完成
                log_thread_complete(self.thread_name, "success")
                self.logger.info(f"线程执行完成: {self.thread_name}")
                self._update_status(ThreadStatus.COMPLETED)
            else:
                # 记录线程失败
                log_thread_complete(self.thread_name, "failed", {"error": str(self.error)})
                self.logger.error(f"线程执行失败: {self.thread_name}")
                self._update_status(ThreadStatus.FAILED)
                
        except Exception as e:
            # 记录异常
            self.error = e
            log_exception(self.logger, self.thread_name, e)
            log_thread_complete(self.thread_name, "failed", {"error": str(e)})
            self.logger.error(f"线程执行异常: {self.thread_name} - {str(e)}")
            
            # 更新状态为失败
            self._update_status(ThreadStatus.FAILED)
            
            # 发送错误信号
            error_msg = f"{self.thread_name} 执行失败: {str(e)}"
            self.error_signal.emit(error_msg)
            
        finally:
            self.is_running = False
            # 发送完成信号
            self.finished_signal.emit()
            
    def _execute_with_timeout_and_retry(self) -> bool:
        """执行带超时和重试机制的操作"""
        start_time = time.time()
        
        for attempt in range(self.max_retries + 1):
            # 检查是否被取消
            if self._should_cancel:
                self._update_status(ThreadStatus.CANCELLED)
                self.cancelled_signal.emit()
                return False
            
            # 检查超时
            if self.timeout and (time.time() - start_time) > self.timeout:
                self.error = TimeoutError(f"线程执行超时（{self.timeout}秒）")
                self.error_signal.emit(f"{self.thread_name} 执行超时")
                return False
            
            try:
                # 执行具体的线程实现
                self._run_implementation()
                return True
                
            except Exception as e:
                self.retry_count += 1
                
                # 如果是最后一次尝试或不应该重试，则抛出异常
                if attempt >= self.max_retries or not self._should_retry(e):
                    self.error = e
                    raise
                
                # 记录重试信息
                self.logger.warning(f"{self.thread_name} 执行失败，准备重试 ({attempt + 1}/{self.max_retries}): {str(e)}")
                self.progress_signal.emit(f"执行失败，准备重试 ({attempt + 1}/{self.max_retries})...")
                
                # 等待重试间隔
                for _ in range(self.retry_interval * 10):
                    if self._should_cancel:
                        self._update_status(ThreadStatus.CANCELLED)
                        self.cancelled_signal.emit()
                        return False
                    time.sleep(0.1)
        
        return False
    
    def _should_retry(self, exception: Exception) -> bool:
        """判断是否应该重试（可由子类重写）"""
        return True  # 默认所有异常都重试
    
    def _run_implementation(self):
        """具体线程的实现方法，由子类重写"""
        raise NotImplementedError("子类必须实现 _run_implementation 方法")
    
    def cancel(self):
        """取消线程执行"""
        with QMutexLocker(self.mutex):
            if self.status in [ThreadStatus.RUNNING, ThreadStatus.IDLE]:
                self._should_cancel = True
                self.logger.info(f"线程取消请求已发送: {self.thread_name}")
                self.requestInterruption()
    
    def pause(self):
        """暂停线程"""
        with QMutexLocker(self.mutex):
            if self.status == ThreadStatus.RUNNING:
                self._update_status(ThreadStatus.PAUSED)
                self.wait_condition.wait(self.mutex)
    
    def resume(self):
        """恢复线程"""
        with QMutexLocker(self.mutex):
            if self.status == ThreadStatus.PAUSED:
                self._update_status(ThreadStatus.RUNNING)
                self.wait_condition.wakeAll()
    
    def stop(self):
        """停止线程"""
        if self.isRunning():
            self.logger.info(f"正在停止线程: {self.thread_name}")
            self.cancel()
            self.wait()
            self.logger.info(f"线程已停止: {self.thread_name}")
            self.is_running = False
    
    def get_status(self) -> ThreadStatus:
        """获取线程状态"""
        with QMutexLocker(self.mutex):
            return self.status
    
    def get_result(self) -> Optional[Any]:
        """获取执行结果"""
        with QMutexLocker(self.mutex):
            return self.result
    
    def get_error(self) -> Optional[Exception]:
        """获取错误信息"""
        with QMutexLocker(self.mutex):
            return self.error
    
    def _update_status(self, status: ThreadStatus):
        """更新线程状态"""
        with QMutexLocker(self.mutex):
            old_status = self.status
            self.status = status
            
        if old_status != status:
            self.status_changed_signal.emit(status.value)
    
    def check_cancelled(self):
        """检查是否应该取消执行（在长时间操作中定期调用）"""
        if self._should_cancel or self.isInterruptionRequested():
            self._update_status(ThreadStatus.CANCELLED)
            self.cancelled_signal.emit()
            raise RuntimeError("线程已被取消")


class QMutexLocker:
    """QMutex的自动锁管理"""
    
    def __init__(self, mutex: QMutex):
        self.mutex = mutex
        self.mutex.lock()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.mutex.unlock()


class DeviceBaseThread(BaseThread):
    """设备相关线程基类"""
    
    def __init__(self, device_id, thread_name=None):
        super().__init__(thread_name)
        self.device_id = device_id
        
    def _run_implementation(self):
        """设备线程的实现模板"""
        if not self.device_id:
            self.error_signal.emit("设备ID不能为空")
            return
        
        self.progress_signal.emit(f"开始处理设备: {self.device_id}")


class FileBaseThread(BaseThread):
    """文件操作线程基类"""
    
    def __init__(self, file_path, thread_name=None):
        super().__init__(thread_name)
        self.file_path = file_path
        
    def _run_implementation(self):
        """文件线程的实现模板"""
        if not self.file_path:
            self.error_signal.emit("文件路径不能为空")
            return
        
        self.progress_signal.emit(f"开始处理文件: {self.file_path}")
