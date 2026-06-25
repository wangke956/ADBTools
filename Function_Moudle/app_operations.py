# -*- coding: utf-8 -*-
"""
应用操作管理器
负责应用启动、停止、清理缓存、列出包名等应用相关操作
"""

import os
from PyQt5.QtWidgets import QInputDialog, QFileDialog, QMessageBox

from logger_manager import log_button_click, log_method_result, get_logger

logger = get_logger("ADBTools.AppOperations")


class AppOperationsManager:
    """应用操作管理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window
    
    @property
    def textBrowser(self):
        return self.main_window.textBrowser
    
    def show_start_app_dialog(self):
        """显示启动应用对话框"""
        device_id = self.main_window.get_selected_device()
        devices_id_lst = self.main_window.get_new_device_lst()
        
        log_button_click("start_app_button", "启动应用")

        if device_id in devices_id_lst:
            package_name, ok = QInputDialog.getText(
                self.main_window, "输入包名", "请输入要启动的应用包名："
            )
            if ok and package_name:
                package_name = package_name.strip()
                if package_name:
                    self.start_app_action(package_name)
                else:
                    self.textBrowser.append("包名不能为空！")
            else:
                logger.info("用户取消输入或输入为空")
        else:
            self.textBrowser.append("设备未连接！")

    def start_app_action(self, app_name):
        """启动应用 - 使用统一的异步线程"""
        device_id = self.main_window.get_selected_device()
        devices_id_lst = self.main_window.get_new_device_lst()
        
        log_button_click(f"start_{app_name}_button", f"启动{app_name}")

        if device_id in devices_id_lst:
            try:
                # 检查是否正在连接U2
                if getattr(self.main_window, 'u2_connecting', False):
                    self.textBrowser.append("U2正在连接中，请稍候再试...")
                    return
                
                # 使用统一的异步线程启动应用
                self.main_window._start_app_with_thread(app_name)
                log_method_result("start_app_action", True, f"启动线程已启动: {app_name}")
            except Exception as e:
                log_method_result("start_app_action", False, str(e))
                self.textBrowser.append(f"启动应用失败: {e}")
        else:
            log_method_result("start_app_action", False, "设备未连接")
            self.textBrowser.append("设备未连接！")
    

    
    def list_package(self):
        """列出设备上安装的包名"""
        device_id = self.main_window.get_selected_device()
        devices_id_lst = self.main_window.get_new_device_lst()
        
        # 获取Findstr文本框中的过滤关键字
        findstr = self.main_window.Findstr.toPlainText().strip()
        
        log_button_click("list_package_button", "列出包名", f"过滤关键字: {findstr if findstr else '无'}")

        if device_id in devices_id_lst:
            try:
                # 检查连接状态
                if self.main_window.connection_mode == 'u2':
                    if not self.main_window.d:
                        self.main_window.connection_mode = 'adb'
                        self.textBrowser.append("U2连接不可用，切换到ADB模式")
                
                if self.main_window.connection_mode == 'u2' and self.main_window.d:
                    from Function_Moudle.list_package_thread import ListPackageThread
                    self.main_window.list_package_thread = ListPackageThread(self.main_window.d, findstr)
                elif self.main_window.connection_mode == 'adb':
                    from Function_Moudle.adb_list_package_thread import ADBListPackageThread
                    self.main_window.list_package_thread = ADBListPackageThread(device_id, findstr)
                else:
                    log_method_result("list_package", False, "设备未连接")
                    self.textBrowser.append("设备未连接！")
                    return
                
                self.main_window.list_package_thread.progress_signal.connect(self.textBrowser.append)
                self.main_window.list_package_thread.result_signal.connect(
                    lambda packages: [self.textBrowser.append(pkg) for pkg in packages]
                )
                self.main_window.list_package_thread.error_signal.connect(self.textBrowser.append)
                self.main_window.list_package_thread.start()
                
                log_method_result("list_package", True, "列出包名线程已启动")
            except Exception as e:
                log_method_result("list_package", False, str(e))
                self.textBrowser.append(f"启动列出包名线程失败: {e}")
        else:
            log_method_result("list_package", False, "设备未连接")
            self.textBrowser.append("设备未连接！")
    
    def show_force_stop_app_dialog(self):
        """强制停止应用"""
        device_id = self.main_window.get_selected_device()
        devices_id_lst = self.main_window.get_new_device_lst()
        
        log_button_click("force_stop_app_button", "强制停止应用")

        if device_id in devices_id_lst:
            package_name, ok = QInputDialog.getText(
                self.main_window, "输入包名", "请输入要停止的应用包名："
            )
            if ok and package_name:
                logger.info(f"强制停止应用: {package_name}")
                
                try:
                    # 检查连接状态
                    if self.main_window.connection_mode == 'u2':
                        if not self.main_window.d:
                            self.main_window.connection_mode = 'adb'
                            self.textBrowser.append("U2连接不可用，切换到ADB模式")
                    
                    if self.main_window.connection_mode == 'u2' and self.main_window.d:
                        from Function_Moudle.force_stop_app_thread import ForceStopAppThread
                        self.main_window.force_stop_thread = ForceStopAppThread(
                            self.main_window.d, package_name
                        )
                    elif self.main_window.connection_mode == 'adb':
                        from Function_Moudle.adb_force_stop_app_thread import ADBForceStopAppThread
                        self.main_window.force_stop_thread = ADBForceStopAppThread(device_id, package_name)
                    else:
                        log_method_result("show_force_stop_app_dialog", False, "设备未连接")
                        self.textBrowser.append("设备未连接！")
                        return
                    
                    self.main_window.force_stop_thread.progress_signal.connect(self.textBrowser.append)
                    self.main_window.force_stop_thread.result_signal.connect(self.textBrowser.append)
                    self.main_window.force_stop_thread.error_signal.connect(self.textBrowser.append)
                    self.main_window.force_stop_thread.start()
                    
                    log_method_result("show_force_stop_app_dialog", True, f"停止线程已启动: {package_name}")
                except Exception as e:
                    log_method_result("show_force_stop_app_dialog", False, str(e))
                    self.textBrowser.append(f"启动停止线程失败: {e}")
            else:
                logger.info("用户取消输入或输入为空")
        else:
            log_method_result("show_force_stop_app_dialog", False, "设备未连接")
            self.textBrowser.append("设备未连接！")
    
    def show_clear_app_cache_dialog(self):
        """清除应用缓存"""
        device_id = self.main_window.get_selected_device()
        devices_id_lst = self.main_window.get_new_device_lst()
        
        log_button_click("clear_app_cache_button", "清除应用缓存")

        if device_id in devices_id_lst:
            package_name, ok = QInputDialog.getText(
                self.main_window, "输入包名", "请输入要清除缓存的应用包名："
            )
            if ok and package_name:
                logger.info(f"清除应用缓存: {package_name}")
                
                reply = QMessageBox.question(
                    self.main_window,
                    '确认清除',
                    f'确定要清除 {package_name} 的缓存吗？\n此操作不可逆！',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    try:
                        # 检查连接状态
                        if self.main_window.connection_mode == 'u2':
                            if not self.main_window.d:
                                self.main_window.connection_mode = 'adb'
                                self.textBrowser.append("U2连接不可用，切换到ADB模式")
                        
                        if self.main_window.connection_mode == 'u2' and self.main_window.d:
                            from Function_Moudle.clear_app_cache_thread import ClearAppCacheThread
                            self.main_window.clear_cache_thread = ClearAppCacheThread(
                                self.main_window.d, package_name
                            )
                        elif self.main_window.connection_mode == 'adb':
                            from Function_Moudle.adb_clear_app_cache_thread import ADBClearAppCacheThread
                            self.main_window.clear_cache_thread = ADBClearAppCacheThread(device_id, package_name)
                        else:
                            log_method_result("show_clear_app_cache_dialog", False, "设备未连接")
                            self.textBrowser.append("设备未连接！")
                            return
                        
                        self.main_window.clear_cache_thread.progress_signal.connect(self.textBrowser.append)
                        self.main_window.clear_cache_thread.result_signal.connect(self.textBrowser.append)
                        self.main_window.clear_cache_thread.error_signal.connect(self.textBrowser.append)
                        self.main_window.clear_cache_thread.start()
                        
                        log_method_result("show_clear_app_cache_dialog", True, f"清除缓存线程已启动: {package_name}")
                    except Exception as e:
                        log_method_result("show_clear_app_cache_dialog", False, str(e))
                        self.textBrowser.append(f"启动清除缓存线程失败: {e}")
                else:
                    logger.info("用户取消清除缓存操作")
            else:
                logger.info("用户取消输入或输入为空")
        else:
            log_method_result("show_clear_app_cache_dialog", False, "设备未连接")
            self.textBrowser.append("设备未连接！")
    
    def get_foreground_package(self):
        """获取前台应用包名"""
        device_id = self.main_window.get_selected_device()
        devices_id_lst = self.main_window.get_new_device_lst()
        
        log_button_click("get_foreground_package_button", "获取前台应用包名")

        if device_id in devices_id_lst:
            try:
                # 检查连接状态
                if self.main_window.connection_mode == 'u2':
                    if not self.main_window.d:
                        self.main_window.connection_mode = 'adb'
                        self.textBrowser.append("U2连接不可用，切换到ADB模式")
                
                if self.main_window.connection_mode == 'u2' and self.main_window.d:
                    from Function_Moudle.get_foreground_package_thread import GetForegroundPackageThread
                    self.main_window.foreground_package_thread = GetForegroundPackageThread(
                        self.main_window.d
                    )
                elif self.main_window.connection_mode == 'adb':
                    from Function_Moudle.adb_get_foreground_package_thread import ADBGetForegroundPackageThread
                    self.main_window.foreground_package_thread = ADBGetForegroundPackageThread(device_id)
                else:
                    log_method_result("get_foreground_package", False, "设备未连接")
                    self.textBrowser.append("设备未连接！")
                    return
                
                self.main_window.foreground_package_thread.progress_signal.connect(self.textBrowser.append)
                self.main_window.foreground_package_thread.result_signal.connect(self.textBrowser.append)
                self.main_window.foreground_package_thread.error_signal.connect(self.textBrowser.append)
                self.main_window.foreground_package_thread.start()
                
                log_method_result("get_foreground_package", True, "获取前台包名线程已启动")
            except Exception as e:
                log_method_result("get_foreground_package", False, str(e))
                self.textBrowser.append(f"启动获取前台包名线程失败: {e}")
        else:
            log_method_result("get_foreground_package", False, "设备未连接")
            self.textBrowser.append("设备未连接！")
    
    def get_running_app_info(self):
        """获取正在运行的应用信息"""
        device_id = self.main_window.get_selected_device()
        devices_id_lst = self.main_window.get_new_device_lst()
        
        log_button_click("get_running_app_info_button", "获取运行应用信息")

        if device_id in devices_id_lst:
            try:
                # 检查连接状态
                if self.main_window.connection_mode == 'u2':
                    if not self.main_window.d:
                        self.main_window.connection_mode = 'adb'
                        self.textBrowser.append("U2连接不可用，切换到ADB模式")
                
                if self.main_window.connection_mode == 'u2' and self.main_window.d:
                    from Function_Moudle.get_running_app_info_thread import GetRunningAppInfoThread
                    self.main_window.running_app_thread = GetRunningAppInfoThread(self.main_window.d)
                elif self.main_window.connection_mode == 'adb':
                    from Function_Moudle.adb_get_running_app_info_thread import ADBGetRunningAppInfoThread
                    self.main_window.running_app_thread = ADBGetRunningAppInfoThread(device_id)
                else:
                    log_method_result("get_running_app_info", False, "设备未连接")
                    self.textBrowser.append("设备未连接！")
                    return
                
                self.main_window.running_app_thread.progress_signal.connect(self.textBrowser.append)
                self.main_window.running_app_thread.result_signal.connect(self.textBrowser.append)
                self.main_window.running_app_thread.error_signal.connect(self.textBrowser.append)
                self.main_window.running_app_thread.start()
                
                log_method_result("get_running_app_info", True, "获取运行应用信息线程已启动")
            except Exception as e:
                log_method_result("get_running_app_info", False, str(e))
                self.textBrowser.append(f"启动获取运行应用信息线程失败: {e}")
        else:
            log_method_result("get_running_app_info", False, "设备未连接")
            self.textBrowser.append("设备未连接！")
    
    def aapt_getpackage_name_dilog(self):
        """使用aapt获取APK包名"""
        log_button_click("aapt_get_package_name_button", "使用aapt获取包名")
        
        apk_path, _ = QFileDialog.getOpenFileName(
            self.main_window, "选择APK文件", "", "APK Files (*.apk)"
        )
        
        if apk_path:
            logger.info(f"选择APK: {apk_path}")
            
            try:
                from adb_utils import ADBUtils
                package_name = ADBUtils.aapt_get_package_name(apk_path)
                
                if package_name:
                    self.textBrowser.append(f"包名: {package_name}")
                    log_method_result("aapt_getpackage_name_dilog", True, f"包名: {package_name}")
                else:
                    self.textBrowser.append("无法获取包名，请确保aapt工具可用")
                    log_method_result("aapt_getpackage_name_dilog", False, "无法获取包名")
            except Exception as e:
                log_method_result("aapt_getpackage_name_dilog", False, str(e))
                self.textBrowser.append(f"获取包名失败: {e}")
        else:
            logger.info("用户取消文件选择")
    
    def view_apk_path_wrapper(self):
        """查看APK安装路径"""
        device_id = self.main_window.get_selected_device()
        devices_id_lst = self.main_window.get_new_device_lst()
        
        log_button_click("view_apk_path", "查看应用安装路径")

        if device_id in devices_id_lst:
            package_name, ok = QInputDialog.getText(
                self.main_window, "输入应用包名", "请输入要查看安装路径的应用包名："
            )
            if not ok:
                logger.info("用户取消输入")
                return
            
            if not package_name or not package_name.strip():
                logger.info("包名为空，跳过查询")
                self.textBrowser.append("包名不能为空！")
                return
            
            package_name = package_name.strip()
            logger.info(f"查看APK路径: {package_name}")
            
            try:
                from Function_Moudle.view_apk_path_wrapper_thread import ViewApkPathWrapperThread
                self.main_window.view_apk_thread = ViewApkPathWrapperThread(device_id, package_name)
                self.main_window.view_apk_thread.progress_signal.connect(self.textBrowser.append)
                self.main_window.view_apk_thread.result_signal.connect(self.textBrowser.append)
                self.main_window.view_apk_thread.error_signal.connect(self.textBrowser.append)
                self.main_window.view_apk_thread.start()
                
                log_method_result("view_apk_path_wrapper", True, f"查询线程已启动: {package_name}")
            except Exception as e:
                log_method_result("view_apk_path_wrapper", False, str(e))
                self.textBrowser.append(f"启动查询线程失败: {e}")
        else:
            log_method_result("view_apk_path_wrapper", False, "设备未连接")
            self.textBrowser.append("设备未连接！")
    
    def app_version_check(self):
        """应用版本检查 - 读取本地集成清单文件，不需要设备连接"""
        log_button_click("start_check_button", "检查应用版本", f"集成清单: {self.main_window.releasenote_file}")

        try:
            from Function_Moudle.app_version_check_thread import AppVersionCheckThread
            self.main_window.releasenote_dict = {}
            self.main_window.app_version_check_thread = AppVersionCheckThread(
                None, self.main_window.releasenote_file
            )
            self.main_window.app_version_check_thread.progress_signal.connect(self.textBrowser.append)
            self.main_window.app_version_check_thread.error_signal.connect(self.textBrowser.append)
            self.main_window.app_version_check_thread.release_note_signal.connect(
                self.main_window.handle_progress
            )
            self.main_window.app_version_check_thread.start()
            
            log_method_result("app_version_check", True, "版本检查线程已启动")
        except Exception as e:
            log_method_result("app_version_check", False, str(e))
            self.textBrowser.append(f"启动版本检查线程失败: {e}")
    
    # def show_network_proxy_dialog(self):
    #     """显示网络代理管理对话框"""
    #     log_button_click("network_proxy_button", "网络代理管理")
    #
    #     # 创建对话框
    #     from PyQt5.QtWidgets import (
    #         QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    #         QPushButton, QGroupBox, QComboBox, QTextBrowser
    #     )
    #     dialog = QDialog(self.main_window)
    #     dialog.setWindowTitle("网络代理管理")
    #     dialog.setMinimumWidth(600)
    #     dialog.setMinimumHeight(500)
    #
    #     layout = QVBoxLayout()
    #     layout.setSpacing(10)
    #     layout.setContentsMargins(20, 20, 20, 20)
    #
    #     # 标题
    #     title_label = QLabel("网络代理设置")
    #     title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #0078d4;")
    #     layout.addWidget(title_label)
    #
    #     # 设备选择区域
    #     device_group = QGroupBox("设备选择")
    #     device_layout = QHBoxLayout()
    #
    #     device_label = QLabel("选择设备:")
    #     device_combo = QComboBox()
    #     device_combo.setMinimumWidth(300)
    #
    #     # 刷新设备按钮
    #     refresh_device_btn = QPushButton("🔄 刷新设备")
    #
    #     device_layout.addWidget(device_label)
    #     device_layout.addWidget(device_combo)
    #     device_layout.addWidget(refresh_device_btn)
    #     device_group.setLayout(device_layout)
    #     layout.addWidget(device_group)
    #
    #     # 代理地址输入组
    #     proxy_group = QGroupBox("代理服务器")
    #     proxy_layout = QVBoxLayout()
    #
    #     address_layout = QHBoxLayout()
    #     address_label = QLabel("地址:")
    #     proxy_address_input = QLineEdit("192.168.137.1")
    #     proxy_address_input.setPlaceholderText("例如: 192.168.137.1")
    #     address_layout.addWidget(address_label)
    #     address_layout.addWidget(proxy_address_input)
    #
    #     port_layout = QHBoxLayout()
    #     port_label = QLabel("端口:")
    #     proxy_port_input = QLineEdit("7897")
    #     proxy_port_input.setPlaceholderText("例如: 7897")
    #     port_layout.addWidget(port_label)
    #     port_layout.addWidget(proxy_port_input)
    #
    #     proxy_layout.addLayout(address_layout)
    #     proxy_layout.addLayout(port_layout)
    #     proxy_group.setLayout(proxy_layout)
    #     layout.addWidget(proxy_group)
    #
    #     # 操作按钮组
    #     button_layout = QHBoxLayout()
    #     button_layout.setSpacing(8)
    #
    #     # 获取代理按钮
    #     get_proxy_btn = QPushButton("获取当前代理")
    #     button_layout.addWidget(get_proxy_btn)
    #
    #     # 设置代理按钮
    #     set_proxy_btn = QPushButton("设置代理")
    #     button_layout.addWidget(set_proxy_btn)
    #
    #     # 清除代理按钮
    #     clear_proxy_btn = QPushButton("清除代理")
    #     button_layout.addWidget(clear_proxy_btn)
    #
    #     layout.addLayout(button_layout)
    #
    #     # 输出文本框
    #     output_group = QGroupBox("操作日志")
    #     output_layout = QVBoxLayout()
    #     output_text = QTextBrowser()
    #     output_text.setMinimumHeight(200)
    #     output_text.setStyleSheet("""
    #         QTextBrowser {
    #             background-color: #1e1e1e;
    #             color: #d4d4d4;
    #             font-family: 'Consolas', 'Courier New', monospace;
    #             font-size: 12px;
    #             border: 1px solid #3c3c3c;
    #             border-radius: 4px;
    #             padding: 8px;
    #         }
    #     """)
    #     output_layout.addWidget(output_text)
    #     output_group.setLayout(output_layout)
    #     layout.addWidget(output_group)
    #
    #     # 关闭按钮
    #     close_btn = QPushButton("关闭")
    #     close_btn.clicked.connect(dialog.accept)
    #     layout.addWidget(close_btn)
    #
    #     dialog.setLayout(layout)
    #
    #     # ========== 功能实现 ==========
    #     log_method_result("代理管理器", True, "代理管理器已启动")
    #     # 用于保存线程引用，防止被垃圾回收
    #     dialog.threads = []
    #
    #     def refresh_devices():
    #         """刷新设备列表"""
    #         device_combo.clear()
    #         devices = self.main_window.get_new_device_lst()
    #         if devices:
    #             device_combo.addItems(devices)
    #             output_text.append(f"✓ 找到 {len(devices)} 个设备")
    #             # 自动选择第一个设备
    #             if device_combo.count() > 0:
    #                 device_combo.setCurrentIndex(0)
    #         else:
    #             output_text.append("⚠ 未找到任何设备")
    #
    #     def append_output(text):
    #         """追加输出到对话框的文本框"""
    #         from datetime import datetime
    #         timestamp = datetime.now().strftime("%H:%M:%S")
    #         output_text.append(f"[{timestamp}] {text}")
    #         # 自动滚动到底部
    #         output_text.verticalScrollBar().setValue(
    #             output_text.verticalScrollBar().maximum()
    #         )
    #
    #     def get_selected_device():
    #         """获取当前选择的设备ID"""
    #         return device_combo.currentText()
    #
    #     def check_device_connection(device_id):
    #         """检查设备是否连接"""
    #         devices = self.main_window.get_new_device_lst()
    #         return device_id in devices
    #
    #     def get_current_connection_mode(device_id):
    #         """获取当前设备的连接模式"""
    #         # 如果主窗口当前连接的是这个设备，使用主窗口的模式
    #         if self.main_window.device_id == device_id:
    #             return self.main_window.connection_mode, self.main_window.d
    #         # 否则默认使用ADB模式
    #         return 'adb', None
    #
    #     def _get_network_proxy():
    #         """获取网络代理信息"""
    #         device_id = get_selected_device()
    #         if not device_id:
    #             append_output("请先选择设备")
    #             return
    #
    #         if not check_device_connection(device_id):
    #             append_output("设备未连接！")
    #             return
    #
    #         try:
    #             connection_mode, u2_device = get_current_connection_mode(device_id)
    #
    #             if connection_mode == 'u2' and u2_device:
    #                 from Function_Moudle.adb_network_proxy_thread import GetProxyThread
    #                 self.thread = GetProxyThread(
    #                     device_id=device_id,
    #                     connection_mode='u2',
    #                     u2_device=u2_device
    #                 )
    #             elif connection_mode == 'adb':
    #                 from Function_Moudle.adb_network_proxy_thread import GetProxyThread
    #                 self.thread = GetProxyThread(
    #                     device_id=device_id,
    #                     connection_mode='adb'
    #                 )
    #             else:
    #                 append_output("⚠ 设备未连接！")
    #                 return
    #
    #             self.thread.progress_signal.connect(append_output)
    #             self.thread.result_signal.connect(append_output)
    #             self.thread.error_signal.connect(append_output)
    #             self.thread.start()
    #             append_output("✓ 获取代理线程已启动")
    #         except Exception as e:
    #             append_output(f"✗ 启动获取代理线程失败: {e}")
    #
    #     def _set_network_proxy():
    #         """设置网络代理"""
    #         device_id = get_selected_device()
    #         if not device_id:
    #             append_output("⚠ 请先选择设备")
    #             return
    #
    #         if not check_device_connection(device_id):
    #             append_output("⚠ 设备未连接！")
    #             return
    #
    #         proxy_address = proxy_address_input.text().strip()
    #         proxy_port = proxy_port_input.text().strip()
    #
    #         if not proxy_address or not proxy_port:
    #             append_output("⚠ 代理地址和端口不能为空！")
    #             return
    #
    #         try:
    #             int(proxy_port)
    #         except ValueError:
    #             append_output("⚠ 端口号必须是数字！")
    #             return
    #
    #         try:
    #             connection_mode, u2_device = get_current_connection_mode(device_id)
    #
    #             if connection_mode == 'u2' and u2_device:
    #                 from Function_Moudle.adb_network_proxy_thread import SetProxyThread
    #                 self.thread = SetProxyThread(
    #                     device_id=device_id,
    #                     proxy_address=proxy_address,
    #                     proxy_port=proxy_port,
    #                     connection_mode='u2',
    #                     u2_device=u2_device
    #                 )
    #             elif connection_mode == 'adb':
    #                 from Function_Moudle.adb_network_proxy_thread import SetProxyThread
    #                 self.thread = SetProxyThread(
    #                     device_id=device_id,
    #                     proxy_address=proxy_address,
    #                     proxy_port=proxy_port,
    #                     connection_mode='adb'
    #                 )
    #             else:
    #                 append_output("⚠ 设备未连接！")
    #                 return
    #
    #             self.thread.progress_signal.connect(append_output)
    #             self.thread.result_signal.connect(append_output)
    #             self.thread.error_signal.connect(append_output)
    #             self.thread.start()
    #
    #             append_output(f"✓ 设置代理线程已启动: {proxy_address}:{proxy_port}")
    #         except Exception as e:
    #             append_output(f"✗ 启动设置代理线程失败: {e}")
    #
    #     def _clear_network_proxy():
    #         """清除网络代理"""
    #         device_id = get_selected_device()
    #         if not device_id:
    #             append_output("⚠ 请先选择设备")
    #             return
    #
    #         if not check_device_connection(device_id):
    #             append_output("⚠ 设备未连接！")
    #             return
    #
    #         try:
    #             connection_mode, u2_device = get_current_connection_mode(device_id)
    #
    #             if connection_mode == 'u2' and u2_device:
    #                 from Function_Moudle.adb_network_proxy_thread import ClearProxyThread
    #                 self.thread = ClearProxyThread(
    #                     device_id=device_id,
    #                     connection_mode='u2',
    #                     u2_device=u2_device
    #                 )
    #             elif connection_mode == 'adb':
    #                 from Function_Moudle.adb_network_proxy_thread import ClearProxyThread
    #                 self.thread = ClearProxyThread(
    #                     device_id=device_id,
    #                     connection_mode='adb'
    #                 )
    #             else:
    #                 append_output("⚠ 设备未连接！")
    #                 return
    #
    #             self.thread.progress_signal.connect(append_output)
    #             self.thread.result_signal.connect(append_output)
    #             self.thread.error_signal.connect(append_output)
    #             self.thread.start()
    #
    #             append_output("✓ 清除代理线程已启动")
    #         except Exception as e:
    #             append_output(f"✗ 启动清除代理线程失败: {e}")
    #
    #     # 连接信号
    #     refresh_device_btn.clicked.connect(refresh_devices)
    #     get_proxy_btn.clicked.connect(_get_network_proxy)
    #     set_proxy_btn.clicked.connect(_set_network_proxy)
    #     clear_proxy_btn.clicked.connect(_clear_network_proxy)
    #
    #     # 初始化：加载设备列表
    #     refresh_devices()
    #
    #     dialog.exec_()  # 显示对话框



    def show_network_proxy_dialog(self):
        """显示网络代理管理对话框（动态加载Dialog_proxy.ui）"""
        import os
        # 取当前app_operations.py所在目录
        # base_dir = os.path.dirname(os.path.abspath(__file__))
        # 获取当前项目根目录
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # 拼接完整ui路径
        base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ui_full_path = os.path.join(base_dir, "Dialog_proxy.ui")
        print(ui_full_path)
        # ui_full_path = os.path.join(base_dir, "Dialog_proxy.ui")
        # uic.loadUi(ui_full_path, dialog)
        from PyQt5 import uic
        from PyQt5.QtWidgets import (
            QDialog, QLabel, QComboBox, QLineEdit, QPushButton, QGroupBox, QTextBrowser
        )
        log_button_click("network_proxy_button", "网络代理管理")

        # 1. 创建对话框容器 + 加载UI文件
        dialog = QDialog(self.main_window)
        # 核心加载语句，按你要求使用uic.loadUi
        uic.loadUi(ui_full_path, dialog)

        # 2. 获取UI内所有控件（objectName与UI内一一对应）
        title_label = dialog.findChild(QLabel, "title_label")
        device_label = dialog.findChild(QLabel, "device_label")
        address_label = dialog.findChild(QLabel, "address_label")
        port_label = dialog.findChild(QLabel, "port_label")

        device_combo = dialog.findChild(QComboBox, "device_combo")
        proxy_address_input = dialog.findChild(QLineEdit, "proxy_address_input")
        proxy_port_input = dialog.findChild(QLineEdit, "proxy_port_input")

        refresh_device_btn = dialog.findChild(QPushButton, "refresh_device_btn")
        get_proxy_btn = dialog.findChild(QPushButton, "get_proxy_btn")
        set_proxy_btn = dialog.findChild(QPushButton, "set_proxy_btn")
        clear_proxy_btn = dialog.findChild(QPushButton, "clear_proxy_btn")
        close_btn = dialog.findChild(QPushButton, "close_btn")

        output_text = dialog.findChild(QTextBrowser, "output_text")

        # ========== 全局缓存线程，防止GC回收崩溃 ==========
        dialog.work_thread = None

        # ========== 内部工具函数（完全保留原有逻辑无修改） ==========
        def refresh_devices():
            """刷新设备列表"""
            device_combo.clear()
            devices = self.main_window.get_new_device_lst()
            if devices:
                device_combo.addItems(devices)
                append_output(f"✓ 找到 {len(devices)} 个设备")
                # 自动选择第一个设备
                if device_combo.count() > 0:
                    device_combo.setCurrentIndex(0)
            else:
                append_output("⚠ 未找到任何设备")

        def append_output(text):
            """追加输出到对话框的文本框"""
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            output_text.append(f"[{timestamp}] {text}")
            # 自动滚动到底部
            output_text.verticalScrollBar().setValue(
                output_text.verticalScrollBar().maximum()
            )

        def get_selected_device():
            """获取当前选择的设备ID"""
            return device_combo.currentText()

        def check_device_connection(device_id):
            """检查设备是否连接"""
            devices = self.main_window.get_new_device_lst()
            return device_id in devices

        def get_current_connection_mode(device_id):
            """获取当前设备的连接模式"""
            # 如果主窗口当前连接的是这个设备，使用主窗口的模式
            if self.main_window.device_id == device_id:
                return self.main_window.connection_mode, self.main_window.d
            # 否则默认使用ADB模式
            return 'adb', None

        def _get_network_proxy():
            """获取网络代理信息"""
            device_id = get_selected_device()
            if not device_id:
                append_output("请先选择设备")
                return

            if not check_device_connection(device_id):
                append_output("设备未连接！")
                return

            try:
                connection_mode, u2_device = get_current_connection_mode(device_id)

                if connection_mode == 'u2' and u2_device:
                    from Function_Moudle.adb_network_proxy_thread import GetProxyThread
                    dialog.work_thread = GetProxyThread(
                        device_id=device_id,
                        connection_mode='u2',
                        u2_device=u2_device
                    )
                elif connection_mode == 'adb':
                    from Function_Moudle.adb_network_proxy_thread import GetProxyThread
                    dialog.work_thread = GetProxyThread(
                        device_id=device_id,
                        connection_mode='adb'
                    )
                else:
                    append_output("⚠ 设备未连接！")
                    return

                dialog.work_thread.progress_signal.connect(append_output)
                dialog.work_thread.result_signal.connect(append_output)
                dialog.work_thread.error_signal.connect(append_output)
                dialog.work_thread.start()
                append_output("✓ 获取代理线程已启动")
            except Exception as e:
                append_output(f"✗ 启动获取代理线程失败: {e}")

        def _set_network_proxy():
            """设置网络代理"""
            device_id = get_selected_device()
            if not device_id:
                append_output("⚠ 请先选择设备")
                return

            if not check_device_connection(device_id):
                append_output("⚠ 设备未连接！")
                return

            proxy_address = proxy_address_input.text().strip()
            proxy_port = proxy_port_input.text().strip()

            if not proxy_address or not proxy_port:
                append_output("⚠ 代理地址和端口不能为空！")
                return

            try:
                int(proxy_port)
            except ValueError:
                append_output("⚠ 端口号必须是数字！")
                return

            try:
                connection_mode, u2_device = get_current_connection_mode(device_id)

                if connection_mode == 'u2' and u2_device:
                    from Function_Moudle.adb_network_proxy_thread import SetProxyThread
                    dialog.work_thread = SetProxyThread(
                        device_id=device_id,
                        proxy_address=proxy_address,
                        proxy_port=proxy_port,
                        connection_mode='u2',
                        u2_device=u2_device
                    )
                elif connection_mode == 'adb':
                    from Function_Moudle.adb_network_proxy_thread import SetProxyThread
                    dialog.work_thread = SetProxyThread(
                        device_id=device_id,
                        proxy_address=proxy_address,
                        proxy_port=proxy_port,
                        connection_mode='adb'
                    )
                else:
                    append_output("⚠ 设备未连接！")
                    return

                dialog.work_thread.progress_signal.connect(append_output)
                dialog.work_thread.result_signal.connect(append_output)
                dialog.work_thread.error_signal.connect(append_output)
                dialog.work_thread.start()

                append_output(f"✓ 设置代理线程已启动: {proxy_address}:{proxy_port}")
            except Exception as e:
                append_output(f"✗ 启动设置代理线程失败: {e}")

        def _clear_network_proxy():
            """清除网络代理"""
            device_id = get_selected_device()
            if not device_id:
                append_output("⚠ 请先选择设备")
                return

            if not check_device_connection(device_id):
                append_output("⚠ 设备未连接！")
                return

            try:
                connection_mode, u2_device = get_current_connection_mode(device_id)

                if connection_mode == 'u2' and u2_device:
                    from Function_Moudle.adb_network_proxy_thread import ClearProxyThread
                    dialog.work_thread = ClearProxyThread(
                        device_id=device_id,
                        connection_mode='u2',
                        u2_device=u2_device
                    )
                elif connection_mode == 'adb':
                    from Function_Moudle.adb_network_proxy_thread import ClearProxyThread
                    dialog.work_thread = ClearProxyThread(
                        device_id=device_id,
                        connection_mode='adb'
                    )
                else:
                    append_output("⚠ 设备未连接！")
                    return

                dialog.work_thread.progress_signal.connect(append_output)
                dialog.work_thread.result_signal.connect(append_output)
                dialog.work_thread.error_signal.connect(append_output)
                dialog.work_thread.start()

                append_output("✓ 清除代理线程已启动")
            except Exception as e:
                append_output(f"✗ 启动清除代理线程失败: {e}")

        # ========== 信号绑定 ==========
        close_btn.clicked.connect(dialog.accept)
        refresh_device_btn.clicked.connect(refresh_devices)
        get_proxy_btn.clicked.connect(_get_network_proxy)
        set_proxy_btn.clicked.connect(_set_network_proxy)
        clear_proxy_btn.clicked.connect(_clear_network_proxy)

        # 初始化加载设备
        refresh_devices()
        log_method_result("代理管理器", True, "代理管理器已启动")

        # 模态弹窗
        dialog.exec_()


if __name__ == "__main__":
    import sys
    import qdarkstyle
    from PyQt5.QtWidgets import QApplication, QMainWindow


    class MockMainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.device_id = None
            self.connection_mode = "adb"
            self.d = None
            self.releasenote_file = ""
            from PyQt5.QtWidgets import QTextBrowser
            self.textBrowser = QTextBrowser()
            self.Findstr = QTextBrowser()

        def get_selected_device(self):
            return self.device_id

        def get_new_device_lst(self):
            return []


    app = QApplication(sys.argv)
    # 全局加载暗黑样式
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    main_win = MockMainWindow()
    op_mgr = AppOperationsManager(main_win)
    op_mgr.show_network_proxy_dialog()
    sys.exit(app.exec_())