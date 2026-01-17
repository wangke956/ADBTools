#!/usr/bin/env python3
"""
u2重新初始化线程 - 重新初始化设备的uiautomator2服务
"""

from PyQt5.QtCore import QThread, pyqtSignal
import uiautomator2 as u2
import time
from logger_manager import get_logger, log_thread_start, log_thread_complete

logger = get_logger("ADBTools.U2Reinit")


class U2ReinitThread(QThread):
    """重新初始化uiautomator2的线程"""
    
    # 定义信号
    progress_signal = pyqtSignal(str)  # 进度信号
    error_signal = pyqtSignal(str)  # 错误信号
    success_signal = pyqtSignal(str)  # 成功信号
    finished_signal = pyqtSignal()  # 完成信号
    
    def __init__(self, device_id, u2_device=None):
        """
        初始化u2重新初始化线程
        
        Args:
            device_id: 设备ID
            u2_device: 已连接的u2设备对象
        """
        super().__init__()
        self.device_id = device_id
        self.u2_device = u2_device
        self._is_running = True
        
        log_thread_start("U2ReinitThread", {
            "device_id": device_id,
            "action": "重新初始化uiautomator2"
        })
    
    def _capture_u2_logs(self, output):
        """
        捕获并处理uiautomator2的日志输出
        
        Args:
            output: u2的输出内容
        """
        if not output or not output.strip():
            return
        
        for line in output.split('\n'):
            if line.strip():
                # 发送到进度信号（显示在弹窗中）
                self.progress_signal.emit(f"  [U2] {line.strip()}")
                
                # 记录到日志文件
                line_lower = line.lower()
                if 'error' in line_lower or 'failed' in line_lower or 'exception' in line_lower:
                    logger.error(f"  [U2] {line.strip()}")
                elif 'warning' in line_lower or 'warn' in line_lower:
                    logger.warning(f"  [U2] {line.strip()}")
                elif 'info' in line_lower or 'uiautomator back to normal' in line_lower:
                    logger.info(f"  [U2] {line.strip()}")
                else:
                    logger.debug(f"  [U2] {line.strip()}")
    
    def run(self):
        """执行重新初始化"""
        try:
            logger.info("=" * 80)
            logger.info("开始重新初始化uiautomator2服务")
            logger.info("=" * 80)
            
            # 步骤1: 断开现有连接
            self.progress_signal.emit("步骤 1/5: 断开现有连接...")
            logger.info("步骤 1/5: 断开现有连接")
            time.sleep(0.5)
            
            if self.u2_device:
                try:
                    # 尝试断开连接
                    self.progress_signal.emit("  - 正在断开u2连接...")
                    logger.info("  - 正在断开u2连接")
                    time.sleep(1)
                except Exception as e:
                    logger.warning(f"  - 断开连接时出现警告: {e}")
            
            # 步骤2: 停止uiautomator2服务
            self.progress_signal.emit("步骤 2/5: 停止uiautomator2服务...")
            logger.info("步骤 2/5: 停止uiautomator2服务")
            
            try:
                import subprocess
                adb_path = self._get_adb_path()
                
                # 停止uiautomator2服务
                cmd = f'"{adb_path}" -s {self.device_id} shell am force-stop com.github.uiautomator'
                self.progress_signal.emit(f"  - 执行命令: {cmd}")
                logger.info(f"  - 执行命令: {cmd}")
                
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                time.sleep(1)
                
                self.progress_signal.emit("  - ✓ uiautomator2服务已停止")
                logger.info("  - ✓ uiautomator2服务已停止")
            except Exception as e:
                logger.warning(f"  - 停止服务时出现警告: {e}")
                self.progress_signal.emit(f"  - ⚠ 停止服务时出现警告: {e}")
            
            # 步骤3: 清理uiautomator2相关进程
            self.progress_signal.emit("步骤 3/5: 清理uiautomator2相关进程...")
            logger.info("步骤 3/5: 清理uiautomator2相关进程")
            
            try:
                import subprocess
                adb_path = self._get_adb_path()
                
                # 清理进程
                cmd = f'"{adb_path}" -s {self.device_id} shell "ps | grep uiautomator"'
                self.progress_signal.emit(f"  - 查找uiautomator2进程...")
                logger.info(f"  - 查找uiautomator2进程")
                
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                time.sleep(0.5)
                
                if result.stdout.strip():
                    self.progress_signal.emit("  - 发现uiautomator2进程，正在清理...")
                    logger.info("  - 发现uiautomator2进程，正在清理")
                    time.sleep(1)
                
                self.progress_signal.emit("  - ✓ 进程清理完成")
                logger.info("  - ✓ 进程清理完成")
            except Exception as e:
                logger.warning(f"  - 清理进程时出现警告: {e}")
                self.progress_signal.emit(f"  - ⚠ 清理进程时出现警告: {e}")
            
            # 步骤4: 重新初始化uiautomator2
            self.progress_signal.emit("步骤 4/5: 重新初始化uiautomator2...")
            logger.info("步骤 4/5: 重新初始化uiautomator2")
            
            try:
                # 连接设备
                self.progress_signal.emit(f"  - 正在连接设备 {self.device_id}...")
                logger.info(f"  - 正在连接设备 {self.device_id}")
                
                # 添加自定义的logging handler来捕获u2的日志
                import logging
                from queue import Queue
                import threading
                
                # 创建一个队列来接收日志
                log_queue = Queue()
                
                # 创建自定义的handler
                class QueueHandler(logging.Handler):
                    def __init__(self, queue):
                        super().__init__()
                        self.queue = queue
                    
                    def emit(self, record):
                        # 将日志记录放入队列
                        self.queue.put(record)
                
                # 获取u2的logger
                u2_logger = logging.getLogger('uiautomator2')
                u2_logger.setLevel(logging.DEBUG)
                
                # 添加handler
                queue_handler = QueueHandler(log_queue)
                queue_handler.setLevel(logging.DEBUG)
                u2_logger.addHandler(queue_handler)
                
                # 启动一个线程来处理日志队列
                def process_logs():
                    while True:
                        try:
                            record = log_queue.get(timeout=0.1)
                            # 格式化日志消息
                            log_msg = record.getMessage()
                            # 发送到进度信号
                            self.progress_signal.emit(f"  [U2] {log_msg}")
                            # 记录到我们的日志文件
                            if record.levelno >= logging.ERROR:
                                logger.error(f"  [U2] {log_msg}")
                            elif record.levelno >= logging.WARNING:
                                logger.warning(f"  [U2] {log_msg}")
                            elif record.levelno >= logging.INFO:
                                logger.info(f"  [U2] {log_msg}")
                            else:
                                logger.debug(f"  [U2] {log_msg}")
                        except:
                            break
                
                log_thread = threading.Thread(target=process_logs, daemon=True)
                log_thread.start()
                
                # 连接设备并初始化
                d = u2.connect(self.device_id)
                time.sleep(1)
                
                # 安装/更新uiautomator2
                self.progress_signal.emit("  - 正在安装/更新uiautomator2服务...")
                logger.info("  - 正在安装/更新uiautomator2服务")
                
                try:
                    # 尝试获取设备信息，这会触发u2服务初始化
                    device_info = d.info
                    self.progress_signal.emit("  - 设备连接成功，uiautomator2已就绪")
                except:
                    # 如果获取设备信息失败，尝试手动安装
                    self.progress_signal.emit("  - 正在安装uiautomator2 APK...")
                    d.service("uiautomator").stop()
                    time.sleep(0.5)
                    d.service("uiautomator").start()
                    time.sleep(2)
                    # 再次获取设备信息
                    device_info = d.info
                
                # 等待日志处理完成
                time.sleep(1)
                
                # 移除handler
                u2_logger.removeHandler(queue_handler)
                
                time.sleep(1)
                
                self.progress_signal.emit("  - ✓ uiautomator2初始化成功")
                logger.info("  - ✓ uiautomator2初始化成功")
                logger.info(f"  - 设备信息: {device_info}")
                
            except Exception as e:
                error_msg = f"初始化uiautomator2失败: {str(e)}"
                logger.error(error_msg)
                self.error_signal.emit(error_msg)
                log_thread_complete("U2ReinitThread", "failed", {"error": str(e)})
                return
            
            # 步骤5: 验证连接
            self.progress_signal.emit("步骤 5/5: 验证连接...")
            logger.info("步骤 5/5: 验证连接")
            
            try:
                # 获取当前包名来验证连接
                current_package = d.app_current()['package']
                self.progress_signal.emit(f"  - ✓ 连接验证成功，当前应用: {current_package}")
                logger.info(f"  - ✓ 连接验证成功，当前应用: {current_package}")
                
                # 发送成功信号
                success_msg = f"uiautomator2重新初始化成功！\n设备: {self.device_id}\n当前应用: {current_package}"
                self.success_signal.emit(success_msg)
                
            except Exception as e:
                error_msg = f"验证连接失败: {str(e)}"
                logger.error(error_msg)
                self.error_signal.emit(error_msg)
                log_thread_complete("U2ReinitThread", "failed", {"error": str(e)})
                return
            
            logger.info("=" * 80)
            logger.info("uiautomator2重新初始化完成")
            logger.info("=" * 80)
            
            log_thread_complete("U2ReinitThread", "success", {
                "device_id": self.device_id
            })
            
        except Exception as e:
            error_msg = f"重新初始化过程中发生异常: {str(e)}"
            logger.error(error_msg)
            self.error_signal.emit(error_msg)
            log_thread_complete("U2ReinitThread", "failed", {"error": str(e)})
        finally:
            self.finished_signal.emit()
    
    def _get_adb_path(self):
        """获取ADB路径"""
        try:
            from adb_utils import adb_utils
            return adb_utils.get_adb_path()
        except:
            return "adb"
    
    def stop(self):
        """停止线程"""
        self._is_running = False
        self.terminate()