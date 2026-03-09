#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话框样式管理器 - 提供统一的对话框样式
"""

from PyQt5.QtCore import Qt

# 统一的对话框样式
DIALOG_STYLE = """
QDialog {
    background-color: #1e1e2e;
}
QLabel {
    color: #d0d0d0;
    font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
}
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #151521;
    color: #98c379;
    border: 1px solid #3d5a80;
    border-radius: 4px;
    padding: 6px;
    selection-background-color: #3d5a80;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #5a9bd5;
}
QPushButton {
    background-color: #2a3a50;
    color: #d0d0d0;
    border: 1px solid #3d5a80;
    border-radius: 4px;
    padding: 6px 16px;
    min-width: 70px;
}
QPushButton:hover {
    background-color: #3d5a80;
    color: white;
    border: 1px solid #5a9bd5;
}
QPushButton:pressed {
    background-color: #2a4a70;
}
QPushButton:disabled {
    background-color: #2a2a3a;
    color: #5a5a6a;
    border: 1px solid #3a3a4a;
}
QComboBox {
    background-color: #2a2a3a;
    color: #d0d0d0;
    border: 1px solid #3d5a80;
    border-radius: 4px;
    padding: 5px 10px;
    min-width: 100px;
}
QComboBox:hover {
    border: 1px solid #5a9bd5;
}
QComboBox::drop-down {
    border: none;
    width: 25px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #5a9bd5;
}
QComboBox QAbstractItemView {
    background-color: #1e1e2e;
    color: #d0d0d0;
    selection-background-color: #3d5a80;
    border: 1px solid #3d5a80;
}
QListWidget {
    background-color: #151521;
    color: #d0d0d0;
    border: 1px solid #3d5a80;
    border-radius: 4px;
}
QListWidget::item {
    padding: 4px;
}
QListWidget::item:selected {
    background-color: #3d5a80;
}
QListWidget::item:hover {
    background-color: #2a3a50;
}
QTreeWidget {
    background-color: #151521;
    color: #d0d0d0;
    border: 1px solid #3d5a80;
    border-radius: 4px;
}
QTreeWidget::item {
    padding: 2px;
}
QTreeWidget::item:selected {
    background-color: #3d5a80;
}
QTreeWidget::item:hover {
    background-color: #2a3a50;
}
QGroupBox {
    color: #d0d0d0;
    border: 1px solid #3d5a80;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 8px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 6px;
    color: #5a9bd5;
}
QProgressBar {
    background-color: #151521;
    border: 1px solid #3d5a80;
    border-radius: 4px;
    text-align: center;
    color: #d0d0d0;
}
QProgressBar::chunk {
    background-color: #3d5a80;
    border-radius: 3px;
}
QTabWidget::pane {
    border: 1px solid #3d5a80;
    border-radius: 4px;
    background-color: #1e1e2e;
}
QTabBar::tab {
    background-color: #2a2a3a;
    color: #909090;
    border: 1px solid #3d5a80;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 6px 12px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #3d5a80;
    color: white;
}
QTabBar::tab:hover:!selected {
    background-color: #2a3a50;
    color: #b0b0b0;
}
QScrollBar:vertical {
    background-color: #151521;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background-color: #3d5a80;
    border-radius: 5px;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background-color: #151521;
    height: 10px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal {
    background-color: #3d5a80;
    border-radius: 5px;
    min-width: 20px;
}
QCheckBox {
    color: #d0d0d0;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #3d5a80;
    background-color: transparent;
}
QCheckBox::indicator:checked {
    background-color: #3d5a80;
    border: 1px solid #5a9bd5;
}
QSpinBox {
    background-color: #151521;
    color: #d0d0d0;
    border: 1px solid #3d5a80;
    border-radius: 4px;
    padding: 4px;
}
QSpinBox::up-button, QSpinBox::down-button {
    background-color: #2a2a3a;
    border: none;
}
QTableWidget {
    background-color: #151521;
    color: #d0d0d0;
    border: 1px solid #3d5a80;
    border-radius: 4px;
    gridline-color: #3d5a80;
}
QTableWidget::item {
    padding: 4px;
}
QTableWidget::item:selected {
    background-color: #3d5a80;
}
QHeaderView::section {
    background-color: #2a2a3a;
    color: #d0d0d0;
    border: 1px solid #3d5a80;
    padding: 4px;
}
QSplitter::handle {
    background-color: #3d5a80;
}
QFrame[frameShape="4"] {
    background-color: #3d5a80;
}

/* ========== 消息框样式 ========== */
QMessageBox {
    background-color: #1e1e2e;
}
QMessageBox QLabel {
    color: #d0d0d0;
    font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
}
QMessageBox QPushButton {
    background-color: #2a3a50;
    color: #d0d0d0;
    border: 1px solid #3d5a80;
    border-radius: 4px;
    padding: 6px 20px;
    min-width: 80px;
}
QMessageBox QPushButton:hover {
    background-color: #3d5a80;
    color: white;
    border: 1px solid #5a9bd5;
}
QMessageBox QPushButton:pressed {
    background-color: #2a4a70;
}

/* ========== 输入对话框样式 ========== */
QInputDialog {
    background-color: #1e1e2e;
}
QInputDialog QLabel {
    color: #d0d0d0;
    font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
    font-size: 10pt;
}
QInputDialog QLineEdit {
    background-color: #151521;
    color: #98c379;
    border: 1px solid #3d5a80;
    border-radius: 4px;
    padding: 6px 10px;
}
QInputDialog QLineEdit:focus {
    border: 1px solid #5a9bd5;
}
QInputDialog QPushButton {
    background-color: #2a3a50;
    color: #d0d0d0;
    border: 1px solid #3d5a80;
    border-radius: 4px;
    padding: 6px 20px;
    min-width: 70px;
}
QInputDialog QPushButton:hover {
    background-color: #3d5a80;
    color: white;
    border: 1px solid #5a9bd5;
}
QInputDialog QPushButton:default {
    background-color: #3d5a80;
    color: white;
}
"""

# 标题标签样式
TITLE_LABEL_STYLE = """
    font-size: 13pt;
    font-weight: bold;
    color: #5a9bd5;
"""

# 状态标签样式
STATUS_LABEL_STYLE = "color: #909090;"

# 成功状态样式
SUCCESS_STYLE = "color: #98c379;"

# 错误状态样式
ERROR_STYLE = "color: #e06060;"


def apply_dialog_style(dialog):
    """应用统一的对话框样式"""
    dialog.setStyleSheet(DIALOG_STYLE)


def create_styled_label(text, style_type="normal"):
    """创建带样式的标签"""
    from PyQt5.QtWidgets import QLabel
    
    label = QLabel(text)
    if style_type == "title":
        label.setStyleSheet(TITLE_LABEL_STYLE)
        label.setAlignment(Qt.AlignCenter)
    elif style_type == "success":
        label.setStyleSheet(SUCCESS_STYLE)
    elif style_type == "error":
        label.setStyleSheet(ERROR_STYLE)
    
    return label
