from PyQt5.QtWidgets import (QMainWindow, QFileDialog, QInputDialog, QMessageBox)
import io
import subprocess
from Function_Moudle.thread_factory import thread_factory
from Function_Moudle.operation_history import OperationHistoryManager
from Function_Moudle.error_dialog import (
    show_error_message, show_warning_message, 
    show_info_message, show_critical_message
)
from Function_Moudle.operation_guide import (
    show_quick_guide, create_device_setup_guide,
    create_app_install_guide
)
import uiautomator2 as u2

# 确保 Nuitka 兼容性（必须在 import uiautomator2 之后调用）
from nuitka_compat import ensure_nuitka_compatibility
ensure_nuitka_compatibility()

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

from ui_theme_manager import ThemeManager

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
        try:
            # 尝试从当前目录加载
            uic.loadUi('adbtool.ui', self)
            # uic.loadUi('adbtool_modern.ui', self)
        except Exception as e:
            print(f"加载 adbtool.ui 失败: {e}")
            # 尝试从项目根目录加载
            import os
            project_root = os.path.dirname(os.path.abspath(__file__))
            ui_path = os.path.join(project_root, 'adbtool.ui')
            print(f"尝试从 {ui_path} 加载...")
            uic.loadUi(ui_path, self)
        # 假设这里是初始化UI控件的部分，使用findChild方法获取控件
        from PyQt5 import QtWidgets
        self.RefreshButton = self.findChild(QtWidgets.QPushButton, 'RefreshButton')
        self.ComboxButton = self.findChild(QtWidgets.QComboBox, 'ComboxButton')
        self.modeSwitchCheckBox = self.findChild(QtWidgets.QCheckBox, 'modeSwitchCheckBox')
        self.vr_keyevent_combo = self.findChild(QtWidgets.QComboBox, 'vr_keyevent_combo')
        self.datong_factory_button = self.findChild(QtWidgets.QPushButton, 'datong_factory_button')
        self.datong_disable_verity_button = self.findChild(QtWidgets.QPushButton, 'datong_disable_verity_button')
        self.datong_enable_verity_button = self.findChild(QtWidgets.QPushButton, 'datong_enable_verity_button')
        self.datong_batch_install_button = self.findChild(QtWidgets.QPushButton, 'datong_batch_install_button')
        self.datong_batch_install_test_button = self.findChild(QtWidgets.QPushButton, 'datong_batch_install_test_button')
        self.datong_input_password_button = self.findChild(QtWidgets.QPushButton, 'datong_input_password_button')
        self.datong_open_telenav_engineering_button = self.findChild(QtWidgets.QPushButton, 'datong_open_telenav_engineering_button')
        self.datong_set_datetime_button = self.findChild(QtWidgets.QPushButton, 'datong_set_datetime_button')
        self.d = None
        self.device_id = None
        self.connection_mode = None  # 'u2' 或 'adb'
        self.u2_connecting = False  # U2正在连接中的标志
        # 重定向输出流为textBrowser
        self.text_edit_output_stream = TextEditOutputStream(self.textBrowser)
        
        # 初始化功能管理器（必须在信号连接之前）
        from Function_Moudle.datong_manager import DatongManager
        from Function_Moudle.vr_controller import VRController
        from Function_Moudle.device_manager import DeviceManager
        from Function_Moudle.log_operations import LogManager
        from Function_Moudle.file_operations import FileOperationsManager
        from Function_Moudle.input_operations import InputOperationsManager
        from Function_Moudle.app_operations import AppOperationsManager
        self.datong_manager = DatongManager(self)
        self.vr_controller = VRController(self)
        self.device_manager = DeviceManager(self)
        self.log_operations = LogManager(self)
        self.file_operations = FileOperationsManager(self)
        self.input_operations = InputOperationsManager(self)
        self.app_operations = AppOperationsManager(self)
        
        # 初始化操作历史管理器
        self.operation_history = OperationHistoryManager(max_history_size=50)
        
        # 连接操作历史信号
        self.operation_history.can_undo_changed_signal.connect(self._update_undo_redo_status)
        self.operation_history.can_redo_changed_signal.connect(self._update_undo_redo_status)
        
        try:
            # 刷新设备列表（refresh_devices方法内部会尝试u2连接）
            self.refresh_devices()
        except Exception as e:
            self.textBrowser.append(str(e))
        self.ComboxButton.activated[str].connect(self.on_combobox_changed)
        self.modeSwitchCheckBox.stateChanged.connect(self.on_mode_switch_changed)
        self.view_apk_path.clicked.connect(self.view_apk_path_wrapper)  # 显示应用安装路径
        self.input_text_via_adb_button.clicked.connect(self.show_input_text_dialog)  # 输入文本
        self.get_screenshot_button.clicked.connect(self.show_screenshot_dialog)  # 截图
        self.force_stop_app.clicked.connect(self.show_force_stop_app_dialog)  # 强制停止应用
        self.adb_uninstall_button.clicked.connect(self.show_uninstall_dialog)  # 卸载应用
        self.file_manager_button.clicked.connect(self.file_operations.show_file_manager_dialog)  # 文件管理
        self.reboot_adb_service_button.clicked.connect(self.show_simulate_long_press_dialog)  # 模拟长按
        self.adb_install_button.clicked.connect(self.show_install_file_dialog)  # 安装应用
        self.clear_app_cache_button.clicked.connect(self.show_clear_app_cache_dialog)  # 清除应用缓存
        self.app_package_and_activity.clicked.connect(self.get_foreground_package)
        self.get_running_app_info_button.clicked.connect(self.get_running_app_info)  # 获取当前运行的应用信息
        self.aapt_getpackagename_button.clicked.connect(self.aapt_getpackage_name_dilog)  # 获取apk包名
        self.textBrowser.textChanged.connect(self.scroll_to_bottom)  # 自动滚动到底部
        
        # VR 功能信号连接
        self.switch_vr_env_button.clicked.connect(self.vr_controller.switch_vr_env)  # 切换VR环境
        self.VR_nework_check_button.clicked.connect(self.vr_controller.check_vr_network)  # 检查VR网络
        self.activate_VR_button.clicked.connect(self.vr_controller.activate_vr)  # 激活VR
        self.skipping_powerlimit_button.clicked.connect(self.vr_controller.skip_power_limit)  # 跳过电源挡位限制
        self.set_vr_server_timout.clicked.connect(self.vr_controller.set_vr_timeout)  # 设置VR服务器超时
        
        # 设备管理信号连接
        self.RefreshButton.clicked.connect(self.device_manager.refresh_devices)  # 刷新设备列表
        self.button_reboot.clicked.connect(self.device_manager.reboot_device)  # 重启设备
        self.DisconnectButton.clicked.connect(self.device_manager.disconnect_device)  # 断开设备连接
        
        # 日志操作信号连接
        self.browse_log_save_path_button.clicked.connect(self.log_operations.browse_log_save_path)  # 浏览日志保存路径
        self.pull_log_button.clicked.connect(self.log_operations.pull_log)  # 拉取日志
        self.open_path_buttom.clicked.connect(self.log_operations.open_path)  # 打开文件所在目录
        self.voice_start_record_button.clicked.connect(self.log_operations.voice_start_record)  # 开始语音录制
        self.voice_stop_record_button.clicked.connect(self.log_operations.voice_stop_record)  # 停止语音录制
        self.voice_pull_record_file_button.clicked.connect(self.log_operations.voice_pull_record_file)  # 拉取录音文件
        self.remove_record_file_button.clicked.connect(self.log_operations.remove_voice_record_file)  # 删除语音录制文件
        
        # 其他信号连接
        self.list_package_button.clicked.connect(self.list_package)
        self.adb_root_button.clicked.connect(self.adb_root_wrapper)  # 获取root权限
        self.enter_engineering_mode_button.clicked.connect(self.open_engineering_mode)  # 进入工程模式
        self.AS33_CR_enter_engineering_mode_button.clicked.connect(self.as33_cr_enter_engineering)
        self.AS33R_open_engineering_mode_button.clicked.connect(self.as33r_open_engineering_mode)  # AS33R国项目打开工程模式
        self.AS33R_open_secondary_engineering_mode_button.clicked.connect(self.as33r_enter_secondary_engineering_mode)
        self.open_update_page_button.clicked.connect(self.open_soimt_update)  # 打开资源升级页面
        self.select_releasenote_excel_button.clicked.connect(self.select_releasenote_excel)  # 选择集成清单文件
        self.start_check_button.clicked.connect(self.app_version_check)
        self.upgrade_page_button.clicked.connect(self.open_yf_page)
        self.start_app.clicked.connect(self.app_operations.show_start_app_dialog)  # 启动应用
        
        # 大通功能信号连接
        self.datong_factory_button.clicked.connect(self.datong_manager.factory_action)  # 拉起中环工厂
        self.datong_disable_verity_button.clicked.connect(self.datong_manager.disable_verity_action)  # 禁用verity校验
        self.datong_enable_verity_button.clicked.connect(self.datong_manager.enable_verity_action)  # 启用verity校验
        self.datong_batch_install_button.clicked.connect(self.datong_manager.batch_install_action)  # 批量安装APK文件
        self.datong_batch_install_test_button.clicked.connect(self.datong_manager.batch_verify_version_action)  # 验证批量推包版本号
        self.datong_input_password_button.clicked.connect(self.datong_manager.input_password_action)  # 一键输入密码
        self.datong_open_telenav_engineering_button.clicked.connect(self.datong_manager.open_telenav_engineering_action)  # 打开泰维地图工程模式
        self.datong_set_datetime_button.clicked.connect(self.datong_manager.set_datetime_action)  # 设置设备日期时间
        
        # 添加重新初始化u2按钮（如果UI中有）
        try:
            self.reinit_u2_button = self.findChild(QtWidgets.QPushButton, 'reinit_u2_button')
            if self.reinit_u2_button:
                self.reinit_u2_button.clicked.connect(self.reinit_uiautomator2)
        except Exception:
            pass
        
        # ========== 侧边栏导航按钮绑定 ==========
        self._init_navigation_buttons()
        
        # 添加配置菜单
        self.add_config_menu()
        self.add_theme_menu()
        
        # 添加配置按钮（如果UI中有）
        try:
            self.config_button = self.findChild(QtWidgets.QPushButton, 'config_button')
            if self.config_button:
                self.config_button.clicked.connect(self.open_config_dialog)
        except Exception:
            pass
        
        # 窗口缩放功能初始化
        self.init_window_scaling()
        
        # 设置窗口标题包含版本号
        self.setWindowTitle(f"ADBTools v{self.VERSION}")
        
        # 启动时自动检查更新（延迟3秒执行，避免阻塞启动）
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(3000, self.check_for_updates_silent)

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

    def _init_navigation_buttons(self):
        """初始化侧边栏导航按钮"""
        from PyQt5 import QtWidgets
        
        # 导航按钮名称列表（对应UI中的按钮名称）
        self.nav_buttons = []
        self.nav_button_names = [
            'nav_adb_button',        # ADB工具
            'nav_datong_button',     # 大通项目
            'nav_cr_button',         # CR项目
            'nav_pulllog_button',    # Pull Log
            'nav_internet_button',   # 网联版项目
            'nav_voice_button',      # 语音相关
            'nav_checkversion_button' # 集成版本检查
        ]
        
        # 获取所有导航按钮
        for name in self.nav_button_names:
            btn = self.findChild(QtWidgets.QPushButton, name)
            if btn:
                self.nav_buttons.append(btn)
        
        # 绑定点击事件
        for index, btn in enumerate(self.nav_buttons):
            btn.clicked.connect(lambda checked, idx=index: self._on_nav_button_clicked(idx))
        
        # 默认选中第一个按钮
        if self.nav_buttons:
            self._update_nav_button_style(0)
    
    def _on_nav_button_clicked(self, index):
        """导航按钮点击事件处理"""
        # 切换tabWidget页面
        if hasattr(self, 'tabWidget') and self.tabWidget:
            self.tabWidget.setCurrentIndex(index)
        
        # 更新按钮样式
        self._update_nav_button_style(index)
    
    def _update_nav_button_style(self, active_index):
        """更新导航按钮的选中状态样式"""
        from ui_theme_manager import ThemeManager
        is_dark = ThemeManager.is_dark_theme()
        
        # 根据深浅色主题自动选择文字颜色
        active_text_color = "white" if is_dark else "#0078d4"
        inactive_text_color = "#909090" if is_dark else "#404040"
        
        # 移除硬编码的颜色，改用半透明背景和自适应边框，以适应不同主题
        active_style = f"""QPushButton {{
    background: rgba(0, 120, 212, 0.4);
    color: {active_text_color};
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 6px;
    text-align: left;
    padding-left: 10px;
    font-weight: bold;
}}
QPushButton:hover {{
    background: rgba(0, 120, 212, 0.6);
}}"""
        
        inactive_style = f"""QPushButton {{
    background: transparent;
    color: {inactive_text_color};
    border: none;
    border-radius: 6px;
    text-align: left;
    padding-left: 10px;
}}
QPushButton:hover {{
    background: rgba(128, 128, 128, 0.2);
}}"""
        
        for i, btn in enumerate(self.nav_buttons):
            if i == active_index:
                btn.setStyleSheet(active_style)
            else:
                btn.setStyleSheet(inactive_style)

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
        
        # 打开日志目录
        open_log_dir_action = QtWidgets.QAction('打开日志目录', self)
        open_log_dir_action.triggered.connect(self.open_log_directory)
        settings_menu.addAction(open_log_dir_action)
        
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
        
        # 编辑菜单（添加撤销/重做功能）
        edit_menu = menubar.addMenu('编辑')
        
        # 撤销操作
        self.undo_action = QtWidgets.QAction('撤销', self)
        self.undo_action.setShortcut('Ctrl+Z')
        self.undo_action.triggered.connect(self.undo)
        self.undo_action.setEnabled(False)
        edit_menu.addAction(self.undo_action)
        
        # 重做操作
        self.redo_action = QtWidgets.QAction('重做', self)
        self.redo_action.setShortcut('Ctrl+Y')
        self.redo_action.triggered.connect(self.redo)
        self.redo_action.setEnabled(False)
        edit_menu.addAction(self.redo_action)
        
        # 分隔线
        edit_menu.addSeparator()
        
        # 快速入门
        quick_start_action = QtWidgets.QAction('快速入门', self)
        quick_start_action.triggered.connect(self.show_quick_start_guide)
        edit_menu.addAction(quick_start_action)

    def add_theme_menu(self):
        """添加皮肤切换菜单"""
        from PyQt5 import QtWidgets
        from ui_theme_manager import ThemeManager
        
        menubar = self.menuBar()
        self.theme_menu = menubar.addMenu('皮肤主题')
        self.theme_actions = {}  # 存储 action 以便后续更新对勾
        
        current_theme = ThemeManager.get_current_theme()
        
        # 遍历所有主题选项
        for theme_id, theme_name in ThemeManager.THEMES.items():
            action = QtWidgets.QAction(theme_name, self)
            action.setCheckable(True)
            # 如果是当前主题，则勾选
            if theme_id == current_theme:
                action.setChecked(True)
                
            action.triggered.connect(lambda checked, t=theme_id: self.change_theme(t))
            self.theme_menu.addAction(action)
            self.theme_actions[theme_id] = action

    def change_theme(self, theme_id):
        """切换主题"""
        app = QApplication.instance()
        if app:
            # 获取当前主题名用于日志
            theme_name = ThemeManager.THEMES.get(theme_id, theme_id)
            
            # 在 apply_theme 内部已经处理了配置保存
            try:
                success, msg = ThemeManager.apply_theme(app, theme_id)
                if success:
                    self.textBrowser.append(msg)
                    # 更新菜单对勾
                    self.update_theme_menu_checks(theme_id)
                    # 如果切换到高级 Win11 模式，提示需要重启
                    if "win11" in theme_id:
                        self.textBrowser.append("提示：检测到您开启了高级 Win11 模式，部分组件将在重启后完全应用。")
                else:
                    self.textBrowser.append(f"切换主题失败: {theme_name}")
                    self.textBrowser.append(f"错误详情:\n{msg}")
                    # 恢复之前的勾选状态
                    self.update_theme_menu_checks(ThemeManager.get_current_theme())
            except Exception as e:
                import traceback
                self.textBrowser.append(f"切换主题异常: {theme_name}")
                self.textBrowser.append(f"错误信息: {e}\n{traceback.format_exc()}")

    def update_theme_menu_checks(self, active_theme_id):
        """更新皮肤菜单的对勾状态"""
        if hasattr(self, 'theme_actions'):
            for theme_id, action in self.theme_actions.items():
                action.setChecked(theme_id == active_theme_id)

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

    def open_log_directory(self):
        """打开日志目录"""
        import os
        import subprocess
        import sys
        from logger_manager import logger_manager
        
        try:
            log_dir = logger_manager.log_dir
            
            # 确保日志目录存在
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            # 根据操作系统打开目录
            if sys.platform == 'win32':
                os.startfile(log_dir)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', log_dir])
            else:  # Linux
                subprocess.run(['xdg-open', log_dir])
                
            self.textBrowser.append(f"已打开日志目录: {log_dir}")
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "错误", f"无法打开日志目录: {e}")
            self.textBrowser.append(f"打开日志目录失败: {e}")

    def check_for_updates(self):
        """检查更新"""
        try:
            # 使用线程工厂创建检查更新线程
            self.check_update_thread = thread_factory.create_thread(
                'check_update', 
                current_version=self.VERSION
            )
            
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

    def check_for_updates_silent(self):
        """
        静默检查更新（启动时自动调用）
        
        - 有更新：弹窗提示
        - 无更新：不做任何提示
        - 检查失败：不做任何提示
        """
        try:
            # 使用线程工厂创建检查更新线程
            self.check_update_thread_silent = thread_factory.create_thread(
                'check_update', 
                current_version=self.VERSION
            )
            
            # 只连接更新可用的信号，无更新和失败时不做任何提示
            self.check_update_thread_silent.update_available_signal.connect(self.handle_update_available_silent)
            
            # 启动线程（静默，不显示任何进度信息）
            self.check_update_thread_silent.start()
            
        except Exception as e:
            # 静默失败，不提示用户
            logger.debug(f"启动时静默检查更新失败: {e}")

    def handle_update_available_silent(self, update_info):
        """
        静默处理有更新可用的信号（启动时自动检查用）
        
        只弹窗提示有新版本，不显示在 textBrowser 中
        """
        from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
        from Function_Moudle.dialog_styles import apply_dialog_style, TITLE_LABEL_STYLE
        
        current_version = update_info.get('current_version', '未知')
        latest_version = update_info.get('latest_version', '未知')
        release_name = update_info.get('release_name', '')
        release_body = update_info.get('release_body', '')
        html_url = update_info.get('html_url', 'https://github.com/wangke956/ADBTools')
        is_fallback = update_info.get('is_fallback', False)
        setup_file = update_info.get('setup_file')
        
        # 如果是备用信息（无发布版本），不弹窗提示
        if is_fallback:
            return
        
        # 构建消息
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
        
        # 有安装文件可用，提供更多选项
        if setup_file:
            # 创建自定义对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("发现新版本")
            dialog.setMinimumWidth(450)
            apply_dialog_style(dialog)
            
            layout = QVBoxLayout()
            layout.setSpacing(10)
            layout.setContentsMargins(20, 20, 20, 20)
            
            # 标题
            title_label = QLabel("发现新版本")
            title_label.setStyleSheet(TITLE_LABEL_STYLE)
            layout.addWidget(title_label)
            
            # 消息标签
            msg_label = QLabel(message)
            msg_label.setWordWrap(True)
            layout.addWidget(msg_label)
            
            # 按钮布局
            button_layout = QHBoxLayout()
            button_layout.setSpacing(8)
            
            # 自动下载并安装按钮
            auto_download_btn = QPushButton("自动下载并安装")
            auto_download_btn.clicked.connect(lambda: self._start_auto_download(update_info, dialog))
            
            # 手动下载按钮
            manual_download_btn = QPushButton("手动下载")
            manual_download_btn.clicked.connect(lambda: self._open_browser(html_url, dialog))
            
            # 稍后提醒按钮
            later_btn = QPushButton("稍后提醒")
            later_btn.clicked.connect(dialog.reject)
            
            button_layout.addWidget(auto_download_btn)
            button_layout.addWidget(manual_download_btn)
            button_layout.addWidget(later_btn)
            
            layout.addLayout(button_layout)
            dialog.setLayout(layout)
            
            dialog.exec_()
        else:
            # 没有安装文件，只有手动下载选项
            message += f"GitHub地址: {html_url}\n\n"
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

    def handle_update_available(self, update_info):
        """处理有更新可用的信号"""
        from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
        from Function_Moudle.dialog_styles import apply_dialog_style, TITLE_LABEL_STYLE
        
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
                dialog = QDialog(self)
                dialog.setWindowTitle("发现新版本")
                dialog.setMinimumWidth(450)
                apply_dialog_style(dialog)
                
                layout = QVBoxLayout()
                layout.setSpacing(10)
                layout.setContentsMargins(20, 20, 20, 20)
                
                # 标题
                title_label = QLabel("发现新版本")
                title_label.setStyleSheet(TITLE_LABEL_STYLE)
                layout.addWidget(title_label)
                
                # 消息标签
                msg_label = QLabel(message)
                msg_label.setWordWrap(True)
                layout.addWidget(msg_label)
                
                # 按钮布局
                button_layout = QHBoxLayout()
                button_layout.setSpacing(8)
                
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
        """打开YF升级页面 - 使用异步线程"""
        log_button_click("open_yf_page", "启动YF升级页面", "com.yfve.usbupdate/.MainActivity")
        self._start_app_with_thread("com.yfve.usbupdate/.MainActivity")

    def open_soimt_update(self):
        """打开SOIMT升级页面 - 使用异步线程"""
        log_button_click("open_soimt_update", "启动SOIMT升级页面", "com.saicmotor.update/.view.MainActivity")
        self._start_app_with_thread("com.saicmotor.update/.view.MainActivity")

    def open_engineering_mode(self):
        """打开工程模式 - 使用异步线程"""
        log_button_click("enter_engineering_mode_button", "启动工程模式", "com.saicmotor.hmi.engmode")
        self._start_app_with_thread("com.saicmotor.hmi.engmode")

    def as33_cr_enter_engineering(self):
        """AS33 CR 进入工程模式 - 使用异步线程"""
        log_button_click("AS33_CR_enter_engineering_mode_button", "启动AS33 CR工程模式", "com.saicmotor.diag")
        self._start_app_with_thread("com.saicmotor.diag")

    def as33r_enter_secondary_engineering_mode(self):
        """AS33R国项目二级工程模式 - 使用异步线程"""
        log_button_click("AS33R_open_secondary_engineering_mode_button", "启动AS33R国项目二级工程模式", "com.carocean.engineermode")
        self._start_app_with_thread("com.carocean.engineermode/.ui.MainActivity")

    def as33r_open_engineering_mode(self):
        """AS33R国项目打开工程模式 - 使用异步线程"""
        log_button_click("AS33R_open_engineering_mode_button", "启动AS33R国工程模式", "com.saicmotor.diag/.ui.main.MainActivity")
        self._start_app_with_thread("com.saicmotor.diag/.ui.main.MainActivity")

    def _start_app_with_thread(self, app_name):
        """使用异步线程启动应用（支持U2和ADB模式）"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        if device_id not in devices_id_lst:
            self.textBrowser.append("设备未连接！")
            return
        
        try:
            # 检查连接状态
            if self.connection_mode == 'u2':
                if not self.d:
                    self.connection_mode = 'adb'
                    self.textBrowser.append("U2连接不可用，切换到ADB模式")
            
            # 导入启动应用线程
            from Function_Moudle.start_app_thread import StartAppThread
            
            # 创建并启动线程
            self.start_app_thread = StartAppThread(
                device_id=device_id,
                app_name=app_name,
                connection_mode=self.connection_mode,
                u2_device=self.d if self.connection_mode == 'u2' else None
            )
            
            # 连接信号
            self.start_app_thread.progress_signal.connect(self.textBrowser.append)
            self.start_app_thread.result_signal.connect(self.textBrowser.append)
            self.start_app_thread.error_signal.connect(self.textBrowser.append)
            
            # 启动线程
            self.start_app_thread.start()
            
            log_method_result("_start_app_with_thread", True, f"启动线程已启动: {app_name}")
            
        except Exception as e:
            log_method_result("_start_app_with_thread", False, str(e))
            self.textBrowser.append(f"启动应用线程失败: {e}")

    # ========== 大通功能 - 已委托给 datong_manager ==========
    
    def datong_factory_action(self):
        """拉起中环工厂应用 - 委托给 datong_manager"""
        self.datong_manager.factory_action()

    def datong_verity_action(self):
        """执行verity命令 - 委托给 datong_manager"""
        self.datong_manager.verity_action()

    def datong_disable_verity_action(self):
        """禁用verity - 委托给 datong_manager"""
        self.datong_manager.disable_verity_action()

    def datong_enable_verity_action(self):
        """启用verity - 委托给 datong_manager"""
        self.datong_manager.enable_verity_action()

    def datong_batch_install_action(self):
        """批量安装APK - 委托给 datong_manager"""
        self.datong_manager.batch_install_action()

    def datong_batch_install_test_action(self):
        """测试批量安装 - 委托给 datong_manager"""
        self.datong_manager.batch_install_test_action()

    def datong_batch_verify_version_action(self):
        """验证批量推包版本号 - 委托给 datong_manager"""
        self.datong_manager.batch_verify_version_action()

    def datong_input_password_action(self):
        """一键输入密码 - 委托给 datong_manager"""
        self.datong_manager.input_password_action()

    def datong_open_telenav_engineering_action(self):
        """打开泰维地图工程模式 - 委托给 datong_manager"""
        self.datong_manager.open_telenav_engineering_action()

    def datong_set_datetime_action(self):
        """设置设备日期时间 - 委托给 datong_manager"""
        self.datong_manager.set_datetime_action()

    # ========== VR功能 - 已委托给 vr_controller ==========

    def set_vr_timeout(self):
        """设置VR服务器超时 - 委托给 vr_controller"""
        self.vr_controller.set_vr_timeout()

    def app_version_check(self):
        """检查应用版本"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("start_check_button", "检查应用版本", f"集成清单: {self.releasenote_file}")

        if device_id in devices_id_lst:
            try:
                # 使用线程工厂创建应用版本检查线程
                self.releasenote_dict = {}
                self.app_version_check_thread = thread_factory.create_thread(
                    'app_version_check',
                    releasenote_file=self.releasenote_file,
                    d = self.d
                )
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
                        from Function_Moudle.adb_device_utils import get_app_version
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


    # ========== 日志操作 - 已委托给 log_operations ==========

    def remove_voice_record_file(self):
        """删除语音录制文件 - 委托给 log_operations"""
        self.log_operations.remove_voice_record_file()

    def voice_start_record(self):
        """开始语音录制 - 委托给 log_operations"""
        self.log_operations.voice_start_record()

    def voice_stop_record(self):
        """停止语音录制 - 委托给 log_operations"""
        self.log_operations.voice_stop_record()

    def voice_pull_record_file(self):
        """拉取录音文件 - 委托给 log_operations"""
        self.log_operations.voice_pull_record_file()

    def open_path(self):
        """打开文件所在目录 - 委托给 log_operations"""
        self.log_operations.open_path()

    def pull_log(self):
        """拉取设备日志 - 委托给 log_operations"""
        self.log_operations.pull_log()

    # ========== 设备管理 - 已委托给 device_manager ==========

    def on_mode_switch_changed(self, state):
        """模式切换 - 委托给 device_manager"""
        self.device_manager.on_mode_switch_changed(state)
    
    def on_combobox_changed(self, text):
        """设备选择切换 - 委托给 device_manager"""
        self.device_manager.on_combobox_changed(text)
    
    def refresh_devices(self):
        """刷新设备列表 - 委托给 device_manager"""
        self.device_manager.refresh_devices()
    
    def reboot_device(self):
        """重启设备 - 委托给 device_manager"""
        self.device_manager.reboot_device()
    
    def disconnect_device(self):
        """断开设备连接 - 委托给 device_manager"""
        self.device_manager.disconnect_device()
    
    def reinit_uiautomator2(self):
        """重新初始化u2 - 委托给 device_manager"""
        self.device_manager.reinit_uiautomator2()

    def get_selected_device(self):
        return self.ComboxButton.currentText()  # 返回的类型为str

    def get_new_device_lst(self):
        """获取设备ID列表 - 委托给 adb_utils"""
        return adb_utils.get_device_list()

    # ========== VR操作 - 已委托给 vr_controller ==========

    def activate_vr(self):
        """激活VR - 委托给 vr_controller"""
        self.vr_controller.activate_vr()

    def check_vr_network(self):
        """检查VR网络 - 委托给 vr_controller"""
        self.vr_controller.check_vr_network()

    def switch_vr_env(self):
        """切换VR环境 - 委托给 vr_controller"""
        self.vr_controller.switch_vr_env()

    def scroll_to_bottom(self):
        """滚动到底部"""
        scrollbar = self.textBrowser.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def skip_power_limit(self):
        """跳过电源挡位限制 - 委托给 vr_controller"""
        self.vr_controller.skip_power_limit()

    def list_package(self):
        """列出包名 - 委托给 app_operations"""
        self.app_operations.list_package()

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
                # 使用线程工厂创建获取Root权限线程
                self.adb_root_thread = thread_factory.create_thread(
                    'adb_root',
                    device_id=device_id
                )
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

    # ========== 文件操作 - 已委托给 file_operations ==========

    @staticmethod
    def get_screenshot(file_path, device_id):
        """截取设备屏幕 - 委托给 adb_utils"""
        return adb_utils.get_screenshot(file_path, device_id)

    def show_screenshot_dialog(self):
        """截取设备屏幕 - 委托给 file_operations"""
        self.file_operations.show_screenshot_dialog()

    def show_uninstall_dialog(self):
        """卸载应用 - 委托给 file_operations"""
        self.file_operations.show_uninstall_dialog()

    def show_install_file_dialog(self):
        """安装应用 - 委托给 file_operations"""
        self.file_operations.show_install_file_dialog()

    @staticmethod
    def adb_push_file(local_file_path, target_path_on_device, device_id):
        """推送文件到设备 - 委托给 adb_utils"""
        return adb_utils.push_file(local_file_path, target_path_on_device, device_id)

    def show_push_file_dialog(self):
        """推送文件到设备 - 委托给 file_operations"""
        self.file_operations.show_push_file_dialog()

    @staticmethod
    def simulate_click(x, y, device_id):
        """模拟点击 - 委托给 adb_utils"""
        return adb_utils.simulate_click(x, y, device_id)

    @staticmethod
    def simulate_long_press(x, y, duration, device_id):
        """模拟长按 - 委托给 adb_utils"""
        return adb_utils.simulate_long_press(x, y, duration, device_id)

    # ========== 输入操作 - 已委托给 input_operations ==========

    def show_simulate_long_press_dialog(self):
        """显示模拟长按对话框 - 委托给 input_operations"""
        self.input_operations.show_simulate_long_press_dialog()

    def show_input_text_dialog(self):
        """显示输入文本对话框 - 委托给 input_operations"""
        self.input_operations.show_input_text_dialog()

    # ========== 应用操作 - 已委托给 app_operations ==========

    def start_app_action(self, app_name):
        """启动应用 - 直接调用统一的异步线程"""
        self._start_app_with_thread(app_name)

    def get_running_app_info(self):
        """获取运行应用信息 - 委托给 app_operations"""
        self.app_operations.get_running_app_info()

    def view_apk_path_wrapper(self):
        """查看APK路径 - 委托给 app_operations"""
        self.app_operations.view_apk_path_wrapper()

    def get_foreground_package(self):
        """获取前台应用包名 - 委托给 app_operations"""
        self.app_operations.get_foreground_package()

    def show_force_stop_app_dialog(self):
        """强制停止应用 - 委托给 app_operations"""
        self.app_operations.show_force_stop_app_dialog()

    def show_clear_app_cache_dialog(self):
        """清除应用缓存 - 委托给 app_operations"""
        self.app_operations.show_clear_app_cache_dialog()

    @staticmethod
    def aapt_get_packagen_name(apk_path):
        """使用aapt获取包名 - 委托给 adb_utils"""
        return adb_utils.aapt_get_package_name(apk_path)

    def aapt_getpackage_name_dilog(self):
        """使用aapt获取APK包名 - 委托给 app_operations"""
        self.app_operations.aapt_getpackage_name_dilog()

    def browse_log_save_path(self):
        """浏览日志保存路径 - 委托给 log_operations"""
        self.log_operations.browse_log_save_path()

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
    
                    
    
                    # 对于刷新设备和断开设备按钮，使用更保守的缩放
    
                    if button_name in ('RefreshButton', 'DisconnectButton'):
    
                        # 这两个按钮保持相对固定的大小
    
                        button.setMinimumSize(100, 30)
    
                        button.setMaximumSize(100, 50)
    
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
            from Function_Moudle.device_threads import U2ReinitThread
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
    
    def _update_undo_redo_status(self):
        """更新撤销/重做按钮状态"""
        if hasattr(self, 'undo_action'):
            self.undo_action.setEnabled(self.operation_history.can_undo())
        if hasattr(self, 'redo_action'):
            self.redo_action.setEnabled(self.operation_history.can_redo())
    
    def add_operation(self, operation_type: str, description: str, data=None):
        """添加操作记录"""
        self.operation_history.add_operation(operation_type, description, data)
        self.textBrowser.append(f"📝 操作记录: {description}")
    
    def undo(self):
        """撤销操作"""
        record = self.operation_history.undo()
        if record:
            self.textBrowser.append(f"↩️ 撤销操作: {record.description}")
            # 这里可以添加具体的撤销逻辑
            return record
        else:
            self.textBrowser.append("⚠️ 没有可撤销的操作")
            return None
    
    def redo(self):
        """重做操作"""
        record = self.operation_history.redo()
        if record:
            self.textBrowser.append(f"↪️ 重做操作: {record.description}")
            # 这里可以添加具体的重做逻辑
            return record
        else:
            self.textBrowser.append("⚠️ 没有可重做的操作")
            return None
    
    def show_error(self, title: str, message: str):
        """显示错误提示"""
        show_error_message(self, title, message)
    
    def show_warning(self, title: str, message: str):
        """显示警告提示"""
        show_warning_message(self, title, message)
    
    def show_info(self, title: str, message: str):
        """显示信息提示"""
        show_info_message(self, title, message)
    
    def show_quick_start_guide(self):
        """显示快速入门引导"""
        show_quick_guide(self)
    
    def show_device_setup_guide(self):
        """显示设备设置引导"""
        guide = create_device_setup_guide(self)
        guide.start()
    
    def show_app_install_guide(self):
        """显示应用安装引导"""
        guide = create_app_install_guide(self)
        guide.start()
