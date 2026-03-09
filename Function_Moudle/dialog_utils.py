#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对话框工具类 - 提供可复用的对话框组件"""

import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt
from Function_Moudle.dialog_styles import apply_dialog_style, TITLE_LABEL_STYLE


class ApkMultiSelectDialog(QDialog):
    """APK文件多选对话框"""
    
    def __init__(self, parent, folder_path, title="选择APK文件"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(600, 400)
        self.selected_files = []
        self.folder_path = folder_path
        
        # 应用统一样式
        apply_dialog_style(self)
        
        # 获取APK文件列表
        self.apk_files = [f for f in os.listdir(folder_path) if f.endswith('.apk')]
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 标签
        title_label = QLabel(f"从 {len(self.apk_files)} 个APK文件中选择:")
        title_label.setStyleSheet(TITLE_LABEL_STYLE)
        layout.addWidget(title_label)
        
        # 文件列表
        self.file_list = QListWidget(self)
        self.file_list.setSelectionMode(QListWidget.ExtendedSelection)
        
        for apk_file in self.apk_files:
            item = QListWidgetItem(apk_file)
            item.setCheckState(Qt.Unchecked)
            self.file_list.addItem(item)
        
        layout.addWidget(self.file_list)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        select_all_btn = QPushButton("全选")
        select_all_btn.clicked.connect(self._select_all)
        button_layout.addWidget(select_all_btn)
        
        invert_btn = QPushButton("反选")
        invert_btn.clicked.connect(self._invert_selection)
        button_layout.addWidget(invert_btn)
        
        clear_btn = QPushButton("清空")
        clear_btn.clicked.connect(self._clear_selection)
        button_layout.addWidget(clear_btn)
        
        button_layout.addStretch()
        
        confirm_btn = QPushButton("确认")
        confirm_btn.clicked.connect(self.accept)
        button_layout.addWidget(confirm_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def _select_all(self):
        """全选"""
        for i in range(self.file_list.count()):
            self.file_list.item(i).setCheckState(Qt.Checked)
    
    def _invert_selection(self):
        """反选"""
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            item.setCheckState(Qt.Checked if item.checkState() == Qt.Unchecked else Qt.Unchecked)
    
    def _clear_selection(self):
        """清空选择"""
        for i in range(self.file_list.count()):
            self.file_list.item(i).setCheckState(Qt.Unchecked)
    
    def get_selected_files(self):
        """获取选中的文件列表"""
        selected = []
        for i in range(self.file_list.count()):
            if self.file_list.item(i).checkState() == Qt.Checked:
                selected.append(self.file_list.item(i).text())
        return selected
    
    @staticmethod
    def select_apk_files(parent, title="选择APK文件"):
        """
        静态方法：弹出文件夹选择对话框，然后显示APK多选对话框
        
        Args:
            parent: 父窗口
            title: 对话框标题
            
        Returns:
            tuple: (folder_path, selected_files) 或 (None, None)
        """
        # 选择文件夹
        folder_path = QFileDialog.getExistingDirectory(
            parent,
            "选择APK文件所在文件夹",
            "."
        )
        
        if not folder_path:
            return None, None
        
        # 检查是否有APK文件
        apk_files = [f for f in os.listdir(folder_path) if f.endswith('.apk')]
        if not apk_files:
            QMessageBox.warning(parent, "未找到APK文件", f"在 {folder_path} 中未找到任何APK文件")
            return None, None
        
        # 显示多选对话框
        dialog = ApkMultiSelectDialog(parent, folder_path, title)
        if dialog.exec_() == QDialog.Accepted:
            selected_files = dialog.get_selected_files()
            if not selected_files:
                QMessageBox.warning(parent, "未选择文件", "请至少选择一个APK文件")
                return folder_path, None
            return folder_path, selected_files
        
        return folder_path, None


class ConfirmDialog:
    """确认对话框工具类"""
    
    @staticmethod
    def confirm(parent, title, message, default_no=True):
        """
        显示确认对话框
        
        Args:
            parent: 父窗口
            title: 对话框标题
            message: 提示信息
            default_no: 默认选择No
            
        Returns:
            bool: 用户是否确认
        """
        default_button = QMessageBox.No if default_no else QMessageBox.Yes
        reply = QMessageBox.question(
            parent,
            title,
            message,
            QMessageBox.Yes | QMessageBox.No,
            default_button
        )
        return reply == QMessageBox.Yes
    
    @staticmethod
    def info(parent, title, message):
        """显示信息对话框"""
        QMessageBox.information(parent, title, message)
    
    @staticmethod
    def warning(parent, title, message):
        """显示警告对话框"""
        QMessageBox.warning(parent, title, message)
