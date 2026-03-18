#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""设备管理器 - 处理设备连接、刷新、模式切换等功能"""

import uiautomator2 as u2
from PyQt5.QtCore import Qt
from logger_manager import (
    get_logger, log_operation, log_exception,
    log_button_click, log_method_result, log_device_operation,
    log_thread_start, log_thread_complete
)

logger = get_logger("ADBTools.DeviceManager")


class DeviceManager:
    """设备管理器 - 处理设备连接、刷新、模式切换等功能"""
    
    def __init__(self, main_window):
        """
        初始化设备管理器
        
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
    
    def on_mode_switch_changed(self, state):
        """模式切换开关变化时的处理"""
        if state == Qt.Checked:
            # 切换到U2模式
            self.main_window.connection_mode = 'u2'
            self.main_window.textBrowser.append("切换到U2模式")
            log_device_operation("mode_switch", "U2", {"mode": "u2", "action": "切换到U2模式"})
        else:
            # 切换到ADB模式
            self.main_window.connection_mode = 'adb'
            self.main_window.textBrowser.append("切换到ADB模式")
            log_device_operation("mode_switch", "ADB", {"mode": "adb", "action": "切换到ADB模式"})
        
        # 如果有已连接的设备，重新连接以应用新模式
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        if device_id in devices_id_lst and self.main_window.d is not None:
            # 重新连接设备以应用新模式
            self._reconnect_device_with_new_mode(device_id)
    
    def _reconnect_device_with_new_mode(self, device_id):
        """使用新模式重新连接设备"""
        try:
            if self.main_window.connection_mode == 'u2':
                # 尝试u2连接
                self.main_window.d = u2.connect(device_id)
                self.main_window.textBrowser.append(f"U2模式重新连接设备: {device_id}")
                log_device_operation("reconnect_u2", device_id, {"mode": "u2", "status": "success"})
            else:
                # ADB模式，清理u2连接
                self._cleanup_u2_connection()
                self.main_window.textBrowser.append(f"切换到ADB模式，设备: {device_id}")
                log_device_operation("reconnect_adb", device_id, {"mode": "adb", "status": "success"})
        except Exception as e:
            self.main_window.textBrowser.append(f"重新连接设备失败: {e}")
            log_device_operation("reconnect_failed", device_id, {"mode": self.main_window.connection_mode, "error": str(e)})
    
    def on_combobox_changed(self, text):
        """设备选择下拉框变化时立即更新连接"""
        log_button_click("ComboxButton", "切换设备连接", f"目标设备: {text}")
        
        try:
            # 如果选择的设备与当前连接的设备不同，或者没有连接，则重新连接
            if not self.main_window.d or text != self.main_window.device_id:
                # 设备ID改变，先清理旧连接
                if self.main_window.d and text != self.main_window.device_id:
                    self._cleanup_u2_connection()
                
                # 使用当前选择的模式进行连接
                if self.main_window.modeSwitchCheckBox.isChecked():
                    # U2模式
                    log_device_operation("u2_connect_attempt", text, {"mode": "u2", "reason": "设备切换"})
                    self.main_window.d = u2.connect(text)
                    if self.main_window.d:
                        self.main_window.connection_mode = 'u2'
                        self.main_window.device_id = text
                        self.main_window.textBrowser.append(f"U2连接成功：{text}")
                        log_device_operation("u2_connect_success", text, {"mode": "u2", "status": "connected"})
                    else:
                        raise Exception("u2连接返回空对象")
                else:
                    # ADB模式
                    self._cleanup_u2_connection()
                    self.main_window.connection_mode = 'adb'
                    self.main_window.device_id = text
                    self.main_window.textBrowser.append(f"切换到ADB模式：{text}")
                    log_device_operation("switch_to_adb", text, {"mode": "adb", "status": "connected"})
            else:
                # 已经连接到该设备，确认连接状态
                mode_text = "U2" if self.main_window.connection_mode == 'u2' else "ADB"
                self.main_window.textBrowser.append(f"已连接到设备（{mode_text}模式）：{text}")
                log_device_operation("device_already_connected", text, {"mode": self.main_window.connection_mode, "status": "already_connected"})
        except Exception as connect_error:
            # 连接失败，根据当前模式处理
            if self.main_window.modeSwitchCheckBox.isChecked():
                # U2模式失败，尝试切换到ADB模式
                self._cleanup_u2_connection()
                self.main_window.connection_mode = 'adb'
                self.main_window.device_id = text
                self.main_window.textBrowser.append(f"U2连接失败，切换到ADB模式：{text}")
                self.main_window.textBrowser.append(f"错误信息：{connect_error}")
                log_device_operation("u2_fallback_to_adb", text, {"mode": "adb", "reason": str(connect_error)})
            else:
                # ADB模式，显示错误信息
                self.main_window.textBrowser.append(f"ADB模式连接失败：{text}")
                self.main_window.textBrowser.append(f"错误信息：{connect_error}")
                log_device_operation("adb_connect_failed", text, {"mode": "adb", "error": str(connect_error)})
    
    def _cleanup_u2_connection(self):
        """清理旧的u2连接"""
        if self.main_window.d is not None:
            try:
                logger.info(f"清理旧的u2连接: {self.main_window.device_id}")
                self.main_window.d = None
                logger.info("旧连接已清理")
            except Exception as e:
                logger.warning(f"清理u2连接时出错: {e}")
                self.main_window.d = None
    
    def disconnect_device(self):
        """断开当前设备连接"""
        log_button_click("DisconnectButton", "断开设备连接")
        
        device_id = self.main_window.device_id
        connection_mode = self.main_window.connection_mode
        
        if not device_id:
            self.main_window.textBrowser.append("当前没有连接的设备")
            log_device_operation("disconnect_device", "无设备", {"status": "no_device"})
            return
        
        try:
            # 显示当前连接信息
            mode_text = "U2" if connection_mode == 'u2' else "ADB"
            
            # 如果是 U2 模式，清理 u2 连接
            if connection_mode == 'u2' and self.main_window.d is not None:
                self._cleanup_u2_connection()
                self.main_window.textBrowser.append(f"已断开 U2 连接: {device_id}")
            else:
                # ADB 模式，只需清理状态
                self.main_window.textBrowser.append(f"已断开 ADB 连接: {device_id}")
            
            # 重置连接状态
            self.main_window.d = None
            self.main_window.device_id = None
            self.main_window.connection_mode = None
            
            log_device_operation("disconnect_device", device_id, {
                "mode": connection_mode,
                "status": "success"
            })
            
            log_method_result("disconnect_device", True, f"已断开 {mode_text} 连接: {device_id}")
            
        except Exception as e:
            error_msg = f"断开设备连接失败: {e}"
            self.main_window.textBrowser.append(error_msg)
            log_device_operation("disconnect_device", device_id, {
                "mode": connection_mode,
                "status": "error",
                "error": str(e)
            })
            log_method_result("disconnect_device", False, str(e))
    
    def refresh_devices(self):
        """刷新设备列表（多线程执行，避免阻塞主界面）"""
        log_button_click("RefreshButton", "刷新设备列表")
        
        # 检查是否已经有刷新线程在运行
        if hasattr(self.main_window, 'refresh_devices_thread') and self.main_window.refresh_devices_thread.isRunning():
            logger.warning("刷新设备列表线程已在运行中")
            self.main_window.textBrowser.append("刷新正在进行中，请稍候...")
            return
        
        # 使用线程刷新设备列表
        try:
            from Function_Moudle.refresh_devices_thread import RefreshDevicesThread
            self.main_window.refresh_devices_thread = RefreshDevicesThread()
            
            # 连接信号
            self.main_window.refresh_devices_thread.progress_signal.connect(self.main_window.textBrowser.append)
            self.main_window.refresh_devices_thread.devices_signal.connect(self._handle_refreshed_devices)
            self.main_window.refresh_devices_thread.error_signal.connect(self.main_window.textBrowser.append)
            
            # 启动线程
            self.main_window.refresh_devices_thread.start()
            log_thread_start("RefreshDevicesThread", {"action": "刷新设备列表"})
            
        except Exception as e:
            logger.error(f"启动刷新线程失败: {e}")
            log_exception(logger, "refresh_devices", e)
            self.main_window.textBrowser.append(f"启动刷新线程失败: {e}")
    
    def _on_refresh_thread_finished(self):
        """刷新线程完成后的清理工作"""
        logger.info("设备列表刷新完成")
    
    def _connect_device_with_current_mode(self, device_id):
        """使用当前选择的模式连接设备"""
        if not device_id:
            return
            
        # 清理旧连接
        if self.main_window.d:
            self._cleanup_u2_connection()
        
        # 使用当前选择的模式连接
        if self.main_window.modeSwitchCheckBox.isChecked():
            # U2模式
            self.main_window.connection_mode = 'u2'
            self.main_window.device_id = device_id
            # 在单独的线程中尝试u2连接，避免阻塞主界面
            self._try_u2_connection_in_thread(device_id)
        else:
            # ADB模式
            self.main_window.connection_mode = 'adb'
            self.main_window.device_id = device_id
            self.main_window.textBrowser.append(f"使用ADB模式连接设备: {device_id}")
            log_device_operation("connect_adb", device_id, {"mode": "adb", "status": "connected"})
    
    def _handle_refreshed_devices(self, device_ids):
        """处理刷新后的设备列表（在主线程中执行）"""
        # 清空 ComboxButton 并添加新的设备ID
        self.main_window.ComboxButton.clear()
        for device_id in device_ids:
            self.main_window.ComboxButton.addItem(device_id)
        
        if device_ids:
            # 只在有设备时尝试连接
            device_id = self.get_selected_device()
            if device_id and device_id != "请点击刷新设备":
                # 检查设备ID是否改变，或者没有连接，则重新连接
                if not self.main_window.d or device_id != self.main_window.device_id:
                    # 设备ID改变了，需要清理旧连接并重新连接
                    self._connect_device_with_current_mode(device_id)
                else:
                    mode_text = "U2" if self.main_window.connection_mode == 'u2' else "ADB"
                    self.main_window.textBrowser.append(f"已使用{mode_text}模式连接到设备: {device_id}")
        # 无设备时不重复输出，由线程输出
    
    def _try_u2_connection_in_thread(self, device_id):
        """在单独的线程中尝试u2连接"""
        log_device_operation("u2_connect_attempt", device_id, {"mode": "u2", "action": "尝试u2连接"})
        
        # 设置正在连接标志
        self.main_window.u2_connecting = True
        
        try:
            from Function_Moudle.u2_connect_thread import U2ConnectThread
            self.main_window.u2_connect_thread = U2ConnectThread(device_id)
            
            # 连接信号
            self.main_window.u2_connect_thread.progress_signal.connect(self.main_window.textBrowser.append)
            self.main_window.u2_connect_thread.error_signal.connect(self.main_window.textBrowser.append)
            self.main_window.u2_connect_thread.connected_signal.connect(self._handle_u2_connection_result)
            
            # 启动线程
            self.main_window.u2_connect_thread.start()
            log_thread_start("U2ConnectThread", {"device_id": device_id, "mode": "u2"})
            
        except Exception as e:
            logger.error(f"启动u2连接线程失败: {e}")
            self.main_window.textBrowser.append(f"启动u2连接线程失败: {e}")
            # 回退到ADB模式
            self.main_window.d = None
            self.main_window.connection_mode = 'adb'
            self.main_window.u2_connecting = False  # 清除连接标志
            log_device_operation("fallback_to_adb", device_id, {"reason": "u2连接失败", "mode": "adb"})
            self.main_window.textBrowser.append(f"切换到ADB模式: {device_id}")
    
    def _handle_u2_connection_result(self, u2_device, device_id):
        """处理u2连接结果"""
        # 清除正在连接标志
        self.main_window.u2_connecting = False
        
        if u2_device:
            # u2连接成功
            self.main_window.d = u2_device
            self.main_window.connection_mode = 'u2'
            self.main_window.device_id = device_id
            self.main_window.textBrowser.append(f"U2连接成功: {device_id}")
            log_device_operation("u2_connect_success", device_id, {"mode": "u2", "status": "connected"})
            log_thread_complete("U2ConnectThread", "success", {"device_id": device_id, "mode": "u2"})
        else:
            # u2连接失败，降级到ADB模式
            self.main_window.d = None
            self.main_window.connection_mode = 'adb'
            self.main_window.device_id = device_id
            self.main_window.textBrowser.append(f"U2连接失败，使用ADB模式: {device_id}")
            log_device_operation("u2_connect_failed", device_id, {"mode": "adb", "reason": "u2连接失败"})
            log_thread_complete("U2ConnectThread", "failed", {"device_id": device_id, "fallback_mode": "adb"})
    
    def reboot_device(self):
        """重启设备"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("button_reboot", "重启设备")

        if device_id in devices_id_lst:
            from PyQt5.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self.main_window,
                '确认重启',
                '确定要重启设备吗？此操作不可逆！',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                try:
                    from Function_Moudle.reboot_device_thread import RebootDeviceThread
                    self.main_window.reboot_thread = RebootDeviceThread(device_id)
                    self.main_window.reboot_thread.progress_signal.connect(self.main_window.textBrowser.append)
                    self.main_window.reboot_thread.error_signal.connect(self.main_window.textBrowser.append)
                    self.main_window.reboot_thread.start()
                    log_method_result("reboot_device", True, "重启线程已启动")
                except Exception as e:
                    log_method_result("reboot_device", False, str(e))
                    self.main_window.textBrowser.append(f"启动设备重启线程失败: {e}")
            else:
                logger.info("用户取消重启操作")
        else:
            log_method_result("reboot_device", False, "设备未连接")
            self.main_window.textBrowser.append("设备未连接！")
    
    def reinit_uiautomator2(self):
        """重新初始化uiautomator2服务"""
        log_button_click("reinit_u2_button", "重新初始化uiautomator2")
        
        # 获取当前选择的设备
        device_id = self.get_selected_device()
        
        if not device_id:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self.main_window, "未选择设备", "请先选择一个设备！")
            return
        
        # 确认对话框
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self.main_window,
            '确认重新初始化',
            f'是否要重新初始化设备 {device_id} 的 uiautomator2 服务？\n\n'
            '此操作将会：\n'
            '1. 断开现有的u2连接\n'
            '2. 停止uiautomator2服务\n'
            '3. 清理相关进程\n'
            '4. 重新安装和初始化uiautomator2\n\n'
            '注意：此过程可能需要1-2分钟，请勿关闭程序。',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            self.main_window.textBrowser.append("用户取消重新初始化操作")
            return
        
        try:
            # 创建进度对话框
            from Function_Moudle.u2_reinit_dialog import U2ReinitDialog
            self.main_window.u2_reinit_dialog = U2ReinitDialog(self.main_window)
            
            # 创建重新初始化线程
            from Function_Moudle.u2_reinit_thread import U2ReinitThread
            self.main_window.u2_reinit_thread = U2ReinitThread(device_id, self.main_window.d)
            
            # 连接信号
            self.main_window.u2_reinit_thread.progress_signal.connect(self.main_window.u2_reinit_dialog.add_progress)
            self.main_window.u2_reinit_thread.error_signal.connect(self.main_window.u2_reinit_dialog.set_error)
            self.main_window.u2_reinit_thread.success_signal.connect(self.main_window.u2_reinit_dialog.set_success)
            self.main_window.u2_reinit_thread.finished_signal.connect(self._on_u2_reinit_finished)
            
            # 同时也输出到主窗口的textBrowser
            self.main_window.u2_reinit_thread.progress_signal.connect(self.main_window.textBrowser.append)
            self.main_window.u2_reinit_thread.error_signal.connect(self.main_window.textBrowser.append)
            self.main_window.u2_reinit_thread.success_signal.connect(self.main_window.textBrowser.append)
            
            # 开始初始化
            self.main_window.u2_reinit_dialog.start()
            self.main_window.u2_reinit_thread.start()
            
            # 显示对话框
            self.main_window.u2_reinit_dialog.exec_()
            
        except ImportError as e:
            self.main_window.textBrowser.append(f"无法导入重新初始化模块: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self.main_window, "重新初始化失败", 
                f"无法启动重新初始化功能:\n\n{str(e)}")
        except Exception as e:
            self.main_window.textBrowser.append(f"启动重新初始化失败: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self.main_window, "重新初始化失败", 
                f"启动重新初始化时发生错误:\n\n{str(e)}")
    
    def _on_u2_reinit_finished(self):
        """u2重新初始化完成后的处理"""
        if self.main_window.u2_reinit_thread and self.main_window.u2_reinit_thread.isRunning():
            return
        
        # 重新连接设备
        try:
            self.main_window.textBrowser.append("正在重新连接设备...")
            
            # 延迟一下，确保u2服务完全启动
            import time
            time.sleep(1)
            
            # 重新刷新设备列表
            self.refresh_devices()
            
            self.main_window.textBrowser.append("✓ 设备重新连接成功")
            
        except Exception as e:
            self.main_window.textBrowser.append(f"重新连接设备时出错: {e}")
        
        # 清理
        if self.main_window.u2_reinit_thread:
            self.main_window.u2_reinit_thread.deleteLater()
            self.main_window.u2_reinit_thread = None
