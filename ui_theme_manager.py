#!/usr/bin/env python3
"""主题管理器 - 仅保留用户指定的四种现代 PyQt6 皮肤，并提供彻底的样式重置功能"""

import os
import sys
from PyQt6.QtWidgets import QApplication, QStyleFactory
from PyQt6.QtGui import QPalette
from config_manager import config_manager


def _apply_fusion_dark_palette(app):
    """应用 Fusion 深色调色板（当 qdarkstyle 等库未安装时使用）"""
    from PyQt6.QtGui import QPalette, QColor
    from PyQt6.QtGui import QPalette as QPaletteClass
    
    palette = QPalette()
    
    # 基础颜色
    dark_color = QColor(45, 45, 45)
    mid_color = QColor(60, 60, 60)
    light_color = QColor(180, 180, 180)
    text_color = QColor(200, 200, 200)
    highlight_color = QColor(42, 130, 218)
    
    palette.setColor(QPalette.ColorRole.Window, dark_color)
    palette.setColor(QPalette.ColorRole.WindowText, text_color)
    palette.setColor(QPalette.ColorRole.Base, QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.AlternateBase, dark_color)
    palette.setColor(QPalette.ColorRole.ToolTipBase, text_color)
    palette.setColor(QPalette.ColorRole.ToolTipText, text_color)
    palette.setColor(QPalette.ColorRole.Text, text_color)
    palette.setColor(QPalette.ColorRole.Button, dark_color)
    palette.setColor(QPalette.ColorRole.ButtonText, text_color)
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 51, 51))
    palette.setColor(QPalette.ColorRole.Link, highlight_color)
    palette.setColor(QPalette.ColorRole.Highlight, highlight_color)
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(240, 240, 240))
    
    app.setPalette(palette)

class ThemeManager:
    """主题管理器"""
    
    THEMES = {
        "qdarkstyle_dark": "QDarkStyle (深色)",
        "pyqtdarktheme_dark": "PyQtDarkTheme (深色)",
        "fluent_light": "Fluent Design (浅色)",
        "qtmodern": "QtModern",
    }
    
    # 静态变量用于存储原始状态
    _original_palette = None
    _original_style_name = None
    
    @staticmethod
    def get_current_theme():
        """获取当前配置的主题"""
        theme = config_manager.get("ui.theme", "qdarkstyle_dark")
        # 如果当前主题不在精简后的列表中，回退到默认
        if theme not in ThemeManager.THEMES:
            return "qdarkstyle_dark"
        return theme
    
    @classmethod
    def is_dark_theme(cls, theme_name=None):
        """判断指定或当前主题是否为深色主题"""
        if theme_name is None:
            theme_name = cls.get_current_theme()
            
        if theme_name == "fluent_light":
            return False
        return True
    
    @classmethod
    def _reset_app_style(cls, app):
        """在应用新主题前，彻底清除旧主题留下的痕迹"""
        # 1. 记录初始状态 (仅第一次执行)
        if cls._original_palette is None:
            cls._original_palette = QPalette(app.palette())
            cls._original_style_name = app.style().objectName()
            
        # 2. 清除 QSS 样式表
        app.setStyleSheet("")
        
        # 3. 恢复原始调色板
        app.setPalette(cls._original_palette)
        
        # 4. 恢复基础样式风格 (推荐使用 Fusion 作为所有现代主题的底座)
        # Fusion 风格在 Windows/Linux/macOS 上表现最一致
        app.setStyle(QStyleFactory.create('Fusion'))

    @classmethod
    def apply_theme(cls, app, theme_name=None):
        """
        应用指定的主题
        
        Args:
            app: QApplication 实例
            theme_name: 主题名称，如果为 None 则从配置中读取
            
        Returns:
            (bool, str): (是否成功, 消息)
        """
        if theme_name is None:
            theme_name = cls.get_current_theme()
        
        # 兼容旧配置
        if theme_name == "dark": theme_name = "qdarkstyle_dark"
        if theme_name == "light": theme_name = "fluent_light"
        
        print(f"正在切换主题: {theme_name}")
        
        try:
            # 关键：先彻底重置
            cls._reset_app_style(app)
            
            # 明确设置环境变量
            os.environ['QT_API'] = 'PyQt6'
            
            # 根据主题名称应用新样式
            if theme_name == "qdarkstyle_dark":
                try:
                    import qdarkstyle
                    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='PyQt6'))
                    msg = "成功切换到 QDarkStyle (深色)"
                except ImportError:
                    # qdarkstyle 未安装，使用 Fusion 深色作为回退
                    app.setStyle(QStyleFactory.create('Fusion'))
                    _apply_fusion_dark_palette(app)
                    msg = "已应用 Fusion 深色 (QDarkStyle 未安装)"
                    
            elif theme_name == "pyqtdarktheme_dark":
                try:
                    import qdarktheme
                    qdarktheme.setup_theme("dark")
                    msg = "成功切换到 PyQtDarkTheme (深色)"
                except ImportError:
                    app.setStyle(QStyleFactory.create('Fusion'))
                    _apply_fusion_dark_palette(app)
                    msg = "已应用 Fusion 深色 (PyQtDarkTheme 未安装)"
                    
            elif theme_name == "fluent_light":
                try:
                    from qfluentwidgets import setTheme, Theme, FluentStyleSheet, setStyleSheet
                    setTheme(Theme.LIGHT)
                    setStyleSheet(app, FluentStyleSheet.FLUENT_WINDOW)
                    msg = "成功切换到 Fluent Design (浅色)"
                except ImportError:
                    # qfluentwidgets 未安装，使用 Fusion 浅色作为回退
                    app.setStyle(QStyleFactory.create('Fusion'))
                    msg = "已应用 Fusion 浅色 (Fluent Widgets 未安装)"

            elif theme_name == "qtmodern":
                try:
                    import qtmodern.styles
                    qtmodern.styles.dark(app)
                    msg = "成功切换到 QtModern"
                except ImportError:
                    app.setStyle(QStyleFactory.create('Fusion'))
                    _apply_fusion_dark_palette(app)
                    msg = "已应用 Fusion 深色 (QtModern 未安装)"
            
            else:
                # 默认回退
                app.setStyle(QStyleFactory.create('Fusion'))
                _apply_fusion_dark_palette(app)
                theme_name = "qdarkstyle_dark"
                msg = "已回退到 Fusion 深色"
            
            # 保存配置
            config_manager.set("ui.theme", theme_name)
            return True, msg
            
        except Exception as e:
            import traceback
            error_msg = f"切换主题 {theme_name} 失败: {e}\n{traceback.format_exc()}"
            print(error_msg)
            return False, error_msg

    @classmethod
    def setup_default_theme(cls, app):
        """初始化时设置默认主题"""
        theme = cls.get_current_theme()
        cls.apply_theme(app, theme)
