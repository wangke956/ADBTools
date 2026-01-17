#!/usr/bin/env python3
"""
u2重新初始化进度对话框 - 显示uiautomator2重新初始化的进度
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
                             QPushButton, QLabel, QProgressBar)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from logger_manager import get_logger

logger = get_logger("ADBTools.U2ReinitDialog")


class U2ReinitDialog(QDialog):
    """u2重新初始化进度对话框"""
    
    def __init__(self, parent=None):
        """
        初始化对话框
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self.setWindowTitle("重新初始化 uiautomator2")
        self.setMinimumSize(500, 400)
        self.setModal(True)
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        
        # 创建UI
        self._init_ui()
        
        logger.info("u2重新初始化对话框已创建")
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("uiautomator2 重新初始化")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 分隔线
        from PyQt5.QtWidgets import QFrame
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # 进度显示区域
        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        self.progress_text.setMaximumHeight(250)
        self.progress_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.progress_text)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 不确定进度
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("准备开始...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.close_button = QPushButton("关闭")
        self.close_button.setEnabled(False)
        self.close_button.clicked.connect(self.close)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def add_progress(self, message):
        """
        添加进度信息
        
        Args:
            message: 进度消息
        """
        self.progress_text.append(message)
        # 自动滚动到底部
        cursor = self.progress_text.textCursor()
        cursor.movePosition(cursor.End)
        self.progress_text.setTextCursor(cursor)
        
        # 更新状态标签
        self.status_label.setText(message.split(":")[0].strip() if ":" in message else message)
        
        logger.debug(f"进度更新: {message}")
    
    def set_error(self, error_message):
        """
        设置错误信息
        
        Args:
            error_message: 错误消息
        """
        self.progress_text.append(f"\n❌ 错误: {error_message}")
        self.progress_bar.setRange(0, 1)  # 停止进度条
        self.status_label.setText("初始化失败")
        self.status_label.setStyleSheet("color: red;")
        self.close_button.setEnabled(True)
        
        logger.error(f"初始化失败: {error_message}")
    
    def set_success(self, success_message):
        """
        设置成功信息
        
        Args:
            success_message: 成功消息
        """
        self.progress_text.append(f"\n✓ {success_message}")
        self.progress_bar.setRange(0, 1)  # 停止进度条
        self.progress_bar.setValue(1)
        self.status_label.setText("初始化成功")
        self.status_label.setStyleSheet("color: green;")
        self.close_button.setEnabled(True)
        
        logger.info(f"初始化成功: {success_message}")
    
    def start(self):
        """开始初始化"""
        self.progress_text.clear()
        self.progress_bar.setRange(0, 0)  # 不确定进度
        self.status_label.setText("正在初始化...")
        self.status_label.setStyleSheet("color: black;")
        self.close_button.setEnabled(False)
        self.progress_text.append("=" * 60)
        self.progress_text.append("开始重新初始化 uiautomator2 服务")
        self.progress_text.append("=" * 60)
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.close_button.isEnabled():
            event.accept()
        else:
            # 如果正在初始化，不允许关闭
            event.ignore()