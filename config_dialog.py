#!/usr/bin/env python3
"""高性能多线程配置对话框"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFileDialog, QMessageBox,
                             QGroupBox, QFormLayout, QCheckBox, QSpinBox,
                             QComboBox, QTabWidget, QWidget)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
import os
import sys
import threading
import time

try:
    from config_manager import config_manager
except ImportError:
    # 简单的配置管理器回退
    class ConfigManagerFallback:
        def get(self, key, default=None):
            return default
        def set(self, key, value):
            return True
        def save_config(self):
            return True
    
    config_manager = ConfigManagerFallback()

class ThreadPoolManager:
    """高性能线程池管理器"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_pool()
            return cls._instance
    
    def _init_pool(self):
        """初始化线程池"""
        self._thread_pool = {}
        self._task_queue = []
        self._max_workers = 4  # 最大线程数
        self._running_tasks = 0
        self._pool_lock = threading.Lock()
    
    def submit_task(self, task_id, task_func, *args, **kwargs):
        """提交任务到线程池"""
        with self._pool_lock:
            # 如果任务已存在，先取消
            if task_id in self._thread_pool:
                self.cancel_task(task_id)
            
            # 创建新线程
            thread = threading.Thread(
                target=self._task_wrapper,
                args=(task_id, task_func, args, kwargs),
                daemon=True
            )
            
            self._thread_pool[task_id] = {
                'thread': thread,
                'running': True,
                'result': None,
                'error': None
            }
            
            thread.start()
            return True
    
    def _task_wrapper(self, task_id, task_func, args, kwargs):
        """任务包装器，处理异常和结果"""
        try:
            result = task_func(*args, **kwargs)
            with self._pool_lock:
                if task_id in self._thread_pool:
                    self._thread_pool[task_id]['result'] = result
        except Exception as e:
            with self._pool_lock:
                if task_id in self._thread_pool:
                    self._thread_pool[task_id]['error'] = str(e)
        finally:
            with self._pool_lock:
                if task_id in self._thread_pool:
                    self._thread_pool[task_id]['running'] = False
    
    def cancel_task(self, task_id):
        """取消任务"""
        with self._pool_lock:
            if task_id in self._thread_pool:
                # 注意：Python线程不能真正强制停止，只能标记为停止
                self._thread_pool[task_id]['running'] = False
                del self._thread_pool[task_id]
                return True
        return False
    
    def get_task_status(self, task_id):
        """获取任务状态"""
        with self._pool_lock:
            if task_id in self._thread_pool:
                task = self._thread_pool[task_id]
                return {
                    'running': task['running'],
                    'result': task['result'],
                    'error': task['error']
                }
        return None
    
    def wait_for_task(self, task_id, timeout=None):
        """等待任务完成"""
        start_time = time.time()
        while True:
            status = self.get_task_status(task_id)
            if status is None or not status['running']:
                return status
            
            if timeout is not None and time.time() - start_time > timeout:
                return None
            
            time.sleep(0.01)  # 短暂休眠，避免CPU占用过高
    
    def cleanup(self):
        """清理所有任务"""
        with self._pool_lock:
            task_ids = list(self._thread_pool.keys())
            for task_id in task_ids:
                self.cancel_task(task_id)

# 全局线程池实例
thread_pool = ThreadPoolManager()

