from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QProgressBar)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from typing import List, Dict, Any, Optional


class GuideStep:
    """引导步骤类"""
    
    def __init__(self, title: str, description: str, tips: Optional[str] = None):
        self.title = title
        self.description = description
        self.tips = tips
        self.completed = False


class OperationGuide(QDialog):
    """操作引导对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.steps: List[GuideStep] = []
        self.current_step = 0
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("操作引导")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # 主布局
        main_layout = QVBoxLayout()
        
        # 标题
        self.title_label = QLabel()
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(16)
        self.title_label.setFont(title_font)
        main_layout.addWidget(self.title_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        main_layout.addWidget(self.progress_bar)
        
        # 描述
        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setLineWrapMode(QTextEdit.WidgetWidth)
        main_layout.addWidget(self.description_text)
        
        # 提示信息
        self.tips_text = QTextEdit()
        self.tips_text.setReadOnly(True)
        self.tips_text.setLineWrapMode(QTextEdit.WidgetWidth)
        self.tips_text.setVisible(False)
        main_layout.addWidget(self.tips_text)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 上一步按钮
        self.prev_button = QPushButton("上一步")
        self.prev_button.clicked.connect(self._previous_step)
        button_layout.addWidget(self.prev_button)
        
        # 下一步按钮
        self.next_button = QPushButton("下一步")
        self.next_button.clicked.connect(self._next_step)
        button_layout.addWidget(self.next_button)
        
        # 完成按钮
        self.finish_button = QPushButton("完成")
        self.finish_button.clicked.connect(self.accept)
        self.finish_button.setVisible(False)
        button_layout.addWidget(self.finish_button)
        
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def add_step(self, title: str, description: str, tips: Optional[str] = None) -> None:
        """添加引导步骤"""
        step = GuideStep(title, description, tips)
        self.steps.append(step)
    
    def start(self) -> int:
        """开始引导"""
        if not self.steps:
            return QDialog.Rejected
        
        self.current_step = 0
        self._update_ui()
        return self.exec_()
    
    def _update_ui(self):
        """更新UI"""
        if 0 <= self.current_step < len(self.steps):
            step = self.steps[self.current_step]
            
            # 更新标题
            self.title_label.setText(f"步骤 {self.current_step + 1}/{len(self.steps)}: {step.title}")
            
            # 更新描述
            self.description_text.setPlainText(step.description)
            
            # 更新提示
            if step.tips:
                self.tips_text.setPlainText(f"💡 提示：{step.tips}")
                self.tips_text.setVisible(True)
            else:
                self.tips_text.setVisible(False)
            
            # 更新进度条
            progress = int((self.current_step + 1) / len(self.steps) * 100)
            self.progress_bar.setValue(progress)
            
            # 更新按钮状态
            self.prev_button.setEnabled(self.current_step > 0)
            
            if self.current_step == len(self.steps) - 1:
                self.next_button.setVisible(False)
                self.finish_button.setVisible(True)
            else:
                self.next_button.setVisible(True)
                self.finish_button.setVisible(False)
    
    def _previous_step(self):
        """上一步"""
        if self.current_step > 0:
            self.current_step -= 1
            self._update_ui()
    
    def _next_step(self):
        """下一步"""
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self._update_ui()


class QuickGuide(QDialog):
    """快速引导对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("快速入门")
        self.setMinimumWidth(500)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.WindowCloseButtonHint)
        
        # 主布局
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("欢迎使用ADBTools！")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(16)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 内容
        content_text = QTextEdit()
        content_text.setReadOnly(True)
        content_text.setPlainText("""
ADBTools 是一个强大的Android设备管理工具，主要功能包括：

📱 设备管理：连接、刷新、重启设备
📦 应用管理：安装、卸载、停止应用
📁 文件管理：拉取文件、截图、日志
🔧 系统工具：获取Root权限、设置日期时间
🎮 VR功能：VR环境切换、网络检查
⚙️ 项目功能：批量安装、版本验证

入门指南：
1. 点击"刷新设备"按钮连接设备
2. 在设备列表中选择设备
3. 使用各个功能模块进行操作

查看更多详细帮助，请点击菜单"帮助"。
        """)
        layout.addWidget(content_text)
        
        # 按钮
        ok_button = QPushButton("我知道了")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)
        
        self.setLayout(layout)


def show_quick_guide(parent) -> None:
    """显示快速入门引导"""
    guide = QuickGuide(parent)
    guide.exec_()


def create_device_setup_guide(parent) -> OperationGuide:
    """创建设备设置引导"""
    guide = OperationGuide(parent)
    
    guide.add_step(
        "连接设备",
        "请确保您的Android设备已通过USB连接到电脑，并已开启USB调试模式。",
        "USB调试模式通常在开发者选项中开启"
    )
    
    guide.add_step(
        "刷新设备",
        "点击主界面的'刷新设备'按钮，系统将扫描并显示已连接的设备。",
        "如果设备未显示，请检查USB连接和驱动安装"
    )
    
    guide.add_step(
        "选择设备",
        "在设备列表中选择您要操作的设备。",
        "设备ID通常以字母和数字组成"
    )
    
    guide.add_step(
        "开始使用",
        "现在您可以使用各个功能模块进行设备操作了！",
        "建议先熟悉基本功能，再尝试高级功能"
    )
    
    return guide


def create_app_install_guide(parent) -> OperationGuide:
    """创建应用安装引导"""
    guide = OperationGuide(parent)
    
    guide.add_step(
        "选择APK文件",
        "点击'安装APK'按钮，选择要安装的APK文件。",
        "支持选择单个或多个APK文件"
    )
    
    guide.add_step(
        "开始安装",
        "点击'开始安装'按钮，系统将自动安装选中的APK文件。",
        "安装过程中请不要断开设备连接"
    )
    
    guide.add_step(
        "查看结果",
        "安装完成后，查看日志输出确认安装结果。",
        "失败时会显示详细错误信息"
    )
    
    return guide
