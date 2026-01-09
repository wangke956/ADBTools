from PyQt5.QtWidgets import (QMainWindow, QFileDialog, QInputDialog, QMessageBox)
import io
import subprocess
from Function_Moudle.adb_root_wrapper_thread import AdbRootWrapperThread
import uiautomator2 as u2
import os
from PyQt5 import uic
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QFont, QResizeEvent
from PyQt5.QtWidgets import QMainWindow, QApplication, QSizePolicy, QPushButton, QWidget, QComboBox
from adb_utils import adb_utils

class TextEditOutputStream(io.TextIOBase):  # 继承 io.TextIOBase 类

    def __init__(self, textbrowser):
        super().__init__()  # 调用父类构造函数
        self.textBrowser = textbrowser  # 绑定 textEdit
        self.buffer = io.StringIO()  # 创建一个缓存区
        self.clear_before_write = False  # 添加一个标志来控制是否清空内容

    def write(self, s):
        if self.clear_before_write:
            self.textBrowser.clear()  # 如果标志为 True，则清空 textEdit 的内容
            self.clear_before_write = False  # 重置标志
        self.buffer.write(s)
        self.textBrowser.append(s)
        return len(s)

    def flush(self):
        self.buffer.flush()

    def set_clear_before_write(self, clear):
        self.clear_before_write = clear