class HighPerformanceADBManager:
    """高性能ADB管理器"""
    
    def __init__(self):
        self._cache = {}
        self._cache_lock = threading.Lock()
        self._last_check_time = {}
    
    def check_adb_status(self, force_refresh=False):
        """高性能ADB状态检查"""
        task_id = f"adb_status_{int(time.time() * 1000)}"
        
        def _check_adb():
            try:
                from adb_utils import adb_utils
                adb_path = adb_utils.get_adb_path()
                
                # 检查缓存
                cache_key = f"status_{adb_path}"
                with self._cache_lock:
                    if not force_refresh and cache_key in self._cache:
                        cached_result = self._cache[cache_key]
                        if time.time() - cached_result.get('timestamp', 0) < 30:  # 30秒缓存
                            return cached_result['result']
                
                # 执行检查
                if os.path.isfile(adb_path):
                    import subprocess
                    result = subprocess.run([adb_path, "--version"], 
                                          capture_output=True, text=True, timeout=2)
                    if result.returncode == 0:
                        version_line = result.stdout.split('\n')[0]
                        status = f"ADB状态: 正常 ({version_line})"
                        color = "green"
                    else:
                        status = "ADB状态: 文件存在但无法执行"
                        color = "orange"
                elif adb_path == "adb":
                    status = "ADB状态: 使用系统PATH中的adb"
                    color = "blue"
                else:
                    status = "ADB状态: 未找到"
                    color = "red"
                
                # 更新缓存
                result_data = {'status': status, 'color': color, 'path': adb_path}
                with self._cache_lock:
                    self._cache[cache_key] = {
                        'result': result_data,
                        'timestamp': time.time()
                    }
                
                return result_data
                
            except subprocess.TimeoutExpired:
                return {'status': 'ADB状态: 检查超时', 'color': 'orange', 'path': ''}
            except Exception as e:
                return {'status': f'ADB状态: 检查失败 ({str(e)})', 'color': 'red', 'path': ''}
        
        # 提交到线程池
        thread_pool.submit_task(task_id, _check_adb)
        return task_id
    
    def test_adb_connection(self, custom_path=None):
        """高性能ADB连接测试"""
        task_id = f"adb_test_{int(time.time() * 1000)}"
        
        def _test_adb():
            try:
                from adb_utils import adb_utils
                
                # 获取ADB路径
                if custom_path and os.path.isfile(custom_path):
                    adb_path = custom_path
                else:
                    adb_path = adb_utils.get_adb_path()
                
                # 测试ADB
                import subprocess
                timeout = 5
                
                if adb_path == "adb":
                    result = subprocess.run(["adb", "--version"], 
                                          shell=True, capture_output=True, 
                                          text=True, timeout=timeout)
                else:
                    result = subprocess.run([adb_path, "--version"], 
                                          capture_output=True, text=True, 
                                          timeout=timeout)
                
                if result.returncode == 0:
                    version_info = result.stdout.strip()
                    version_line = version_info.split('\n')[0] if '\n' in version_info else version_info
                    return {
                        'success': True,
                        'message': f"ADB测试成功！\n\n路径: {adb_path}\n版本: {version_line}",
                        'path': adb_path,
                        'version': version_line
                    }
                else:
                    return {
                        'success': False,
                        'message': f"ADB执行失败:\n路径: {adb_path}\n错误: {result.stderr}",
                        'path': adb_path,
                        'error': result.stderr
                    }
                    
            except subprocess.TimeoutExpired:
                return {
                    'success': False,
                    'message': "ADB测试超时（5秒）",
                    'path': custom_path or '',
                    'error': 'timeout'
                }
            except Exception as e:
                return {
                    'success': False,
                    'message': f"测试ADB时出错:\n{str(e)}",
                    'path': custom_path or '',
                    'error': str(e)
                }
        
        # 提交到线程池
        thread_pool.submit_task(task_id, _test_adb)
        return task_id
    
    def scan_adb_paths(self):
        """高性能ADB路径扫描"""
        task_id = f"adb_scan_{int(time.time() * 1000)}"
        
        def _scan_paths():
            try:
                from adb_utils import adb_utils
                import subprocess
                
                possible_paths = []
                
                # 系统PATH中的adb
                if sys.platform == "win32":
                    result = subprocess.run(["where", "adb"], capture_output=True, text=True)
                else:
                    result = subprocess.run(["which", "adb"], capture_output=True, text=True)
                
                if result.returncode == 0:
                    paths = result.stdout.strip().split('\n')
                    possible_paths.extend([p.strip() for p in paths if p.strip()])
                
                # 常见Android SDK路径
                common_paths = []
                if sys.platform == "win32":
                    common_paths = [
                        os.path.join(os.environ.get("ANDROID_HOME", ""), "platform-tools", "adb.exe"),
                        os.path.join(os.environ.get("ANDROID_SDK_ROOT", ""), "platform-tools", "adb.exe"),
                        r"C:\Program Files (x86)\Android\android-sdk\platform-tools\adb.exe",
                        r"C:\Users\Public\adb\adb.exe",
                        r"D:\work_tools\adb-1\adb.exe",
                    ]
                else:
                    common_paths = [
                        os.path.join(os.environ.get("ANDROID_HOME", ""), "platform-tools", "adb"),
                        os.path.join(os.environ.get("ANDROID_SDK_ROOT", ""), "platform-tools", "adb"),
                        "/usr/bin/adb",
                        "/usr/local/bin/adb",
                        "/opt/android-sdk/platform-tools/adb",
                    ]
                
                # 检查常见路径
                valid_paths = []
                for path in common_paths:
                    if os.path.isfile(path):
                        valid_paths.append(path)
                
                # 程序同目录
                current_dir = os.path.dirname(os.path.abspath(__file__))
                local_paths = []
                if sys.platform == "win32":
                    local_paths.append(os.path.join(current_dir, "adb.exe"))
                    local_paths.append(os.path.join(current_dir, "tools", "adb.exe"))
                else:
                    local_paths.append(os.path.join(current_dir, "adb"))
                    local_paths.append(os.path.join(current_dir, "tools", "adb"))
                
                for path in local_paths:
                    if os.path.isfile(path):
                        valid_paths.append(path)
                
                return {
                    'system_paths': possible_paths,
                    'common_paths': [p for p in common_paths if os.path.isfile(p)],
                    'local_paths': [p for p in local_paths if os.path.isfile(p)],
                    'all_valid_paths': valid_paths
                }
                
            except Exception as e:
                return {
                    'system_paths': [],
                    'common_paths': [],
                    'local_paths': [],
                    'all_valid_paths': [],
                    'error': str(e)
                }
        
        # 提交到线程池
        thread_pool.submit_task(task_id, _scan_paths)
        return task_id
    
    def get_cached_status(self, adb_path):
        """获取缓存的ADB状态"""
        cache_key = f"status_{adb_path}"
        with self._cache_lock:
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                if time.time() - cached['timestamp'] < 30:  # 30秒内有效
                    return cached['result']
        return None

