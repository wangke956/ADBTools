# -*- coding: utf-8 -*-
"""
输入操作管理器
负责点击、长按、文本输入等模拟操作
"""

import os
from PyQt5.QtWidgets import QInputDialog, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout

from logger_manager import log_button_click, log_method_result


class InputOperationsManager:
    """输入操作管理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window
    
    @property
    def textBrowser(self):
        return self.main_window.textBrowser
    
    def show_simulate_long_press_dialog(self):
        """显示模拟长按对话框"""
        device_id = self.main_window.get_selected_device()
        devices_id_lst = self.main_window.get_new_device_lst()
        
        log_button_click("simulate_long_press_button", "模拟长按")

        if device_id in devices_id_lst:
            try:
                from Function_Moudle.simulate_long_press_dialog_thread import SimulateLongPressDialogThread
                self.main_window.simulate_long_press_thread = SimulateLongPressDialogThread(
                    self.main_window, device_id
                )
                self.main_window.simulate_long_press_thread.result_signal.connect(self.textBrowser.append)
                self.main_window.simulate_long_press_thread.error_signal.connect(self.textBrowser.append)
                self.main_window.simulate_long_press_thread.start()
                
                log_method_result("show_simulate_long_press_dialog", True, "长按模拟线程已启动")
            except Exception as e:
                log_method_result("show_simulate_long_press_dialog", False, str(e))
                self.textBrowser.append(f"启动长按模拟线程失败: {e}")
        else:
            log_method_result("show_simulate_long_press_dialog", False, "设备未连接")
            self.textBrowser.append("设备未连接！")
    
    def show_input_text_dialog(self):
        """显示输入文本对话框"""
        device_id = self.main_window.get_selected_device()
        devices_id_lst = self.main_window.get_new_device_lst()
        
        log_button_click("input_text_button", "输入文本")

        if device_id in devices_id_lst:
            text, ok = QInputDialog.getText(self.main_window, "输入文本", "请输入要发送的文本：")
            if ok and text:
                self.main_window.logger.info(f"输入文本: {text}")
                
                try:
                    if self.main_window.connection_mode == 'u2' and self.main_window.d:
                        # 使用u2输入
                        self.main_window.d.send_keys(text)
                        self.textBrowser.append(f"已输入文本: {text}")
                        log_method_result("show_input_text_dialog", True, f"已输入: {text}")
                    elif self.main_window.connection_mode == 'adb':
                        # 使用ADB输入
                        from Function_Moudle.adb_input_text_thread import ADBInputTextThread
                        self.main_window.input_text_thread = ADBInputTextThread(device_id, text)
                        self.main_window.input_text_thread.progress_signal.connect(self.textBrowser.append)
                        self.main_window.input_text_thread.error_signal.connect(self.textBrowser.append)
                        self.main_window.input_text_thread.start()
                        
                        log_method_result("show_input_text_dialog", True, f"输入线程已启动: {text[:20]}...")
                    else:
                        log_method_result("show_input_text_dialog", False, "设备未连接")
                        self.textBrowser.append("设备未连接！")
                except Exception as e:
                    log_method_result("show_input_text_dialog", False, str(e))
                    self.textBrowser.append(f"输入文本失败: {e}")
            else:
                self.main_window.logger.info("用户取消输入或输入为空")
        else:
            log_method_result("show_input_text_dialog", False, "设备未连接")
            self.textBrowser.append("设备未连接！")