# noinspection DuplicatedCode,SpellCheckingInspection
class ADB_Mainwindow(QMainWindow):
    # 软件版本常量
    VERSION = "1.3"
    
    def __init__(self, parent=None):
        super(ADB_Mainwindow, self).__init__(parent)
        self.app_name = None
        self.devices_screen_thread = None
        self.pull_files_thread = None
        self.releasenote_package_version = None
        self.releasenote_dict = None
        self.app_version_check_thread = None
        self.releasenote_file = None
        self.voice_record_thread = None
        self.file_path = None
        self.PullLogSaveThread = None
        self.install_file_thread = None
        self.simulate_long_press_dialog_thread = None
        self.GetForegroundPackageThread = None
        self.input_text_thread = None
        self.Clear_app_cache_thread = None
        self.Force_app_thread = None
        self.uninstall_thread = None
        self.reboot_thread = None
        self.view_apk_thread = None
        self.skip_power_limit_thread = None
        self.upgrade_page_thread = None
        self.update_thread = None
        self.adb_root_thread = None
        self.get_running_app_info_thread = None
        self.check_vr_env_thread = None
        self.mzs3ett_thread = None
        self.check_vr_network_thread = None
        self.vr_thread = None
        self.list_package_thread = None
        self.input_keyevent_287_thread = None
        self.engineering_thread = None
        self.app_action_thread = None
        self.verity_thread = None
        self.batch_install_thread = None

        # 动态加载ui文件
        uic.loadUi('adbtool.ui', self)
        # 假设这里是初始化UI控件的部分，使用findChild方法获取控件
        from PyQt5 import QtWidgets
        self.RefreshButton = self.findChild(QtWidgets.QPushButton, 'RefreshButton')
        self.ComboxButton = self.findChild(QtWidgets.QComboBox, 'ComboxButton')
        self.vr_keyevent_combo = self.findChild(QtWidgets.QComboBox, 'vr_keyevent_combo')
        self.datong_factory_button = self.findChild(QtWidgets.QPushButton, 'datong_factory_button')
        self.datong_disable_verity_button = self.findChild(QtWidgets.QPushButton, 'datong_disable_verity_button')
        self.datong_enable_verity_button = self.findChild(QtWidgets.QPushButton, 'datong_enable_verity_button')
        self.datong_batch_install_button = self.findChild(QtWidgets.QPushButton, 'datong_batch_install_button')
        self.datong_batch_install_test_button = self.findChild(QtWidgets.QPushButton, 'datong_batch_install_test_button')
        self.datong_input_password_button = self.findChild(QtWidgets.QPushButton, 'datong_input_password_button')
        self.datong_open_telenav_engineering_button = self.findChild(QtWidgets.QPushButton, 'datong_open_telenav_engineering_button')
        self.d = None
        self.device_id = None
        self.connection_mode = None  # 'u2' 或 'adb'
        # 重定向输出流为textBrowser
        self.text_edit_output_stream = TextEditOutputStream(self.textBrowser)
        try:
            # 刷新设备列表（refresh_devices方法内部会尝试u2连接）
            self.refresh_devices()
        except Exception as e:
            self.textBrowser.append(str(e))
        self.ComboxButton.activated[str].connect(self.on_combobox_changed)
        self.view_apk_path.clicked.connect(self.view_apk_path_wrapper)  # 显示应用安装路径
        self.input_text_via_adb_button.clicked.connect(self.show_input_text_dialog)  # 输入文本
        self.get_screenshot_button.clicked.connect(self.show_screenshot_dialog)  # 截图
        self.force_stop_app.clicked.connect(self.show_force_stop_app_dialog)  # 强制停止应用
        self.adb_uninstall_button.clicked.connect(self.show_uninstall_dialog)  # 卸载应用
        self.adb_pull_file_button.clicked.connect(self.show_pull_file_dialog)  # 拉取文件
        self.reboot_adb_service_button.clicked.connect(self.show_simulate_long_press_dialog)  # 模拟长按
        self.adb_install_button.clicked.connect(self.show_install_file_dialog)  # 安装应用
        self.clear_app_cache_button.clicked.connect(self.show_clear_app_cache_dialog)  # 清除应用缓存
        self.app_package_and_activity.clicked.connect(self.get_foreground_package)
        self.adb_push_file_button.clicked.connect(self.show_push_file_dialog)  # 推送文件
        self.button_reboot.clicked.connect(self.reboot_device)  # 重启设备
        self.RefreshButton.clicked.connect(self.refresh_devices)  # 刷新设备列表
        self.adb_root_button.clicked.connect(self.adb_root_wrapper)  # 以 root 权限运行 ADB
        self.start_app.clicked.connect(self.start_app_action)  # 启动应用
        self.get_running_app_info_button.clicked.connect(self.get_running_app_info)  # 获取当前运行的应用信息
        self.aapt_getpackagename_button.clicked.connect(self.aapt_getpackage_name_dilog)  # 获取apk包名
        self.textBrowser.textChanged.connect(self.scroll_to_bottom)  # 自动滚动到底部
        self.switch_vr_env_button.clicked.connect(self.switch_vr_env)  # 切换VR环境
        self.VR_nework_check_button.clicked.connect(self.check_vr_network)  # 检查VR网络
        self.activate_VR_button.clicked.connect(self.activate_vr)  # 激活VR
        self.list_package_button.clicked.connect(self.list_package)
        self.skipping_powerlimit_button.clicked.connect(self.skip_power_limit)  # 跳过电源挡位限制
        self.enter_engineering_mode_button.clicked.connect(self.open_engineering_mode)  # 进入工程模式
        self.AS33_CR_enter_engineering_mode_button.clicked.connect(self.as33_cr_enter_engineering)
        self.open_update_page_button.clicked.connect(self.open_soimt_update)  # 打开资源升级页面
        self.browse_log_save_path_button.clicked.connect(self.browse_log_save_path)  # 浏览日志保存路径
        self.pull_log_button.clicked.connect(self.pull_log)  # 拉取日志
        self.open_path_buttom.clicked.connect(self.open_path)  # 打开文件所在目录
        self.voice_start_record_button.clicked.connect(self.voice_start_record)  # 开始语音录制
        self.voice_stop_record_button.clicked.connect(self.voice_stop_record)  # 停止语音录制
        self.voice_pull_record_file_button.clicked.connect(self.voice_pull_record_file)  # 拉取录音文件
        self.remove_record_file_button.clicked.connect(self.remove_voice_record_file)  # 删除语音录制文件
        self.select_releasenote_excel_button.clicked.connect(self.select_releasenote_excel)  # 选择集成清单文件
        self.start_check_button.clicked.connect(self.app_version_check)
        self.set_vr_server_timout.clicked.connect(self.set_vr_timeout)
        self.upgrade_page_button.clicked.connect(self.open_yf_page)
        self.datong_factory_button.clicked.connect(self.datong_factory_action)  # 拉起中环工厂
        self.datong_disable_verity_button.clicked.connect(self.datong_disable_verity_action)  # 禁用verity校验 (adb disable-verity)
        self.datong_enable_verity_button.clicked.connect(self.datong_enable_verity_action)  # 启用verity校验 (adb enable-verity)
        self.datong_batch_install_button.clicked.connect(self.datong_batch_install_action)  # 批量安装APK文件
        self.datong_batch_install_test_button.clicked.connect(self.datong_batch_verify_version_action)  # 验证批量推包版本号
        self.datong_input_password_button.clicked.connect(self.datong_input_password_action)  # 一键输入密码
        self.datong_open_telenav_engineering_button.clicked.connect(self.datong_open_telenav_engineering_action)  # 打开泰维地图工程模式
        
        # 添加配置菜单
        self.add_config_menu()
        
        # 添加配置按钮（如果UI中有）
        try:
            self.config_button = self.findChild(QtWidgets.QPushButton, 'config_button')
            if self.config_button:
                self.config_button.clicked.connect(self.open_config_dialog)
        except:
            pass
        
        # 窗口缩放功能初始化
        self.init_window_scaling()
        
        # 设置窗口标题包含版本号
        self.setWindowTitle(f"ADBTools v{self.VERSION}")

    def init_window_scaling(self):
        """初始化窗口缩放功能"""
        # 存储原始窗口大小作为基准
        self.original_size = QSize(584, 601)  # UI文件中定义的原始大小
        self.current_size = self.size()
        
        # 存储需要调整字体的控件类型
        self.scalable_widget_types = ['QPushButton', 'QLabel', 'QComboBox', 'QTabWidget', 'QTextBrowser']
        
        # 基础字体大小（对应原始窗口大小）
        self.base_font_size = 11  # 基础字体大小（从9增加到11）
        
        # 设置窗口缩放策略
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 获取中央部件并设置缩放策略
        central_widget = self.centralWidget()
        if central_widget:
            central_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def add_config_menu(self):
        """添加配置菜单"""
        from PyQt5 import QtWidgets
        menubar = self.menuBar()
        
        # 设置菜单
        settings_menu = menubar.addMenu('设置')
        
        # ADB配置
        adb_config_action = QtWidgets.QAction('ADB配置', self)
        adb_config_action.triggered.connect(self.open_config_dialog)
        settings_menu.addAction(adb_config_action)
        
        # 检查更新
        check_update_action = QtWidgets.QAction('检查更新', self)
        check_update_action.triggered.connect(self.check_for_updates)
        settings_menu.addAction(check_update_action)
        
        # 分隔线
        settings_menu.addSeparator()
        
        # 关于
        about_action = QtWidgets.QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        settings_menu.addAction(about_action)

    def open_config_dialog(self):
        """打开配置对话框"""
        try:
            from config_dialog import ConfigDialog
            dialog = ConfigDialog(self)
            dialog.exec_()
        except Exception as e:
            self.textBrowser.append(f"打开配置对话框失败: {e}")

    def show_about(self):
        """显示关于信息"""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.about(self, "关于 ADBTools", 
            f"ADBTools v{self.VERSION}\n\n"
            "一个功能强大的ADB调试工具\n"
            "支持多种设备管理功能\n\n"
            "作者: 王克\n"
            "GitHub: https://github.com/wangke956/ADBTools")

    def check_for_updates(self):
        """检查更新"""
        try:
            from Function_Moudle.check_update_thread import CheckUpdateThread
            
            # 创建检查更新线程
            self.check_update_thread = CheckUpdateThread(current_version=self.VERSION)
            
            # 连接信号
            self.check_update_thread.progress_signal.connect(self.textBrowser.append)
            self.check_update_thread.error_signal.connect(self.textBrowser.append)
            self.check_update_thread.update_available_signal.connect(self.handle_update_available)
            self.check_update_thread.no_update_signal.connect(self.handle_no_update)
            self.check_update_thread.check_failed_signal.connect(self.handle_check_failed)
            
            # 启动线程
            self.check_update_thread.start()
            
            self.textBrowser.append("正在检查更新，请稍候...")
            
        except ImportError as e:
            self.textBrowser.append(f"无法导入检查更新模块: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "检查更新失败", 
                f"无法启动检查更新功能:\n\n{str(e)}\n\n请确保requests库已安装。")
        except Exception as e:
            self.textBrowser.append(f"启动检查更新失败: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "检查更新失败", 
                f"启动检查更新时发生错误:\n\n{str(e)}")

    def handle_update_available(self, update_info):
        """处理有更新可用的信号"""
        from PyQt5.QtWidgets import QMessageBox
        
        current_version = update_info.get('current_version', '未知')
        latest_version = update_info.get('latest_version', '未知')
        release_name = update_info.get('release_name', '')
        release_body = update_info.get('release_body', '')
        html_url = update_info.get('html_url', 'https://github.com/wangke956/ADBTools')
        is_fallback = update_info.get('is_fallback', False)
        setup_file = update_info.get('setup_file')
        
        # 构建消息
        if is_fallback:
            message = f"GitHub仓库信息\n\n"
            message += f"当前版本: v{current_version}\n"
            message += f"仓库状态: 尚未创建发布版本\n\n"
        else:
            message = f"发现新版本！\n\n"
            message += f"当前版本: v{current_version}\n"
            message += f"最新版本: v{latest_version}\n\n"
        
        if release_name:
            message += f"名称: {release_name}\n\n"
        
        if release_body:
            # 限制更新说明的长度
            if len(release_body) > 300:
                release_body = release_body[:300] + "..."
            message += f"说明:\n{release_body}\n\n"
        
        # 添加安装文件信息
        if setup_file and not is_fallback:
            file_name = setup_file.get('name', '未知文件')
            file_size = setup_file.get('size', 0)
            
            # 格式化文件大小
            def format_size(size):
                if size < 1024:
                    return f"{size} B"
                elif size < 1024 * 1024:
                    return f"{size/1024:.1f} KB"
                elif size < 1024 * 1024 * 1024:
                    return f"{size/(1024*1024):.1f} MB"
                else:
                    return f"{size/(1024*1024*1024):.1f} GB"
                    
            size_str = format_size(file_size)
            message += f"安装文件: {file_name} ({size_str})\n\n"
        
        message += f"GitHub地址: {html_url}\n\n"
        
        if is_fallback:
            message += "此仓库尚未创建发布版本。是否要打开浏览器访问GitHub仓库？"
            
            # 显示更新提示对话框
            title = "GitHub仓库信息"
            reply = QMessageBox.information(
                self,
                title,
                message,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                # 打开浏览器
                import webbrowser
                try:
                    webbrowser.open(html_url)
                except Exception as e:
                    self.textBrowser.append(f"打开浏览器失败: {e}")
                    QMessageBox.warning(self, "打开浏览器失败", 
                        f"无法打开浏览器访问页面:\n\n{str(e)}\n\n请手动访问: {html_url}")
        else:
            # 有安装文件可用，提供更多选项
            if setup_file:
                # 创建自定义对话框
                from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
                
                dialog = QDialog(self)
                dialog.setWindowTitle("发现新版本")
                dialog.setMinimumWidth(400)
                
                layout = QVBoxLayout()
                
                # 消息标签
                msg_label = QLabel(message)
                msg_label.setWordWrap(True)
                layout.addWidget(msg_label)
                
                # 按钮布局
                button_layout = QHBoxLayout()
                
                # 自动下载并安装按钮
                auto_download_btn = QPushButton("自动下载并安装")
                auto_download_btn.clicked.connect(lambda: self._start_auto_download(update_info, dialog))
                
                # 手动下载按钮
                manual_download_btn = QPushButton("手动下载")
                manual_download_btn.clicked.connect(lambda: self._open_browser(html_url, dialog))
                
                # 取消按钮
                cancel_btn = QPushButton("取消")
                cancel_btn.clicked.connect(dialog.reject)
                
                button_layout.addWidget(auto_download_btn)
                button_layout.addWidget(manual_download_btn)
                button_layout.addWidget(cancel_btn)
                
                layout.addLayout(button_layout)
                dialog.setLayout(layout)
                
                dialog.exec_()
            else:
                # 没有安装文件，只有手动下载选项
                message += "是否要打开浏览器访问下载页面？"
                
                reply = QMessageBox.information(
                    self,
                    "发现新版本",
                    message,
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    self._open_browser(html_url)

    def _open_browser(self, url, dialog=None):
        """打开浏览器"""
        import webbrowser
        try:
            webbrowser.open(url)
            if dialog:
                dialog.accept()
        except Exception as e:
            self.textBrowser.append(f"打开浏览器失败: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "打开浏览器失败", 
                f"无法打开浏览器访问页面:\n\n{str(e)}\n\n请手动访问: {url}")
            if dialog:
                dialog.reject()
                
    def _start_auto_download(self, update_info, dialog=None):
        """启动自动下载"""
        try:
            from Function_Moudle.download_dialog import DownloadDialog
            
            # 创建下载对话框
            download_dialog = DownloadDialog(self, update_info)
            
            if dialog:
                dialog.accept()
                
            # 显示下载对话框
            download_dialog.exec_()
            
        except ImportError as e:
            self.textBrowser.append(f"无法导入下载模块: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "自动下载失败", 
                f"无法启动自动下载功能:\n\n{str(e)}\n\n请尝试手动下载。")
            if dialog:
                dialog.reject()
        except Exception as e:
            self.textBrowser.append(f"启动自动下载失败: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "自动下载失败", 
                f"启动自动下载时发生错误:\n\n{str(e)}")
            if dialog:
                dialog.reject()

    def handle_no_update(self, message):
        """处理无更新的信号"""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "检查更新", message)

    def handle_check_failed(self, error_message):
        """处理检查更新失败的信号"""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.warning(self, "检查更新失败", 
            f"检查更新时发生错误:\n\n{error_message}\n\n"
            "请检查网络连接后重试。")

    def open_yf_page(self):
        self.start_app_action(app_name = "com.yfve.usbupdate")

    def open_soimt_update(self):
        self.start_app_action(app_name = "com.saicmotor.update")

    def open_engineering_mode(self):
        self.start_app_action(app_name = "com.saicmotor.hmi.engmode")

    def as33_cr_enter_engineering(self):
        self.start_app_action(app_name = "com.saicmotor.diag")

    def datong_factory_action(self):
        """拉起中环工厂应用"""
        self.start_app_action(app_name = "com.zhonghuan.factory")

    def datong_verity_action(self):
        """执行adb enable-verity和adb disable-verity命令"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        if device_id in devices_id_lst:
            try:
                # 弹出确认对话框
                from PyQt5.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    self, 
                    '确认执行verity命令',
                    f'是否要在设备 {device_id} 上执行adb disable-verity和adb enable-verity命令？\n\n'
                    '注意：执行此操作可能需要设备重启才能生效。',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # 根据连接模式创建相应的线程
                    if self.connection_mode == 'u2':
                        from Function_Moudle.adb_verity_thread import ADBVerityThread
                        self.verity_thread = ADBVerityThread(
                            device_id, 
                            connection_mode='u2',
                            u2_device=self.d
                        )
                    elif self.connection_mode == 'adb':
                        from Function_Moudle.adb_verity_thread import ADBVerityThread
                        self.verity_thread = ADBVerityThread(
                            device_id, 
                            connection_mode='adb'
                        )
                    else:
                        self.textBrowser.append("设备未连接！")
                        return
                    
                    # 连接信号
                    self.verity_thread.progress_signal.connect(self.textBrowser.append)
                    self.verity_thread.error_signal.connect(self.textBrowser.append)
                    self.verity_thread.result_signal.connect(self.textBrowser.append)
                    
                    # 启动线程
                    self.verity_thread.start()
                else:
                    self.textBrowser.append("用户取消执行verity命令")
                    
            except Exception as e:
                self.textBrowser.append(f"启动verity命令线程失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def datong_disable_verity_action(self):
        """执行adb disable-verity命令"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        if device_id in devices_id_lst:
            try:
                # 弹出确认对话框
                from PyQt5.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    self, 
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
                    # 根据连接模式创建相应的线程
                    if self.connection_mode == 'u2':
                        from Function_Moudle.adb_verity_thread import ADBDisableVerityThread
                        self.disable_verity_thread = ADBDisableVerityThread(
                            device_id, 
                            connection_mode='u2',
                            u2_device=self.d
                        )
                    elif self.connection_mode == 'adb':
                        from Function_Moudle.adb_verity_thread import ADBDisableVerityThread
                        self.disable_verity_thread = ADBDisableVerityThread(
                            device_id, 
                            connection_mode='adb'
                        )
                    else:
                        self.textBrowser.append("设备未连接！")
                        return
                    
                    # 连接信号
                    self.disable_verity_thread.progress_signal.connect(self.textBrowser.append)
                    self.disable_verity_thread.error_signal.connect(self.textBrowser.append)
                    self.disable_verity_thread.result_signal.connect(self.handle_disable_verity_result)
                    
                    # 启动线程
                    self.disable_verity_thread.start()
                else:
                    self.textBrowser.append("用户取消执行adb disable-verity命令")
                    
            except Exception as e:
                self.textBrowser.append(f"启动adb disable-verity命令线程失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def handle_disable_verity_result(self, result_message):
        """处理adb disable-verity执行结果"""
        self.textBrowser.append(result_message)
        
        # 检查是否执行成功
        if "执行完成" in result_message or "成功" in result_message:
            # 弹出成功提示对话框
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
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

    def datong_enable_verity_action(self):
        """执行adb enable-verity命令"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        if device_id in devices_id_lst:
            try:
                # 弹出确认对话框
                from PyQt5.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    self, 
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
                    # 根据连接模式创建相应的线程
                    if self.connection_mode == 'u2':
                        from Function_Moudle.adb_verity_thread import ADBEnableVerityThread
                        self.enable_verity_thread = ADBEnableVerityThread(
                            device_id, 
                            connection_mode='u2',
                            u2_device=self.d
                        )
                    elif self.connection_mode == 'adb':
                        from Function_Moudle.adb_verity_thread import ADBEnableVerityThread
                        self.enable_verity_thread = ADBEnableVerityThread(
                            device_id, 
                            connection_mode='adb'
                        )
                    else:
                        self.textBrowser.append("设备未连接！")
                        return
                    
                    # 连接信号
                    self.enable_verity_thread.progress_signal.connect(self.textBrowser.append)
                    self.enable_verity_thread.error_signal.connect(self.textBrowser.append)
                    self.enable_verity_thread.result_signal.connect(self.handle_enable_verity_result)
                    
                    # 启动线程
                    self.enable_verity_thread.start()
                else:
                    self.textBrowser.append("用户取消执行adb enable-verity命令")
                    
            except Exception as e:
                self.textBrowser.append(f"启动adb enable-verity命令线程失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def handle_enable_verity_result(self, result_message):
        """处理adb enable-verity执行结果"""
        self.textBrowser.append(result_message)
        
        # 检查是否执行成功
        if "执行完成" in result_message or "成功" in result_message:
            # 弹出成功提示对话框
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
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

    def datong_batch_install_action(self):
        """批量安装APK文件"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        if device_id in devices_id_lst:
            try:
                # 弹出文件夹选择框
                from PyQt5.QtWidgets import QFileDialog, QMessageBox
                folder_path = QFileDialog.getExistingDirectory(
                    self,
                    "选择APK文件夹",
                    "",  # 默认路径为空
                    QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
                )
                
                if not folder_path:
                    self.textBrowser.append("用户取消选择文件夹")
                    return
                
                # 检查文件夹是否存在
                import os
                if not os.path.exists(folder_path):
                    self.textBrowser.append(f"文件夹不存在: {folder_path}")
                    return
                
                if not os.path.isdir(folder_path):
                    self.textBrowser.append(f"路径不是文件夹: {folder_path}")
                    return
                
                # 创建自定义对话框询问是否允许降级安装
                from PyQt5.QtWidgets import QCheckBox, QVBoxLayout, QDialog, QDialogButtonBox, QLabel
                
                class BatchInstallDialog(QDialog):
                    def __init__(self, parent=None, device_id="", folder_path=""):
                        super().__init__(parent)
                        self.setWindowTitle('确认批量安装')
                        
                        layout = QVBoxLayout()
                        
                        # 添加说明标签
                        info_label = QLabel(
                            f'是否要在设备 {device_id} 上批量安装文件夹中的APK文件？\n\n'
                            f'文件夹路径: {folder_path}\n\n'
                            '注意：\n'
                            '1. 对于普通APK文件，将执行adb install操作\n'
                            '2. 对于特殊包名的APK（如@com.saicmotor.adapterservice、@com.saicmotor.voiceservice）：\n'
                            '   - 先执行adb shell pm path查询安装路径\n'
                            '   - 根据配置文件决定是否删除原文件\n'
                            '   - 将本地apk push到原路径，保持原文件名不变\n'
                            '3. 当前配置的特殊包名处理方式：\n'
                            '   - @com.saicmotor.adapterservice：删除原文件后推送\n'
                            '   - @com.saicmotor.voiceservice：直接推送（不删除）\n'
                            '4. 操作可能需要较长时间，请耐心等待'
                        )
                        layout.addWidget(info_label)
                        
                        # 添加降级安装复选框
                        self.allow_downgrade_checkbox = QCheckBox("允许降级安装 (使用 -d 参数)")
                        self.allow_downgrade_checkbox.setToolTip("勾选此项将允许安装版本号低于当前已安装版本的APK")
                        layout.addWidget(self.allow_downgrade_checkbox)
                        
                        # 添加按钮
                        button_box = QDialogButtonBox(QDialogButtonBox.Yes | QDialogButtonBox.No)
                        button_box.accepted.connect(self.accept)
                        button_box.rejected.connect(self.reject)
                        layout.addWidget(button_box)
                        
                        self.setLayout(layout)
                
                # 显示对话框
                dialog = BatchInstallDialog(self, device_id, folder_path)
                result = dialog.exec_()
                
                if result == QDialog.Accepted:
                    # 获取用户选择的降级安装选项
                    allow_downgrade = dialog.allow_downgrade_checkbox.isChecked()
                    
                    # 根据连接模式创建相应的线程
                    if self.connection_mode == 'u2':
                        from Function_Moudle.adb_batch_install_thread import ADBBatchInstallThread
                        self.batch_install_thread = ADBBatchInstallThread(
                            device_id, 
                            folder_path,
                            connection_mode='u2',
                            u2_device=self.d,
                            allow_downgrade=allow_downgrade
                        )
                    elif self.connection_mode == 'adb':
                        from Function_Moudle.adb_batch_install_thread import ADBBatchInstallThread
                        self.batch_install_thread = ADBBatchInstallThread(
                            device_id, 
                            folder_path,
                            connection_mode='adb',
                            allow_downgrade=allow_downgrade
                        )
                    else:
                        self.textBrowser.append("设备未连接！")
                        return
                    
                    # 连接信号
                    self.batch_install_thread.progress_signal.connect(self.textBrowser.append)
                    self.batch_install_thread.error_signal.connect(self.textBrowser.append)
                    self.batch_install_thread.result_signal.connect(self.textBrowser.append)
                    self.batch_install_thread.realtime_output_signal.connect(self.textBrowser.append)
                    
                    # 启动线程
                    self.batch_install_thread.start()
                else:
                    self.textBrowser.append("用户取消批量安装")
                    
            except Exception as e:
                self.textBrowser.append(f"启动批量安装线程失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def datong_batch_install_test_action(self):
        """测试批量安装功能 - 打印所有流程中的值和命令"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        if device_id in devices_id_lst:
            try:
                # 弹出文件夹选择框
                from PyQt5.QtWidgets import QFileDialog, QMessageBox
                folder_path = QFileDialog.getExistingDirectory(
                    self,
                    "选择APK文件夹（测试模式）",
                    "",  # 默认路径为空
                    QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
                )
                
                if not folder_path:
                    self.textBrowser.append("用户取消选择文件夹")
                    return
                
                # 检查文件夹是否存在
                import os
                if not os.path.exists(folder_path):
                    self.textBrowser.append(f"文件夹不存在: {folder_path}")
                    return
                
                if not os.path.isdir(folder_path):
                    self.textBrowser.append(f"路径不是文件夹: {folder_path}")
                    return
                
                # 弹出确认对话框
                reply = QMessageBox.question(
                    self, 
                    '确认测试批量安装',
                    f'是否要在设备 {device_id} 上测试批量安装功能？\n\n'
                    f'文件夹路径: {folder_path}\n\n'
                    '注意：\n'
                    '1. 此功能仅用于测试，不会实际安装任何APK\n'
                    '2. 将打印所有流程中的值、命令和状态\n'
                    '3. 用于验证逻辑是否正确，防止误操作损坏设备',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # 创建测试线程
                    from Function_Moudle.adb_batch_install_test_thread import ADBBatchInstallTestThread
                    
                    if self.connection_mode == 'u2':
                        self.batch_install_test_thread = ADBBatchInstallTestThread(
                            device_id, 
                            folder_path,
                            connection_mode='u2',
                            u2_device=self.d
                        )
                    elif self.connection_mode == 'adb':
                        self.batch_install_test_thread = ADBBatchInstallTestThread(
                            device_id, 
                            folder_path,
                            connection_mode='adb'
                        )
                    else:
                        self.textBrowser.append("设备未连接！")
                        return
                    
                    # 连接信号
                    self.batch_install_test_thread.progress_signal.connect(self.textBrowser.append)
                    self.batch_install_test_thread.error_signal.connect(self.textBrowser.append)
                    self.batch_install_test_thread.result_signal.connect(self.textBrowser.append)
                    self.batch_install_test_thread.debug_signal.connect(self.textBrowser.append)
                    
                    # 启动线程
                    self.batch_install_test_thread.start()
                else:
                    self.textBrowser.append("用户取消测试")
                    
            except Exception as e:
                self.textBrowser.append(f"启动批量安装测试线程失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def datong_batch_verify_version_action(self):
        """验证批量推包版本号 - 检查APK文件版本号与设备中版本号是否一致"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        if device_id in devices_id_lst:
            try:
                # 弹出文件夹选择框
                from PyQt5.QtWidgets import QFileDialog, QMessageBox
                folder_path = QFileDialog.getExistingDirectory(
                    self,
                    "选择APK文件夹（验证版本号）",
                    "",  # 默认路径为空
                    QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
                )
                
                if not folder_path:
                    self.textBrowser.append("用户取消选择文件夹")
                    return
                
                # 检查文件夹是否存在
                import os
                if not os.path.exists(folder_path):
                    self.textBrowser.append(f"文件夹不存在: {folder_path}")
                    return
                
                if not os.path.isdir(folder_path):
                    self.textBrowser.append(f"路径不是文件夹: {folder_path}")
                    return
                
                # 弹出确认对话框
                reply = QMessageBox.question(
                    self, 
                    '确认验证版本号',
                    f'是否要在设备 {device_id} 上验证批量推包版本号？\n\n'
                    f'文件夹路径: {folder_path}\n\n'
                    '功能说明：\n'
                    '1. 扫描文件夹内所有APK文件\n'
                    '2. 提取每个APK的包名和版本号\n'
                    '3. 在设备上查询对应包名的版本号\n'
                    '4. 对比APK版本号和设备版本号\n'
                    '5. 显示验证结果（成功/失败）',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # 创建验证线程
                    from Function_Moudle.adb_batch_verify_version_thread import ADBBatchVerifyVersionThread
                    
                    if self.connection_mode == 'u2':
                        self.batch_verify_version_thread = ADBBatchVerifyVersionThread(
                            device_id, 
                            folder_path,
                            connection_mode='u2',
                            u2_device=self.d
                        )
                    elif self.connection_mode == 'adb':
                        self.batch_verify_version_thread = ADBBatchVerifyVersionThread(
                            device_id, 
                            folder_path,
                            connection_mode='adb'
                        )
                    else:
                        self.textBrowser.append("设备未连接！")
                        return
                    
                    # 连接信号
                    self.batch_verify_version_thread.progress_signal.connect(self.textBrowser.append)
                    self.batch_verify_version_thread.error_signal.connect(self.textBrowser.append)
                    self.batch_verify_version_thread.result_signal.connect(self.textBrowser.append)
                    self.batch_verify_version_thread.verify_result_signal.connect(self.textBrowser.append)
                    
                    # 启动线程
                    self.batch_verify_version_thread.start()
                else:
                    self.textBrowser.append("用户取消验证")
                    
            except Exception as e:
                self.textBrowser.append(f"启动批量验证版本号线程失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def datong_input_password_action(self):
        """一键输入密码 Kfs73p940a"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        if device_id in devices_id_lst:
            try:
                # 弹出确认对话框
                from PyQt5.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    self, 
                    '确认输入密码',
                    f'是否要在设备 {device_id} 上输入密码？\n\n'
                    f'密码: Kfs73p940a\n\n'
                    '注意：\n'
                    '1. 此操作将模拟键盘输入密码\n'
                    '2. 请确保设备当前处于输入框焦点状态\n'
                    '3. 密码将作为普通文本输入',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # 根据连接模式创建相应的线程
                    if self.connection_mode == 'u2':
                        from Function_Moudle.datong_input_password_thread import DatongInputPasswordThread
                        self.input_password_thread = DatongInputPasswordThread(
                            device_id, 
                            password="Kfs73p940a",
                            connection_mode='u2',
                            u2_device=self.d
                        )
                    elif self.connection_mode == 'adb':
                        from Function_Moudle.datong_input_password_thread import DatongInputPasswordThread
                        self.input_password_thread = DatongInputPasswordThread(
                            device_id, 
                            password="Kfs73p940a",
                            connection_mode='adb'
                        )
                    else:
                        self.textBrowser.append("设备未连接！")
                        return
                    
                    # 连接信号
                    self.input_password_thread.progress_signal.connect(self.textBrowser.append)
                    self.input_password_thread.error_signal.connect(self.textBrowser.append)
                    self.input_password_thread.result_signal.connect(self.textBrowser.append)
                    
                    # 启动线程
                    self.input_password_thread.start()
                else:
                    self.textBrowser.append("用户取消输入密码")
                    
            except Exception as e:
                self.textBrowser.append(f"启动密码输入线程失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def datong_open_telenav_engineering_action(self):
        """打开泰维地图工程模式"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        if device_id in devices_id_lst:
            try:
                # 弹出确认对话框
                from PyQt5.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    self, 
                    '确认打开泰维地图工程模式',
                    f'是否要在设备 {device_id} 上打开泰维地图工程模式？\n\n'
                    '命令: adb shell am start -n com.telenav.app.arp/com.telenav.arp.module.secret.SecretScreenActivity\n\n'
                    '注意：此操作将尝试启动泰维地图的工程模式界面',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    self.textBrowser.append("正在打开泰维地图工程模式...")
                    
                    # 执行adb命令
                    command = "shell am start -n com.telenav.app.arp/com.telenav.arp.module.secret.SecretScreenActivity"
                    result = adb_utils.run_adb_command(command, device_id)
                    
                    if result.returncode == 0:
                        self.textBrowser.append("泰维地图工程模式已成功启动")
                        if result.stdout and result.stdout.strip():
                            self.textBrowser.append(f"输出: {result.stdout.strip()}")
                    else:
                        self.textBrowser.append(f"打开泰维地图工程模式失败: {result.stderr}")
                        if result.stdout and result.stdout.strip():
                            self.textBrowser.append(f"输出: {result.stdout.strip()}")
                else:
                    self.textBrowser.append("用户取消打开泰维地图工程模式")
                    
            except Exception as e:
                self.textBrowser.append(f"打开泰维地图工程模式失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def set_vr_timeout(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            try:
                if self.connection_mode == 'u2':
                    from Function_Moudle.set_vr_timeout_thread import SetVrTimeoutThread
                    self.mzs3ett_thread = SetVrTimeoutThread(self.d)
                elif self.connection_mode == 'adb':
                    from Function_Moudle.adb_set_vr_timeout_thread import ADBSetVrTimeoutThread
                    self.mzs3ett_thread = ADBSetVrTimeoutThread(device_id)
                else:
                    self.textBrowser.append("设备未连接！")
                    return
                
                self.mzs3ett_thread.signal_timeout.connect(self.textBrowser.append)
                self.mzs3ett_thread.start()
            except Exception as e:
                self.textBrowser.append(f"启动mzs3ett线程失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")
    def app_version_check(self):
        # 读取self.releasenote_file表格文件中的B8单元格是否等于packageName
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            try:
                from Function_Moudle.app_version_check_thread import AppVersionCheckThread
                self.releasenote_dict = {}
                self.app_version_check_thread = AppVersionCheckThread(self.d, self.releasenote_file)
                self.app_version_check_thread.progress_signal.connect(self.textBrowser.append)
                self.app_version_check_thread.error_signal.connect(self.textBrowser.append)
                self.app_version_check_thread.release_note_signal.connect(self.handle_progress)
                self.app_version_check_thread.start()
            except Exception as e:
                self.textBrowser.append(f"启动版本检查线程失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def handle_progress(self, result_dict):
        self.releasenote_dict.update(result_dict)  # 更新暂存字典
        self.releasenote_package_version = result_dict
        
        # 检查设备连接
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id not in devices_id_lst:
            self.textBrowser.append("设备未连接！")
            return
        
        # 从字典result_dict中挨个读取packageName并用该包名取设备上获取该包名的版本号
        true_count = 0
        false_count = 0
        for i in result_dict.keys():
            if i is not None:
                try:
                    if self.connection_mode == 'u2':
                        app_info = self.d.app_info(i)
                        if app_info is None:
                            self.textBrowser.append(f"应用 {i} 不存在")
                            false_count += 1
                            continue
                        version_name = app_info.get('versionName', '未知版本')
                    elif self.connection_mode == 'adb':
                        # 使用ADB命令获取应用版本信息
                        from Function_Moudle.adb_utils import get_app_version
                        version_success, version_info = get_app_version(device_id, i)
                        if not version_success:
                            self.textBrowser.append(f"应用 {i} 版本信息获取失败: {version_info}")
                            false_count += 1
                            continue
                        version_name = version_info
                    else:
                        self.textBrowser.append("设备未连接！")
                        return
                        
                    if str(version_name) == str(result_dict[i]):
                        self.textBrowser.append(f"包名: {i}, 已安装版本号: {version_name}， 集成清单版本号: {result_dict[i]}")
                        true_count += 1
                        self.textBrowser.append(f"版本号匹配成功！")
                    else:
                        self.textBrowser.append(f"包名: {i}, 已安装版本号: {version_name}， 集成清单版本号: {result_dict[i]}")
                        false_count += 1
                        self.textBrowser.append(f"版本号匹配失败！")
                except Exception as e:
                    self.textBrowser.append(f"获取应用 {i} 信息失败: {e}")
                    false_count += 1
        self.textBrowser.append(f"匹配成功数: {true_count}, 匹配失败数: {false_count}")



    def select_releasenote_excel(self):
        self.releasenote_file, _ = QFileDialog.getOpenFileName(self, "选择集成清单文件", "", "Excel Files (*.xlsx *.xls)")
        if self.releasenote_file is not None:
            # 显示文件名
            file_name = self.releasenote_file.split('/')[-1]
            self.releasenote_file_name_view.setText(file_name)


    def remove_voice_record_file(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        device_record_file_path = self.device_record_path.text()
        if self.d is not None:
            # 弹出弹窗询问用户是否要执行此操作
            reply = QMessageBox.question(self, '删除语音录制文件', f"是否要删除设备{device_id}的语音录制文件？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                # 启动删除语音录制文件线程
                if device_id in devices_id_lst:
                    try:
                        from Function_Moudle.remove_record_file_thread import RemoveRecordFileThread
                        self.voice_record_thread = RemoveRecordFileThread(self.d, device_record_file_path)
                        self.voice_record_thread.signal_remove_voice_record_file.connect(self.textBrowser.append)
                        self.voice_record_thread.start()
                    except Exception as e:
                        self.textBrowser.append(f"启动删除语音录制文件线程失败: {e}")
                else:
                    self.textBrowser.append("设备未连接！")

        else:
            self.textBrowser.append("设备未连接！")

    def voice_start_record(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            try:
                from Function_Moudle.voice_record_thread import VoiceRecordThread
                self.voice_record_thread = VoiceRecordThread(device_id)
                self.voice_record_thread.progress_signal.connect(self.textBrowser.append)
                self.voice_record_thread.record_signal.connect(self.textBrowser.append)
                self.voice_record_thread.start()
            except Exception as e:
                self.textBrowser.append(f"启动语音录制线程失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def voice_stop_record(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            try:
                from Function_Moudle.voice_stop_record_thread import VoiceStopRecordThread
                self.voice_record_thread = VoiceStopRecordThread(device_id)
                self.voice_record_thread.voice_stop_record_signal.connect(self.textBrowser.append)
                self.voice_record_thread.start()
            except Exception as e:
                self.textBrowser.append(f"启动语音录制线程失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def voice_pull_record_file(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        file_path = self.inputbox_log_path.text()
        device_record_file_path = self.device_record_path.text()
        # self.textBrowser.append(f"设备录音文件路径: {device_record_file_path}")
        if device_id in devices_id_lst:
            # 弹出目录选择弹窗
            if file_path is not None:
                try:
                    from Function_Moudle.voice_pull_record_file_thread import VoicePullRecordFileThread
                    self.voice_record_thread = VoicePullRecordFileThread(device_id, file_path, device_record_file_path)
                    self.voice_record_thread.signal_voice_pull_record_file.connect(self.textBrowser.append)
                    self.voice_record_thread.start()
                except Exception as e:
                    self.textBrowser.append(f"启动拉取录音文件线程失败: {e}")
            else:
                self.textBrowser.append("请选择保存路径！")
        else:
            self.textBrowser.append("设备未连接！")

    def open_path(self):
        # 使用资源管理器打开一个地址
        self.file_path = self.inputbox_log_path.text()
        try:
            if self.file_path is not None:
                os.startfile(self.file_path)
            else:
                self.textBrowser.append("路径不能为空！")
        except Exception as e:
            self.textBrowser.append(f"路径不存在！: {e}")

    def pull_log(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        self.file_path = self.inputbox_log_path.text()
        if device_id in devices_id_lst:
            try:
                if self.file_path is None:
                    self.textBrowser.append(f"路径不能为空！")
                elif os.path.exists(self.file_path):
                    from Function_Moudle.pull_log_thread import PullLogThread
                    self.PullLogSaveThread = PullLogThread(self.file_path, device_id)
                    self.PullLogSaveThread.progress_signal.connect(self.textBrowser.append)
                    self.PullLogSaveThread.error_signal.connect(self.textBrowser.append)
                    self.PullLogSaveThread.start()
                    # self.pull_log_button.setText("停止拉取")
                else:
                    self.textBrowser.append(f"路径不存在！")
            except Exception as e:
                self.textBrowser.append(f"启动拉取日志线程失败: {e}")

    def on_combobox_changed(self, text):
        try:
            # 检查是否已经连接到相同的设备
            if self.d and self.connection_mode == 'u2' and text == self.device_id:
                # 已经连接到该设备，无需重新连接
                return
            
            # 尝试u2连接
            self.d = u2.connect(text)
            if self.d:
                self.connection_mode = 'u2'
                self.device_id = text
                self.textBrowser.append(f"u2连接成功：{text}")
            else:
                raise Exception("u2连接返回空对象")
        except Exception as u2_error:
            # u2连接失败，使用ADB模式
            self.d = None
            self.connection_mode = 'adb'
            self.device_id = text
            self.textBrowser.append(f"u2连接失败：{u2_error}")
            self.textBrowser.append(f"切换到ADB模式：{text}")

    def get_selected_device(self):
        return self.ComboxButton.currentText()  # 返回的类型为str

    @staticmethod
    def get_new_device_lst():  # 静态方法，返回设备ID列表
        try:
            # 导入adb_utils
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from adb_utils import adb_utils
            
            result = adb_utils.run_adb_command("devices", check=True)
            devices = result.stdout.strip().split('\n')[1:]  # 获取设备列表
            device_ids = [line.split('\t')[0] for line in devices if line]  # 提取设备ID
            return device_ids
        except Exception:
            # 回退到原来的方法
            import subprocess
            result = subprocess.run("adb devices", shell=True, check=True, capture_output=True, encoding='utf-8', errors='ignore',
                                    text=True)  # 执行 adb devices 命令
            devices = result.stdout.strip().split('\n')[1:]  # 获取设备列表
            device_ids = [line.split('\t')[0] for line in devices if line]  # 提取设备ID
            return device_ids

    def start_app_action(self, app_name):
        device_ids = self.get_new_device_lst()
        device_id = self.get_selected_device()
        self.app_name = app_name
        try:
            if not self.app_name:
                input_text, ok = QInputDialog.getText(self, '输入应用信息',
                                                      '请输入应用包名')
                if ok and input_text:
                    package_name = input_text
                    if self.connection_mode == 'u2':
                        from Function_Moudle.app_action_thread import AppActionThread
                        self.app_action_thread = AppActionThread(self.d, package_name)
                    elif self.connection_mode == 'adb':
                        from Function_Moudle.adb_app_action_thread import ADBAppActionThread
                        self.app_action_thread = ADBAppActionThread(device_id, package_name)
                    else:
                        self.textBrowser.append("设备未连接！")
                        return
                    
                    self.app_action_thread.progress_signal.connect(self.textBrowser.append)
                    self.app_action_thread.error_signal.connect(self.textBrowser.append)
                    self.app_action_thread.start()
                else:
                    self.textBrowser.append("用户取消输入或输入为空")
            else:
                package_name = self.app_name
                if self.connection_mode == 'u2':
                    from Function_Moudle.app_action_thread import AppActionThread
                    self.app_action_thread = AppActionThread(self.d, package_name)
                elif self.connection_mode == 'adb':
                    from Function_Moudle.adb_app_action_thread import ADBAppActionThread
                    self.app_action_thread = ADBAppActionThread(device_id, package_name)
                else:
                    self.textBrowser.append("设备未连接！")
                    return
                
                self.app_action_thread.progress_signal.connect(self.textBrowser.append)
                self.app_action_thread.error_signal.connect(self.textBrowser.append)
                self.app_action_thread.start()
        except Exception as e:
            self.textBrowser.append(f"启动应用失败: {e}")
        if device_id in device_ids:
            pass
        else:
            self.textBrowser.append("未连接设备！")

    def skip_power_limit(self):
        """跳过电源挡位限制"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            try:
                from Function_Moudle.skip_power_limit_thread import SkipPowerLimitThread
                self.skip_power_limit_thread = SkipPowerLimitThread(device_id)
                self.skip_power_limit_thread.progress_signal.connect(self.textBrowser.append)
                self.skip_power_limit_thread.error_signal.connect(self.textBrowser.append)
                self.skip_power_limit_thread.start()
            except Exception as e:
                self.textBrowser.append(f"启动跳过电源限制线程失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def list_package(self):
        """获取设备上安装的应用列表"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        findstr = self.Findstr.toPlainText()

        if device_id in devices_id_lst:
            try:
                if self.connection_mode == 'u2':
                    from Function_Moudle.list_package_thread import ListPackageThread
                    self.list_package_thread = ListPackageThread(self.d, findstr)
                elif self.connection_mode == 'adb':
                    from Function_Moudle.adb_list_package_thread import ADBListPackageThread
                    self.list_package_thread = ADBListPackageThread(device_id, findstr)
                else:
                    self.textBrowser.append("设备未连接！")
                    return

                # 连接信号
                self.list_package_thread.progress_signal.connect(self.textBrowser.append)
                self.list_package_thread.result_signal.connect(
                    lambda results: self.textBrowser.append('\n'.join(results)))
                self.list_package_thread.finished_signal.connect(self.textBrowser.append)
                self.list_package_thread.error_signal.connect(self.textBrowser.append)

                # 启动线程
                self.list_package_thread.start()
            except Exception as e:
                self.textBrowser.append(f"启动应用列表获取线程失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def activate_vr(self):
        """激活VR"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            try:
                # 获取下拉选择框的值
                keyevent_value = self.vr_keyevent_combo.currentText()
                
                # 使用线程执行命令
                from Function_Moudle.activate_vr_thread import ActivateVrThread
                
                if self.connection_mode == 'u2' and self.d:
                    # u2模式使用press_keycode方法
                    self.activate_vr_thread = ActivateVrThread(
                        device_id, 
                        keyevent_value, 
                        connection_mode='u2',
                        u2_device=self.d
                    )
                elif self.connection_mode == 'adb':
                    # ADB模式使用keyevent命令
                    self.activate_vr_thread = ActivateVrThread(
                        device_id, 
                        keyevent_value, 
                        connection_mode='adb'
                    )
                else:
                    self.textBrowser.append("设备连接失败或模式不支持！")
                    return
                
                self.activate_vr_thread.progress_signal.connect(self.textBrowser.append)
                self.activate_vr_thread.error_signal.connect(self.textBrowser.append)
                self.activate_vr_thread.start()
                    
            except Exception as e:
                self.textBrowser.append(f"执行VR唤醒命令失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def check_vr_network(self):
        """检查VR网络"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            try:
                if self.connection_mode == 'u2':
                    from Function_Moudle.check_vr_network_thread import CheckVRNetworkThread
                    self.check_vr_network_thread = CheckVRNetworkThread(self.d)
                elif self.connection_mode == 'adb':
                    from Function_Moudle.adb_check_vr_network_thread import ADBCheckVRNetworkThread
                    self.check_vr_network_thread = ADBCheckVRNetworkThread(device_id)
                else:
                    self.textBrowser.append("设备未连接！")
                    return
                
                self.check_vr_network_thread.progress_signal.connect(self.textBrowser.append)
                self.check_vr_network_thread.result_signal.connect(self.textBrowser.append)
                self.check_vr_network_thread.error_signal.connect(self.textBrowser.append)
                self.check_vr_network_thread.start()
            except Exception as e:
                self.textBrowser.append(f"检查VR网络失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def switch_vr_env(self):
        """切换VR环境"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            try:
                if self.connection_mode == 'u2':
                    from Function_Moudle.switch_vr_env_thread import SwitchVrEnvThread
                    self.check_vr_env_thread = SwitchVrEnvThread(self.d)
                elif self.connection_mode == 'adb':
                    from Function_Moudle.adb_switch_vr_env_thread import ADBSwitchVrEnvThread
                    self.check_vr_env_thread = ADBSwitchVrEnvThread(device_id)
                else:
                    self.textBrowser.append("设备未连接！")
                    return
                
                self.check_vr_env_thread.progress_signal.connect(self.textBrowser.append)
                self.check_vr_env_thread.result_signal.connect(self.textBrowser.append)
                self.check_vr_env_thread.error_signal.connect(self.textBrowser.append)
                self.check_vr_env_thread.start()
            except Exception as e:
                self.textBrowser.append(f"切换VR环境失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def scroll_to_bottom(self):
        scrollbar = self.textBrowser.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def get_running_app_info(self):
        # 获取当前前景应用的版本号
        device_id = self.get_selected_device()  # 获取当前选定的设备ID
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            try:
                if self.connection_mode == 'u2':
                    from Function_Moudle.get_running_app_info_thread import GetRunningAppInfoThread
                    self.get_running_app_info_thread = GetRunningAppInfoThread(self.d)
                elif self.connection_mode == 'adb':
                    from Function_Moudle.adb_get_running_app_info_thread import ADBGetRunningAppInfoThread
                    self.get_running_app_info_thread = ADBGetRunningAppInfoThread(device_id)
                else:
                    self.textBrowser.append("设备未连接！")
                    return
                
                self.get_running_app_info_thread.progress_signal.connect(self.textBrowser.append)
                self.get_running_app_info_thread.result_signal.connect(self.textBrowser.append)
                self.get_running_app_info_thread.error_signal.connect(self.textBrowser.append)
                self.get_running_app_info_thread.start()
            except Exception as e:
                self.textBrowser.append(f"启动获取运行应用信息线程失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def view_apk_path_wrapper(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        try:
            if device_id in devices_id_lst:
                package_name, ok = QInputDialog.getText(self, "输入应用包名", "请输入要查看安装路径的应用包名：")
                if not ok:
                    self.textBrowser.append("已取消！")
                    return
                from Function_Moudle.view_apk_path_wrapper_thread import ViewApkPathWrapperThread
                self.view_apk_thread = ViewApkPathWrapperThread(device_id, package_name)
                self.view_apk_thread.progress_signal.connect(self.textBrowser.append)
                self.view_apk_thread.result_signal.connect(self.textBrowser.append)
                self.view_apk_thread.error_signal.connect(self.textBrowser.append)
                self.view_apk_thread.start()
            else:
                self.textBrowser.append("未连接设备！")
        except Exception as e:
            self.textBrowser.append(f"初始化线程失败: {e}")

    # @staticmethod
    # def run_cmd():
    #     user_directory = os.path.expanduser("~")
    #     subprocess.Popen(["start", "cmd", "/k", "cd /d " + user_directory], shell=True)

    def refresh_devices(self):
        """刷新设备列表（多线程执行，避免阻塞主界面）"""
        # 检查是否已经有刷新线程在运行
        if hasattr(self, 'refresh_devices_thread') and self.refresh_devices_thread.isRunning():
            self.textBrowser.append("刷新设备列表线程正在运行，请稍候...")
            return
        
        # 使用线程刷新设备列表
        try:
            from Function_Moudle.refresh_devices_thread import RefreshDevicesThread
            self.refresh_devices_thread = RefreshDevicesThread()
            
            # 连接信号
            self.refresh_devices_thread.progress_signal.connect(self.textBrowser.append)
            self.refresh_devices_thread.devices_signal.connect(self._handle_refreshed_devices)
            self.refresh_devices_thread.error_signal.connect(self.textBrowser.append)
            
            # 连接线程完成信号
            self.refresh_devices_thread.finished.connect(self._on_refresh_thread_finished)
            
            # 启动线程
            self.refresh_devices_thread.start()
            self.textBrowser.append("开始刷新设备列表...")
            
        except Exception as e:
            self.textBrowser.append(f"启动刷新线程失败: {e}")
    
    def _on_refresh_thread_finished(self):
        """刷新线程完成后的清理工作"""
        self.textBrowser.append("设备列表刷新完成")
        # 可以在这里添加其他清理工作
    
    def _handle_refreshed_devices(self, device_ids):
        """处理刷新后的设备列表（在主线程中执行）"""
        # 清空 ComboxButton 并添加新的设备ID
        self.ComboxButton.clear()
        for device_id in device_ids:
            self.ComboxButton.addItem(device_id)
        
        if device_ids:
            # 只在有设备时尝试连接
            device_id = self.get_selected_device()
            if device_id and device_id != "请点击刷新设备":
                self.device_id = device_id
                # 检查是否已经连接过（避免重复连接）
                if not self.d or self.connection_mode != 'u2':
                    # 使用单独的线程尝试u2连接，避免阻塞主界面
                    self._try_u2_connection_in_thread(device_id)
                else:
                    self.textBrowser.append(f"已使用u2模式连接到设备: {device_id}")
        else:
            self.textBrowser.append("未检测到任何设备")
    
    def _try_u2_connection_in_thread(self, device_id):
        """在单独的线程中尝试u2连接"""
        try:
            from Function_Moudle.u2_connect_thread import U2ConnectThread
            self.u2_connect_thread = U2ConnectThread(device_id)
            
            # 连接信号
            self.u2_connect_thread.progress_signal.connect(self.textBrowser.append)
            self.u2_connect_thread.error_signal.connect(self.textBrowser.append)
            self.u2_connect_thread.connected_signal.connect(self._handle_u2_connection_result)
            
            # 启动线程
            self.u2_connect_thread.start()
            
        except Exception as e:
            self.textBrowser.append(f"启动u2连接线程失败: {e}")
            # 回退到ADB模式
            self.d = None
            self.connection_mode = 'adb'
            self.textBrowser.append(f"使用ADB模式: {device_id}")
    
    def _handle_u2_connection_result(self, u2_device, device_id):
        """处理u2连接结果"""
        if u2_device:
            self.d = u2_device
            self.connection_mode = 'u2'
            self.textBrowser.append(f"u2连接成功: {device_id}")
        else:
            # u2连接失败，使用ADB模式
            self.d = None
            self.connection_mode = 'adb'
            self.textBrowser.append(f"u2连接失败，使用ADB模式: {device_id}")

    def adb_root_wrapper(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            try:
                self.adb_root_thread = AdbRootWrapperThread(device_id)
                self.adb_root_thread.progress_signal.connect(self.textBrowser.append)
                self.adb_root_thread.error_signal.connect(self.textBrowser.append)
                self.adb_root_thread.start()
            except Exception as e:
                self.textBrowser.append(f"获取root权限失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def reboot_device(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            reply = QMessageBox.question(
                self,
                '确认重启',
                '确定要重启设备吗？此操作不可逆！',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                try:
                    from Function_Moudle.reboot_device_thread import RebootDeviceThread
                    self.reboot_thread = RebootDeviceThread(device_id)
                    self.reboot_thread.progress_signal.connect(self.textBrowser.append)
                    self.reboot_thread.error_signal.connect(self.textBrowser.append)
                    self.reboot_thread.start()
                except Exception as e:
                    self.textBrowser.append(f"启动设备重启线程失败: {e}")
            else:
                self.textBrowser.append("用户取消重启操作")
        else:
            self.textBrowser.append("设备未连接！")

    @staticmethod
    def get_screenshot(file_path, device_id):
        command = f"adb -s {device_id} shell screencap -p /sdcard/screenshot.png && adb -s {device_id} pull /sdcard/screenshot.png {file_path} && adb -s {device_id} shell rm /sdcard/screenshot.png"
        try:
            subprocess.run(command, shell=True, check=True)
            return f"截图已保存到 {file_path}"
        except subprocess.CalledProcessError as e:
            return f"截图失败: {e}"

    def show_screenshot_dialog(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            file_path, _ = QFileDialog.getSaveFileName(self, "保存截图", "", "PNG Files (*.png);;All Files (*)")
            if file_path:
                if self.connection_mode == 'u2':
                    # 使用u2截图
                    from Function_Moudle.devices_screen_thread import DevicesScreenThread
                    self.devices_screen_thread = DevicesScreenThread(self.d, file_path)
                    self.devices_screen_thread.signal.connect(self.textBrowser.append)
                    self.devices_screen_thread.start()
                elif self.connection_mode == 'adb':
                    # 使用ADB截图
                    from Function_Moudle.adb_screenshot_thread import ADBScreenshotThread
                    self.devices_screen_thread = ADBScreenshotThread(device_id, file_path)
                    self.devices_screen_thread.signal.connect(self.textBrowser.append)
                    self.devices_screen_thread.start()
                else:
                    self.textBrowser.append("设备未连接！")
            else:
                self.textBrowser.append("已取消！")
        else:
            self.textBrowser.append("未连接设备！")

    def show_uninstall_dialog(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            package_name, ok = QInputDialog.getText(self, "输入应用包名", "请输入要卸载的应用包名：")
            if ok and package_name:
                from Function_Moudle.show_uninstall_thread import ShowUninstallThread
                self.uninstall_thread = ShowUninstallThread(self.d, package_name)
                self.uninstall_thread.progress_signal.connect(self.textBrowser.append)
                self.uninstall_thread.result_signal.connect(self.textBrowser.append)
                self.uninstall_thread.error_signal.connect(self.textBrowser.append)
                self.uninstall_thread.start()
            else:
                self.textBrowser.append("已取消！")
        else:
            self.textBrowser.append("未连接设备！")

    def show_pull_file_dialog(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        try:
            if device_id in devices_id_lst:
                file_path_on_device, ok = QInputDialog.getText(self, "输入设备文件路径", "请输入车机上的文件路径:")
                import pathlib
                file_path = pathlib.Path(file_path_on_device)
                apk_file_name = pathlib.Path(file_path).name
                if ok and file_path_on_device:
                    local_path = QFileDialog.getExistingDirectory(self, "选择文件夹", ".")
                    if local_path:
                        try:
                            if self.connection_mode == 'u2':
                                from Function_Moudle.pull_files_thread import PullFilesThread
                                self.pull_files_thread = PullFilesThread(self.d, file_path_on_device, local_path, apk_file_name)
                            elif self.connection_mode == 'adb':
                                from Function_Moudle.adb_pull_files_thread import ADBPullFilesThread
                                self.pull_files_thread = ADBPullFilesThread(device_id, file_path_on_device, local_path, apk_file_name)
                            else:
                                self.textBrowser.append("设备未连接！")
                                return
                            
                            self.pull_files_thread.signal.connect(self.textBrowser.append)
                            self.pull_files_thread.start()
                        except Exception as e:
                            self.textBrowser.append(f"拉取文件失败: {e}")
                    else:
                        self.textBrowser.append("已取消！")
                else:
                    self.textBrowser.append("已取消！")
            else:
                self.textBrowser.append("未连接设备！")
        except Exception as e:
            self.textBrowser.append(f"初始化线程失败: {e}")

    def show_install_file_dialog(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            package_path, ok = QFileDialog.getOpenFileName(self, "选择应用安装包", "",
                                                          "APK Files (*.apk);;All Files (*)")
            if ok:
                from Function_Moudle.install_file_thread import InstallFileThread
                self.install_file_thread = InstallFileThread(self.d, package_path)
                self.install_file_thread.progress_signal.connect(self.textBrowser.append)
                self.install_file_thread.signal_status.connect(self.textBrowser.append)
                self.install_file_thread.start()
            else:
                self.textBrowser.append("已取消！")
        else:
            self.textBrowser.append("未连接设备！")

    @staticmethod
    def adb_push_file(local_file_path, target_path_on_device, device_id):
        command = f"adb -s {device_id} push {local_file_path} {target_path_on_device}"
        try:
            subprocess.run(command, shell=True, check=True)
            return "文件推送成功！"
        except subprocess.CalledProcessError as e:
            return f"文件推送失败: {e}"

    def show_push_file_dialog(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            local_file_path, _ = QFileDialog.getOpenFileName(self, "选择本地文件", "", "All Files (*)")
            if local_file_path:
                target_path_on_device, ok = QInputDialog.getText(self, "输入设备文件路径",
                                                                 "请输入车机上的目标路径:")
                if ok and target_path_on_device:
                    res = self.adb_push_file(local_file_path, target_path_on_device, device_id)
                    self.textBrowser.append(res)
                else:
                    self.textBrowser.append("已取消！")
            else:
                self.textBrowser.append("已取消！")
        else:
            self.textBrowser.append("未连接设备！")

    @staticmethod
    def simulate_click(x, y, device_id):
        command = f"adb -s {device_id} shell input tap {x} {y}"
        try:
            subprocess.run(command, shell=True, check=True)
            return "点击成功！"
        except subprocess.CalledProcessError as e:
            return f"点击失败: {e}"

    @staticmethod
    def simulate_long_press(x, y, duration, device_id):
        command = f"adb -s {device_id} shell input swipe {x} {y} {x} {y} {duration}"
        try:
            subprocess.run(command, shell=True, check=True)
            return "长按模拟成功！"
        except subprocess.CalledProcessError as e:
            return f"长按模拟失败: {e}"

    def show_simulate_long_press_dialog(self):
        # 执行adb kill-server
        # 执行adb start-server
        from Function_Moudle.simulate_long_press_dialog_thread import simulate_long_press_dialog_thread
        self.simulate_long_press_dialog_thread = simulate_long_press_dialog_thread(self.d)
        self.simulate_long_press_dialog_thread.result_signal.connect(self.textBrowser.append)
        self.simulate_long_press_dialog_thread.error_signal.connect(self.textBrowser.append)
        self.simulate_long_press_dialog_thread.start()

    def show_input_text_dialog(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            text_to_input, ok = QInputDialog.getText(self, "输入文本", "请输入要通过 ADB 输入的文本:")
            if ok and text_to_input:
                # self.textBrowser.append(text_to_input)
                from Function_Moudle.input_text_thread import InputTextThread
                self.input_text_thread = InputTextThread(self.d, text_to_input)
                self.input_text_thread.progress_signal.connect(self.textBrowser.append)
                self.input_text_thread.error_signal.connect(self.textBrowser.append)
                self.input_text_thread.start()
            else:
                self.textBrowser.append("已取消！")
        else:
            self.textBrowser.append("未连接设备！")

    def show_force_stop_app_dialog(self):
        try:
            device_id = self.get_selected_device()
            devices_id_lst = self.get_new_device_lst()
            if device_id in devices_id_lst:
                if self.connection_mode == 'u2':
                    # u2连接成功，自动获取当前前台app并强制停止
                    try:
                        # 获取当前前台应用信息
                        current_app = self.d.app_current()
                        if current_app and 'package' in current_app:
                            package_name = current_app['package']
                            self.textBrowser.append(f"检测到当前前台应用: {package_name}")
                            self.textBrowser.append(f"开始强制停止 {package_name}...")
                            
                            from Function_Moudle.force_stop_app_thread import ForceStopAppThread
                            self.Force_app_thread = ForceStopAppThread(self.d, package_name)
                            
                            self.Force_app_thread.progress_signal.connect(self.textBrowser.append)
                            self.Force_app_thread.error_signal.connect(self.textBrowser.append)
                            self.Force_app_thread.start()
                        else:
                            self.textBrowser.append("无法获取当前前台应用信息，请手动输入包名")
                            # 回退到手动输入
                            self._show_force_stop_input_dialog(device_id)
                    except Exception as u2_error:
                        self.textBrowser.append(f"u2获取前台应用失败: {u2_error}")
                        # 回退到手动输入
                        self._show_force_stop_input_dialog(device_id)
                        
                elif self.connection_mode == 'adb':
                    # ADB模式，需要用户输入包名
                    self._show_force_stop_input_dialog(device_id)
                else:
                    self.textBrowser.append("设备未连接！")
                    return
            else:
                self.textBrowser.append("未连接设备！")
        except Exception as e:
            self.textBrowser.append(f"强制停止应用失败: {e}")
    
    def _show_force_stop_input_dialog(self, device_id):
        """显示强制停止应用输入对话框（用于ADB模式或u2失败时）"""
        package_name, ok = QInputDialog.getText(self, "强制停止应用", "请输入要停止的应用包名：")
        if not ok or not package_name.strip():
            self.textBrowser.append("用户取消输入或输入为空")
            return
        
        try:
            if self.connection_mode == 'u2':
                from Function_Moudle.force_stop_app_thread import ForceStopAppThread
                self.Force_app_thread = ForceStopAppThread(self.d, package_name.strip())
            elif self.connection_mode == 'adb':
                from Function_Moudle.adb_force_stop_app_thread import ADBForceStopAppThread
                self.Force_app_thread = ADBForceStopAppThread(device_id, package_name.strip())
            else:
                self.textBrowser.append("设备未连接！")
                return
            
            self.Force_app_thread.progress_signal.connect(self.textBrowser.append)
            self.Force_app_thread.error_signal.connect(self.textBrowser.append)
            self.Force_app_thread.start()
        except Exception as e:
            self.textBrowser.append(f"强制停止应用失败: {e}")

    def show_clear_app_cache_dialog(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            try:
                if self.connection_mode == 'u2':
                    # u2连接成功，自动获取当前前台app并清除缓存
                    try:
                        # 获取当前前台应用信息
                        current_app = self.d.app_current()
                        if current_app and 'package' in current_app:
                            package_name = current_app['package']
                            self.textBrowser.append(f"检测到当前前台应用: {package_name}")
                            self.textBrowser.append(f"开始清除 {package_name} 的缓存...")
                            
                            from Function_Moudle.clear_app_cache_thread import ClearAppCacheThread
                            self.Clear_app_cache_thread = ClearAppCacheThread(self.d, package_name)
                            
                            self.Clear_app_cache_thread.progress_signal.connect(self.textBrowser.append)
                            self.Clear_app_cache_thread.error_signal.connect(self.textBrowser.append)
                            self.Clear_app_cache_thread.start()
                        else:
                            self.textBrowser.append("无法获取当前前台应用信息，请手动输入包名")
                            # 回退到手动输入
                            self._show_clear_cache_input_dialog(device_id)
                    except Exception as u2_error:
                        self.textBrowser.append(f"u2获取前台应用失败: {u2_error}")
                        # 回退到手动输入
                        self._show_clear_cache_input_dialog(device_id)
                        
                elif self.connection_mode == 'adb':
                    # ADB模式，需要用户输入包名
                    self._show_clear_cache_input_dialog(device_id)
                else:
                    self.textBrowser.append("设备未连接！")
                    return
                    
            except Exception as e:
                self.textBrowser.append(f"清除应用缓存失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")
    
    def _show_clear_cache_input_dialog(self, device_id):
        """显示清除缓存输入对话框（用于ADB模式或u2失败时）"""
        package_name, ok = QInputDialog.getText(self, "清除应用缓存", "请输入要清除缓存的应用包名：")
        if not ok or not package_name.strip():
            self.textBrowser.append("用户取消输入或输入为空")
            return
        
        try:
            if self.connection_mode == 'u2':
                from Function_Moudle.clear_app_cache_thread import ClearAppCacheThread
                self.Clear_app_cache_thread = ClearAppCacheThread(self.d, package_name.strip())
            elif self.connection_mode == 'adb':
                from Function_Moudle.adb_clear_app_cache_thread import ADBClearAppCacheThread
                self.Clear_app_cache_thread = ADBClearAppCacheThread(device_id, package_name.strip())
            else:
                self.textBrowser.append("设备未连接！")
                return
            
            self.Clear_app_cache_thread.progress_signal.connect(self.textBrowser.append)
            self.Clear_app_cache_thread.error_signal.connect(self.textBrowser.append)
            self.Clear_app_cache_thread.start()
        except Exception as e:
            self.textBrowser.append(f"清除应用缓存失败: {e}")

    def get_foreground_package(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        try:
            if device_id in devices_id_lst:
                if self.connection_mode == 'u2':
                    from Function_Moudle.get_foreground_package_thread import GetForegroundPackageThread
                    self.GetForegroundPackageThread = GetForegroundPackageThread(self.d)
                elif self.connection_mode == 'adb':
                    from Function_Moudle.adb_get_foreground_package_thread import ADBGetForegroundPackageThread
                    self.GetForegroundPackageThread = ADBGetForegroundPackageThread(device_id)
                else:
                    self.textBrowser.append("设备连接失败")
                    return
                
                self.GetForegroundPackageThread.signal_package.connect(self.textBrowser.append)
                self.GetForegroundPackageThread.start()
            else:
                self.textBrowser.append("设备连接失败")
        except Exception as e:
            self.textBrowser.append(f"获取前台正在运行的应用包名失败: {e}")

    @staticmethod
    def aapt_get_packagen_name(apk_path):
        quoted_apk_path = f'"{apk_path}"'
        command = f"aapt dump badging {quoted_apk_path} | findstr name"
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            package_name = result.stdout.strip().split('\'')[1]
            return package_name
        except subprocess.CalledProcessError as e:
            return f"获取包名失败: {e}"

    def aapt_getpackage_name_dilog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择APK文件", "", "APK文件 (*.apk)")
        if file_path:
            try:
                from Function_Moudle.aapt_get_package_name_thread import AaptGetPackageNameThread
                self.aapt_thread = AaptGetPackageNameThread(file_path)
                self.aapt_thread.result_signal.connect(self.textBrowser.append)
                self.aapt_thread.error_signal.connect(self.textBrowser.append)
                self.aapt_thread.start()
            except Exception as e:
                self.textBrowser.append(f"启动aapt线程失败: {e}")
        else:
            self.textBrowser.append("未选择APK文件")


    def browse_log_save_path(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            if hasattr(self, 'PullLogSaveThread') and self.PullLogSaveThread and self.PullLogSaveThread.isRunning():
                self.PullLogSaveThread.stop()
                self.pull_log_button.setText("拉取日志")
            else:
                #  弹出选择路径的窗口
                self.file_path = QFileDialog.getExistingDirectory(self, "选择保存路径", "")
                if self.file_path:
                    self.inputbox_log_path.setText(self.file_path)
                else:
                    self.textBrowser.append("已取消！")
        else:
            self.textBrowser.append("未连接设备！")
    
    # ============================================
    # 窗口缩放功能相关方法
    # ============================================
    
    def resizeEvent(self, event):
        """重写窗口缩放事件"""
        super().resizeEvent(event)
        
        # 更新当前窗口大小
        self.current_size = self.size()
        
        # 计算缩放比例
        width_ratio = self.current_size.width() / self.original_size.width()
        height_ratio = self.current_size.height() / self.original_size.height()
        
        # 使用较小的缩放比例，避免过度缩放
        scale_ratio = min(width_ratio, height_ratio)
        
        # 限制缩放范围在0.8到1.5之间
        scale_ratio = max(0.8, min(1.5, scale_ratio))
        
        # 调整字体大小
        self.adjust_font_sizes(scale_ratio)
        
        # 调整控件大小
        self.adjust_widget_sizes(scale_ratio)
    
    def adjust_font_sizes(self, scale_ratio):
        """根据缩放比例调整字体大小"""
        try:
            # 计算新的字体大小
            new_font_size = max(1, int(self.base_font_size * scale_ratio))
            
            # 获取所有子控件
            all_widgets = self.findChildren(QWidget)
            
            for widget in all_widgets:
                widget_type = widget.__class__.__name__
                
                # 只调整特定类型的控件字体
                if widget_type in self.scalable_widget_types:
                    current_font = widget.font()
                    
                    # 根据控件类型设置不同的字体大小
                    if widget_type == 'QTextBrowser':
                        # 文本浏览器使用稍小的字体
                        font_size = max(8, int(new_font_size * 0.9))
                    elif widget_type == 'QPushButton':
                        # 按钮使用标准字体大小
                        font_size = new_font_size
                    elif widget_type == 'QTabWidget':
                        # 标签页使用标准字体大小
                        font_size = new_font_size
                    else:
                        # 其他控件使用标准字体大小
                        font_size = new_font_size
                    
                    current_font.setPointSize(font_size)
                    widget.setFont(current_font)
                    
        except Exception as e:
            # 字体调整失败时不中断程序
            print(f"调整字体大小时出错: {e}")
    
    def adjust_widget_sizes(self, scale_ratio):
        """根据缩放比例调整控件最小/最大尺寸"""
        try:
            # 获取所有按钮控件
            buttons = self.findChildren(QPushButton)
            
            for button in buttons:
                button_name = button.objectName()
                button_text = button.text()
                
                # 对于刷新设备按钮，使用更保守的缩放
                if button_name == 'RefreshButton':
                    # 刷新按钮保持相对固定的大小
                    button.setMinimumSize(120, 30)
                    button.setMaximumSize(300, 50)
                else:
                    # 获取当前的最小尺寸
                    current_min_size = button.minimumSize()
                    if current_min_size.width() > 0 and current_min_size.height() > 0:
                        # 计算新的最小尺寸
                        new_min_width = int(current_min_size.width() * scale_ratio)
                        new_min_height = int(current_min_size.height() * scale_ratio)
                        
                        # 为长文字按钮设置更大的最小宽度
                        if len(button_text) > 10:  # 文字长度超过10个字符
                            # 根据文字长度调整最小宽度
                            text_length_factor = len(button_text) / 10.0
                            new_min_width = max(new_min_width, int(120 * text_length_factor * scale_ratio))
                        
                        # 确保最小宽度足够显示文字
                        new_min_width = max(new_min_width, 80)  # 最小80像素
                        new_min_height = max(new_min_height, 25)  # 最小25像素
                        
                        # 设置新的最小尺寸
                        button.setMinimumSize(new_min_width, new_min_height)
                    
                    # 获取当前的最大尺寸
                    current_max_size = button.maximumSize()
                    if current_max_size.width() < 16777215 and current_max_size.height() < 16777215:
                        # 计算新的最大尺寸
                        new_max_width = int(current_max_size.width() * scale_ratio)
                        new_max_height = int(current_max_size.height() * scale_ratio)
                        
                        # 设置新的最大尺寸
                        button.setMaximumSize(new_max_width, new_max_height)
            
            # 处理ComboBox控件
            comboboxes = self.findChildren(QComboBox)
            for combobox in comboboxes:
                combobox_name = combobox.objectName()
                
                if combobox_name == 'ComboxButton':
                    # 设备选择下拉框保持合理的最大宽度
                    combobox.setMinimumSize(150, 30)
                    combobox.setMaximumSize(500, 50)
                    
        except Exception as e:
            # 控件大小调整失败时不中断程序
            print(f"调整控件大小时出错: {e}")
    
    def update_scaling_settings(self):
        """更新缩放设置（可用于配置对话框）"""
        # 这里可以添加从配置文件读取缩放设置的逻辑
        pass