# 全局高性能ADB管理器实例
adb_manager = HighPerformanceADBManager()

class ConfigDialog(QDialog):
    """高性能多线程配置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ADBTools 配置 (高性能多线程版)")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        # 任务ID跟踪
        self._current_tasks = {
            'status_check': None,
            'adb_test': None,
            'path_scan': None
        }
        
        # 定时器用于检查任务状态
        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self._check_task_status)
        self._status_timer.start(100)  # 每100ms检查一次
        
        self.init_ui()
        self.load_config()
        
        # 延迟启动ADB状态检查
        QTimer.singleShot(100, self.start_adb_status_check)
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # ADB配置标签页
        self.adb_tab = self.create_adb_tab()
        self.tab_widget.addTab(self.adb_tab, "ADB设置")
        
        # UI配置标签页
        self.ui_tab = self.create_ui_tab()
        self.tab_widget.addTab(self.ui_tab, "界面设置")
        
        # 设备配置标签页
        self.devices_tab = self.create_devices_tab()
        self.tab_widget.addTab(self.devices_tab, "设备设置")
        
        # 性能监控标签页
        self.performance_tab = self.create_performance_tab()
        self.tab_widget.addTab(self.performance_tab, "性能监控")
        
        layout.addWidget(self.tab_widget)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.test_adb_button = QPushButton("测试ADB (多线程)")
        self.test_adb_button.clicked.connect(self.test_adb)
        
        self.scan_paths_button = QPushButton("扫描ADB路径")
        self.scan_paths_button.clicked.connect(self.scan_adb_paths)
        
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.save_config)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.test_adb_button)
        button_layout.addWidget(self.scan_paths_button)
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def create_adb_tab(self):
        """创建ADB配置标签页"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # ADB路径组
        adb_group = QGroupBox("ADB路径设置 (高性能多线程)")
        adb_layout = QFormLayout()
        
        # 自定义ADB路径
        self.adb_path_edit = QLineEdit()
        self.adb_path_browse = QPushButton("浏览...")
        self.adb_path_browse.clicked.connect(self.browse_adb_path)
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.adb_path_edit)
        path_layout.addWidget(self.adb_path_browse)
        
        adb_layout.addRow("自定义ADB路径:", path_layout)
        
        # 自动检测
        self.auto_detect_check = QCheckBox("自动检测ADB")
        adb_layout.addRow("", self.auto_detect_check)
        
        # 当前ADB状态
        self.adb_status_label = QLabel("ADB状态: 等待检查...")
        self.adb_status_label.setStyleSheet("font-weight: bold;")
        adb_layout.addRow("状态:", self.adb_status_label)
        
        # 性能信息
        self.performance_label = QLabel("线程池: 就绪 | 缓存: 0")
        self.performance_label.setStyleSheet("color: gray; font-size: 10pt;")
        adb_layout.addRow("性能:", self.performance_label)
        
        adb_group.setLayout(adb_layout)
        layout.addWidget(adb_group)
        
        # 搜索路径组
        search_group = QGroupBox("ADB搜索路径（多线程扫描）")
        search_layout = QVBoxLayout()
        
        self.search_paths_text = QLabel("点击'扫描ADB路径'按钮开始多线程扫描")
        self.search_paths_text.setWordWrap(True)
        self.search_paths_text.setStyleSheet("background-color: #f0f0f0; padding: 5px;")
        search_layout.addWidget(self.search_paths_text)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def create_ui_tab(self):
        """创建UI配置标签页"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        ui_group = QGroupBox("界面设置")
        ui_layout = QFormLayout()
        
        # 主题
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light", "auto"])
        ui_layout.addRow("主题:", self.theme_combo)
        
        # 语言
        self.language_combo = QComboBox()
        self.language_combo.addItems(["zh_CN", "en_US"])
        ui_layout.addRow("语言:", self.language_combo)
        
        # 字体大小
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 20)
        self.font_size_spin.setValue(10)
        ui_layout.addRow("字体大小:", self.font_size_spin)
        
        ui_group.setLayout(ui_layout)
        layout.addWidget(ui_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def create_devices_tab(self):
        """创建设备配置标签页"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        devices_group = QGroupBox("设备设置")
        devices_layout = QFormLayout()
        
        # 自动刷新
        self.auto_refresh_check = QCheckBox("自动刷新设备列表")
        devices_layout.addRow("", self.auto_refresh_check)
        
        # 刷新间隔
        self.refresh_interval_spin = QSpinBox()
        self.refresh_interval_spin.setRange(1, 60)
        self.refresh_interval_spin.setSuffix(" 秒")
        devices_layout.addRow("刷新间隔:", self.refresh_interval_spin)
        
        # 多线程刷新
        self.multithread_refresh_check = QCheckBox("使用多线程刷新设备列表")
        devices_layout.addRow("", self.multithread_refresh_check)
        
        devices_group.setLayout(devices_layout)
        layout.addWidget(devices_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def create_performance_tab(self):
        """创建性能监控标签页"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 线程池状态
        pool_group = QGroupBox("线程池状态")
        pool_layout = QVBoxLayout()
        
        self.thread_pool_status = QLabel("线程池: 初始化中...")
        self.thread_pool_status.setStyleSheet("font-weight: bold; color: blue;")
        pool_layout.addWidget(self.thread_pool_status)
        
        self.active_threads_label = QLabel("活动线程: 0")
        pool_layout.addWidget(self.active_threads_label)
        
        self.task_queue_label = QLabel("任务队列: 0")
        pool_layout.addWidget(self.task_queue_label)
        
        self.cache_status_label = QLabel("缓存命中: 0 | 缓存大小: 0")
        pool_layout.addWidget(self.cache_status_label)
        
        pool_group.setLayout(pool_layout)
        layout.addWidget(pool_group)
        
        # 性能统计
        stats_group = QGroupBox("性能统计")
        stats_layout = QVBoxLayout()
        
        self.status_check_time = QLabel("状态检查平均时间: -- ms")
        stats_layout.addWidget(self.status_check_time)
        
        self.test_adb_time = QLabel("ADB测试平均时间: -- ms")
        stats_layout.addWidget(self.test_adb_time)
        
        self.path_scan_time = QLabel("路径扫描平均时间: -- ms")
        stats_layout.addWidget(self.path_scan_time)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        
        self.clear_cache_button = QPushButton("清除缓存")
        self.clear_cache_button.clicked.connect(self.clear_cache)
        
        self.thread_pool_info_button = QPushButton("线程池信息")
        self.thread_pool_info_button.clicked.connect(self.show_thread_pool_info)
        
        control_layout.addWidget(self.clear_cache_button)
        control_layout.addWidget(self.thread_pool_info_button)
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
    def browse_adb_path(self):
        """浏览ADB路径"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择ADB可执行文件", "", 
            "可执行文件 (*.exe);;所有文件 (*.*)"
        )
        
        if file_path:
            self.adb_path_edit.setText(file_path)
            # 路径变化后强制刷新状态
            self.start_adb_status_check(force_refresh=True)
    
    def load_config(self):
        """加载配置到UI"""
        # ADB配置
        self.adb_path_edit.setText(config_manager.get("adb.custom_path", ""))
        self.auto_detect_check.setChecked(config_manager.get("adb.auto_detect", True))
        
        # UI配置
        self.theme_combo.setCurrentText(config_manager.get("ui.theme", "dark"))
        self.language_combo.setCurrentText(config_manager.get("ui.language", "zh_CN"))
        self.font_size_spin.setValue(config_manager.get("ui.font_size", 10))
        
        # 设备配置
        self.auto_refresh_check.setChecked(config_manager.get("devices.auto_refresh", True))
        self.refresh_interval_spin.setValue(config_manager.get("devices.refresh_interval", 5))
        self.multithread_refresh_check.setChecked(config_manager.get("devices.multithread_refresh", False))
        
        # 设置初始ADB状态
        self.adb_status_label.setText("ADB状态: 检查中...")
        self.adb_status_label.setStyleSheet("color: gray; font-weight: bold;")
    
    def start_adb_status_check(self, force_refresh=False):
        """启动ADB状态检查（高性能多线程版）"""
        # 取消之前的检查任务
        if self._current_tasks['status_check']:
            thread_pool.cancel_task(self._current_tasks['status_check'])
        
        # 提交新任务
        task_id = adb_manager.check_adb_status(force_refresh)
        self._current_tasks['status_check'] = task_id
        
        # 更新UI
        self.adb_status_label.setText("ADB状态: 检查中...")
        self.adb_status_label.setStyleSheet("color: blue; font-weight: bold;")
    
    def test_adb(self):
        """测试ADB连接（高性能多线程版）"""
        # 如果测试正在进行中，直接返回
        if self._current_tasks['adb_test']:
            status = thread_pool.get_task_status(self._current_tasks['adb_test'])
            if status and status['running']:
                return
        
        # 禁用测试按钮，避免重复点击
        self.test_adb_button.setEnabled(False)
        self.test_adb_button.setText("测试中...")
        
        # 获取自定义ADB路径
        custom_path = None
        custom_path_text = self.adb_path_edit.text().strip()
        if custom_path_text and os.path.isfile(custom_path_text):
            custom_path = custom_path_text
        
        # 提交测试任务
        task_id = adb_manager.test_adb_connection(custom_path)
        self._current_tasks['adb_test'] = task_id
        
        # 更新UI
        self.adb_status_label.setText("ADB测试: 进行中...")
        self.adb_status_label.setStyleSheet("color: orange; font-weight: bold;")
    
    def scan_adb_paths(self):
        """扫描ADB路径（高性能多线程版）"""
        # 如果扫描正在进行中，直接返回
        if self._current_tasks['path_scan']:
            status = thread_pool.get_task_status(self._current_tasks['path_scan'])
            if status and status['running']:
                return
        
        # 禁用扫描按钮
        self.scan_paths_button.setEnabled(False)
        self.scan_paths_button.setText("扫描中...")
        
        # 提交扫描任务
        task_id = adb_manager.scan_adb_paths()
        self._current_tasks['path_scan'] = task_id
        
        # 更新UI
        self.search_paths_text.setText("ADB路径扫描中...")
        self.search_paths_text.setStyleSheet("background-color: #fff0cc; padding: 5px;")
    
    def _check_task_status(self):
        """检查任务状态（定时调用）"""
        # 检查ADB状态任务
        if self._current_tasks['status_check']:
            status = thread_pool.get_task_status(self._current_tasks['status_check'])
            if status and not status['running']:
                if status['result']:
                    result = status['result']
                    self.adb_status_label.setText(result['status'])
                    color = result.get('color', 'black')
                    self.adb_status_label.setStyleSheet(f"color: {color}; font-weight: bold;")
                self._current_tasks['status_check'] = None
        
        # 检查ADB测试任务
        if self._current_tasks['adb_test']:
            status = thread_pool.get_task_status(self._current_tasks['adb_test'])
            if status and not status['running']:
                if status['result']:
                    result = status['result']
                    if result['success']:
                        QMessageBox.information(self, "成功", result['message'])
                        self.adb_status_label.setText("ADB状态: 测试成功")
                        self.adb_status_label.setStyleSheet("color: green; font-weight: bold;")
                    else:
                        QMessageBox.warning(self, "警告", result['message'])
                        self.adb_status_label.setText("ADB状态: 测试失败")
                        self.adb_status_label.setStyleSheet("color: red; font-weight: bold;")
                
                # 恢复按钮状态
                self.test_adb_button.setEnabled(True)
                self.test_adb_button.setText("测试ADB (多线程)")
                self._current_tasks['adb_test'] = None
        
        # 检查路径扫描任务
        if self._current_tasks['path_scan']:
            status = thread_pool.get_task_status(self._current_tasks['path_scan'])
            if status and not status['running']:
                if status['result']:
                    result = status['result']
                    paths_text = "找到的ADB路径:\n\n"
                    
                    if result.get('system_paths'):
                        paths_text += "系统PATH中的adb:\n"
                        for path in result['system_paths']:
                            paths_text += f"  • {path}\n"
                        paths_text += "\n"
                    
                    if result.get('common_paths'):
                        paths_text += "常见Android SDK路径:\n"
                        for path in result['common_paths']:
                            paths_text += f"  • {path}\n"
                        paths_text += "\n"
                    
                    if result.get('local_paths'):
                        paths_text += "程序同目录路径:\n"
                        for path in result['local_paths']:
                            paths_text += f"  • {path}\n"
                    
                    if not result.get('system_paths') and not result.get('common_paths') and not result.get('local_paths'):
                        paths_text = "未找到任何ADB路径"
                    
                    self.search_paths_text.setText(paths_text)
                    self.search_paths_text.setStyleSheet("background-color: #f0f0f0; padding: 5px;")
                
                # 恢复按钮状态
                self.scan_paths_button.setEnabled(True)
                self.scan_paths_button.setText("扫描ADB路径")
                self._current_tasks['path_scan'] = None
        
        # 更新性能监控信息
        self._update_performance_info()
    
    def _update_performance_info(self):
        """更新性能监控信息"""
        # 更新线程池状态
        active_tasks = 0
        for task_id in thread_pool._thread_pool:
            task = thread_pool._thread_pool[task_id]
            if task['running']:
                active_tasks += 1
        
        self.active_threads_label.setText(f"活动线程: {active_tasks}")
        self.task_queue_label.setText(f"任务队列: {len(thread_pool._task_queue)}")
        
        # 更新缓存信息
        cache_size = len(adb_manager._cache)
        self.cache_status_label.setText(f"缓存命中: -- | 缓存大小: {cache_size}")
        
        # 更新性能标签
        self.performance_label.setText(f"线程池: {active_tasks}活动 | 缓存: {cache_size}")
    
    def clear_cache(self):
        """清除缓存"""
        with adb_manager._cache_lock:
            adb_manager._cache.clear()
        QMessageBox.information(self, "成功", "缓存已清除")
        self._update_performance_info()
    
    def show_thread_pool_info(self):
        """显示线程池信息"""
        info = "线程池信息:\n\n"
        
        # 活动任务
        active_tasks = []
        for task_id, task in thread_pool._thread_pool.items():
            if task['running']:
                active_tasks.append(task_id)
        
        info += f"活动任务 ({len(active_tasks)}):\n"
        for task_id in active_tasks:
            info += f"  • {task_id}\n"
        
        info += f"\n任务队列: {len(thread_pool._task_queue)} 个任务等待\n"
        info += f"最大工作线程: {thread_pool._max_workers}\n"
        
        QMessageBox.information(self, "线程池信息", info)
    
    def save_config(self):
        """保存配置"""
        try:
            # ADB配置
            config_manager.set("adb.custom_path", self.adb_path_edit.text())
            config_manager.set("adb.auto_detect", self.auto_detect_check.isChecked())
            
            # UI配置
            config_manager.set("ui.theme", self.theme_combo.currentText())
            config_manager.set("ui.language", self.language_combo.currentText())
            config_manager.set("ui.font_size", self.font_size_spin.value())
            
            # 设备配置
            config_manager.set("devices.auto_refresh", self.auto_refresh_check.isChecked())
            config_manager.set("devices.refresh_interval", self.refresh_interval_spin.value())
            config_manager.set("devices.multithread_refresh", self.multithread_refresh_check.isChecked())
            
            # 保存到文件
            if config_manager.save_config():
                QMessageBox.information(self, "成功", "配置保存成功！")
                # 强制刷新ADB状态
                self.start_adb_status_check(force_refresh=True)
                self.accept()
            else:
                QMessageBox.warning(self, "警告", "配置保存失败！")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置时出错:\n{str(e)}")
    
    def closeEvent(self, event):
        """对话框关闭事件"""
        # 清理所有任务
        for task_type, task_id in self._current_tasks.items():
            if task_id:
                thread_pool.cancel_task(task_id)
        
        # 停止定时器
        self._status_timer.stop()
        
        super().closeEvent(event)