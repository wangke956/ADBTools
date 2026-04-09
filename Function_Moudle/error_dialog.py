from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTextEdit, QPushButton, QMessageBox)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QPixmap, QIcon
from enum import Enum
from typing import Optional


class ErrorLevel(Enum):
    """错误级别枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorDialog(QDialog):
    """错误提示对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("操作提示")
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # 主布局
        main_layout = QVBoxLayout()
        
        # 图标和标题布局
        header_layout = QHBoxLayout()
        
        # 图标
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(48, 48)
        header_layout.addWidget(self.icon_label)
        
        # 标题
        self.title_label = QLabel()
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        self.title_label.setFont(title_font)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        main_layout.addLayout(header_layout)
        
        # 详细信息
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setLineWrapMode(QTextEdit.WidgetWidth)
        main_layout.addWidget(self.details_text)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 帮助按钮
        self.help_button = QPushButton("查看帮助")
        self.help_button.clicked.connect(self._show_help)
        button_layout.addWidget(self.help_button)
        
        # 复制按钮
        self.copy_button = QPushButton("复制错误信息")
        self.copy_button.clicked.connect(self._copy_to_clipboard)
        button_layout.addWidget(self.copy_button)
        
        button_layout.addStretch()
        
        # 确定按钮
        self.ok_button = QPushButton("确定")
        self.ok_button.setDefault(True)
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def show_error(self, title: str, message: str, details: Optional[str] = None, 
                   level: ErrorLevel = ErrorLevel.ERROR):
        """显示错误信息"""
        self.title_label.setText(title)
        self.details_text.setPlainText(message)
        
        # 设置图标
        self._set_icon(level)
        
        # 显示对话框
        return self.exec_()
    
    def _set_icon(self, level: ErrorLevel):
        """设置图标"""
        icon_path = None
        
        if level == ErrorLevel.INFO:
            icon_path = "icons/info.png"
        elif level == ErrorLevel.WARNING:
            icon_path = "icons/warning.png"
        elif level == ErrorLevel.ERROR:
            icon_path = "icons/error.png"
        elif level == ErrorLevel.CRITICAL:
            icon_path = "icons/critical.png"
        
        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(48, 48, Qt.KeepAspectRatio)
            self.icon_label.setPixmap(pixmap)
        else:
            # 使用系统图标
            if level == ErrorLevel.INFO:
                icon = QMessageBox.Information
            elif level == ErrorLevel.WARNING:
                icon = QMessageBox.Warning
            elif level == ErrorLevel.ERROR:
                icon = QMessageBox.Critical
            else:
                icon = QMessageBox.Critical
            
            qbox = QMessageBox(self)
            qbox.setIcon(icon)
            pixmap = qbox.iconPixmap()
            self.icon_label.setPixmap(pixmap.scaled(48, 48, Qt.KeepAspectRatio))
    
    def _show_help(self):
        """显示帮助信息"""
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle("帮助信息")
        help_dialog.setMinimumWidth(600)
        
        layout = QVBoxLayout()
        
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setPlainText("""
常见问题解决方法：

1. 设备连接问题：
   - 检查USB连接线是否正常
   - 确保设备已开启USB调试
   - 尝试重新安装ADB驱动

2. 权限问题：
   - 确保ADB有足够权限
   - 尝试使用管理员权限运行程序

3. 网络问题：
   - 检查网络连接
   - 确保防火墙未阻止连接

4. 文件操作问题：
   - 检查文件路径是否正确
   - 确保有足够的文件访问权限

如果问题仍然存在，请查看详细日志文件获取更多信息。
        """)
        
        layout.addWidget(help_text)
        
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(help_dialog.accept)
        layout.addWidget(ok_button)
        
        help_dialog.setLayout(layout)
        help_dialog.exec_()
    
    def _copy_to_clipboard(self):
        """复制错误信息到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.details_text.toPlainText())


# 简化的错误提示函数
def show_error_dialog(parent, title: str, message: str, details: Optional[str] = None, 
                     level: ErrorLevel = ErrorLevel.ERROR):
    """显示错误对话框"""
    dialog = ErrorDialog(parent)
    return dialog.show_error(title, message, details, level)


def show_info_message(parent, title: str, message: str):
    """显示信息提示"""
    return show_error_dialog(parent, title, message, level=ErrorLevel.INFO)


def show_warning_message(parent, title: str, message: str):
    """显示警告提示"""
    return show_error_dialog(parent, title, message, level=ErrorLevel.WARNING)


def show_error_message(parent, title: str, message: str):
    """显示错误提示"""
    return show_error_dialog(parent, title, message, level=ErrorLevel.ERROR)


def show_critical_message(parent, title: str, message: str):
    """显示严重错误提示"""
    return show_error_dialog(parent, title, message, level=ErrorLevel.CRITICAL)


import os
from PyQt5.QtWidgets import QApplication
