#!/usr/bin/env python3
"""配置对话框"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFileDialog, QMessageBox,
                             QGroupBox, QFormLayout, QCheckBox, QSpinBox,
                             QComboBox, QTabWidget, QWidget)
from PyQt5.QtCore import Qt
import os

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

class ConfigDialog(QDialog):
    """配置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ADBTools 配置")
        self.setMinimumWidth(500)
        
        self.init_ui()
        self.load_config()
    
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
        
        layout.addWidget(self.tab_widget)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.save_config)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        
        self.test_adb_button = QPushButton("测试ADB")
        self.test_adb_button.clicked.connect(self.test_adb)
        
        button_layout.addWidget(self.test_adb_button)
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
        adb_group = QGroupBox("ADB路径设置")
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
        self.adb_status_label = QLabel("ADB状态: 未知")
        adb_layout.addRow("状态:", self.adb_status_label)
        
        adb_group.setLayout(adb_layout)
        layout.addWidget(adb_group)
        
        # 搜索路径组
        search_group = QGroupBox("ADB搜索路径（按顺序查找）")
        search_layout = QVBoxLayout()
        
        self.search_paths_label = QLabel("1. 系统环境变量PATH\n2. 程序同目录\n3. 配置文件中的路径")
        self.search_paths_label.setWordWrap(True)
        search_layout.addWidget(self.search_paths_label)
        
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
        self.theme_combo.addItems(["dark", "light"])
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
        
        devices_group.setLayout(devices_layout)
        layout.addWidget(devices_group)
        
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
        
        # 更新ADB状态
        self.update_adb_status()
    
    def update_adb_status(self):
        """更新ADB状态显示"""
        try:
            from adb_utils import adb_utils
            adb_path = adb_utils.get_adb_path()
            
            if os.path.isfile(adb_path):
                # 测试ADB版本
                import subprocess
                result = subprocess.run([adb_path, "--version"], capture_output=True, text=True)
                if result.returncode == 0:
                    version_line = result.stdout.split('\n')[0]
                    self.adb_status_label.setText(f"ADB状态: 正常 ({version_line})")
                    self.adb_status_label.setStyleSheet("color: green")
                else:
                    self.adb_status_label.setText("ADB状态: 文件存在但无法执行")
                    self.adb_status_label.setStyleSheet("color: orange")
            elif adb_path == "adb":
                self.adb_status_label.setText("ADB状态: 使用系统PATH中的adb")
                self.adb_status_label.setStyleSheet("color: blue")
            else:
                self.adb_status_label.setText("ADB状态: 未找到")
                self.adb_status_label.setStyleSheet("color: red")
        except Exception as e:
            self.adb_status_label.setText(f"ADB状态: 检查失败 ({str(e)})")
            self.adb_status_label.setStyleSheet("color: red")
    
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
            
            # 保存到文件
            if config_manager.save_config():
                QMessageBox.information(self, "成功", "配置保存成功！")
                self.update_adb_status()
                self.accept()
            else:
                QMessageBox.warning(self, "警告", "配置保存失败！")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置时出错:\n{str(e)}")
    
    def test_adb(self):
        """测试ADB连接"""
        try:
            from adb_utils import adb_utils
            
            # 清除ADB路径缓存，强制重新查找
            adb_utils._adb_path = None
            
            adb_path = adb_utils.get_adb_path()
            
            if not os.path.isfile(adb_path) and adb_path != "adb":
                QMessageBox.warning(self, "警告", f"ADB文件不存在:\n{adb_path}")
                return
            
            # 测试ADB版本
            import subprocess
            if adb_path == "adb":
                result = subprocess.run(["adb", "--version"], shell=True, capture_output=True, text=True)
            else:
                result = subprocess.run([adb_path, "--version"], capture_output=True, text=True)
            
            if result.returncode == 0:
                version_info = result.stdout.strip()
                QMessageBox.information(self, "成功", f"ADB测试成功！\n\n{version_info}")
            else:
                QMessageBox.warning(self, "警告", f"ADB执行失败:\n{result.stderr}")
            
            # 更新状态显示
            self.update_adb_status()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"测试ADB时出错:\n{str(e)}")
