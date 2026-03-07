# -*- coding: utf-8 -*-
"""
文件操作管理器
负责文件拉取、推送、截图等文件相关操作
"""

import os
import pathlib
from PyQt5.QtWidgets import QFileDialog, QInputDialog

from logger_manager import log_button_click, log_method_result, get_logger

logger = get_logger("ADBTools.FileOperations")


class FileOperationsManager:
    """文件操作管理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window
    
    @property
    def textBrowser(self):
        return self.main_window.textBrowser
    
    def show_screenshot_dialog(self):
        """截取设备屏幕"""
        device_id = self.main_window.get_selected_device()
        devices_id_lst = self.main_window.get_new_device_lst()
        
        log_button_click("get_screenshot_button", "截取设备屏幕")

        if device_id in devices_id_lst:
            file_path, _ = QFileDialog.getSaveFileName(
                self.main_window, "保存截图", "", "PNG Files (*.png);;All Files (*)"
            )
            if file_path:
                logger.info(f"保存截图到: {file_path}")
                
                try:
                    if self.main_window.connection_mode == 'u2' and self.main_window.d:
                        from Function_Moudle.devices_screen_thread import DevicesScreenThread
                        self.main_window.devices_screen_thread = DevicesScreenThread(
                            self.main_window.d, file_path
                        )
                        self.main_window.devices_screen_thread.signal.connect(self.textBrowser.append)
                        self.main_window.devices_screen_thread.start()
                    elif self.main_window.connection_mode == 'adb':
                        from Function_Moudle.adb_screenshot_thread import ADBScreenshotThread
                        self.main_window.devices_screen_thread = ADBScreenshotThread(device_id, file_path)
                        self.main_window.devices_screen_thread.signal.connect(self.textBrowser.append)
                        self.main_window.devices_screen_thread.start()
                    else:
                        log_method_result("show_screenshot_dialog", False, "设备未连接")
                        self.textBrowser.append("设备未连接！")
                        return
                    
                    log_method_result("show_screenshot_dialog", True, f"截图线程已启动: {os.path.basename(file_path)}")
                except Exception as e:
                    log_method_result("show_screenshot_dialog", False, str(e))
                    self.textBrowser.append(f"启动截图线程失败: {e}")
            else:
                logger.info("用户取消文件选择")
        else:
            log_method_result("show_screenshot_dialog", False, "设备未连接")
            self.textBrowser.append("设备未连接！")

    def show_uninstall_dialog(self):
        """卸载应用"""
        device_id = self.main_window.get_selected_device()
        devices_id_lst = self.main_window.get_new_device_lst()
        
        log_button_click("adb_uninstall_button", "卸载应用")

        if device_id in devices_id_lst:
            package_name, ok = QInputDialog.getText(
                self.main_window, "输入应用包名", "请输入要卸载的应用包名："
            )
            if ok and package_name:
                logger.info(f"卸载应用: {package_name}")
                
                try:
                    if self.main_window.connection_mode == 'u2' and self.main_window.d:
                        from Function_Moudle.show_uninstall_thread import ShowUninstallThread
                        self.main_window.uninstall_thread = ShowUninstallThread(
                            self.main_window.d, package_name
                        )
                    elif self.main_window.connection_mode == 'adb':
                        from Function_Moudle.adb_show_uninstall_thread import ADBShowUninstallThread
                        self.main_window.uninstall_thread = ADBShowUninstallThread(device_id, package_name)
                    else:
                        log_method_result("show_uninstall_dialog", False, "设备未连接")
                        self.textBrowser.append("设备未连接！")
                        return
                    
                    self.main_window.uninstall_thread.progress_signal.connect(self.textBrowser.append)
                    self.main_window.uninstall_thread.result_signal.connect(self.textBrowser.append)
                    self.main_window.uninstall_thread.error_signal.connect(self.textBrowser.append)
                    self.main_window.uninstall_thread.start()
                    
                    log_method_result("show_uninstall_dialog", True, f"卸载线程已启动: {package_name}")
                except Exception as e:
                    log_method_result("show_uninstall_dialog", False, str(e))
                    self.textBrowser.append(f"启动卸载线程失败: {e}")
            else:
                logger.info("用户取消输入或输入为空")
                self.textBrowser.append("已取消！")
        else:
            log_method_result("show_uninstall_dialog", False, "设备未连接")
            self.textBrowser.append("未连接设备！")

    def show_pull_file_dialog(self):
        """从设备拉取文件"""
        device_id = self.main_window.get_selected_device()
        devices_id_lst = self.main_window.get_new_device_lst()
        
        log_button_click("adb_pull_file_button", "从设备拉取文件")

        if device_id in devices_id_lst:
            try:
                file_path_on_device, ok = QInputDialog.getText(
                    self.main_window, "输入设备文件路径", "请输入车机上的文件路径:"
                )
                file_path = pathlib.Path(file_path_on_device)
                apk_file_name = pathlib.Path(file_path).name
                if ok and file_path_on_device:
                    local_path = QFileDialog.getExistingDirectory(self.main_window, "选择文件夹", ".")
                    if local_path:
                        logger.info(f"拉取文件: {file_path_on_device} -> {local_path}")
                        
                        if self.main_window.connection_mode == 'u2' and self.main_window.d:
                            from Function_Moudle.pull_files_thread import PullFilesThread
                            self.main_window.pull_files_thread = PullFilesThread(
                                self.main_window.d, file_path_on_device, local_path, apk_file_name
                            )
                        else:
                            from Function_Moudle.adb_pull_files_thread import ADBPullFilesThread
                            self.main_window.pull_files_thread = ADBPullFilesThread(
                                device_id, file_path_on_device, local_path, apk_file_name
                            )
                        
                        self.main_window.pull_files_thread.signal.connect(self.textBrowser.append)
                        self.main_window.pull_files_thread.start()
                        
                        log_method_result("show_pull_file_dialog", True, f"拉取线程已启动: {apk_file_name}")
                    else:
                        logger.info("用户取消文件夹选择")
                else:
                    logger.info("用户取消输入或输入为空")
            except Exception as e:
                log_method_result("show_pull_file_dialog", False, str(e))
                self.textBrowser.append(f"初始化线程失败: {e}")
        else:
            log_method_result("show_pull_file_dialog", False, "设备未连接")
            self.textBrowser.append("设备未连接！")

    def show_install_file_dialog(self):
        """安装应用"""
        device_id = self.main_window.get_selected_device()
        devices_id_lst = self.main_window.get_new_device_lst()
        
        log_button_click("adb_install_button", "安装应用")

        if device_id in devices_id_lst:
            package_path, ok = QFileDialog.getOpenFileName(
                self.main_window, "选择应用安装包", "", "APK Files (*.apk);;All Files (*)"
            )
            if ok and package_path:
                logger.info(f"选择文件: {package_path}")
                
                try:
                    # 检查连接状态
                    if self.main_window.connection_mode == 'u2':
                        if not self.main_window.d:
                            self.main_window.connection_mode = 'adb'
                            self.textBrowser.append("U2连接不可用，切换到ADB模式")
                    
                    from Function_Moudle.install_file_thread import InstallFileThread
                    # InstallFileThread 内部使用 adb install 命令，传入 device_id
                    self.main_window.install_file_thread = InstallFileThread(device_id, package_path)
                    self.main_window.install_file_thread.progress_signal.connect(self.textBrowser.append)
                    self.main_window.install_file_thread.signal_status.connect(self.textBrowser.append)
                    self.main_window.install_file_thread.start()
                    
                    log_method_result("show_install_file_dialog", True, f"安装线程已启动: {os.path.basename(package_path)}")
                except Exception as e:
                    log_method_result("show_install_file_dialog", False, str(e))
                    self.textBrowser.append(f"启动安装线程失败: {e}")
            else:
                logger.info("用户取消文件选择")
        else:
            log_method_result("show_install_file_dialog", False, "设备未连接")
            self.textBrowser.append("设备未连接！")

    def show_push_file_dialog(self):
        """推送文件到设备"""
        device_id = self.main_window.get_selected_device()
        devices_id_lst = self.main_window.get_new_device_lst()
        
        log_button_click("adb_push_file_button", "推送文件到设备")

        if device_id in devices_id_lst:
            local_file_path, ok1 = QFileDialog.getOpenFileName(
                self.main_window, "选择要推送的文件", "", "All Files (*)"
            )
            if ok1 and local_file_path:
                target_path, ok2 = QInputDialog.getText(
                    self.main_window, "目标路径", "请输入设备上的目标路径:",
                    text="/sdcard/Download/"
                )
                if ok2 and target_path:
                    logger.info(f"推送文件: {local_file_path} -> {target_path}")
                    
                    try:
                        if self.main_window.connection_mode == 'u2' and self.main_window.d:
                            self.main_window.d.push(local_file_path, target_path)
                            self.textBrowser.append(f"文件推送成功: {os.path.basename(local_file_path)}")
                            log_method_result("show_push_file_dialog", True, f"推送成功: {os.path.basename(local_file_path)}")
                        elif self.main_window.connection_mode == 'adb':
                            import adb_utils
                            result = adb_utils.push_file(local_file_path, target_path, device_id)
                            self.textBrowser.append(result)
                            log_method_result("show_push_file_dialog", True, f"推送完成")
                        else:
                            log_method_result("show_push_file_dialog", False, "设备未连接")
                            self.textBrowser.append("设备未连接！")
                    except Exception as e:
                        log_method_result("show_push_file_dialog", False, str(e))
                        self.textBrowser.append(f"推送文件失败: {e}")
                else:
                    logger.info("用户取消输入或输入为空")
            else:
                logger.info("用户取消文件选择")
        else:
            log_method_result("show_push_file_dialog", False, "设备未连接")
            self.textBrowser.append("设备未连接！")