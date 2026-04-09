from PyQt5.QtCore import pyqtSignal
from .base_thread import BaseThread, DeviceBaseThread, FileBaseThread
from logger_manager import log_operation, log_file_operation, measure_performance
import os
import time


class PullFilesThread(DeviceBaseThread):
    """拉取文件线程"""
    
    file_signal = pyqtSignal(str)  # 发送文件路径
    
    def __init__(self, device_id, device_files_path, local_files_path, d=None):
        super().__init__(device_id, "PullFilesThread")
        self.device_files_path = device_files_path
        self.local_files_path = local_files_path
        self.d = d  # U2设备对象
        
    def _run_implementation(self):
        """执行文件拉取操作"""
        self.progress_signal.emit(f"开始拉取文件: {self.device_files_path}")
        
        try:
            if self.d:
                # 使用U2模式拉取
                self.d.pull(self.device_files_path, self.local_files_path)
                self.progress_signal.emit(f"文件已保存到: {self.local_files_path}")
                self.file_signal.emit(self.local_files_path)
                self.success_signal.emit("文件拉取成功")
            else:
                # 使用ADB模式拉取
                from adb_utils import ADBUtils
                
                result = ADBUtils.run_adb_command(
                    command=f"pull {self.device_files_path} {self.local_files_path}",
                    device_id=self.device_id,
                    timeout=60
                )
                
                if result.returncode == 0:
                    self.progress_signal.emit(f"文件已保存到: {self.local_files_path}")
                    self.file_signal.emit(self.local_files_path)
                    self.success_signal.emit("文件拉取成功")
                else:
                    self.error_signal.emit(f"文件拉取失败: {result.stderr}")
                    
        except Exception as e:
            self.error_signal.emit(f"拉取文件时发生错误: {str(e)}")


class PullLogThread(DeviceBaseThread):
    """拉取日志线程"""
    
    log_path_signal = pyqtSignal(str)
    
    def __init__(self, device_id, log_save_path):
        super().__init__(device_id, "PullLogThread")
        self.log_save_path = log_save_path
        
    def _run_implementation(self):
        """执行日志拉取操作"""
        self.progress_signal.emit("开始拉取日志文件...")
        
        try:
            from adb_utils import ADBUtils
            
            # 创建日志目录
            if not os.path.exists(self.log_save_path):
                os.makedirs(self.log_save_path, exist_ok=True)
                
            # 定义要拉取的日志文件
            log_files = [
                "/sdcard/logcat.log",
                "/sdcard/main_log.txt",
                "/sdcard/console.txt"
            ]
            
            success_count = 0
            for log_file in log_files:
                local_path = os.path.join(self.log_save_path, os.path.basename(log_file))
                
                result = ADBUtils.run_adb_command(
                    command=f"pull {log_file} {local_path}",
                    device_id=self.device_id,
                    timeout=30
                )
                
                if result.returncode == 0:
                    success_count += 1
                    self.progress_signal.emit(f"已拉取: {os.path.basename(log_file)}")
                else:
                    self.progress_signal.emit(f"跳过不存在的日志: {os.path.basename(log_file)}")
            
            if success_count > 0:
                self.progress_signal.emit(f"共拉取 {success_count} 个日志文件")
                self.log_path_signal.emit(self.log_save_path)
                self.success_signal.emit("日志拉取成功")
            else:
                self.error_signal.emit("未找到可拉取的日志文件")
                
        except Exception as e:
            self.error_signal.emit(f"拉取日志时发生错误: {str(e)}")


class ScreenshotThread(DeviceBaseThread):
    """截图线程"""
    
    screenshot_path_signal = pyqtSignal(str)
    
    def __init__(self, device_id, save_path):
        super().__init__(device_id, "ScreenshotThread")
        self.save_path = save_path
        
    def _run_implementation(self):
        """执行截图操作"""
        self.progress_signal.emit("正在截取屏幕...")
        
        try:
            from adb_utils import ADBUtils
            
            # 生成截图文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            screenshot_name = f"screenshot_{timestamp}.png"
            full_path = os.path.join(self.save_path, screenshot_name)
            
            # 先保存到设备
            device_path = "/sdcard/screenshot.png"
            result1 = ADBUtils.run_adb_command(
                command=f"shell screencap -p {device_path}",
                device_id=self.device_id,
                timeout=10
            )
            
            if result1.returncode != 0:
                self.error_signal.emit(f"截图失败: {result1.stderr}")
                return
                
            # 拉取到本地
            result2 = ADBUtils.run_adb_command(
                command=f"pull {device_path} {full_path}",
                device_id=self.device_id,
                timeout=10
            )
            
            if result2.returncode != 0:
                self.error_signal.emit(f"拉取截图失败: {result2.stderr}")
                return
                
            # 删除设备上的临时文件
            ADBUtils.run_adb_command(
                command=f"shell rm {device_path}",
                device_id=self.device_id
            )
            
            self.progress_signal.emit(f"截图已保存到: {full_path}")
            self.screenshot_path_signal.emit(full_path)
            self.success_signal.emit("截图成功")
            
        except Exception as e:
            self.error_signal.emit(f"截图时发生错误: {str(e)}")


class BrowseLogSavePathThread(BaseThread):
    """浏览日志保存路径线程"""
    
    path_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__("BrowseLogSavePathThread")
        
    def _run_implementation(self):
        """执行浏览日志保存路径操作"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            
            # 在主线程中执行文件对话框
            from PyQt5.QtCore import QObject, pyqtSignal
            
            class PathEmitter(QObject):
                path_selected = pyqtSignal(str)
                
            emitter = PathEmitter()
            
            def select_path():
                path = QFileDialog.getExistingDirectory(None, "选择日志保存目录", "")
                emitter.path_selected.emit(path)
                
            # 延迟执行文件对话框
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, select_path)
            
            # 等待路径选择
            import threading
            path = [None]
            
            def on_path_selected(selected_path):
                path[0] = selected_path
                
            emitter.path_selected.connect(on_path_selected)
            
            # 等待选择完成
            timeout = 30  # 30秒超时
            start_time = time.time()
            
            while path[0] is None and time.time() - start_time < timeout:
                time.sleep(0.1)
                
            if path[0]:
                self.progress_signal.emit(f"已选择日志保存路径: {path[0]}")
                self.path_signal.emit(path[0])
            else:
                self.progress_signal.emit("未选择日志保存路径")
                self.path_signal.emit("")
                
        except Exception as e:
            self.error_signal.emit(f"浏览日志保存路径时发生错误: {str(e)}")
            self.path_signal.emit("")
