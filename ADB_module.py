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
from logger_manager import (
    get_logger, log_operation, measure_performance, log_exception,
    log_button_click, log_method_result, log_device_operation,
    log_file_operation, log_thread_start, log_thread_complete
)

# 创建日志记录器
logger = get_logger("ADBTools.ADB_Module")

class TextEditOutputStream(io.TextIOBase):  # 继承 io.TextIOBase 类

    def __init__(self, textbrowser):
        super().__init__()  # 调用父类构造函数
        self.textBrowser = textbrowser  # 绑定 textEdit
        self.buffer = io.StringIO()  # 创建一个缓存区
        self.clear_before_write = False  # 添加一个标志来控制是否清空内容
        self.last_output_type = None  # 记录上一次输出的类型
        self.output_count = 0  # 输出计数器

    def write(self, s):
        if self.clear_before_write:
            self.textBrowser.clear()  # 如果标志为 True，则清空 textEdit 的内容
            self.clear_before_write = False  # 重置标志
        self.buffer.write(s)
        self.textBrowser.append(s)
        
        # 同时记录到日志（只记录非空内容）
        if s and s.strip():
            import threading
            from datetime import datetime
            
            thread_id = threading.current_thread().ident
            thread_name = threading.current_thread().name
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            self.output_count += 1
            
            # 判断输出类型
            s_lower = s.lower()
            s_stripped = s.strip()
            
            # 错误信息
            if any(keyword in s_lower for keyword in ['错误', '失败', 'error', 'failed', 'not found', 'exception', 'traceback']):
                log_level = 'ERROR'
                self.last_output_type = 'error'
                logger.error(f"[{timestamp}] [Thread-{thread_id}] UI输出[ERROR]: {s_stripped}")
            # 警告信息
            elif any(keyword in s_lower for keyword in ['警告', 'warning', 'warn']):
                log_level = 'WARNING'
                self.last_output_type = 'warning'
                logger.warning(f"[{timestamp}] [Thread-{thread_id}] UI输出[WARNING]: {s_stripped}")
            # 成功信息
            elif any(keyword in s_lower for keyword in ['成功', '完成', 'success', 'completed', 'finished', 'done']):
                log_level = 'INFO'
                self.last_output_type = 'success'
                logger.info(f"[{timestamp}] [Thread-{thread_id}] UI输出[SUCCESS]: {s_stripped}")
            # 进度信息
            elif any(keyword in s_lower for keyword in ['正在', '处理中', 'processing', 'progress', 'loading']):
                log_level = 'DEBUG'
                self.last_output_type = 'progress'
                logger.debug(f"[{timestamp}] [Thread-{thread_id}] UI输出[PROGRESS]: {s_stripped}")
            # 普通信息
            else:
                log_level = 'INFO'
                self.last_output_type = 'info'
                logger.info(f"[{timestamp}] [Thread-{thread_id}] UI输出[INFO]: {s_stripped}")
        
        return len(s)

    def flush(self):
        self.buffer.flush()

    def set_clear_before_write(self, clear):
        self.clear_before_write = clear
    
    def get_output_stats(self):
        """获取输出统计信息"""
        return {
            "output_count": self.output_count,
            "last_output_type": self.last_output_type
        }


