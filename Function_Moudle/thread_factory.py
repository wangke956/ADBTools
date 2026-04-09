from logger_manager import get_logger, log_operation
from .thread_pool_manager import ThreadPoolManager
from .operation_queue_manager import OperationQueueManager, Operation, OperationPriority
import time
from typing import Dict, Any, Optional


class ThreadFactory:
    """线程工厂类，统一管理线程的创建和生命周期"""
    
    _instance = None
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(ThreadFactory, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化线程工厂"""
        if self._initialized:
            return
            
        self.logger = get_logger("ADBTools.ThreadFactory")
        self.thread_registry = {}  # 线程注册表
        
        # 初始化线程池管理器
        self.thread_pool = ThreadPoolManager(max_workers=4)
        
        # 初始化操作队列管理器
        self.operation_queue = OperationQueueManager(max_concurrent_operations=2)
        
        self._initialized = True
        
    def create_thread(self, thread_type, **kwargs):
        """
        创建线程实例
        
        Args:
            thread_type: 线程类型
            **kwargs: 线程参数
            
        Returns:
            线程实例
        """
        try:
            thread_class = self._get_thread_class(thread_type)
            
            # 创建线程实例
            thread = thread_class(**kwargs)
            
            # 注册线程
            thread_id = id(thread)
            self.thread_registry[thread_id] = {
                'thread': thread,
                'type': thread_type,
                'status': 'created',
                'kwargs': kwargs
            }
            
            self.logger.info(f"创建线程成功: {thread_type} (ID: {thread_id})")
            log_operation("thread_create", {
                "thread_type": thread_type,
                "thread_id": thread_id,
                "params": kwargs
            }, result="success")
            
            return thread
            
        except Exception as e:
            self.logger.error(f"创建线程失败: {thread_type} - {str(e)}")
            log_operation("thread_create_failed", {
                "thread_type": thread_type,
                "error": str(e),
                "params": kwargs
            }, result="failed")
            raise
    
    def create_thread_with_pool(self, thread_type, **kwargs) -> str:
        """
        通过线程池创建线程
        
        Args:
            thread_type: 线程类型
            **kwargs: 线程参数
            
        Returns:
            线程ID
        """
        try:
            thread = self.create_thread(thread_type, **kwargs)
            thread_id = self.thread_pool.add_thread(thread, thread_type)
            
            self.logger.info(f"通过线程池创建线程成功: {thread_type} (ID: {thread_id})")
            return thread_id
            
        except Exception as e:
            self.logger.error(f"通过线程池创建线程失败: {thread_type} - {str(e)}")
            raise
    
    def create_operation(self, operation_type, callback, **kwargs) -> str:
        """
        创建操作并加入队列
        
        Args:
            operation_type: 操作类型
            callback: 操作回调函数
            **kwargs: 操作参数
            
        Returns:
            操作ID
        """
        try:
            operation_id = f"operation_{int(time.time() * 1000)}_{id(callback)}"
            
            # 创建操作对象
            operation = Operation(
                operation_id=operation_id,
                operation_type=operation_type,
                callback=callback,
                priority=kwargs.get('priority', OperationPriority.NORMAL),
                dependencies=kwargs.get('dependencies'),
                timeout=kwargs.get('timeout'),
                metadata=kwargs.get('metadata', {})
            )
            
            # 添加到队列
            success = self.operation_queue.add_operation(operation)
            
            if success:
                self.logger.info(f"创建操作成功: {operation_type} (ID: {operation_id})")
                return operation_id
            else:
                raise RuntimeError(f"添加操作到队列失败: {operation_type}")
                
        except Exception as e:
            self.logger.error(f"创建操作失败: {operation_type} - {str(e)}")
            raise
    
    def _get_thread_class(self, thread_type):
        """根据线程类型获取对应的线程类"""
        # 动态导入线程类，避免循环导入
        if thread_type == 'refresh_devices':
            from Function_Moudle.device_threads import RefreshDevicesThread
            return RefreshDevicesThread
            
        elif thread_type == 'u2_connect':
            from Function_Moudle.device_threads import U2ConnectThread
            return U2ConnectThread
            
        elif thread_type == 'reboot_device':
            from Function_Moudle.device_threads import RebootDeviceThread
            return RebootDeviceThread
            
        elif thread_type == 'u2_reinit':
            from Function_Moudle.device_threads import U2ReinitThread
            return U2ReinitThread
            
        elif thread_type == 'adb_root':
            from Function_Moudle.device_threads import AdbRootThread
            return AdbRootThread
            
        elif thread_type == 'install_file':
            from Function_Moudle.app_threads import InstallFileThread
            return InstallFileThread
            
        elif thread_type == 'uninstall_app':
            from Function_Moudle.app_threads import UninstallAppThread
            return UninstallAppThread
            
        elif thread_type == 'force_stop_app':
            from Function_Moudle.app_threads import ForceStopAppThread
            return ForceStopAppThread
            
        elif thread_type == 'clear_app_cache':
            from Function_Moudle.app_threads import ClearAppCacheThread
            return ClearAppCacheThread
            
        elif thread_type == 'list_package':
            from Function_Moudle.app_threads import ListPackageThread
            return ListPackageThread
            
        elif thread_type == 'get_foreground_package':
            from Function_Moudle.app_threads import GetForegroundPackageThread
            return GetForegroundPackageThread
            
        elif thread_type == 'get_running_app_info':
            from Function_Moudle.app_threads import GetRunningAppInfoThread
            return GetRunningAppInfoThread
            
        elif thread_type == 'input_text':
            from Function_Moudle.app_threads import InputTextThread
            return InputTextThread
            
        elif thread_type == 'pull_files':
            from Function_Moudle.file_threads import PullFilesThread
            return PullFilesThread
            
        elif thread_type == 'pull_log':
            from Function_Moudle.file_threads import PullLogThread
            return PullLogThread
            
        elif thread_type == 'screenshot':
            from Function_Moudle.file_threads import ScreenshotThread
            return ScreenshotThread
            
        elif thread_type == 'check_update':
            from Function_Moudle.update_threads import CheckUpdateThread
            return CheckUpdateThread
            
        elif thread_type == 'download_update':
            from Function_Moudle.update_threads import DownloadUpdateThread
            return DownloadUpdateThread
            
        elif thread_type == 'vr_switch_env':
            from Function_Moudle.vr_threads import SwitchVREnvThread
            return SwitchVREnvThread
            
        elif thread_type == 'vr_check_network':
            from Function_Moudle.vr_threads import CheckVRNetworkThread
            return CheckVRNetworkThread
            
        elif thread_type == 'vr_activate':
            from Function_Moudle.vr_threads import ActivateVRThread
            return ActivateVRThread
            
        elif thread_type == 'vr_set_timeout':
            from Function_Moudle.vr_threads import SetVRTimeoutThread
            return SetVRTimeoutThread
            
        elif thread_type == 'vr_skip_power_limit':
            from Function_Moudle.vr_threads import SkipPowerLimitThread
            return SkipPowerLimitThread
            
        elif thread_type == 'datong_batch_install':
            from Function_Moudle.datong_threads import DatongBatchInstallThread
            return DatongBatchInstallThread
            
        elif thread_type == 'datong_batch_verify':
            from Function_Moudle.datong_threads import DatongBatchVerifyVersionThread
            return DatongBatchVerifyVersionThread
            
        elif thread_type == 'datong_input_password':
            from Function_Moudle.datong_threads import DatongInputPasswordThread
            return DatongInputPasswordThread
            
        elif thread_type == 'datong_set_datetime':
            from Function_Moudle.datong_threads import DatongSetDatetimeThread
            return DatongSetDatetimeThread
            
        elif thread_type == 'datong_open_telenav':
            from Function_Moudle.datong_threads import DatongOpenTelenavEngineeringThread
            return DatongOpenTelenavEngineeringThread
            
        else:
            raise ValueError(f"未知的线程类型: {thread_type}")
    
    def start_thread(self, thread):
        """启动线程"""
        if thread and not thread.isRunning():
            thread_id = id(thread)
            if thread_id in self.thread_registry:
                self.thread_registry[thread_id]['status'] = 'running'
            
            thread.start()
            self.logger.info(f"线程已启动: {thread.__class__.__name__} (ID: {thread_id})")
            
            return True
        return False
    
    def start_thread_from_pool(self, thread_id: str) -> bool:
        """启动线程池中的线程"""
        return self.thread_pool.start_thread(thread_id)
    
    def stop_thread(self, thread):
        """停止线程"""
        if thread and thread.isRunning():
            thread_id = id(thread)
            if thread_id in self.thread_registry:
                self.thread_registry[thread_id]['status'] = 'stopped'
            
            thread.stop()
            self.logger.info(f"线程已停止: {thread.__class__.__name__} (ID: {thread_id})")
            
            return True
        return False
    
    def stop_thread_from_pool(self, thread_id: str) -> bool:
        """停止线程池中的线程"""
        return self.thread_pool.cancel_thread(thread_id)
    
    def cancel_operation(self, operation_id: str) -> bool:
        """取消队列中的操作"""
        return self.operation_queue.cancel_operation(operation_id)
    
    def get_thread_status(self, thread):
        """获取线程状态"""
        if thread:
            thread_id = id(thread)
            if thread_id in self.thread_registry:
                return self.thread_registry[thread_id]['status']
        return 'unknown'
    
    def get_pool_thread_status(self, thread_id: str):
        """获取线程池中的线程状态"""
        return self.thread_pool.get_thread_status(thread_id)
    
    def get_operation_status(self, operation_id: str):
        """获取操作状态"""
        return self.operation_queue.get_operation_status(operation_id)
    
    def cleanup_thread(self, thread):
        """清理线程资源"""
        if thread:
            thread_id = id(thread)
            if thread_id in self.thread_registry:
                del self.thread_registry[thread_id]
                self.logger.info(f"线程资源已清理: {thread.__class__.__name__} (ID: {thread_id})")
    
    def cleanup_pool_threads(self):
        """清理线程池中已完成的线程"""
        self.thread_pool.clear_completed_threads()
    
    def cleanup_completed_operations(self):
        """清理已完成的操作"""
        self.operation_queue.clear_completed_operations()
    
    def get_active_threads(self):
        """获取所有活动线程"""
        active_threads = []
        
        # 获取注册表中的活动线程
        for thread_info in self.thread_registry.values():
            thread = thread_info['thread']
            if thread.isRunning():
                active_threads.append({
                    'thread': thread,
                    'type': thread_info['type'],
                    'status': 'running'
                })
        
        # 获取线程池中的活动线程状态
        pool_status = self.thread_pool.get_pool_status()
        
        return {
            'registry_threads': active_threads,
            'pool_status': pool_status,
            'queue_status': self.operation_queue.get_queue_status()
        }
    
    def shutdown(self):
        """关闭线程工厂，停止所有线程和队列"""
        self.logger.info("开始关闭线程工厂...")
        
        # 关闭操作队列
        self.logger.info("关闭操作队列管理器...")
        self.operation_queue.shutdown()
        
        # 关闭线程池
        self.logger.info("关闭线程池管理器...")
        self.thread_pool.shutdown()
        
        # 停止所有运行中的线程
        for thread_info in list(self.thread_registry.values()):
            thread = thread_info['thread']
            if thread.isRunning():
                self.stop_thread(thread)
        
        # 清空注册表
        self.thread_registry.clear()
        self.logger.info("线程工厂已关闭")


# 全局线程工厂实例
thread_factory = ThreadFactory()
