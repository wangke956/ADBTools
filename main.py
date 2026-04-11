#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ADBTools 主程序入口
使用最原始的方式记录启动日志，确保在任何情况下都能记录
"""

import sys
import os
import traceback
from datetime import datetime

# ==================== 全局变量 ====================
_CRASH_LOG_FILE = None


def _write_crash_log(message):
    """最原始的日志写入方式 - 不依赖任何模块"""
    global _CRASH_LOG_FILE
    try:
        if _CRASH_LOG_FILE is None:
            # 确定日志目录 - 尝试多个位置
            log_dirs = []
            
            # 1. 用户APPDATA目录（最可靠）
            appdata = os.environ.get('APPDATA', '')
            if appdata:
                log_dirs.append(os.path.join(appdata, 'ADBTools', 'logs'))
            
            # 2. 临时目录
            temp = os.environ.get('TEMP', '') or os.environ.get('TMP', '')
            if temp:
                log_dirs.append(os.path.join(temp, 'ADBTools', 'logs'))
            
            # 3. 程序所在目录
            if getattr(sys, 'frozen', False):
                exe_dir = os.path.dirname(sys.executable)
            else:
                exe_dir = os.path.dirname(os.path.abspath(__file__))
            log_dirs.append(os.path.join(exe_dir, 'logs'))
            
            # 4. 当前工作目录
            log_dirs.append('logs')
            log_dirs.append('.')
            
            # 尝试创建日志文件
            for log_dir in log_dirs:
                try:
                    if log_dir:
                        os.makedirs(log_dir, exist_ok=True)
                        log_file = os.path.join(log_dir, f'crash_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
                        _CRASH_LOG_FILE = open(log_file, 'w', encoding='utf-8', buffering=1)  # 行缓冲
                        _CRASH_LOG_FILE.write(f"日志文件: {log_file}\n")
                        _CRASH_LOG_FILE.flush()
                        break
                except:
                    continue
        
        if _CRASH_LOG_FILE:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            _CRASH_LOG_FILE.write(f"[{timestamp}] {message}\n")
            _CRASH_LOG_FILE.flush()
    except:
        pass


def _log(message):
    """同时写入文件和控制台"""
    _write_crash_log(message)
    try:
        print(message)
    except:
        pass


def _show_error(title, message):
    """显示错误对话框 - 使用Windows API"""
    _log(f"[FATAL] {title}: {message}")
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, f"{message}\n\n请查看日志文件获取详细信息。", title, 0x10)
    except:
        try:
            # 尝试使用tkinter作为后备
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(title, message)
            root.destroy()
        except:
            pass


# ==================== 第一时间开始记录 ====================
_log("=" * 80)
_log("ADBTools 程序启动")
_log("=" * 80)

try:
    _log(f"Python 版本: {sys.version}")
    _log(f"Python 路径: {sys.executable}")
    _log(f"工作目录: {os.getcwd()}")
    _log(f"程序目录: {os.path.dirname(os.path.abspath(__file__))}")
    _log(f"命令行参数: {sys.argv}")
    _log(f"系统平台: {sys.platform}")
    _log(f"是否打包: {getattr(sys, 'frozen', False)}")
    if getattr(sys, 'frozen', False):
        _log(f"可执行文件: {sys.executable}")
except Exception as e:
    _log(f"获取系统信息失败: {e}")

_log("-" * 80)


# ==================== 导入标准库模块 ====================
_log("[STEP] 导入标准库模块")
try:
    import logging
    _log("logging 模块导入成功")
except ImportError as e:
    _show_error("ADBTools 启动失败", f"无法导入标准库模块:\n{e}")
    sys.exit(1)


# ==================== 高DPI设置 ====================
_log("[STEP] 设置高DPI支持")
try:
    from PyQt5.QtCore import Qt, QCoreApplication
    from PyQt5.Qt import QT_VERSION_STR
    
    _log(f"Qt 版本: {QT_VERSION_STR}")
    
    qt_version = tuple(map(int, QT_VERSION_STR.split('.')))
    
    if qt_version >= (5, 14, 0):
        try:
            from PyQt5.QtGui import QGuiApplication
            QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
                Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
            )
            _log("高DPI新API设置成功 (Qt >= 5.14)")
        except Exception as e:
            _log(f"高DPI新API设置失败: {e}")
    
    try:
        QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        _log("高DPI属性设置成功")
    except Exception as e:
        _log(f"高DPI属性设置失败（不影响运行）: {e}")
        
except ImportError as e:
    _log(f"[ERROR] 导入PyQt5失败: {e}")
    _show_error("ADBTools 启动失败", 
        f"无法导入PyQt5模块:\n{e}\n\n请确保已正确安装PyQt5:\npip install PyQt5")
    sys.exit(1)
except Exception as e:
    _log(f"[ERROR] 高DPI设置异常: {e}")
    _log(traceback.format_exc())


# ==================== 创建QApplication ====================
_log("[STEP] 创建QApplication")
try:
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    _log("QApplication创建成功")
except Exception as e:
    _log(f"[ERROR] 创建QApplication失败: {e}")
    _log(traceback.format_exc())
    _show_error("ADBTools 启动失败", f"创建QApplication失败:\n{e}")
    sys.exit(1)


# ==================== 加载样式 ====================
_log("[STEP] 加载样式表")
try:
    from ui_theme_manager import ThemeManager
    ThemeManager.setup_default_theme(app)
    _log("样式加载成功")
except Exception as e:
    _log(f"样式加载失败: {e}")
    _log(traceback.format_exc())


# ==================== 初始化应用日志管理器 ====================
_log("[STEP] 初始化日志管理器")
logger = None
try:
    from logger_manager import get_logger, log_operation
    logger = get_logger("ADBTools.Main")
    logger.info("日志管理器初始化成功")
    _log("日志管理器初始化成功")
except Exception as e:
    _log(f"日志管理器初始化失败: {e}")
    logger = None


# ==================== Nuitka 兼容性初始化 ====================
_log("[STEP] 初始化 Nuitka 兼容性")
try:
    from nuitka_compat import ensure_nuitka_compatibility
    ensure_nuitka_compatibility()
    _log("Nuitka 兼容性初始化成功")
except Exception as e:
    _log(f"Nuitka 兼容性初始化失败（非致命）: {e}")


# ==================== 加载主窗口 ====================
_log("[STEP] 加载主窗口模块")
try:
    from ADB_module import ADB_Mainwindow
    _log("ADB_module导入成功")
except ImportError as e:
    _log(f"[ERROR] 导入ADB_module失败: {e}")
    _log(traceback.format_exc())
    _show_error("ADBTools 启动失败", 
        f"无法导入主窗口模块:\n{e}\n\n详细信息请查看日志文件。")
    sys.exit(1)
except Exception as e:
    _log(f"[ERROR] 导入ADB_module异常: {e}")
    _log(traceback.format_exc())
    _show_error("ADBTools 启动失败", 
        f"导入主窗口模块时发生错误:\n{e}\n\n详细信息请查看日志文件。")
    sys.exit(1)


# ==================== 创建主窗口 ====================
_log("[STEP] 创建主窗口")
try:
    window = ADB_Mainwindow()
    _log(f"主窗口创建成功，版本: {window.VERSION}")
except Exception as e:
    _log(f"[ERROR] 创建主窗口失败: {e}")
    _log(traceback.format_exc())
    _show_error("ADBTools 启动失败", 
        f"创建主窗口失败:\n{e}\n\n详细信息请查看日志文件。")
    sys.exit(1)


# ==================== 显示窗口 ====================
_log("[STEP] 显示主窗口")
try:
    window.show()
    _log("主窗口已显示")
except Exception as e:
    _log(f"[ERROR] 显示主窗口失败: {e}")
    _log(traceback.format_exc())
    _show_error("ADBTools 启动失败", f"显示主窗口失败:\n{e}")
    sys.exit(1)


# ==================== 记录启动完成 ====================
_log("=" * 80)
_log("ADBTools 应用程序启动完成")
_log("=" * 80)

if logger:
    try:
        logger.info("ADBTools 应用程序启动完成")
        logger.info(f"版本: {window.VERSION}")
        log_operation("app_start", {"version": window.VERSION, "action": "启动应用程序"})
    except:
        pass


# ==================== 设置关闭事件 ====================
from PyQt5.QtCore import QThread

def closeevent(event):
    _log("应用程序正在关闭...")
    if logger:
        try:
            logger.info("应用程序正在关闭...")
            log_operation("app_close", {"action": "关闭应用程序"})
        except:
            pass
    
    # 清理线程
    for attr_name in dir(window):
        try:
            attr = getattr(window, attr_name)
            if isinstance(attr, QThread) and attr.isRunning():
                _log(f"终止线程: {attr_name}")
                attr.terminate()
                attr.wait()
        except:
            pass
    
    _log("应用程序已正常关闭")
    event.accept()

window.closeEvent = closeevent


# ==================== 进入主循环 ====================
_log("[STEP] 进入主事件循环")

try:
    exit_code = app.exec_()
    _log(f"主循环退出，退出码: {exit_code}")
    sys.exit(exit_code)
except Exception as e:
    _log(f"[ERROR] 主循环异常: {e}")
    _log(traceback.format_exc())
    _show_error("ADBTools 运行错误", f"主事件循环发生错误:\n{e}")
    sys.exit(1)
finally:
    # 关闭日志文件
    if _CRASH_LOG_FILE:
        try:
            _CRASH_LOG_FILE.close()
        except:
            pass