# noinspection DuplicatedCode,SpellCheckingInspection
class ADB_Mainwindow(QMainWindow):
    # 软件版本 - 从全局配置管理器获取
    @property
    def VERSION(self):
        """获取软件版本号"""
        try:
            from config_manager import config_manager
            return config_manager.get_version()
        except ImportError:
            # 如果config_manager不可用，返回默认版本
            return "1.5.0"
    
    def __init__(self, parent=None):
        logger.info("初始化 ADB 主窗口...")
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
        self.datong_open_telenav_engineering_thread = None
        self.list_package_thread = None
        self.input_keyevent_287_thread = None
        self.engineering_thread = None
        self.app_action_thread = None
        self.verity_thread = None
        self.batch_install_thread = None
        self.u2_reinit_thread = None
        self.u2_reinit_dialog = None

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
        
        # 添加重新初始化u2按钮（如果UI中有）
        try:
            self.reinit_u2_button = self.findChild(QtWidgets.QPushButton, 'reinit_u2_button')
            if self.reinit_u2_button:
                self.reinit_u2_button.clicked.connect(self.reinit_uiautomator2)
        except:
            pass
        
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
        
        # 设置窗口缩放策略
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 获取中央部件并设置缩放策略
        central_widget = self.centralWidget()
        if central_widget:
            central_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 初始化大通页面布局
        self.init_datong_layout()
    
    def init_datong_layout(self):
        """初始化大通页面布局"""
        try:
            from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
            
            # 查找大通页面的布局容器
            layout_widget = self.findChild(QWidget, "layoutWidget")
            if layout_widget:
                # 移除固定几何尺寸，改用布局管理
                layout_widget.setGeometry(0, 0, 0, 0)  # 清除固定尺寸
                
                # 获取或创建布局
                layout = layout_widget.layout()
                if not layout:
                    layout = QVBoxLayout(layout_widget)
                    layout_widget.setLayout(layout)
                
                # 设置布局的边距和间距
                layout.setContentsMargins(10, 10, 10, 10)
                layout.setSpacing(8)
                
                # 设置布局容器的尺寸策略
                layout_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                
                print("大通页面布局初始化完成")
                
        except Exception as e:
            print(f"初始化大通页面布局时出错: {e}")

    def add_config_menu(self):
        """添加配置菜单"""
        from PyQt5 import QtWidgets
        menubar = self.menuBar()
        
        # 设置菜单
        settings_menu = menubar.addMenu('设置')
        
        # 配置管理器
        config_action = QtWidgets.QAction('配置管理器', self)
        config_action.triggered.connect(self.open_enhanced_config_dialog)
        settings_menu.addAction(config_action)
        
        # 分隔线
        settings_menu.addSeparator()
        
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

    def open_enhanced_config_dialog(self):
        """打开配置对话框"""
        try:
            from config_dialog_enhanced import EnhancedConfigDialog
            dialog = EnhancedConfigDialog(self)
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
        """打开YF升级页面"""
        log_button_click("open_yf_page", "启动YF升级页面", "com.yfve.usbupdate")
        self.start_app_action(app_name = "com.yfve.usbupdate")

    def open_soimt_update(self):
        """打开SOIMT升级页面"""
        log_button_click("open_soimt_update", "启动SOIMT升级页面", "com.saicmotor.update")
        self.start_app_action(app_name = "com.saicmotor.update")

    def open_engineering_mode(self):
        """打开工程模式"""
        log_button_click("enter_engineering_mode_button", "启动工程模式", "com.saicmotor.hmi.engmode")
        self.start_app_action(app_name = "com.saicmotor.hmi.engmode")

    def as33_cr_enter_engineering(self):
        """AS33 CR 进入工程模式"""
        log_button_click("AS33_CR_enter_engineering_mode_button", "启动AS33 CR工程模式", "com.saicmotor.diag")
        self.start_app_action(app_name = "com.saicmotor.diag")

    def datong_factory_action(self):
        """拉起中环工厂应用"""
        log_button_click("datong_factory_button", "启动中环工厂应用", "com.zhonghuan.factory")
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
        
        log_button_click("datong_disable_verity_button", "禁用verity校验")

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
                        log_method_result("datong_disable_verity_action", False, "设备未连接")
                        self.textBrowser.append("设备未连接！")
                        return
                    
                    # 连接信号
                    self.disable_verity_thread.progress_signal.connect(self.textBrowser.append)
                    self.disable_verity_thread.error_signal.connect(self.textBrowser.append)
                    self.disable_verity_thread.result_signal.connect(self.handle_disable_verity_result)
                    
                    # 启动线程
                    self.disable_verity_thread.start()
                    log_method_result("datong_disable_verity_action", True, "disable-verity命令已发送")
                else:
                    logger.info("用户取消执行adb disable-verity命令")
            except Exception as e:
                log_method_result("datong_disable_verity_action", False, str(e))
                self.textBrowser.append(f"启动disable-verity命令线程失败: {e}")
        else:
            log_method_result("datong_disable_verity_action", False, "设备未连接")
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
        
        log_button_click("datong_enable_verity_button", "启用verity校验")

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
                        log_method_result("datong_enable_verity_action", False, "设备未连接")
                        self.textBrowser.append("设备未连接！")
                        return
                    
                    # 连接信号
                    self.enable_verity_thread.progress_signal.connect(self.textBrowser.append)
                    self.enable_verity_thread.error_signal.connect(self.textBrowser.append)
                    self.enable_verity_thread.result_signal.connect(self.handle_enable_verity_result)
                    
                    # 启动线程
                    self.enable_verity_thread.start()
                    log_method_result("datong_enable_verity_action", True, "enable-verity命令已发送")
                else:
                    logger.info("用户取消执行adb enable-verity命令")
            except Exception as e:
                log_method_result("datong_enable_verity_action", False, str(e))
                self.textBrowser.append(f"启动enable-verity命令线程失败: {e}")
        else:
            log_method_result("datong_enable_verity_action", False, "设备未连接")
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
        
        log_button_click("datong_batch_install_button", "批量安装APK文件")

        if device_id in devices_id_lst:
            try:
                # 弹出文件夹选择框
                from PyQt5.QtWidgets import QFileDialog, QMessageBox
                folder_path = QFileDialog.getExistingDirectory(
                    self,
                    "选择APK文件所在文件夹",
                    "."
                )
                
                if not folder_path:
                    logger.info("用户取消文件夹选择")
                    return
                
                logger.info(f"选择文件夹: {folder_path}")
                
                # 获取文件夹中的所有APK文件
                import os
                apk_files = [f for f in os.listdir(folder_path) if f.endswith('.apk')]
                
                if not apk_files:
                    log_method_result("datong_batch_install_action", False, "未找到APK文件")
                    QMessageBox.warning(self, "未找到APK文件", f"在 {folder_path} 中未找到任何APK文件")
                    return
                
                logger.info(f"找到 {len(apk_files)} 个APK文件")
                
                # 显示确认对话框
                reply = QMessageBox.question(
                    self,
                    '确认批量安装',
                    f'找到 {len(apk_files)} 个APK文件，是否继续批量安装？\n\n'
                    f'文件列表:\n' + '\n'.join(apk_files[:10]),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    from Function_Moudle.adb_batch_install_thread import ADBBatchInstallThread
                    self.batch_install_thread = ADBBatchInstallThread(
                        device_id,
                        folder_path,
                        apk_files
                    )
                    self.batch_install_thread.progress_signal.connect(self.textBrowser.append)
                    self.batch_install_thread.result_signal.connect(self.textBrowser.append)
                    self.batch_install_thread.error_signal.connect(self.textBrowser.append)
                    self.batch_install_thread.start()
                    
                    log_method_result("datong_batch_install_action", True, f"批量安装线程已启动 ({len(apk_files)}个文件)")
                else:
                    logger.info("用户取消批量安装")
            except Exception as e:
                log_method_result("datong_batch_install_action", False, str(e))
                self.textBrowser.append(f"批量安装失败: {e}")
        else:
            log_method_result("datong_batch_install_action", False, "设备未连接")
            self.textBrowser.append("设备未连接！")

    def datong_batch_install_test_action(self):
        """测试批量安装功能 - 打印所有流程中的值和命令"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("datong_batch_install_test_button", "测试批量安装功能")
        
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
                    logger.info("用户取消文件夹选择")
                    return
                
                logger.info(f"选择文件夹: {folder_path}")
                
                # 检查文件夹是否存在
                import os
                if not os.path.exists(folder_path):
                    log_method_result("datong_batch_install_test_action", False, "文件夹不存在")
                    self.textBrowser.append(f"文件夹不存在: {folder_path}")
                    return
                
                if not os.path.isdir(folder_path):
                    log_method_result("datong_batch_install_test_action", False, "路径不是文件夹")
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
                        log_method_result("datong_batch_install_test_action", False, "设备未连接")
                        self.textBrowser.append("设备未连接！")
                        return
                    
                    # 连接信号
                    self.batch_install_test_thread.progress_signal.connect(self.textBrowser.append)
                    self.batch_install_test_thread.error_signal.connect(self.textBrowser.append)
                    self.batch_install_test_thread.result_signal.connect(self.textBrowser.append)
                    self.batch_install_test_thread.debug_signal.connect(self.textBrowser.append)
                    
                    # 启动线程
                    self.batch_install_test_thread.start()
                    log_method_result("datong_batch_install_test_action", True, "测试线程已启动")
                else:
                    logger.info("用户取消测试")
            except Exception as e:
                log_method_result("datong_batch_install_test_action", False, str(e))
                self.textBrowser.append(f"启动批量安装测试线程失败: {e}")
        else:
            log_method_result("datong_batch_install_test_action", False, "设备未连接")
            self.textBrowser.append("设备未连接！")

    def datong_batch_verify_version_action(self):
        """验证批量推包版本号"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("datong_batch_install_test_button", "验证批量推包版本号")

        if device_id in devices_id_lst:
            try:
                # 弹出文件夹选择框
                from PyQt5.QtWidgets import QFileDialog, QMessageBox
                folder_path = QFileDialog.getExistingDirectory(
                    self,
                    "选择APK文件所在文件夹",
                    "."
                )
                
                if not folder_path:
                    logger.info("用户取消文件夹选择")
                    return
                
                logger.info(f"选择文件夹: {folder_path}")
                
                # 获取文件夹中的所有APK文件
                import os
                apk_files = [f for f in os.listdir(folder_path) if f.endswith('.apk')]
                
                if not apk_files:
                    log_method_result("datong_batch_verify_version_action", False, "未找到APK文件")
                    QMessageBox.warning(self, "未找到APK文件", f"在 {folder_path} 中未找到任何APK文件")
                    return
                
                logger.info(f"找到 {len(apk_files)} 个APK文件")
                
                # 显示确认对话框
                reply = QMessageBox.question(
                    self,
                    '确认版本验证',
                    f'找到 {len(apk_files)} 个APK文件，是否继续验证版本？\n\n'
                    f'文件列表:\n' + '\n'.join(apk_files[:10]),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    from Function_Moudle.adb_batch_verify_version_thread import ADBBatchVerifyVersionThread
                    self.batch_install_test_thread = ADBBatchVerifyVersionThread(
                        device_id,
                        folder_path,
                        apk_files
                    )
                    self.batch_install_test_thread.progress_signal.connect(self.textBrowser.append)
                    self.batch_install_test_thread.result_signal.connect(self.textBrowser.append)
                    self.batch_install_test_thread.error_signal.connect(self.textBrowser.append)
                    self.batch_install_test_thread.debug_signal.connect(self.textBrowser.append)
                    
                    # 启动线程
                    self.batch_install_test_thread.start()
                    
                    log_method_result("datong_batch_verify_version_action", True, f"版本验证线程已启动 ({len(apk_files)}个文件)")
                else:
                    logger.info("用户取消版本验证")
            except Exception as e:
                log_method_result("datong_batch_verify_version_action", False, str(e))
                self.textBrowser.append(f"版本验证失败: {e}")
        else:
            log_method_result("datong_batch_verify_version_action", False, "设备未连接")
            self.textBrowser.append("设备未连接！")

    def datong_input_password_action(self):
        """一键输入密码 Kfs73p940a"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        password = "Kfs73p940a"
        
        log_button_click("datong_input_password_button", "一键输入密码")

        if device_id in devices_id_lst:
            try:
                # 弹出确认对话框
                from PyQt5.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    self, 
                    '确认输入密码',
                    f'确定要在设备 {device_id} 上输入密码 {password} 吗？',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    logger.info(f"输入密码: {password}")
                    
                    from Function_Moudle.datong_input_password_thread import DatongInputPasswordThread
                    self.input_password_thread = DatongInputPasswordThread(device_id, password)
                    self.input_password_thread.progress_signal.connect(self.textBrowser.append)
                    self.input_password_thread.result_signal.connect(self.textBrowser.append)
                    self.input_password_thread.error_signal.connect(self.textBrowser.append)
                    
                    # 启动线程
                    self.input_password_thread.start()
                    
                    log_method_result("datong_input_password_action", True, "密码输入线程已启动")
                else:
                    logger.info("用户取消输入密码")
            except Exception as e:
                log_method_result("datong_input_password_action", False, str(e))
                self.textBrowser.append(f"启动密码输入线程失败: {e}")
        else:
            log_method_result("datong_input_password_action", False, "设备未连接")
            self.textBrowser.append("设备未连接！")

    def datong_open_telenav_engineering_action(self):
        """打开泰维地图工程模式"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("datong_open_telenav_engineering_button", "打开泰维地图工程模式")

        if device_id in devices_id_lst:
            try:
                from Function_Moudle.datong_open_telenav_engineering_thread import DatongOpenTelenavEngineeringThread
                self.datong_open_telenav_engineering_thread = DatongOpenTelenavEngineeringThread(device_id)
                self.datong_open_telenav_engineering_thread.progress_signal.connect(self.textBrowser.append)
                self.datong_open_telenav_engineering_thread.result_signal.connect(self.textBrowser.append)
                self.datong_open_telenav_engineering_thread.error_signal.connect(self.textBrowser.append)
                self.datong_open_telenav_engineering_thread.start()
                
                log_method_result("datong_open_telenav_engineering_action", True, "线程已启动")
            except Exception as e:
                log_method_result("datong_open_telenav_engineering_action", False, str(e))
                self.textBrowser.append(f"打开泰维地图工程模式失败: {e}")
        else:
            log_method_result("datong_open_telenav_engineering_action", False, "设备未连接")
            self.textBrowser.append("设备未连接！")

    def set_vr_timeout(self):
        """设置VR服务器超时"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("set_vr_server_timout", "设置VR服务器超时")

        if device_id in devices_id_lst:
            try:
                if self.connection_mode == 'u2':
                    from Function_Moudle.set_vr_timeout_thread import SetVrTimeoutThread
                    self.mzs3ett_thread = SetVrTimeoutThread(self.d)
                elif self.connection_mode == 'adb':
                    from Function_Moudle.adb_set_vr_timeout_thread import ADBSetVrTimeoutThread
                    self.mzs3ett_thread = ADBSetVrTimeoutThread(device_id)
                else:
                    log_method_result("set_vr_timeout", False, "设备未连接")
                    self.textBrowser.append("设备未连接！")
                    return
                
                self.mzs3ett_thread.progress_signal.connect(self.textBrowser.append)
                self.mzs3ett_thread.result_signal.connect(self.textBrowser.append)
                self.mzs3ett_thread.error_signal.connect(self.textBrowser.append)
                self.mzs3ett_thread.start()
                
                log_method_result("set_vr_timeout", True, "线程已启动")
            except Exception as e:
                log_method_result("set_vr_timeout", False, str(e))
                self.textBrowser.append(f"设置VR超时失败: {e}")
        else:
            log_method_result("set_vr_timeout", False, "设备未连接")
            self.textBrowser.append("设备未连接！")

    def app_version_check(self):
        """检查应用版本"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("start_check_button", "检查应用版本", f"集成清单: {self.releasenote_file}")

        if device_id in devices_id_lst:
            try:
                from Function_Moudle.app_version_check_thread import AppVersionCheckThread
                self.releasenote_dict = {}
                self.app_version_check_thread = AppVersionCheckThread(self.d, self.releasenote_file)
                self.app_version_check_thread.progress_signal.connect(self.textBrowser.append)
                self.app_version_check_thread.error_signal.connect(self.textBrowser.append)
                self.app_version_check_thread.release_note_signal.connect(self.handle_progress)
                self.app_version_check_thread.start()
                
                log_method_result("app_version_check", True, "版本检查线程已启动")
            except Exception as e:
                log_method_result("app_version_check", False, str(e))
                self.textBrowser.append(f"启动版本检查线程失败: {e}")
        else:
            log_method_result("app_version_check", False, "设备未连接")
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
        """选择集成清单文件"""
        log_button_click("select_releasenote_excel_button", "选择集成清单文件")
        
        self.releasenote_file, _ = QFileDialog.getOpenFileName(self, "选择集成清单文件", "", "Excel Files (*.xlsx *.xls)")
        
        if self.releasenote_file:
            logger.info(f"选择文件: {self.releasenote_file}")
            file_name = self.releasenote_file.split('/')[-1]
            self.releasenote_file_name_view.setText(file_name)
        else:
            logger.info("用户取消选择文件")


    def remove_voice_record_file(self):
        """删除语音录制文件"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("remove_record_file_button", "删除语音录制文件")

        if device_id in devices_id_lst:
            try:
                from Function_Moudle.remove_record_file_thread import RemoveRecordFileThread
                self.remove_record_file_thread = RemoveRecordFileThread(device_id)
                self.remove_record_file_thread.progress_signal.connect(self.textBrowser.append)
                self.remove_record_file_thread.result_signal.connect(self.textBrowser.append)
                self.remove_record_file_thread.start()
                
                log_method_result("remove_voice_record_file", True, "删除线程已启动")
            except Exception as e:
                log_method_result("remove_voice_record_file", False, str(e))
                self.textBrowser.append(f"删除录音文件失败: {e}")
        else:
            log_method_result("remove_voice_record_file", False, "设备未连接")
            self.textBrowser.append("设备未连接！")

    def voice_start_record(self):
        """开始语音录制"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("voice_start_record_button", "开始语音录制")

        if device_id in devices_id_lst:
            try:
                from Function_Moudle.voice_record_thread import VoiceRecordThread
                self.voice_record_thread = VoiceRecordThread(device_id)
                self.voice_record_thread.progress_signal.connect(self.textBrowser.append)
                self.voice_record_thread.record_signal.connect(self.textBrowser.append)
                self.voice_record_thread.start()
                
                log_method_result("voice_start_record", True, "录制线程已启动")
            except Exception as e:
                log_method_result("voice_start_record", False, str(e))
                self.textBrowser.append(f"启动语音录制线程失败: {e}")
        else:
            log_method_result("voice_start_record", False, "设备未连接")
            self.textBrowser.append("设备未连接！")

    def voice_stop_record(self):
        """停止语音录制"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("voice_stop_record_button", "停止语音录制")

        if device_id in devices_id_lst:
            try:
                from Function_Moudle.voice_stop_record_thread import VoiceStopRecordThread
                self.voice_record_thread = VoiceStopRecordThread(device_id)
                self.voice_record_thread.voice_stop_record_signal.connect(self.textBrowser.append)
                self.voice_record_thread.start()
                
                log_method_result("voice_stop_record", True, "停止录制线程已启动")
            except Exception as e:
                log_method_result("voice_stop_record", False, str(e))
                self.textBrowser.append(f"停止语音录制失败: {e}")
        else:
            log_method_result("voice_stop_record", False, "设备未连接")
            self.textBrowser.append("设备未连接！")

    def voice_pull_record_file(self):
        """拉取录音文件"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("voice_pull_record_file_button", "拉取录音文件")

        if device_id in devices_id_lst:
            try:
                from Function_Moudle.voice_pull_record_file_thread import VoicePullRecordFileThread
                self.voice_pull_record_file_thread = VoicePullRecordFileThread(device_id)
                self.voice_pull_record_file_thread.progress_signal.connect(self.textBrowser.append)
                self.voice_pull_record_file_thread.result_signal.connect(self.textBrowser.append)
                self.voice_pull_record_file_thread.start()
                
                log_method_result("voice_pull_record_file", True, "拉取线程已启动")
            except Exception as e:
                log_method_result("voice_pull_record_file", False, str(e))
                self.textBrowser.append(f"拉取录音文件失败: {e}")
        else:
            log_method_result("voice_pull_record_file", False, "设备未连接")
            self.textBrowser.append("设备未连接！")

    def open_path(self):
        """打开文件所在目录"""
        log_button_click("open_path_buttom", "打开文件所在目录")
        
        self.file_path = self.inputbox_log_path.text()
        
        try:
            if self.file_path:
                logger.info(f"打开路径: {self.file_path}")
                os.startfile(self.file_path)
                log_method_result("open_path", True, f"已打开: {self.file_path}")
            else:
                log_method_result("open_path", False, "路径不能为空")
                self.textBrowser.append("路径不能为空！")
        except Exception as e:
            log_method_result("open_path", False, str(e))
            self.textBrowser.append(f"路径不存在！: {e}")

    def pull_log(self):
        """拉取设备日志"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        self.file_path = self.inputbox_log_path.text()
        
        log_button_click("pull_log_button", "拉取设备日志", f"保存路径: {self.file_path}")
        
        if device_id in devices_id_lst:
            try:
                if not self.file_path:
                    log_method_result("pull_log", False, "路径不能为空")
                    self.textBrowser.append(f"路径不能为空！")
                elif os.path.exists(self.file_path):
                    from Function_Moudle.pull_log_thread import PullLogThread
                    self.PullLogSaveThread = PullLogThread(self.file_path, device_id)
                    self.PullLogSaveThread.progress_signal.connect(self.textBrowser.append)
                    self.PullLogSaveThread.error_signal.connect(self.textBrowser.append)
                    self.PullLogSaveThread.start()
                    log_method_result("pull_log", True, "拉取日志线程已启动")
                else:
                    log_method_result("pull_log", False, "路径不存在")
                    self.textBrowser.append(f"路径不存在！")
            except Exception as e:
                log_method_result("pull_log", False, str(e))
                self.textBrowser.append(f"启动拉取日志线程失败: {e}")
        else:
            log_method_result("pull_log", False, "设备未连接")
            self.textBrowser.append("设备未连接！")

    def on_combobox_changed(self, text):
        """设备选择下拉框变化时立即更新连接"""
        log_button_click("ComboxButton", "切换设备连接", f"目标设备: {text}")
        
        try:
            # 如果选择的设备与当前连接的设备不同，或者没有连接，则重新连接
            if not self.d or self.connection_mode != 'u2' or text != self.device_id:
                # 尝试u2连接
                log_device_operation("u2_connect_attempt", text, {"mode": "u2", "reason": "设备切换"})
                self.d = u2.connect(text)
                if self.d:
                    self.connection_mode = 'u2'
                    self.device_id = text
                    self.textBrowser.append(f"u2连接成功：{text}")
                    log_device_operation("u2_connect_success", text, {"mode": "u2", "status": "connected"})
                else:
                    raise Exception("u2连接返回空对象")
            else:
                # 已经连接到该设备，确认连接状态
                self.textBrowser.append(f"已连接到设备：{text}")
                log_device_operation("device_already_connected", text, {"mode": self.connection_mode, "status": "already_connected"})
        except Exception as u2_error:
            # u2连接失败，使用ADB模式
            self.d = None
            self.connection_mode = 'adb'
            self.device_id = text
            self.textBrowser.append(f"u2连接失败：{u2_error}")
            self.textBrowser.append(f"切换到ADB模式：{text}")
            log_device_operation("fallback_to_adb", text, {"mode": "adb", "reason": str(u2_error)})

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
        """启动应用"""
        device_ids = self.get_new_device_lst()
        device_id = self.get_selected_device()
        self.app_name = app_name
        
        log_button_click("start_app", f"启动应用: {app_name or '待输入'}")
        
        try:
            if not self.app_name:
                input_text, ok = QInputDialog.getText(self, '输入应用信息',
                                                      '请输入应用包名')
                if ok and input_text:
                    package_name = input_text
                    logger.info(f"输入包名: {package_name}")
                    
                    if self.connection_mode == 'u2':
                        from Function_Moudle.app_action_thread import AppActionThread
                        self.app_action_thread = AppActionThread(self.d, package_name)
                    elif self.connection_mode == 'adb':
                        from Function_Moudle.adb_app_action_thread import ADBAppActionThread
                        self.app_action_thread = ADBAppActionThread(device_id, package_name)
                    else:
                        log_method_result("start_app_action", False, "设备未连接")
                        self.textBrowser.append("设备未连接！")
                        return
                    
                    self.app_action_thread.progress_signal.connect(self.textBrowser.append)
                    self.app_action_thread.error_signal.connect(self.textBrowser.append)
                    self.app_action_thread.start()
                    log_method_result("start_app_action", True, f"启动线程已启动: {package_name}")
                else:
                    logger.info("用户取消输入")
                    self.textBrowser.append("用户取消输入或输入为空")
            else:
                package_name = self.app_name
                logger.info(f"启动应用: {package_name}")
                
                if self.connection_mode == 'u2':
                    from Function_Moudle.app_action_thread import AppActionThread
                    self.app_action_thread = AppActionThread(self.d, package_name)
                elif self.connection_mode == 'adb':
                    from Function_Moudle.adb_app_action_thread import ADBAppActionThread
                    self.app_action_thread = ADBAppActionThread(device_id, package_name)
                else:
                    log_method_result("start_app_action", False, "设备未连接")
                    self.textBrowser.append("设备未连接！")
                    return
                
                self.app_action_thread.progress_signal.connect(self.textBrowser.append)
                self.app_action_thread.error_signal.connect(self.textBrowser.append)
                self.app_action_thread.start()
                log_method_result("start_app_action", True, f"启动线程已启动: {package_name}")
        except Exception as e:
            log_method_result("start_app_action", False, str(e))
            self.textBrowser.append(f"启动应用失败: {e}")
        
        if device_id not in device_ids:
            self.textBrowser.append("未连接设备！")

    def skip_power_limit(self):
        """跳过电源挡位限制"""
        log_button_click("skipping_powerlimit_button", "跳过电源挡位限制")
        
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            try:
                from Function_Moudle.skip_power_limit_thread import SkipPowerLimitThread
                self.skip_power_limit_thread = SkipPowerLimitThread(device_id)
                self.skip_power_limit_thread.progress_signal.connect(self.textBrowser.append)
                self.skip_power_limit_thread.error_signal.connect(self.textBrowser.append)
                self.skip_power_limit_thread.start()
                
                log_method_result("skip_power_limit", True, "线程已启动")
            except Exception as e:
                log_method_result("skip_power_limit", False, str(e))
                self.textBrowser.append(f"启动跳过电源限制线程失败: {e}")
        else:
            log_method_result("skip_power_limit", False, "设备未连接")
            self.textBrowser.append("设备未连接！")

    def list_package(self):
        """获取设备上安装的应用列表"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        findstr = self.Findstr.toPlainText()
        
        log_button_click("list_package_button", "获取应用列表", f"搜索: {findstr}")

        if device_id in devices_id_lst:
            try:
                if self.connection_mode == 'u2':
                    from Function_Moudle.list_package_thread import ListPackageThread
                    self.list_package_thread = ListPackageThread(self.d, findstr)
                elif self.connection_mode == 'adb':
                    from Function_Moudle.adb_list_package_thread import ADBListPackageThread
                    self.list_package_thread = ADBListPackageThread(device_id, findstr)
                else:
                    log_method_result("list_package", False, "设备未连接")
                    self.textBrowser.append("设备未连接！")
                    return

                # 连接信号
                self.list_package_thread.progress_signal.connect(self.textBrowser.append)
                self.list_package_thread.result_signal.connect(
                    lambda results: self._handle_list_package_results(results))
                self.list_package_thread.finished_signal.connect(lambda: log_method_result("list_package", True, "获取完成"))
                self.list_package_thread.error_signal.connect(self.textBrowser.append)

                # 启动线程
                self.list_package_thread.start()
            except Exception as e:
                log_method_result("list_package", False, str(e))
                self.textBrowser.append(f"启动应用列表获取线程失败: {e}")
        else:
            log_method_result("list_package", False, "设备未连接")
            self.textBrowser.append("设备未连接！")
    
    def _handle_list_package_results(self, results):
        """处理应用列表结果"""
        if results:
            logger.info(f"✓ 找到 {len(results)} 个应用")
            self.textBrowser.append(f"✓ 找到 {len(results)} 个应用")
            # 只记录前5个应用，避免日志过长
            for i, app in enumerate(results[:5]):
                logger.info(f"  {i+1}. {app}")
                self.textBrowser.append(f"  {i+1}. {app}")
            if len(results) > 5:
                logger.info(f"  ... 还有 {len(results) - 5} 个应用")
                self.textBrowser.append(f"  ... 还有 {len(results) - 5} 个应用")
        else:
            logger.warning("✗ 未找到任何应用")
            self.textBrowser.append("✗ 未找到任何应用")

    def activate_vr(self):
        """激活VR"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        keyevent_value = self.vr_keyevent_combo.currentText()
        
        log_button_click("activate_VR_button", "激活VR", f"Keyevent: {keyevent_value}")

        if device_id in devices_id_lst:
            try:
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
                    log_method_result("activate_vr", False, "设备连接失败")
                    self.textBrowser.append("设备连接失败或模式不支持！")
                    return
                
                self.activate_vr_thread.progress_signal.connect(self.textBrowser.append)
                self.activate_vr_thread.error_signal.connect(self.textBrowser.append)
                self.activate_vr_thread.start()
                
                log_method_result("activate_vr", True, f"线程已启动 (Keyevent: {keyevent_value})")
                    
            except Exception as e:
                log_method_result("activate_vr", False, str(e))
                self.textBrowser.append(f"执行VR唤醒命令失败: {e}")
        else:
            log_method_result("activate_vr", False, "设备未连接")
            self.textBrowser.append("设备未连接！")

    def check_vr_network(self):
        """检查VR网络"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("VR_nework_check_button", "检查VR网络")

        if device_id in devices_id_lst:
            try:
                if self.connection_mode == 'u2':
                    from Function_Moudle.check_vr_network_thread import CheckVRNetworkThread
                    self.check_vr_network_thread = CheckVRNetworkThread(self.d)
                elif self.connection_mode == 'adb':
                    from Function_Moudle.adb_check_vr_network_thread import ADBCheckVRNetworkThread
                    self.check_vr_network_thread = ADBCheckVRNetworkThread(device_id)
                else:
                    log_method_result("check_vr_network", False, "设备未连接")
                    self.textBrowser.append("设备未连接！")
                    return
                
                self.check_vr_network_thread.progress_signal.connect(self.textBrowser.append)
                self.check_vr_network_thread.result_signal.connect(self.textBrowser.append)
                self.check_vr_network_thread.error_signal.connect(self.textBrowser.append)
                self.check_vr_network_thread.start()
                
                log_method_result("check_vr_network", True, "线程已启动")
            except Exception as e:
                log_method_result("check_vr_network", False, str(e))
                self.textBrowser.append(f"检查VR网络失败: {e}")
        else:
            log_method_result("check_vr_network", False, "设备未连接")
            self.textBrowser.append("设备未连接！")

    def switch_vr_env(self):
        """切换VR环境"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("switch_vr_env_button", "切换VR环境")

        if device_id in devices_id_lst:
            try:
                if self.connection_mode == 'u2':
                    from Function_Moudle.switch_vr_env_thread import SwitchVrEnvThread
                    self.check_vr_env_thread = SwitchVrEnvThread(self.d)
                elif self.connection_mode == 'adb':
                    from Function_Moudle.adb_switch_vr_env_thread import ADBSwitchVrEnvThread
                    self.check_vr_env_thread = ADBSwitchVrEnvThread(device_id)
                else:
                    log_method_result("switch_vr_env", False, "设备未连接")
                    self.textBrowser.append("设备未连接！")
                    return
                
                self.check_vr_env_thread.progress_signal.connect(self.textBrowser.append)
                self.check_vr_env_thread.result_signal.connect(self.textBrowser.append)
                self.check_vr_env_thread.error_signal.connect(self.textBrowser.append)
                self.check_vr_env_thread.start()
                
                log_method_result("switch_vr_env", True, "线程已启动")
            except Exception as e:
                log_method_result("switch_vr_env", False, str(e))
                self.textBrowser.append(f"切换VR环境失败: {e}")
        else:
            log_method_result("switch_vr_env", False, "设备未连接")
            self.textBrowser.append("设备未连接！")

    def scroll_to_bottom(self):
        scrollbar = self.textBrowser.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def get_running_app_info(self):
        """获取当前运行的应用信息"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("get_running_app_info_button", "获取运行应用信息")

        if device_id in devices_id_lst:
            try:
                if self.connection_mode == 'u2':
                    from Function_Moudle.get_running_app_info_thread import GetRunningAppInfoThread
                    self.get_running_app_info_thread = GetRunningAppInfoThread(self.d)
                elif self.connection_mode == 'adb':
                    from Function_Moudle.adb_get_running_app_info_thread import ADBGetRunningAppInfoThread
                    self.get_running_app_info_thread = ADBGetRunningAppInfoThread(device_id)
                else:
                    log_method_result("get_running_app_info", False, "设备未连接")
                    self.textBrowser.append("设备未连接！")
                    return
                
                self.get_running_app_info_thread.progress_signal.connect(self.textBrowser.append)
                self.get_running_app_info_thread.result_signal.connect(self._handle_running_app_info_result)
                self.get_running_app_info_thread.error_signal.connect(self.textBrowser.append)
                self.get_running_app_info_thread.start()
                
                log_method_result("get_running_app_info", True, "线程已启动")
            except Exception as e:
                log_method_result("get_running_app_info", False, str(e))
                self.textBrowser.append(f"启动获取运行应用信息线程失败: {e}")
        else:
            log_method_result("get_running_app_info", False, "设备未连接")
            self.textBrowser.append("设备未连接！")
    
    def _handle_running_app_info_result(self, app_info):
        """处理运行应用信息结果"""
        if app_info:
            logger.info(f"✓ 当前运行应用: {app_info}")
            self.textBrowser.append(f"✓ 当前运行应用: {app_info}")
        else:
            logger.warning("✗ 未获取到运行应用信息")
            self.textBrowser.append("✗ 未获取到运行应用信息")

    def view_apk_path_wrapper(self):
        """查看应用安装路径"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("view_apk_path", "查看应用安装路径")

        if device_id in devices_id_lst:
            package_name, ok = QInputDialog.getText(self, "输入应用包名", "请输入要查看安装路径的应用包名：")
            if not ok:
                logger.info("用户取消输入")
                return
            
            logger.info(f"查看应用: {package_name}")
            
            try:
                from Function_Moudle.view_apk_path_wrapper_thread import ViewApkPathWrapperThread
                self.view_apk_thread = ViewApkPathWrapperThread(device_id, package_name)
                self.view_apk_thread.progress_signal.connect(self.textBrowser.append)
                self.view_apk_thread.result_signal.connect(self.textBrowser.append)
                self.view_apk_thread.start()
                
                log_method_result("view_apk_path_wrapper", True, f"查询线程已启动: {package_name}")
            except Exception as e:
                log_method_result("view_apk_path_wrapper", False, str(e))
                self.textBrowser.append(f"启动查询线程失败: {e}")
        else:
            log_method_result("view_apk_path_wrapper", False, "设备未连接")
            self.textBrowser.append("设备未连接！")

    # @staticmethod
    # def run_cmd():
    #     user_directory = os.path.expanduser("~")
    #     subprocess.Popen(["start", "cmd", "/k", "cd /d " + user_directory], shell=True)

    def refresh_devices(self):
        """刷新设备列表（多线程执行，避免阻塞主界面）"""
        log_button_click("RefreshButton", "刷新设备列表")
        
        # 检查是否已经有刷新线程在运行
        if hasattr(self, 'refresh_devices_thread') and self.refresh_devices_thread.isRunning():
            logger.warning("刷新设备列表线程已在运行中")
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
            log_thread_start("RefreshDevicesThread", {"action": "刷新设备列表"})
            self.textBrowser.append("开始刷新设备列表...")
            
        except Exception as e:
            logger.error(f"启动刷新线程失败: {e}")
            log_exception(logger, "refresh_devices", e)
            self.textBrowser.append(f"启动刷新线程失败: {e}")
    
    def _on_refresh_thread_finished(self):
        """刷新线程完成后的清理工作"""
        logger.info("设备列表刷新完成")
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
        log_device_operation("u2_connect_attempt", device_id, {"mode": "u2", "action": "尝试u2连接"})
        
        try:
            from Function_Moudle.u2_connect_thread import U2ConnectThread
            self.u2_connect_thread = U2ConnectThread(device_id)
            
            # 连接信号
            self.u2_connect_thread.progress_signal.connect(self.textBrowser.append)
            self.u2_connect_thread.error_signal.connect(self.textBrowser.append)
            self.u2_connect_thread.connected_signal.connect(self._handle_u2_connection_result)
            
            # 启动线程
            self.u2_connect_thread.start()
            log_thread_start("U2ConnectThread", {"device_id": device_id, "mode": "u2"})
            
        except Exception as e:
            logger.error(f"启动u2连接线程失败: {e}")
            self.textBrowser.append(f"启动u2连接线程失败: {e}")
            # 回退到ADB模式
            self.d = None
            self.connection_mode = 'adb'
            log_device_operation("fallback_to_adb", device_id, {"reason": "u2连接失败", "mode": "adb"})
            self.textBrowser.append(f"使用ADB模式: {device_id}")
    
    def _handle_u2_connection_result(self, u2_device, device_id):
        """处理u2连接结果"""
        if u2_device:
            self.d = u2_device
            self.connection_mode = 'u2'
            self.textBrowser.append(f"u2连接成功: {device_id}")
            log_device_operation("u2_connect_success", device_id, {"mode": "u2", "status": "connected"})
            log_thread_complete("U2ConnectThread", "success", {"device_id": device_id, "mode": "u2"})
        else:
            # u2连接失败，使用ADB模式
            self.d = None
            self.connection_mode = 'adb'
            self.textBrowser.append(f"u2连接失败，使用ADB模式: {device_id}")
            log_device_operation("u2_connect_failed", device_id, {"mode": "adb", "reason": "u2连接失败"})
            log_thread_complete("U2ConnectThread", "failed", {"device_id": device_id, "fallback_mode": "adb"})

    def adb_root_wrapper(self):
        """以root权限运行ADB"""
        logger.info("用户操作: 点击 adb_root_button 按钮 -> 以root权限运行ADB")
        
        log_operation("button_click", {
            "button": "adb_root_button",
            "action": "以root权限运行ADB"
        })
        
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            try:
                self.adb_root_thread = AdbRootWrapperThread(device_id)
                self.adb_root_thread.progress_signal.connect(self.textBrowser.append)
                self.adb_root_thread.error_signal.connect(self.textBrowser.append)
                self.adb_root_thread.start()
                
                logger.info("✓ Root权限线程已启动")
            except Exception as e:
                logger.error(f"✗ 获取root权限失败: {e}")
                self.textBrowser.append(f"获取root权限失败: {e}")
        else:
            logger.warning("✗ 设备未连接")
            self.textBrowser.append("设备未连接！")

    def reboot_device(self):
        """重启设备"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("button_reboot", "重启设备")

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
                    log_method_result("reboot_device", True, "重启线程已启动")
                except Exception as e:
                    log_method_result("reboot_device", False, str(e))
                    self.textBrowser.append(f"启动设备重启线程失败: {e}")
            else:
                logger.info("用户取消重启操作")
        else:
            log_method_result("reboot_device", False, "设备未连接")
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
        """截取设备屏幕"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("get_screenshot_button", "截取设备屏幕")

        if device_id in devices_id_lst:
            file_path, _ = QFileDialog.getSaveFileName(self, "保存截图", "", "PNG Files (*.png);;All Files (*)")
            if file_path:
                logger.info(f"保存截图到: {file_path}")
                
                try:
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
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("adb_uninstall_button", "卸载应用")

        if device_id in devices_id_lst:
            package_name, ok = QInputDialog.getText(self, "输入应用包名", "请输入要卸载的应用包名：")
            if ok and package_name:
                logger.info(f"卸载应用: {package_name}")
                
                try:
                    from Function_Moudle.show_uninstall_thread import ShowUninstallThread
                    self.uninstall_thread = ShowUninstallThread(self.d, package_name)
                    self.uninstall_thread.progress_signal.connect(self.textBrowser.append)
                    self.uninstall_thread.result_signal.connect(self.textBrowser.append)
                    self.uninstall_thread.error_signal.connect(self.textBrowser.append)
                    self.uninstall_thread.start()
                    
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
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("adb_pull_file_button", "从设备拉取文件")

        if device_id in devices_id_lst:
            try:
                file_path_on_device, ok = QInputDialog.getText(self, "输入设备文件路径", "请输入车机上的文件路径:")
                import pathlib
                file_path = pathlib.Path(file_path_on_device)
                apk_file_name = pathlib.Path(file_path).name
                if ok and file_path_on_device:
                    local_path = QFileDialog.getExistingDirectory(self, "选择文件夹", ".")
                    if local_path:
                        logger.info(f"拉取文件: {file_path_on_device} -> {local_path}")
                        
                        from Function_Moudle.pull_files_thread import PullFilesThread
                        self.pull_files_thread = PullFilesThread(device_id, file_path_on_device, local_path)
                        self.pull_files_thread.progress_signal.connect(self.textBrowser.append)
                        self.pull_files_thread.result_signal.connect(self.textBrowser.append)
                        self.pull_files_thread.start()
                        
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
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("adb_install_button", "安装应用")

        if device_id in devices_id_lst:
            package_path, ok = QFileDialog.getOpenFileName(self, "选择应用安装包", "",
                                                          "APK Files (*.apk);;All Files (*)")
            if ok:
                logger.info(f"选择文件: {package_path}")
                
                try:
                    from Function_Moudle.install_file_thread import InstallFileThread
                    self.install_file_thread = InstallFileThread(self.d, package_path)
                    self.install_file_thread.progress_signal.connect(self.textBrowser.append)
                    self.install_file_thread.signal_status.connect(self.textBrowser.append)
                    self.install_file_thread.start()
                    
                    log_method_result("show_install_file_dialog", True, f"安装线程已启动: {os.path.basename(package_path)}")
                except Exception as e:
                    log_method_result("show_install_file_dialog", False, str(e))
                    self.textBrowser.append(f"启动安装线程失败: {e}")
            else:
                logger.info("用户取消文件选择")
        else:
            log_method_result("show_install_file_dialog", False, "设备未连接")
            self.textBrowser.append("设备未连接！")

    @staticmethod
    def adb_push_file(local_file_path, target_path_on_device, device_id):
        command = f"adb -s {device_id} push {local_file_path} {target_path_on_device}"
        try:
            subprocess.run(command, shell=True, check=True)
            return "文件推送成功！"
        except subprocess.CalledProcessError as e:
            return f"文件推送失败: {e}"

    def show_push_file_dialog(self):
        """推送文件到设备"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("adb_push_file_button", "推送文件到设备")

        if device_id in devices_id_lst:
            local_file_path, _ = QFileDialog.getOpenFileName(self, "选择本地文件", "", "All Files (*)")
            if local_file_path:
                logger.info(f"选择文件: {local_file_path}")
                
                target_path_on_device, ok = QInputDialog.getText(self, "输入设备文件路径",
                                                                 "请输入车机上的目标路径:")
                if ok and target_path_on_device:
                    logger.info(f"目标路径: {target_path_on_device}")
                    
                    res = self.adb_push_file(local_file_path, target_path_on_device, device_id)
                    self.textBrowser.append(res)
                    
                    if "成功" in res:
                        log_method_result("show_push_file_dialog", True, f"{os.path.basename(local_file_path)} -> {target_path_on_device}")
                    else:
                        log_method_result("show_push_file_dialog", False, res)
                else:
                    logger.info("用户取消输入目标路径")
            else:
                logger.info("用户取消文件选择")
        else:
            log_method_result("show_push_file_dialog", False, "设备未连接")
            self.textBrowser.append("设备未连接！")

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
        """重启ADB服务"""
        log_button_click("reboot_adb_service_button", "重启ADB服务")
        
        from Function_Moudle.simulate_long_press_dialog_thread import simulate_long_press_dialog_thread
        self.simulate_long_press_dialog_thread = simulate_long_press_dialog_thread(self.d)
        self.simulate_long_press_dialog_thread.result_signal.connect(self.textBrowser.append)
        self.simulate_long_press_dialog_thread.error_signal.connect(self.textBrowser.append)
        self.simulate_long_press_dialog_thread.start()
        
        log_method_result("show_simulate_long_press_dialog", True, "ADB服务重启线程已启动")

    def show_input_text_dialog(self):
        """输入文本到设备"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("input_text_via_adb_button", "输入文本到设备")

        if device_id in devices_id_lst:
            text_to_input, ok = QInputDialog.getText(self, "输入文本", "请输入要通过 ADB 输入的文本:")
            if ok and text_to_input:
                logger.info(f"输入文本: {text_to_input}")
                
                try:
                    from Function_Moudle.input_text_thread import InputTextThread
                    self.input_text_thread = InputTextThread(self.d, text_to_input)
                    self.input_text_thread.progress_signal.connect(self.textBrowser.append)
                    self.input_text_thread.error_signal.connect(self.textBrowser.append)
                    self.input_text_thread.start()
                    
                    log_method_result("show_input_text_dialog", True, f"输入线程已启动: {text_to_input[:20]}...")
                except Exception as e:
                    log_method_result("show_input_text_dialog", False, str(e))
                    self.textBrowser.append(f"启动输入线程失败: {e}")
            else:
                logger.info("用户取消输入或输入为空")
        else:
            log_method_result("show_input_text_dialog", False, "设备未连接")
            self.textBrowser.append("设备未连接！")

    def show_force_stop_app_dialog(self):
        """强制停止应用"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("force_stop_app", "强制停止应用")

        if device_id in devices_id_lst:
            try:
                if self.connection_mode == 'u2':
                    # u2连接成功，自动获取当前前台app并停止
                    try:
                        # 获取当前前台应用信息
                        current_app = self.d.app_current()
                        if current_app and 'package' in current_app:
                            package_name = current_app['package']
                            logger.info(f"强制停止应用: {package_name}")
                            
                            from Function_Moudle.force_stop_app_thread import ForceStopAppThread
                            self.Force_app_thread = ForceStopAppThread(self.d, package_name)
                            self.Force_app_thread.progress_signal.connect(self.textBrowser.append)
                            self.Force_app_thread.result_signal.connect(self.textBrowser.append)
                            self.Force_app_thread.start()
                            
                            log_method_result("show_force_stop_app_dialog", True, f"已停止: {package_name}")
                        else:
                            log_method_result("show_force_stop_app_dialog", False, "未获取到前台应用")
                            self.textBrowser.append("未获取到当前前台应用！")
                    except Exception as e:
                        log_method_result("show_force_stop_app_dialog", False, str(e))
                        self.textBrowser.append(f"获取前台应用失败: {e}")
                elif self.connection_mode == 'adb':
                    # ADB模式，需要手动输入包名
                    package_name, ok = QInputDialog.getText(self, "强制停止应用", "请输入要停止的应用包名：")
                    if not ok or not package_name.strip():
                        logger.info("用户取消输入或输入为空")
                        self.textBrowser.append("用户取消输入或输入为空")
                        return
                    
                    logger.info(f"强制停止应用: {package_name}")
                    
                    from Function_Moudle.force_stop_app_thread import ForceStopAppThread
                    self.Force_app_thread = ForceStopAppThread(self.d, package_name)
                    self.Force_app_thread.progress_signal.connect(self.textBrowser.append)
                    self.Force_app_thread.result_signal.connect(self.textBrowser.append)
                    self.Force_app_thread.start()
                    
                    log_method_result("show_force_stop_app_dialog", True, f"已停止: {package_name}")
                else:
                    log_method_result("show_force_stop_app_dialog", False, "设备未连接")
                    self.textBrowser.append("设备未连接！")
            except Exception as e:
                log_method_result("show_force_stop_app_dialog", False, str(e))
                self.textBrowser.append(f"强制停止应用失败: {e}")
        else:
            log_method_result("show_force_stop_app_dialog", False, "设备未连接")
            self.textBrowser.append("未连接设备！")
    
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
        """清除应用缓存"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("clear_app_cache_button", "清除应用缓存")

        try:
            if device_id not in devices_id_lst:
                log_method_result("show_clear_app_cache_dialog", False, "设备未连接")
                self.textBrowser.append("设备未连接！")
                return
            
            if self.connection_mode == 'u2':
                # u2连接成功，自动获取当前前台app并清除缓存
                self.textBrowser.append("正在获取当前前台应用...")
                
                # 获取当前前台应用
                current_app = self.d.app_current()
                if current_app and 'package' in current_app:
                    package_name = current_app['package']
                    logger.info(f"清除缓存: {package_name}")
                    self.textBrowser.append(f"当前前台应用: {package_name}")
                    self.textBrowser.append(f"正在清除应用 {package_name} 的缓存...")
                    
                    from Function_Moudle.clear_app_cache_thread import ClearAppCacheThread
                    self.Clear_app_cache_thread = ClearAppCacheThread(self.d, package_name)
                    self.Clear_app_cache_thread.progress_signal.connect(self.textBrowser.append)
                    self.Clear_app_cache_thread.result_signal.connect(self.textBrowser.append)
                    self.Clear_app_cache_thread.error_signal.connect(self.textBrowser.append)
                    self.Clear_app_cache_thread.start()
                    
                    log_method_result("show_clear_app_cache_dialog", True, f"清除缓存线程已启动: {package_name}")
                else:
                    log_method_result("show_clear_app_cache_dialog", False, "未获取到前台应用")
                    self.textBrowser.append("未获取到当前前台应用！")
                    
            elif self.connection_mode == 'adb':
                # ADB模式，需要手动输入包名
                package_name, ok = QInputDialog.getText(self, "清除应用缓存", "请输入要清除缓存的应用包名：")
                if not ok or not package_name.strip():
                    logger.info("用户取消输入或输入为空")
                    self.textBrowser.append("用户取消输入或输入为空")
                    return
                
                logger.info(f"清除缓存: {package_name}")
                self.textBrowser.append(f"正在清除应用 {package_name} 的缓存...")
                
                from Function_Moudle.clear_app_cache_thread import ClearAppCacheThread
                self.Clear_app_cache_thread = ClearAppCacheThread(self.d, package_name)
                self.Clear_app_cache_thread.progress_signal.connect(self.textBrowser.append)
                self.Clear_app_cache_thread.result_signal.connect(self.textBrowser.append)
                self.Clear_app_cache_thread.error_signal.connect(self.textBrowser.append)
                self.Clear_app_cache_thread.start()
                
                log_method_result("show_clear_app_cache_dialog", True, f"清除缓存线程已启动: {package_name}")
            else:
                log_method_result("show_clear_app_cache_dialog", False, "设备未连接")
                self.textBrowser.append("设备未连接！")
                
        except Exception as e:
            log_method_result("show_clear_app_cache_dialog", False, str(e))
            self.textBrowser.append(f"清除应用缓存失败: {e}")
    
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
        """获取当前前台应用包名"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("app_package_and_activity", "获取前台应用包名")

        if device_id in devices_id_lst:
            try:
                if self.connection_mode == 'u2':
                    from Function_Moudle.get_foreground_package_thread import GetForegroundPackageThread
                    self.GetForegroundPackageThread = GetForegroundPackageThread(self.d)
                elif self.connection_mode == 'adb':
                    from Function_Moudle.adb_get_foreground_package_thread import ADBGetForegroundPackageThread
                    self.GetForegroundPackageThread = ADBGetForegroundPackageThread(device_id)
                else:
                    log_method_result("get_foreground_package", False, "设备未连接")
                    self.textBrowser.append("设备未连接！")
                    return
                
                self.GetForegroundPackageThread.progress_signal.connect(self.textBrowser.append)
                self.GetForegroundPackageThread.result_signal.connect(self._handle_foreground_package_result)
                self.GetForegroundPackageThread.error_signal.connect(self.textBrowser.append)
                self.GetForegroundPackageThread.start()
                
                log_method_result("get_foreground_package", True, "线程已启动")
            except Exception as e:
                log_method_result("get_foreground_package", False, str(e))
                self.textBrowser.append(f"启动获取前台应用线程失败: {e}")
        else:
            log_method_result("get_foreground_package", False, "设备未连接")
            self.textBrowser.append("设备未连接！")
    
    def _handle_foreground_package_result(self, package_info):
        """处理前台应用包名结果"""
        if package_info:
            logger.info(f"✓ 前台应用: {package_info}")
            self.textBrowser.append(f"✓ 前台应用: {package_info}")
        else:
            logger.warning("✗ 未获取到前台应用信息")
            self.textBrowser.append("✗ 未获取到前台应用信息")

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
        """获取APK包名"""
        log_button_click("aapt_getpackagename_button", "获取APK包名")
        
        file_path, _ = QFileDialog.getOpenFileName(self, "选择APK文件", "", "APK文件 (*.apk)")
        if file_path:
            logger.info(f"选择APK: {file_path}")
            try:
                from Function_Moudle.aapt_get_package_name_thread import AaptGetPackageNameThread
                self.aapt_thread = AaptGetPackageNameThread(file_path)
                self.aapt_thread.result_signal.connect(self.textBrowser.append)
                self.aapt_thread.error_signal.connect(self.textBrowser.append)
                self.aapt_thread.start()
                log_method_result("aapt_getpackage_name_dilog", True, f"aapt线程已启动: {os.path.basename(file_path)}")
            except Exception as e:
                log_method_result("aapt_getpackage_name_dilog", False, str(e))
                self.textBrowser.append(f"启动aapt线程失败: {e}")
        else:
            logger.info("未选择APK文件")
            self.textBrowser.append("未选择APK文件")


    def browse_log_save_path(self):
        """浏览日志保存路径"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("browse_log_save_path_button", "浏览日志保存路径")
        
        if device_id in devices_id_lst:
            if hasattr(self, 'PullLogSaveThread') and self.PullLogSaveThread and self.PullLogSaveThread.isRunning():
                self.PullLogSaveThread.stop()
                self.pull_log_button.setText("拉取日志")
                logger.info("停止拉取日志")
            else:
                self.file_path = QFileDialog.getExistingDirectory(self, "选择保存路径", "")
                if self.file_path:
                    self.inputbox_log_path.setText(self.file_path)
                    logger.info(f"选择路径: {self.file_path}")
                else:
                    logger.info("用户取消选择")
                    self.textBrowser.append("已取消！")
        else:
            log_method_result("browse_log_save_path", False, "设备未连接")
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
        
        # 调整控件大小
        self.adjust_widget_sizes(scale_ratio)
    
    
    
    def adjust_widget_sizes(self, scale_ratio):
    
            """根据缩放比例调整控件最小/最大尺寸"""
    
            try:
    
                from PyQt5.QtWidgets import QSizePolicy
    
                
    
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
    
                        # 所有其他按钮都使用与ADB页面一致的Expanding缩放方式
    
                        # 设置Expanding尺寸策略
    
                        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    
                        button.setSizePolicy(size_policy)
    
                        
    
                        # 不设置固定的最小/最大尺寸，让布局自动调整
    
                        button.setMinimumSize(0, 0)
    
                        button.setMaximumSize(16777215, 16777215)
    
                
    
                # 处理ComboBox控件
    
                comboboxes = self.findChildren(QComboBox)
    
                for combobox in comboboxes:
    
                    combobox_name = combobox.objectName()
    
                    
    
                    if combobox_name == 'ComboxButton':
    
                        # 设备选择下拉框保持合理的最大宽度
    
                        combobox.setMinimumSize(150, 30)
    
                        combobox.setMaximumSize(500, 50)
    
                    else:
    
                        # 其他下拉框也使用Expanding策略
    
                        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    
                        combobox.setSizePolicy(size_policy)
    
                        combobox.setMinimumSize(0, 0)
    
                        combobox.setMaximumSize(16777215, 16777215)
    
                
    
                # 特别处理大通页面布局容器
    
                self.adjust_datong_layout(scale_ratio)
    
                        
    
            except Exception as e:
    
                # 控件大小调整失败时不中断程序
    
                print(f"调整控件大小时出错: {e}")
    
    def adjust_datong_layout(self, scale_ratio):
        """调整大通页面布局容器大小"""
        try:
            from PyQt5.QtWidgets import QWidget
            
            # 查找大通页面的布局容器
            layout_widget = self.findChild(QWidget, "layoutWidget")
            if layout_widget:
                # 获取原始布局容器尺寸（从UI文件中读取的原始尺寸）
                original_width = 301
                original_height = 235
                
                # 计算新的尺寸
                new_width = int(original_width * scale_ratio)
                new_height = int(original_height * scale_ratio)
                
                # 确保最小尺寸
                new_width = max(new_width, 280)  # 稍微小于原始宽度，给按钮留出边距
                new_height = max(new_height, 280)  # 增加高度以容纳所有按钮
                
                # 设置固定尺寸（resize方法）
                layout_widget.resize(new_width, new_height)
                
                # 更新布局
                layout_widget.updateGeometry()
                
        except Exception as e:
            # 布局调整失败时不中断程序
            print(f"调整大通页面布局时出错: {e}")
    
    def reinit_uiautomator2(self):
        """重新初始化uiautomator2服务"""
        log_button_click("reinit_u2_button", "重新初始化uiautomator2")
        
        # 获取当前选择的设备
        device_id = self.get_selected_device()
        
        if not device_id:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "未选择设备", "请先选择一个设备！")
            return
        
        # 确认对话框
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
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
            self.textBrowser.append("用户取消重新初始化操作")
            return
        
        try:
            # 创建进度对话框
            from Function_Moudle.u2_reinit_dialog import U2ReinitDialog
            self.u2_reinit_dialog = U2ReinitDialog(self)
            
            # 创建重新初始化线程
            from Function_Moudle.u2_reinit_thread import U2ReinitThread
            self.u2_reinit_thread = U2ReinitThread(device_id, self.d)
            
            # 连接信号
            self.u2_reinit_thread.progress_signal.connect(self.u2_reinit_dialog.add_progress)
            self.u2_reinit_thread.error_signal.connect(self.u2_reinit_dialog.set_error)
            self.u2_reinit_thread.success_signal.connect(self.u2_reinit_dialog.set_success)
            self.u2_reinit_thread.finished_signal.connect(self._on_u2_reinit_finished)
            
            # 同时也输出到主窗口的textBrowser
            self.u2_reinit_thread.progress_signal.connect(self.textBrowser.append)
            self.u2_reinit_thread.error_signal.connect(self.textBrowser.append)
            self.u2_reinit_thread.success_signal.connect(self.textBrowser.append)
            
            # 开始初始化
            self.u2_reinit_dialog.start()
            self.u2_reinit_thread.start()
            
            # 显示对话框
            self.u2_reinit_dialog.exec_()
            
        except ImportError as e:
            self.textBrowser.append(f"无法导入重新初始化模块: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "重新初始化失败", 
                f"无法启动重新初始化功能:\n\n{str(e)}")
        except Exception as e:
            self.textBrowser.append(f"启动重新初始化失败: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "重新初始化失败", 
                f"启动重新初始化时发生错误:\n\n{str(e)}")
    
    def _on_u2_reinit_finished(self):
        """u2重新初始化完成后的处理"""
        if self.u2_reinit_thread and self.u2_reinit_thread.isRunning():
            return
        
        # 重新连接设备
        try:
            self.textBrowser.append("正在重新连接设备...")
            
            # 延迟一下，确保u2服务完全启动
            import time
            time.sleep(1)
            
            # 重新刷新设备列表
            self.refresh_devices()
            
            self.textBrowser.append("✓ 设备重新连接成功")
            
        except Exception as e:
            self.textBrowser.append(f"重新连接设备时出错: {e}")
        
        # 清理
        if self.u2_reinit_thread:
            self.u2_reinit_thread.deleteLater()
            self.u2_reinit_thread = None
    
    def update_scaling_settings(self):
        """更新缩放设置（可用于配置对话框）"""
        # 这里可以添加从配置文件读取缩放设置的逻辑
        pass
