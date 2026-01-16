#!/usr/bin/env python3
"""增强版配置对话框 - 提供完整的配置文件修改功能"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFileDialog, QMessageBox,
                             QGroupBox, QFormLayout, QCheckBox, QSpinBox,
                             QComboBox, QTabWidget, QWidget, QTextEdit,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QSplitter, QTreeWidget, QTreeWidgetItem,
                             QListWidget, QListWidgetItem, QStackedWidget,
                             QInputDialog, QDialogButtonBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize
from PyQt5.QtGui import QFont, QColor, QBrush
import os
import sys
import json
import copy
from datetime import datetime

try:
    from config_manager_enhanced import enhanced_config_manager as config_manager
    from config_manager_enhanced import ConfigBackupManager
except ImportError:
    # 回退到简单配置管理器
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

class EnhancedConfigDialog(QDialog):
    """增强版配置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ADBTools 配置管理器 (增强版)")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        # 备份管理器
        self.backup_manager = ConfigBackupManager(config_manager)
        
        # 当前编辑的配置
        self.current_config = copy.deepcopy(config_manager.config)
        self.modified = False
        
        # 保存对嵌套字典编辑框的引用
        self.dict_editors = {}
        
        self.init_ui()
        self.load_config()
        
        # 连接信号
        self.connect_signals()
    
    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout()
        
        # 创建主分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：配置树
        self.config_tree = QTreeWidget()
        self.config_tree.setHeaderLabel("配置项")
        self.config_tree.setMinimumWidth(200)
        self.config_tree.itemSelectionChanged.connect(self.on_config_item_selected)
        
        # 右侧：配置编辑区
        self.config_stack = QStackedWidget()
        
        # 通用编辑页面
        self.general_edit_page = self.create_general_edit_page()
        self.config_stack.addWidget(self.general_edit_page)
        
        # JSON编辑页面
        self.json_edit_page = self.create_json_edit_page()
        self.config_stack.addWidget(self.json_edit_page)
        
        # 备份管理页面
        self.backup_page = self.create_backup_page()
        self.config_stack.addWidget(self.backup_page)
        
        # 验证页面
        self.validation_page = self.create_validation_page()
        self.config_stack.addWidget(self.validation_page)
        
        splitter.addWidget(self.config_tree)
        splitter.addWidget(self.config_stack)
        splitter.setSizes([200, 600])
        
        main_layout.addWidget(splitter)
        
        # 状态栏
        status_layout = QHBoxLayout()
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: gray;")
        self.modified_label = QLabel("")
        self.modified_label.setStyleSheet("color: red; font-weight: bold;")
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.modified_label)
        
        main_layout.addLayout(status_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.reload_button = QPushButton("重新加载")
        self.reload_button.clicked.connect(self.reload_config)
        
        self.validate_button = QPushButton("验证配置")
        self.validate_button.clicked.connect(self.validate_config)
        
        self.export_button = QPushButton("导出配置")
        self.export_button.clicked.connect(self.export_config)
        
        self.import_button = QPushButton("导入配置")
        self.import_button.clicked.connect(self.import_config)
        
        self.reset_button = QPushButton("重置默认")
        self.reset_button.clicked.connect(self.reset_to_default)
        
        button_layout.addWidget(self.reload_button)
        button_layout.addWidget(self.validate_button)
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.import_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        
        # 对话框按钮
        self.button_box = QDialogButtonBox()
        self.save_button = self.button_box.addButton("保存", QDialogButtonBox.AcceptRole)
        self.cancel_button = self.button_box.addButton("取消", QDialogButtonBox.RejectRole)
        self.save_button.clicked.connect(self.save_config)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.button_box)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
        # 初始化配置树
        self.init_config_tree()
    
    def init_config_tree(self):
        """初始化配置树"""
        self.config_tree.clear()
        
        # 添加根节点
        root_item = QTreeWidgetItem(self.config_tree, ["配置"])
        root_item.setData(0, Qt.UserRole, "root")
        
        # 添加配置分类
        categories = [
            ("ADB路径设置", "adb"),
            ("日志记录设置", "logging"),
            ("批量安装配置", "batch_install"),
            ("自动备份设置", "backup"),
            ("JSON编辑器", "json_edit"),
            ("备份文件管理", "backup_manage"),
            ("配置有效性验证", "validation")
        ]
        
        for name, key in categories:
            item = QTreeWidgetItem(root_item, [name])
            item.setData(0, Qt.UserRole, key)
        
        # 展开所有项
        self.config_tree.expandAll()
    
    def create_general_edit_page(self):
        """创建通用编辑页面"""
        page = QWidget()
        layout = QVBoxLayout()
        
        # 标题
        self.edit_title = QLabel("选择配置项进行编辑")
        self.edit_title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(self.edit_title)
        
        # 编辑表单
        self.edit_form = QFormLayout()
        layout.addLayout(self.edit_form)
        
        # 占位符
        layout.addStretch()
        
        page.setLayout(layout)
        return page
    
    def create_json_edit_page(self):
        """创建JSON编辑页面"""
        page = QWidget()
        layout = QVBoxLayout()
        
        # 标题
        json_title = QLabel("JSON编辑器 (直接编辑配置)")
        json_title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(json_title)
        
        # JSON编辑器
        self.json_editor = QTextEdit()
        self.json_editor.setFont(QFont("Consolas", 10))
        self.json_editor.setMinimumHeight(400)
        self.json_editor.textChanged.connect(self.on_json_changed)
        
        # 格式化按钮
        format_layout = QHBoxLayout()
        self.format_json_button = QPushButton("格式化JSON")
        self.format_json_button.clicked.connect(self.format_json)
        
        self.validate_json_button = QPushButton("验证JSON")
        self.validate_json_button.clicked.connect(self.validate_json)
        
        format_layout.addWidget(self.format_json_button)
        format_layout.addWidget(self.validate_json_button)
        format_layout.addStretch()
        
        layout.addLayout(format_layout)
        layout.addWidget(self.json_editor)
        
        page.setLayout(layout)
        return page
    
    def create_backup_page(self):
        """创建备份管理页面"""
        page = QWidget()
        layout = QVBoxLayout()
        
        # 标题
        backup_title = QLabel("配置备份管理")
        backup_title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(backup_title)
        
        # 备份列表
        self.backup_table = QTableWidget()
        self.backup_table.setColumnCount(5)
        self.backup_table.setHorizontalHeaderLabels(["文件名", "大小", "修改时间", "操作", ""])
        self.backup_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # 按钮
        backup_button_layout = QHBoxLayout()
        
        self.refresh_backups_button = QPushButton("刷新列表")
        self.refresh_backups_button.clicked.connect(self.refresh_backup_list)
        
        self.create_backup_button = QPushButton("创建备份")
        self.create_backup_button.clicked.connect(self.create_backup)
        
        self.delete_backup_button = QPushButton("删除选中")
        self.delete_backup_button.clicked.connect(self.delete_selected_backup)
        
        backup_button_layout.addWidget(self.refresh_backups_button)
        backup_button_layout.addWidget(self.create_backup_button)
        backup_button_layout.addWidget(self.delete_backup_button)
        backup_button_layout.addStretch()
        
        layout.addLayout(backup_button_layout)
        layout.addWidget(self.backup_table)
        
        # 加载备份列表
        self.refresh_backup_list()
        
        page.setLayout(layout)
        return page
    
    def create_validation_page(self):
        """创建验证页面"""
        page = QWidget()
        layout = QVBoxLayout()
        
        # 标题
        validation_title = QLabel("配置验证")
        validation_title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(validation_title)
        
        # 验证结果
        self.validation_result = QTextEdit()
        self.validation_result.setReadOnly(True)
        self.validation_result.setFont(QFont("Consolas", 10))
        
        # 验证按钮
        validation_button_layout = QHBoxLayout()
        
        self.run_validation_button = QPushButton("运行验证")
        self.run_validation_button.clicked.connect(self.run_validation)
        
        self.fix_issues_button = QPushButton("自动修复问题")
        self.fix_issues_button.clicked.connect(self.fix_validation_issues)
        
        validation_button_layout.addWidget(self.run_validation_button)
        validation_button_layout.addWidget(self.fix_issues_button)
        validation_button_layout.addStretch()
        
        layout.addLayout(validation_button_layout)
        layout.addWidget(self.validation_result)
        
        page.setLayout(layout)
        return page
    
    def connect_signals(self):
        """连接信号"""
        # 连接编辑控件的信号
        pass
    
    def load_config(self):
        """加载配置"""
        try:
            self.current_config = copy.deepcopy(config_manager.config)
            self.modified = False
            self.update_modified_label()
            self.status_label.setText("配置已加载")
        except Exception as e:
            self.status_label.setText(f"加载配置失败: {str(e)}")
    
    def on_config_item_selected(self):
        """配置项选择变化"""
        selected_items = self.config_tree.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        key = item.data(0, Qt.UserRole)
        
        if key == "json_edit":
            self.config_stack.setCurrentWidget(self.json_edit_page)
            self.load_json_editor()
        elif key == "backup_manage":
            self.config_stack.setCurrentWidget(self.backup_page)
        elif key == "validation":
            self.config_stack.setCurrentWidget(self.validation_page)
        else:
            self.config_stack.setCurrentWidget(self.general_edit_page)
            self.load_config_section(key)
    
    def load_config_section(self, section_key):
        """加载配置部分到编辑表单"""
        # 清除现有表单
        while self.edit_form.rowCount() > 0:
            self.edit_form.removeRow(0)
        
        # 清除旧的编辑框引用
        self.dict_editors.clear()
        
        if section_key not in self.current_config:
            self.edit_title.setText(f"配置项: {section_key} (未找到)")
            return
        
        section = self.current_config[section_key]
        self.edit_title.setText(f"配置项: {section_key}")
        
        if isinstance(section, dict):
            for key, value in section.items():
                self.add_form_field(section_key, key, value)
        else:
            # 直接值
            self.add_form_field("", section_key, section)
    
    def add_form_field(self, section_key, field_key, value):
        """添加表单字段"""
        full_key = f"{section_key}.{field_key}" if section_key else field_key
        
        if isinstance(value, bool):
            # 复选框
            checkbox = QCheckBox()
            checkbox.setChecked(value)
            checkbox.stateChanged.connect(lambda state, k=full_key: self.on_checkbox_changed(k, state))
            self.edit_form.addRow(field_key, checkbox)
        
        elif isinstance(value, int):
            # 数字输入框
            spinbox = QSpinBox()
            spinbox.setValue(value)
            spinbox.setRange(-999999, 999999)
            spinbox.valueChanged.connect(lambda val, k=full_key: self.on_spinbox_changed(k, val))
            self.edit_form.addRow(field_key, spinbox)
        
        elif isinstance(value, str):
            # 文本输入框
            line_edit = QLineEdit(value)
            line_edit.textChanged.connect(lambda text, k=full_key: self.on_lineedit_changed(k, text))
            self.edit_form.addRow(field_key, line_edit)
        
        elif isinstance(value, list):
            # 列表编辑器
            list_widget = QListWidget()
            for item in value:
                list_widget.addItem(str(item))
            
            # 添加按钮
            button_layout = QHBoxLayout()
            add_button = QPushButton("添加")
            add_button.clicked.connect(lambda: self.add_list_item(full_key, list_widget))
            
            remove_button = QPushButton("删除")
            remove_button.clicked.connect(lambda: self.remove_list_item(full_key, list_widget))
            
            button_layout.addWidget(add_button)
            button_layout.addWidget(remove_button)
            button_layout.addStretch()
            
            widget = QWidget()
            widget_layout = QVBoxLayout()
            widget_layout.addWidget(list_widget)
            widget_layout.addLayout(button_layout)
            widget.setLayout(widget_layout)
            
            self.edit_form.addRow(field_key, widget)
        
        elif isinstance(value, dict):
            # 嵌套字典 - 显示为可编辑文本
            text_edit = QTextEdit()
            text_edit.setPlainText(json.dumps(value, ensure_ascii=False, indent=2))
            text_edit.setFont(QFont("Consolas", 10))
            text_edit.setMinimumHeight(300)
            text_edit.setMaximumHeight(500)
            text_edit.textChanged.connect(lambda: self.on_dict_text_changed(full_key, text_edit))
            # 保存对编辑框的引用
            self.dict_editors[full_key] = text_edit
            self.edit_form.addRow(field_key, text_edit)
        
        else:
            # 其他类型
            label = QLabel(str(value))
            self.edit_form.addRow(field_key, label)
    
    def on_checkbox_changed(self, key, state):
        """复选框变化"""
        value = state == Qt.Checked
        self.update_config_value(key, value)
    
    def on_spinbox_changed(self, key, value):
        """数字输入框变化"""
        self.update_config_value(key, value)
    
    def on_lineedit_changed(self, key, text):
        """文本输入框变化"""
        self.update_config_value(key, text)
    
    def add_list_item(self, key, list_widget):
        """添加列表项"""
        text, ok = QInputDialog.getText(self, "添加项", "请输入值:")
        if ok and text:
            list_widget.addItem(text)
            # 更新配置
            items = [list_widget.item(i).text() for i in range(list_widget.count())]
            self.update_config_value(key, items)
    
    def remove_list_item(self, key, list_widget):
        """删除列表项"""
        current_item = list_widget.currentItem()
        if current_item:
            row = list_widget.row(current_item)
            list_widget.takeItem(row)
            # 更新配置
            items = [list_widget.item(i).text() for i in range(list_widget.count())]
            self.update_config_value(key, items)
    
    def on_dict_text_changed(self, key, text_edit):
        """嵌套字典文本框变化"""
        try:
            text = text_edit.toPlainText()
            data = json.loads(text)
            self.update_config_value(key, data)
        except json.JSONDecodeError:
            # JSON格式错误时不更新配置
            pass
    
    def update_config_value(self, key, value):
        """更新配置值"""
        keys = key.split('.')
        config = self.current_config
        
        try:
            # 遍历到最后一个键的父级
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # 设置值
            config[keys[-1]] = value
            self.modified = True
            self.update_modified_label()
            self.status_label.setText(f"配置已修改: {key}")
        except Exception as e:
            self.status_label.setText(f"更新配置失败: {str(e)}")
    
    def update_modified_label(self):
        """更新修改标签"""
        if self.modified:
            self.modified_label.setText("已修改")
        else:
            self.modified_label.setText("")
    
    def load_json_editor(self):
        """加载JSON到编辑器"""
        try:
            json_text = json.dumps(self.current_config, ensure_ascii=False, indent=2)
            self.json_editor.setPlainText(json_text)
        except Exception as e:
            self.json_editor.setPlainText(f"错误: {str(e)}")
    
    def on_json_changed(self):
        """JSON编辑器内容变化"""
        self.modified = True
        self.update_modified_label()
        self.status_label.setText("JSON已修改")
    
    def format_json(self):
        """格式化JSON"""
        try:
            text = self.json_editor.toPlainText()
            data = json.loads(text)
            formatted = json.dumps(data, ensure_ascii=False, indent=2)
            self.json_editor.setPlainText(formatted)
            self.status_label.setText("JSON已格式化")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"JSON格式错误:\n{str(e)}")
    
    def validate_json(self):
        """验证JSON"""
        try:
            text = self.json_editor.toPlainText()
            data = json.loads(text)
            QMessageBox.information(self, "成功", "JSON格式正确")
            self.status_label.setText("JSON验证通过")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"JSON格式错误:\n{str(e)}")
    
    def refresh_backup_list(self):
        """刷新备份列表"""
        backups = self.backup_manager.list_backups()
        self.backup_table.setRowCount(len(backups))
        
        for i, backup in enumerate(backups):
            # 文件名
            self.backup_table.setItem(i, 0, QTableWidgetItem(backup["filename"]))
            
            # 大小
            size_mb = backup["size"] / 1024 / 1024
            self.backup_table.setItem(i, 1, QTableWidgetItem(f"{size_mb:.2f} MB"))
            
            # 修改时间
            self.backup_table.setItem(i, 2, QTableWidgetItem(backup["modified"]))
            
            # 恢复按钮
            restore_button = QPushButton("恢复")
            restore_button.clicked.connect(lambda checked, path=backup["path"]: self.restore_backup(path))
            self.backup_table.setCellWidget(i, 3, restore_button)
            
            # 查看按钮
            view_button = QPushButton("查看")
            view_button.clicked.connect(lambda checked, path=backup["path"]: self.view_backup(path))
            self.backup_table.setCellWidget(i, 4, view_button)
    
    def create_backup(self):
        """创建备份"""
        if self.backup_manager.create_backup():
            QMessageBox.information(self, "成功", "备份创建成功")
            self.refresh_backup_list()
            self.status_label.setText("备份已创建")
        else:
            QMessageBox.warning(self, "警告", "备份创建失败")
    
    def delete_selected_backup(self):
        """删除选中的备份"""
        selected_rows = self.backup_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请选择要删除的备份")
            return
        
        row = selected_rows[0].row()
        filename = self.backup_table.item(row, 0).text()
        backup_path = os.path.join(self.backup_manager.backup_path, filename)
        
        reply = QMessageBox.question(self, "确认", f"确定要删除备份 '{filename}' 吗？",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                os.remove(backup_path)
                QMessageBox.information(self, "成功", "备份已删除")
                self.refresh_backup_list()
                self.status_label.setText("备份已删除")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"删除备份失败:\n{str(e)}")
    
    def restore_backup(self, backup_path):
        """从备份恢复"""
        reply = QMessageBox.question(self, "确认", "确定要从备份恢复配置吗？当前配置将被覆盖。",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if self.backup_manager.restore_backup(backup_path):
                QMessageBox.information(self, "成功", "配置已从备份恢复")
                self.load_config()
                self.status_label.setText("配置已恢复")
            else:
                QMessageBox.warning(self, "错误", "恢复配置失败")
    
    def view_backup(self, backup_path):
        """查看备份内容"""
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"查看备份: {os.path.basename(backup_path)}")
            dialog.setMinimumSize(600, 400)
            
            layout = QVBoxLayout()
            text_edit = QTextEdit()
            text_edit.setPlainText(content)
            text_edit.setReadOnly(True)
            text_edit.setFont(QFont("Consolas", 10))
            
            layout.addWidget(text_edit)
            dialog.setLayout(layout)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"查看备份失败:\n{str(e)}")
    
    def run_validation(self):
        """运行验证"""
        try:
            # 如果JSON编辑器中有修改，先更新配置
            if self.config_stack.currentWidget() == self.json_edit_page:
                text = self.json_editor.toPlainText()
                self.current_config = json.loads(text)
            
            # 运行验证
            result = config_manager.validate_config()
            
            # 显示结果
            output = "配置验证结果:\n\n"
            
            if result["errors"]:
                output += "❌ 错误:\n"
                for error in result["errors"]:
                    output += f"  • {error}\n"
                output += "\n"
            
            if result["warnings"]:
                output += "⚠️ 警告:\n"
                for warning in result["warnings"]:
                    output += f"  • {warning}\n"
                output += "\n"
            
            if not result["errors"] and not result["warnings"]:
                output += "✅ 配置验证通过，没有发现问题。\n"
            
            self.validation_result.setPlainText(output)
            self.status_label.setText("验证完成")
            
        except Exception as e:
            self.validation_result.setPlainText(f"验证过程中出错:\n{str(e)}")
    
    def fix_validation_issues(self):
        """自动修复验证问题"""
        try:
            # 运行验证
            result = config_manager.validate_config()
            
            if not result["errors"] and not result["warnings"]:
                QMessageBox.information(self, "信息", "没有需要修复的问题")
                return
            
            # 这里可以添加自动修复逻辑
            # 例如：修复无效的数值范围
            
            QMessageBox.information(self, "信息", "自动修复功能尚未实现")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"修复过程中出错:\n{str(e)}")
    
    def reload_config(self):
        """重新加载配置"""
        reply = QMessageBox.question(self, "确认", "确定要重新加载配置吗？未保存的修改将丢失。",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if config_manager.reload_config():
                self.load_config()
                self.status_label.setText("配置已重新加载")
            else:
                QMessageBox.warning(self, "警告", "重新加载配置失败")
    
    def validate_config(self):
        """验证配置"""
        self.run_validation()
    
    def export_config(self):
        """导出配置"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出配置", "", "JSON文件 (*.json);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                # 如果JSON编辑器中有修改，先更新配置
                if self.config_stack.currentWidget() == self.json_edit_page:
                    text = self.json_editor.toPlainText()
                    self.current_config = json.loads(text)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.current_config, f, ensure_ascii=False, indent=2)
                
                QMessageBox.information(self, "成功", f"配置已导出到:\n{file_path}")
                self.status_label.setText("配置已导出")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"导出配置失败:\n{str(e)}")
    
    def import_config(self):
        """导入配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入配置", "", "JSON文件 (*.json);;所有文件 (*.*)"
        )
        
        if file_path:
            reply = QMessageBox.question(self, "确认", 
                "导入配置将覆盖当前配置。\n选择导入方式：",
                "合并配置|替换配置|取消", 
                defaultButton=0)
            
            if reply == 0:  # 合并
                merge = True
            elif reply == 1:  # 替换
                merge = False
            else:  # 取消
                return
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_config = json.load(f)
                
                if merge:
                    # 深度合并
                    self.deep_merge(self.current_config, imported_config)
                else:
                    # 替换
                    self.current_config = imported_config
                
                self.modified = True
                self.update_modified_label()
                
                # 更新UI
                if self.config_stack.currentWidget() == self.json_edit_page:
                    self.load_json_editor()
                
                QMessageBox.information(self, "成功", "配置已导入")
                self.status_label.setText("配置已导入")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"导入配置失败:\n{str(e)}")
    
    def deep_merge(self, target, source):
        """深度合并字典"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self.deep_merge(target[key], value)
            else:
                target[key] = value
    
    def reset_to_default(self):
        """重置到默认值"""
        reply = QMessageBox.question(self, "确认", 
            "确定要重置配置到默认值吗？当前配置将丢失。",
            QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # 获取当前选中的配置项
            selected_items = self.config_tree.selectedItems()
            if selected_items:
                item = selected_items[0]
                key = item.data(0, Qt.UserRole)
                
                if key and key != "root":
                    # 重置特定配置项
                    if config_manager.reset_to_default(key):
                        self.load_config()
                        self.status_label.setText(f"配置项 '{key}' 已重置")
                    else:
                        QMessageBox.warning(self, "警告", f"重置配置项 '{key}' 失败")
                else:
                    # 重置所有配置
                    if config_manager.reset_to_default():
                        self.load_config()
                        self.status_label.setText("所有配置已重置")
                    else:
                        QMessageBox.warning(self, "警告", "重置所有配置失败")
            else:
                # 重置所有配置
                if config_manager.reset_to_default():
                    self.load_config()
                    self.status_label.setText("所有配置已重置")
                else:
                    QMessageBox.warning(self, "警告", "重置所有配置失败")
    
    def save_config(self):
        """保存配置"""
        try:
            # 如果JSON编辑器中有修改，先更新配置
            if self.config_stack.currentWidget() == self.json_edit_page:
                text = self.json_editor.toPlainText()
                self.current_config = json.loads(text)
            else:
                # 从所有嵌套字典编辑框中读取最新值
                for key, text_edit in self.dict_editors.items():
                    try:
                        text = text_edit.toPlainText()
                        data = json.loads(text)
                        self.update_config_value(key, data)
                    except json.JSONDecodeError:
                        # JSON格式错误，跳过
                        pass
            
            # 更新配置管理器
            config_manager.config = copy.deepcopy(self.current_config)
            
            # 保存到文件
            if config_manager.save_config():
                self.modified = False
                self.update_modified_label()
                QMessageBox.information(self, "成功", "配置保存成功")
                self.status_label.setText("配置已保存")
                self.accept()
            else:
                QMessageBox.warning(self, "警告", "配置保存失败")
        except json.JSONDecodeError as e:
            QMessageBox.warning(self, "JSON错误", f"JSON格式错误:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置时出错:\n{str(e)}")
    
    def closeEvent(self, event):
        """对话框关闭事件"""
        if self.modified:
            reply = QMessageBox.question(self, "确认", 
                "配置已修改，是否保存？",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            
            if reply == QMessageBox.Save:
                self.save_config()
                event.accept()
            elif reply == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()