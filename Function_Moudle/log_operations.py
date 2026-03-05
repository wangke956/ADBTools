#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""日志操作管理器 - 处理日志拉取、语音录制等功能"""

import os
from PyQt5.QtWidgets import QFileDialog
from logger_manager import (
    get_logger, log_operation, log_exception,
    log_button_click, log_method_result, log_device_operation
)

logger = get_logger("ADBTools.LogManager")


class LogManager:
    """日志操作管理器 - 处理日志拉取、语音录制等功能"""
    
    def __init__(self, main_window):
        """
        初始化日志管理器
        
        Args:
            main_window: 主窗口实例 (ADB_Mainwindow)
        """
        self.main_window = main_window
    
    def get_selected_device(self):
        """获取当前选中的设备ID"""
        return self.main_window.ComboxButton.currentText()
    
    def get_new_device_lst(self):
        """获取设备ID列表"""
        from adb_utils import adb_utils
        return adb_utils.get_device_list()
    
    def pull_log(self):
        """拉取设备日志"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        file_path = self.main_window.inputbox_log_path.text()
        
        log_button_click("pull_log_button", "拉取设备日志", f"保存路径: {file_path}")
        
        if device_id in devices_id_lst:
            try:
                if not file_path:
                    log_method_result("pull_log", False, "路径不能为空")
                    self.main_window.textBrowser.append("路径不能为空！")
                elif os.path.exists(file_path):
                    from Function_Moudle.pull_log_thread import PullLogThread
                    self.main_window.PullLogSaveThread = PullLogThread(file_path, device_id)
                    self.main_window.PullLogSaveThread.progress_signal.connect(self.main_window.textBrowser.append)
                    self.main_window.PullLogSaveThread.error_signal.connect(self.main_window.textBrowser.append)
                    self.main_window.PullLogSaveThread.start()
                    log_method_result("pull_log", True, "拉取日志线程已启动")
                else:
                    log_method_result("pull_log", False, "路径不存在")
                    self.main_window.textBrowser.append("路径不存在！")
            except Exception as e:
                log_method_result("pull_log", False, str(e))
                self.main_window.textBrowser.append(f"启动拉取日志线程失败: {e}")
        else:
            log_method_result("pull_log", False, "设备未连接")
            self.main_window.textBrowser.append("设备未连接！")
    
    def browse_log_save_path(self):
        """浏览日志保存路径"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("browse_log_save_path_button", "浏览日志保存路径")
        
        if device_id in devices_id_lst:
            if hasattr(self.main_window, 'PullLogSaveThread') and self.main_window.PullLogSaveThread and self.main_window.PullLogSaveThread.isRunning():
                self.main_window.PullLogSaveThread.stop()
                self.main_window.pull_log_button.setText("拉取日志")
                logger.info("停止拉取日志")
            else:
                file_path = QFileDialog.getExistingDirectory(self.main_window, "选择保存路径", "")
                if file_path:
                    self.main_window.inputbox_log_path.setText(file_path)
                    logger.info(f"选择路径: {file_path}")
                else:
                    logger.info("用户取消选择")
                    self.main_window.textBrowser.append("已取消！")
        else:
            log_method_result("browse_log_save_path", False, "设备未连接")
            self.main_window.textBrowser.append("未连接设备！")
    
    def open_path(self):
        """打开文件所在目录"""
        log_button_click("open_path_buttom", "打开文件所在目录")
        
        file_path = self.main_window.inputbox_log_path.text()
        
        try:
            if file_path:
                logger.info(f"打开路径: {file_path}")
                os.startfile(file_path)
                log_method_result("open_path", True, f"已打开: {file_path}")
            else:
                log_method_result("open_path", False, "路径不能为空")
                self.main_window.textBrowser.append("路径不能为空！")
        except Exception as e:
            log_method_result("open_path", False, str(e))
            self.main_window.textBrowser.append(f"路径不存在！: {e}")
    
    def voice_start_record(self):
        """开始语音录制"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("voice_start_record_button", "开始语音录制")

        if device_id in devices_id_lst:
            try:
                from Function_Moudle.voice_record_thread import VoiceRecordThread
                self.main_window.voice_record_thread = VoiceRecordThread(device_id)
                self.main_window.voice_record_thread.progress_signal.connect(self.main_window.textBrowser.append)
                self.main_window.voice_record_thread.record_signal.connect(self.main_window.textBrowser.append)
                self.main_window.voice_record_thread.start()
                
                log_method_result("voice_start_record", True, "录制线程已启动")
            except Exception as e:
                log_method_result("voice_start_record", False, str(e))
                self.main_window.textBrowser.append(f"启动语音录制线程失败: {e}")
        else:
            log_method_result("voice_start_record", False, "设备未连接")
            self.main_window.textBrowser.append("设备未连接！")
    
    def voice_stop_record(self):
        """停止语音录制"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("voice_stop_record_button", "停止语音录制")

        if device_id in devices_id_lst:
            try:
                from Function_Moudle.voice_stop_record_thread import VoiceStopRecordThread
                self.main_window.voice_record_thread = VoiceStopRecordThread(device_id)
                self.main_window.voice_record_thread.voice_stop_record_signal.connect(self.main_window.textBrowser.append)
                self.main_window.voice_record_thread.start()
                
                log_method_result("voice_stop_record", True, "停止录制线程已启动")
            except Exception as e:
                log_method_result("voice_stop_record", False, str(e))
                self.main_window.textBrowser.append(f"停止语音录制失败: {e}")
        else:
            log_method_result("voice_stop_record", False, "设备未连接")
            self.main_window.textBrowser.append("设备未连接！")
    
    def voice_pull_record_file(self):
        """拉取录音文件"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("voice_pull_record_file_button", "拉取录音文件")

        if device_id in devices_id_lst:
            try:
                from Function_Moudle.voice_pull_record_file_thread import VoicePullRecordFileThread
                self.main_window.voice_pull_record_file_thread = VoicePullRecordFileThread(device_id)
                self.main_window.voice_pull_record_file_thread.progress_signal.connect(self.main_window.textBrowser.append)
                self.main_window.voice_pull_record_file_thread.result_signal.connect(self.main_window.textBrowser.append)
                self.main_window.voice_pull_record_file_thread.start()
                
                log_method_result("voice_pull_record_file", True, "拉取线程已启动")
            except Exception as e:
                log_method_result("voice_pull_record_file", False, str(e))
                self.main_window.textBrowser.append(f"拉取录音文件失败: {e}")
        else:
            log_method_result("voice_pull_record_file", False, "设备未连接")
            self.main_window.textBrowser.append("设备未连接！")
    
    def remove_voice_record_file(self):
        """删除语音录制文件"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("remove_record_file_button", "删除语音录制文件")

        if device_id in devices_id_lst:
            try:
                from Function_Moudle.remove_record_file_thread import RemoveRecordFileThread
                self.main_window.remove_record_file_thread = RemoveRecordFileThread(device_id)
                self.main_window.remove_record_file_thread.progress_signal.connect(self.main_window.textBrowser.append)
                self.main_window.remove_record_file_thread.result_signal.connect(self.main_window.textBrowser.append)
                self.main_window.remove_record_file_thread.start()
                
                log_method_result("remove_voice_record_file", True, "删除线程已启动")
            except Exception as e:
                log_method_result("remove_voice_record_file", False, str(e))
                self.main_window.textBrowser.append(f"删除录音文件失败: {e}")
        else:
            log_method_result("remove_voice_record_file", False, "设备未连接")
            self.main_window.textBrowser.append("设备未连接！")
