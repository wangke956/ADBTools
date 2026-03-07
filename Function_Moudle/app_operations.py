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
    
    def start_app_action(self, app_name):
        """启动应用"""
        device_id = self.main_window.get_selected_device()
        devices_id_lst = self.main_window.get_new_device_lst()
        
        log_button_click(f"start_{app_name}_button", f"启动{app_name}")

        if device_id in devices_id_lst:
            try:
                # 检查连接状态
                if self.main_window.connection_mode == 'u2':
                    if not self.main_window.d:
                        self.main_window.connection_mode = 'adb'
                        self.textBrowser.append("U2连接不可用，切换到ADB模式")
                
                if self.main_window.connection_mode == 'u2' and self.main_window.d:
                    self.main_window.d.app_start(app_name)
                    self.textBrowser.append(f"已启动应用: {app_name}")
                    log_method_result("start_app_action", True, f"已启动: {app_name}")
                elif self.main_window.connection_mode == 'adb':
                    from Function_Moudle.adb_app_action_thread import ADBAppActionThread
                    self.main_window.app_action_thread = ADBAppActionThread(device_id, app_name)
                    self.main_window.app_action_thread.progress_signal.connect(self.textBrowser.append)
                    self.main_window.app_action_thread.error_signal.connect(self.textBrowser.append)
                    self.main_window.app_action_thread.start()
                    log_method_result("start_app_action", True, f"启动线程已启动: {app_name}")
                else:
                    log_method_result("start_app_action", False, "设备未连接")
                    self.textBrowser.append("设备未连接！")
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
                import adb_utils
                package_name = adb_utils.aapt_get_package_name(apk_path)
                
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
            
            logger.info(f"查看APK路径: {package_name}")
            
            try:
                from Function_Moudle.view_apk_path_wrapper_thread import ViewApkPathWrapperThread
                self.main_window.view_apk_thread = ViewApkPathWrapperThread(device_id, package_name)
                self.main_window.view_apk_thread.progress_signal.connect(self.textBrowser.append)
                self.main_window.view_apk_thread.result_signal.connect(self.textBrowser.append)
                self.main_window.view_apk_thread.start()
                
                log_method_result("view_apk_path_wrapper", True, f"查询线程已启动: {package_name}")
            except Exception as e:
                log_method_result("view_apk_path_wrapper", False, str(e))
                self.textBrowser.append(f"启动查询线程失败: {e}")
        else:
            log_method_result("view_apk_path_wrapper", False, "设备未连接")
            self.textBrowser.append("设备未连接！")
    
    def app_version_check(self):
        """应用版本检查"""
        device_id = self.main_window.get_selected_device()
        devices_id_lst = self.main_window.get_new_device_lst()
        
        log_button_click("start_check_button", "检查应用版本", f"集成清单: {self.main_window.releasenote_file}")

        if device_id in devices_id_lst:
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
        else:
            log_method_result("app_version_check", False, "设备未连接")
            self.textBrowser.append("设备未连接！")