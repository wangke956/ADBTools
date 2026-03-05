#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大通专用功能管理器

从 ADB_module.py 中拆分出的专用功能模块
"""

from logger_manager import (
    get_logger, log_button_click, log_method_result
)

# 创建日志记录器
logger = get_logger("ADBTools.DatongManager")


class DatongManager:
    """大通专用功能管理器
    
    处理大通车型的特定功能：
    - Verity 校验管理
    - 批量安装 APK
    - 密码输入
    - 工程模式
    - 日期时间设置
    """
    
    def __init__(self, main_window):
        """
        初始化大通管理器
        
        Args:
            main_window: 主窗口实例，用于获取设备和UI控件
        """
        self.main_window = main_window
    
    # ========== 设备和连接信息 ==========
    
    def _get_selected_device(self):
        """获取当前选中的设备ID"""
        return self.main_window.get_selected_device()
    
    def _get_device_list(self):
        """获取设备列表"""
        return self.main_window.get_new_device_lst()
    
    def _get_connection_mode(self):
        """获取当前连接模式"""
        return self.main_window.connection_mode
    
    def _get_u2_device(self):
        """获取U2设备对象"""
        return self.main_window.d
    
    def _is_device_connected(self):
        """检查设备是否已连接"""
        device_id = self._get_selected_device()
        devices = self._get_device_list()
        return device_id in devices
    
    def _append_output(self, text):
        """输出文本到主窗口"""
        self.main_window.textBrowser.append(text)
    
    def _connect_thread_signals(self, thread, extra_result_handler=None):
        """连接线程的通用信号"""
        thread.progress_signal.connect(self._append_output)
        thread.error_signal.connect(self._append_output)
        thread.result_signal.connect(self._append_output)
        if extra_result_handler:
            thread.result_signal.connect(extra_result_handler)
    
    # ========== 工厂模式 ==========
    
    def factory_action(self):
        """拉起中环工厂应用"""
        log_button_click("datong_factory_button", "启动中环工厂应用", "com.zhonghuan.factory")
        self.main_window.start_app_action(app_name="com.zhonghuan.factory")
    
    # ========== Verity 校验管理 ==========
    
    def verity_action(self):
        """执行adb enable-verity和adb disable-verity命令"""
        device_id = self._get_selected_device()
        
        if not self._is_device_connected():
            self._append_output("设备未连接！")
            return
        
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self.main_window,
            '确认执行verity命令',
            f'是否要在设备 {device_id} 上执行adb disable-verity和adb enable-verity命令？\n\n'
            '注意：执行此操作可能需要设备重启才能生效。',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            from Function_Moudle.adb_verity_thread import ADBVerityThread
            self.verity_thread = ADBVerityThread(
                device_id,
                connection_mode=self._get_connection_mode(),
                u2_device=self._get_u2_device() if self._get_connection_mode() == 'u2' else None
            )
            self._connect_thread_signals(self.verity_thread)
            self.verity_thread.start()
        else:
            self._append_output("用户取消执行verity命令")
    
    def disable_verity_action(self):
        """执行adb disable-verity命令"""
        log_button_click("datong_disable_verity_button", "禁用verity校验")
        
        if not self._is_device_connected():
            log_method_result("datong_disable_verity_action", False, "设备未连接")
            self._append_output("设备未连接！")
            return
        
        device_id = self._get_selected_device()
        
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self.main_window,
            '确认执行adb disable-verity',
            f'是否要在设备 {device_id} 上执行adb disable-verity命令？\n\n'
            '注意：\n'
            '1. 此操作将禁用设备的verity校验\n'
            '2. 执行成功后需要将主机断电重启才能生效\n'
            '3. 请确保已保存所有工作',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            from Function_Moudle.adb_verity_thread import ADBDisableVerityThread
            self.disable_verity_thread = ADBDisableVerityThread(
                device_id,
                connection_mode=self._get_connection_mode(),
                u2_device=self._get_u2_device() if self._get_connection_mode() == 'u2' else None
            )
            self._connect_thread_signals(
                self.disable_verity_thread,
                self._handle_disable_verity_result
            )
            self.disable_verity_thread.start()
            log_method_result("datong_disable_verity_action", True, "disable-verity命令已发送")
        else:
            logger.info("用户取消执行adb disable-verity命令")
    
    def _handle_disable_verity_result(self, result_message):
        """处理adb disable-verity执行结果"""
        if "执行完成" in result_message or "成功" in result_message:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(
                self.main_window,
                'adb disable-verity执行成功',
                'adb disable-verity命令执行成功！\n\n'
                '重要提示：\n'
                '请将主机断电重启以使更改生效。\n\n'
                '操作步骤：\n'
                '1. 关闭所有应用程序\n'
                '2. 断开设备连接\n'
                '3. 关闭主机电源\n'
                '4. 等待10秒后重新启动主机',
                QMessageBox.Ok
            )
    
    def enable_verity_action(self):
        """执行adb enable-verity命令"""
        log_button_click("datong_enable_verity_button", "启用verity校验")
        
        if not self._is_device_connected():
            log_method_result("datong_enable_verity_action", False, "设备未连接")
            self._append_output("设备未连接！")
            return
        
        device_id = self._get_selected_device()
        
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self.main_window,
            '确认执行adb enable-verity',
            f'是否要在设备 {device_id} 上执行adb enable-verity命令？\n\n'
            '注意：\n'
            '1. 此操作将启用设备的verity校验\n'
            '2. 执行成功后需要将主机断电重启才能生效\n'
            '3. 请确保已保存所有工作',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            from Function_Moudle.adb_verity_thread import ADBEnableVerityThread
            self.enable_verity_thread = ADBEnableVerityThread(
                device_id,
                connection_mode=self._get_connection_mode(),
                u2_device=self._get_u2_device() if self._get_connection_mode() == 'u2' else None
            )
            self._connect_thread_signals(
                self.enable_verity_thread,
                self._handle_enable_verity_result
            )
            self.enable_verity_thread.start()
            log_method_result("datong_enable_verity_action", True, "enable-verity命令已发送")
        else:
            logger.info("用户取消执行adb enable-verity命令")
    
    def _handle_enable_verity_result(self, result_message):
        """处理adb enable-verity执行结果"""
        if "执行完成" in result_message or "成功" in result_message:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(
                self.main_window,
                'adb enable-verity执行成功',
                'adb enable-verity命令执行成功！\n\n'
                '重要提示：\n'
                '请将主机断电重启以使更改生效。\n\n'
                '操作步骤：\n'
                '1. 关闭所有应用程序\n'
                '2. 断开设备连接\n'
                '3. 关闭主机电源\n'
                '4. 等待10秒后重新启动主机',
                QMessageBox.Ok
            )
    
    # ========== 批量安装 ==========
    
    def batch_install_action(self):
        """批量安装APK文件"""
        log_button_click("datong_batch_install_button", "批量安装APK文件")
        
        if not self._is_device_connected():
            log_method_result("datong_batch_install_action", False, "设备未连接")
            self._append_output("设备未连接！")
            return
        
        from Function_Moudle.dialog_utils import ApkMultiSelectDialog
        folder_path, selected_files = ApkMultiSelectDialog.select_apk_files(
            self.main_window,
            "选择要安装的APK文件"
        )
        
        if not folder_path or not selected_files:
            return
        
        logger.info(f"用户选择了 {len(selected_files)} 个APK文件")
        
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self.main_window,
            '确认批量安装',
            f'已选择 {len(selected_files)} 个APK文件，是否继续批量安装？\n\n'
            f'文件列表:\n' + '\n'.join(selected_files),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            device_id = self._get_selected_device()
            from Function_Moudle.adb_batch_install_thread import ADBBatchInstallThread
            self.batch_install_thread = ADBBatchInstallThread(
                device_id,
                folder_path,
                connection_mode=self._get_connection_mode(),
                u2_device=self._get_u2_device() if self._get_connection_mode() == 'u2' else None,
                selected_files=selected_files
            )
            self._connect_thread_signals(self.batch_install_thread)
            self.batch_install_thread.start()
            log_method_result("datong_batch_install_action", True, f"批量安装线程已启动 ({len(selected_files)}个文件)")
        else:
            logger.info("用户取消批量安装")
    
    def batch_install_test_action(self):
        """测试批量安装功能"""
        log_button_click("datong_batch_install_test_button", "测试批量安装功能")
        
        if not self._is_device_connected():
            log_method_result("datong_batch_install_test_action", False, "设备未连接")
            self._append_output("设备未连接！")
            return
        
        from Function_Moudle.dialog_utils import ApkMultiSelectDialog
        folder_path, selected_files = ApkMultiSelectDialog.select_apk_files(
            self.main_window,
            "选择要测试的APK文件"
        )
        
        if not folder_path or not selected_files:
            return
        
        logger.info(f"用户选择了 {len(selected_files)} 个APK文件进行测试")
        
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self.main_window,
            '确认测试批量安装',
            f'已选择 {len(selected_files)} 个APK文件进行测试，是否继续？\n\n'
            f'文件列表:\n' + '\n'.join(selected_files),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            device_id = self._get_selected_device()
            from Function_Moudle.adb_batch_install_test_thread import ADBBatchInstallTestThread
            self.batch_install_test_thread = ADBBatchInstallTestThread(
                device_id,
                folder_path,
                connection_mode=self._get_connection_mode(),
                u2_device=self._get_u2_device() if self._get_connection_mode() == 'u2' else None,
                selected_files=selected_files
            )
            self._connect_thread_signals(self.batch_install_test_thread)
            self.batch_install_test_thread.debug_signal.connect(self._append_output)
            self.batch_install_test_thread.start()
            log_method_result("datong_batch_install_test_action", True, f"测试线程已启动 ({len(selected_files)}个文件)")
        else:
            logger.info("用户取消测试批量安装")
    
    def batch_verify_version_action(self):
        """验证批量推包版本号"""
        log_button_click("datong_batch_verify_version_button", "验证批量推包版本号")
        
        if not self._is_device_connected():
            log_method_result("datong_batch_verify_version_action", False, "设备未连接")
            self._append_output("设备未连接！")
            return
        
        from Function_Moudle.dialog_utils import ApkMultiSelectDialog
        folder_path, selected_files = ApkMultiSelectDialog.select_apk_files(
            self.main_window,
            "选择要验证版本的APK文件"
        )
        
        if not folder_path or not selected_files:
            return
        
        logger.info(f"用户选择了 {len(selected_files)} 个APK文件进行版本验证")
        
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self.main_window,
            '确认版本验证',
            f'已选择 {len(selected_files)} 个APK文件进行版本验证，是否继续？\n\n'
            f'文件列表:\n' + '\n'.join(selected_files),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            device_id = self._get_selected_device()
            from Function_Moudle.adb_batch_verify_version_thread import ADBBatchVerifyVersionThread
            self.batch_verify_thread = ADBBatchVerifyVersionThread(
                device_id,
                folder_path,
                connection_mode=self._get_connection_mode(),
                u2_device=self._get_u2_device() if self._get_connection_mode() == 'u2' else None,
                selected_files=selected_files
            )
            self._connect_thread_signals(self.batch_verify_thread)
            self.batch_verify_thread.debug_signal.connect(self._append_output)
            self.batch_verify_thread.start()
            log_method_result("datong_batch_verify_version_action", True, f"版本验证线程已启动 ({len(selected_files)}个文件)")
        else:
            logger.info("用户取消版本验证")
    
    # ========== 密码输入 ==========
    
    def input_password_action(self):
        """一键输入密码"""
        log_button_click("datong_input_password_button", "一键输入密码")
        
        if not self._is_device_connected():
            log_method_result("datong_input_password_action", False, "设备未连接")
            self._append_output("设备未连接！")
            return
        
        password = "Kfs73p940a"
        device_id = self._get_selected_device()
        
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self.main_window,
            '确认输入密码',
            f'确定要在设备 {device_id} 上输入密码 {password} 吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            logger.info(f"输入密码: {password}")
            from Function_Moudle.datong_input_password_thread import DatongInputPasswordThread
            self.input_password_thread = DatongInputPasswordThread(device_id, password)
            self._connect_thread_signals(self.input_password_thread)
            self.input_password_thread.start()
            log_method_result("datong_input_password_action", True, "密码输入线程已启动")
        else:
            logger.info("用户取消输入密码")
    
    # ========== 工程模式 ==========
    
    def open_telenav_engineering_action(self):
        """打开泰维地图工程模式"""
        log_button_click("datong_open_telenav_engineering_button", "打开泰维地图工程模式")
        
        if not self._is_device_connected():
            log_method_result("datong_open_telenav_engineering_action", False, "设备未连接")
            self._append_output("设备未连接！")
            return
        
        device_id = self._get_selected_device()
        
        try:
            from Function_Moudle.datong_open_telenav_engineering_thread import DatongOpenTelenavEngineeringThread
            self.telenav_thread = DatongOpenTelenavEngineeringThread(device_id)
            self._connect_thread_signals(self.telenav_thread)
            self.telenav_thread.start()
            log_method_result("datong_open_telenav_engineering_action", True, "线程已启动")
        except Exception as e:
            log_method_result("datong_open_telenav_engineering_action", False, str(e))
            self._append_output(f"打开泰维地图工程模式失败: {e}")
    
    # ========== 日期时间设置 ==========
    
    def set_datetime_action(self):
        """设置设备日期时间"""
        log_button_click("datong_set_datetime_button", "设置设备日期时间")
        
        if not self._is_device_connected():
            log_method_result("datong_set_datetime_action", False, "设备未连接")
            self._append_output("设备未连接！")
            return
        
        device_id = self._get_selected_device()
        
        try:
            from datetime import datetime
            from PyQt5.QtWidgets import QInputDialog
            
            timezones = [
                "Asia/Shanghai (GMT+8)", "Asia/Tokyo (GMT+9)", "Asia/Seoul (GMT+9)",
                "Asia/Bangkok (GMT+7)", "Asia/Dubai (GMT+4)", "Asia/Kolkata (GMT+5:30)",
                "Europe/London (GMT+0)", "Europe/Paris (GMT+1)", "Europe/Moscow (GMT+3)",
                "America/New_York (GMT-5)", "America/Los_Angeles (GMT-8)", "America/Chicago (GMT-6)",
                "Pacific/Auckland (GMT+13)", "Pacific/Fiji (GMT+12)", "UTC"
            ]
            
            timezone, ok = QInputDialog.getItem(
                self.main_window,
                "选择时区",
                "请选择要设置的时区:",
                timezones,
                current=0,
                editable=False
            )
            
            if not ok:
                logger.info("用户取消选择时区")
                return
            
            # 提取时区名称
            timezone_name = timezone.split(' (')[0]
            
            from PyQt5.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self.main_window,
                '确认设置日期时间',
                f'确定要在设备 {device_id} 上设置以下日期时间吗？\n\n'
                f'时区: {timezone}\n'
                f'时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n'
                '注意：\n'
                '1. 此操作将修改设备的系统时间\n'
                '2. 设置成功后需要重启设备以使更改生效\n'
                '3. 请确保已保存所有工作',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                from Function_Moudle.datong_set_datetime_thread import DatongSetDatetimeThread
                self.datetime_thread = DatongSetDatetimeThread(
                    device_id,
                    connection_mode=self._get_connection_mode(),
                    u2_device=self._get_u2_device() if self._get_connection_mode() == 'u2' else None,
                    timezone=timezone_name
                )
                self._connect_thread_signals(self.datetime_thread)
                self.datetime_thread.start()
                log_method_result("datong_set_datetime_action", True, f"设置日期时间线程已启动，时区: {timezone_name}")
            else:
                logger.info("用户取消设置日期时间")
                
        except Exception as e:
            log_method_result("datong_set_datetime_action", False, str(e))
            self._append_output(f"启动设置日期时间线程失败: {e}")