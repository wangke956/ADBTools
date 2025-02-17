import sys
import subprocess
import os
import time
import logging
import re
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTextEdit, QWidget, QLabel,
                             QGridLayout, QFrame, QComboBox, QInputDialog,
                             QFileDialog, QDialog, QLineEdit, QScrollArea,
                             QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QColor

# 设置日志输出格式
APPEARANCE = {
    'window': {
        'background_color': '#f5f5f5',
        'size': (643, 705)
    },
    'buttons': {
        'font_size': 16,
        'background_color': '#5C5D5E',
        'text_color': '#ffffff',
        'hover_color': '#2980b9',
        'pressed_color': '#2070a9',
        'disabled_color': '#bdc3c7',
        'disabled_text_color': '#7f8c8d',
        'border_color': '#5C5D5E',
        'border_radius': 4,
        'min_width': 120,
        'max_width': 150,
        'height': 40,  # 添加这行
        'width': 150,  # 添加这行
    },
    'labels': {
        'font_size': 14,
        'text_color': '#333333'
    },
    'output': {
        'font_size': 20,
        'text_color': '#1A1A1A',
        'font_family': 'Arial',
        'background_color': '#ffffff',
        'border_color': '#bdc3c7',
        # 'font_family': 'Microsoft YaHei'


    },
    'combobox': {
        'background_color': '#ffffff',
        'border_color': '#bdc3c7',
        'text_color': '#333333'
    }
}


# ADB命令执行线程类
class AdbCommand(QThread):
    # 定义信号用于传递命令执行结果
    finished = pyqtSignal(str)

    def __init__(self, command, device_id=None):
        super().__init__()
        self.command = command
        self.device_id = device_id

    def run(self):
        try:
            # 构建ADB命令
            cmd = ['adb']
            if self.device_id:
                cmd.extend(['-s', self.device_id])
            cmd.extend(self.command.split())

            # 执行ADB命令并捕获输出
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # 发送执行结果信号
            self.finished.emit(f"命令: adb {' '.join(cmd[1:])}\n输出:\n{result.stdout}\n{result.stderr}")
        except subprocess.CalledProcessError as e:
            # 如果命令执行失败，发送错误信息
            self.finished.emit(f"错误: 命令执行失败, 返回码: {e.returncode}\n输出:\n{e.stdout}\n错误:\n{e.stderr}")
        except Exception as e:
            # 捕获其他异常
            self.finished.emit(f"错误: {str(e)}")


# 获取设备列表的线程类
class GetDevicesCommand(QThread):
    finished = pyqtSignal(list)

    def run(self):
        try:
            # 执行 'adb devices' 命令获取设备列表
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, check=True)

            # 解析命令输出，提取设备ID
            lines = result.stdout.strip().split('\n')[1:]
            devices = [line.split('\t')[0] for line in lines if line.strip() and '\t' in line]

            # 发送设备列表信号
            self.finished.emit(devices)
        except subprocess.CalledProcessError as e:
            # 如果命令执行失败，记录错误并发送空列表
            logging.error(f"获取设备列表失败: {e}")
            self.finished.emit([])
        except Exception as e:
            # 捕获其他异常
            logging.error(f"获取设备列表时发生未知错误: {e}")
            self.finished.emit([])


# 主窗口类
class AdbUiAutomatorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ADB and uiautomator2 GUI")
        # 设置窗口初始大小
        self.setGeometry(100, 100, *APPEARANCE['window']['size'])
        self.device = None
        self.setup_logging()
        self.init_ui()
        self.apply_styles()

    # 在状态栏显示进度信息
    def show_progress(self, message):
        self.statusBar().showMessage(message)

    def init_ui(self):
        # 创建主窗口部件和布局
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)

        # 顶部设备选择区域
        top_layout = QHBoxLayout()
        self.device_combo = QComboBox()
        # 设置下拉框自动扩展
        self.device_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.device_combo.currentTextChanged.connect(self.on_device_selected)
        refresh_button = QPushButton("刷新设备")
        refresh_button.clicked.connect(self.refresh_devices)
        refresh_button.setIcon(QIcon.fromTheme("view-refresh"))
        top_layout.addWidget(QLabel("选择设备:"))
        top_layout.addWidget(self.device_combo)
        top_layout.addWidget(refresh_button)
        main_layout.addLayout(top_layout)

        # 内容区域布局
        content_layout = QHBoxLayout()

        # 左侧面板 - 基础ADB命令
        left_panel = QFrame()
        left_layout = QGridLayout()
        left_layout.setSpacing(10)
        left_panel.setFrameStyle(QFrame.Shape.NoFrame)

        # 右侧面板 - 高级功能
        right_panel = QFrame()
        right_layout = QGridLayout()
        right_layout.setSpacing(10)
        right_panel.setFrameStyle(QFrame.Shape.NoFrame)

        # 定义所有按钮
        all_buttons = [
            ("重启设备", self.reboot_device),
            ("获取Root权限", lambda: self.run_adb_command("root")),
            ("Pull文件", self.pull_file),
            ("Push文件", self.push_file),
            ("模拟点击", self.simulate_tap),
            ("模拟滑动", self.simulate_swipe),
            ("模拟长按", self.simulate_long_press),
            ("安装应用", self.install_app),
            ("卸载应用", self.uninstall_app),
            ("启动应用", self.start_app),
            ("截图", self.take_screenshot),
            ("获取应用路径", self.get_app_path),
            ("输入文本", self.input_text),
            ("获取应用版本号", self.get_app_version),
            ("拉取所有日志", self.pull_all_logs),
            ("获取apk文件的包名", self.get_apk_package_name),
            ("清除应用缓存", self.clear_app_cache),
            ("获取当前应用信息", self.get_current_app_info),
            ("关闭应用", self.close_current_app),
            # ("检查电池状态", self.check_battery_status),  # 新增检查电池状态按钮
            ("空白", None)  # 添加一个空白按钮以平衡布局
        ]

        # 创建并添加按钮到左右两个面板
        for i, (text, command) in enumerate(all_buttons):
            btn = QPushButton(text)
            if command:
                btn.clicked.connect(command)
            else:
                btn.setEnabled(False)  # 禁用空白按钮
            btn.setFixedSize(150, 40)  # 设置固定大小

            if i < 11:  # 前11个按钮放在左侧，因为新增了一个按钮
                left_layout.addWidget(btn, i // 2, i % 2)
            else:  # 后9个按钮放在右侧
                right_layout.addWidget(btn, (i - 11) // 2, (i - 11) % 2)

        left_panel.setLayout(left_layout)
        right_panel.setLayout(right_layout)

        # 左侧面板滚动区域
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setWidget(left_panel)
        left_scroll.setFrameStyle(QFrame.Shape.NoFrame)
        content_layout.addWidget(left_scroll, 1)

        # 右侧面板滚动区域
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setWidget(right_panel)
        right_scroll.setFrameStyle(QFrame.Shape.NoFrame)
        content_layout.addWidget(right_scroll, 1)

        main_layout.addLayout(content_layout)

        # 输出区域
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        main_layout.addWidget(QLabel("输出:"))
        main_layout.addWidget(self.output)

        # 清空输出按钮
        clear_button = QPushButton("清空输出")
        clear_button.clicked.connect(self.output.clear)
        clear_button.setIcon(QIcon.fromTheme("edit-clear"))
        main_layout.addWidget(clear_button)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # 设置状态栏信息
        self.statusBar().showMessage('作者: 王克    微信: 2315313745')

        # 初始化时刷新设备列表
        self.refresh_devices()
        self.apply_styles()

    # 应用样式表
    def apply_styles(self):
        self.setStyleSheet(f"""
    QMainWindow {{
        background-color: {APPEARANCE['window']['background_color']};
    }}
    QLabel {{
        font-weight: bold;
        color: {APPEARANCE['labels']['text_color']};
        font-size: {APPEARANCE['labels']['font_size']}px;
    }}
    QComboBox {{
        border: 1px solid {APPEARANCE['combobox']['border_color']};
        border-radius: 3px;
        padding: 5px;
        background-color: {APPEARANCE['combobox']['background_color']};
        color: {APPEARANCE['combobox']['text_color']};
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 15px;
        border-left-width: 1px;
        border-left-color: {APPEARANCE['combobox']['border_color']};
        border-left-style: solid;
    }}
    QScrollArea {{
        border: none;
    }}
    QStatusBar {{
        background-color: #ecf0f1;
        color: #34495e;
    }}
    QPushButton {{
        color: {APPEARANCE['buttons']['text_color']};
        background-color: {APPEARANCE['buttons']['background_color']};
        border: 1px solid {APPEARANCE['buttons']['border_color']};
        padding: 5px;
        text-align: center;
        text-decoration: none;
        font-size: {APPEARANCE['buttons']['font_size']}px;
        border-radius: {APPEARANCE['buttons']['border_radius']}px;
        min-width: {APPEARANCE['buttons']['min_width']}px;
        max-width: {APPEARANCE['buttons']['max_width']}px;
    }}
    QPushButton:hover {{
        background-color: {APPEARANCE['buttons']['hover_color']};
    }}
    QPushButton:pressed {{
        background-color: {APPEARANCE['buttons']['pressed_color']};
    }}
    QPushButton:disabled {{
        background-color: {APPEARANCE['buttons']['disabled_color']};
        color: {APPEARANCE['buttons']['disabled_text_color']};
    }}
    QTextEdit {{
        border: 1px solid {APPEARANCE['output']['border_color']};
        border-radius: 3px;
        padding: 5px;
        background-color: {APPEARANCE['output']['background_color']};
        font-family: 'Courier New', monospace;
        font-size: {APPEARANCE['output']['font_size']}px;
        color: {APPEARANCE['output']['text_color']};
    }}
    """)

    # 刷新设备列表
    def refresh_devices(self):
        self.show_progress("正在刷新设备列表...")
        # 创建并启动获取设备列表的线程
        self.thread = GetDevicesCommand()
        self.thread.finished.connect(self.update_device_list)
        self.thread.start()

    # 更新设备列表下拉框
    def update_device_list(self, devices):
        current_device = self.device_combo.currentText()
        self.device_combo.clear()
        self.device_combo.addItems(devices)
        if devices:
            if current_device in devices:
                # 如果之前选中的设备仍在列表中，则保持选中状态
                index = self.device_combo.findText(current_device)
                self.device_combo.setCurrentIndex(index)
            self.output.append(f"已刷新设备列表: {', '.join(devices)}")
        else:
            self.output.append("未检测到设备")
        self.show_progress("设备列表已刷新")

    # 设备选择变更处理
    def on_device_selected(self, device_id):
        if device_id:
            self.output.append(f"已选择设备: {device_id}")

    # 执行ADB命令
    def run_adb_command(self, command):
        device_id = self.device_combo.currentText()
        if not device_id:
            self.output.append("错误: 未选择设备")
            return

        self.show_progress(f"正在执行: adb -s {device_id} {command}")
        # 创建并启动ADB命令执行线程
        self.thread = AdbCommand(command, device_id)
        self.thread.finished.connect(self.command_finished)
        self.thread.start()

    # 命令执行完成处理
    def command_finished(self, text):
        self.update_output(text)
        self.show_progress("准备就绪")

    # 更新输出区域
    def update_output(self, text):
        # 处理输出文本，提取有用信息
        processed_text = self.process_output(text)
        self.output.append(processed_text)
        self.logger.info(f"输出: {processed_text}")

    # 重启设备功能
    def reboot_device(self):
        def on_root_complete(output):
            if "adbd cannot run as root" in output.lower():
                self.output.append("错误: 无法获取Root权限")
                return
            self.output.append("已获取Root权限，正在重启设备...")
            # 延迟2秒后执行重启命令
            QTimer.singleShot(2000, lambda: self.run_adb_command("reboot"))

        # 先尝试获取root权限，然后重启
        self.run_adb_command("root")
        self.thread.finished.connect(on_root_complete)

    # 从设备拉取文件
    def pull_file(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("拉取文件")
        layout = QVBoxLayout()
        source = QLineEdit()
        destination = QLineEdit()
        layout.addWidget(QLabel("设备上的源路径:"))
        layout.addWidget(source)
        layout.addWidget(QLabel("PC上的目标路径:"))
        layout.addWidget(destination)
        buttons = QHBoxLayout()
        ok_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)
        dialog.setLayout(layout)
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.run_adb_command(f"pull {source.text()} {destination.text()}")

    # 推送文件到设备
    def push_file(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("推送文件")
        layout = QVBoxLayout()
        source = QLineEdit()
        destination = QLineEdit()
        layout.addWidget(QLabel("PC上的源路径:"))
        layout.addWidget(source)
        layout.addWidget(QLabel("设备上的目标路径:"))
        layout.addWidget(destination)
        buttons = QHBoxLayout()
        ok_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)
        dialog.setLayout(layout)
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.run_adb_command(f"push {source.text()} {destination.text()}")

    # 模拟点击操作
    def simulate_tap(self):
        x, ok1 = QInputDialog.getInt(self, "模拟点击", "X坐标:")
        if ok1:
            y, ok2 = QInputDialog.getInt(self, "模拟点击", "Y坐标:")
            if ok2:
                self.run_adb_command(f"shell input tap {x} {y}")

    # 模拟滑动操作
    def simulate_swipe(self):
        x1, ok1 = QInputDialog.getInt(self, "模拟滑动", "起始X坐标:")
        if ok1:
            y1, ok2 = QInputDialog.getInt(self, "模拟滑动", "起始Y坐标:")
            if ok2:
                x2, ok3 = QInputDialog.getInt(self, "模拟滑动", "结束X坐标:")
                if ok3:
                    y2, ok4 = QInputDialog.getInt(self, "模拟滑动", "结束Y坐标:")
                    if ok4:
                        duration, ok5 = QInputDialog.getInt(self, "模拟滑动", "持续时间(毫秒):")
                        if ok5:
                            self.run_adb_command(f"shell input swipe {x1} {y1} {x2} {y2} {duration}")

    # 模拟长按操作
    def simulate_long_press(self):
        x, ok1 = QInputDialog.getInt(self, "模拟长按", "X坐标:")
        if ok1:
            y, ok2 = QInputDialog.getInt(self, "模拟长按", "Y坐标:")
            if ok2:
                duration, ok3 = QInputDialog.getInt(self, "模拟长按", "持续时间(毫秒):")
                if ok3:
                    self.run_adb_command(f"shell input swipe {x} {y} {x} {y} {duration}")

    # 安装APK应用
    def install_app(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择APK文件", "", "APK Files (*.apk)")
        if file_path:
            self.run_adb_command(f"install {file_path}")

    # 卸载应用
    def uninstall_app(self):
        package_name, ok = QInputDialog.getText(self, "卸载应用", "输入包名:")
        if ok and package_name:
            self.run_adb_command(f"uninstall {package_name}")

    # 启动应用
    def start_app(self):
        package_activity, ok = QInputDialog.getText(self, "启动应用", "输入<包名>/<活动名>:")
        if ok and package_activity:
            self.run_adb_command(f"shell am start -n {package_activity}")

    # 截取屏幕
    def take_screenshot(self):
        save_path, _ = QFileDialog.getSaveFileName(self, "保存截图", "", "PNG Files (*.png)")
        if save_path:
            temp_file = "/sdcard/screenshot.png"
            self.show_progress("正在截取屏幕...")
            self.run_adb_command(f"shell screencap -p {temp_file}")

            def on_capture_complete(output):
                if "error" in output.lower():
                    self.output.append("错误: 截屏失败")
                    return
                self.show_progress("正在拉取截图...")
                self.run_adb_command(f"pull {temp_file} {save_path}")

                def on_pull_complete(output):
                    if "error" in output.lower():
                        self.output.append("错误: 保存截图失败")
                        return
                    self.run_adb_command(f"shell rm {temp_file}")
                    self.show_progress("截图保存成功")

                self.thread.finished.connect(on_pull_complete)

            self.thread.finished.connect(on_capture_complete)

    # 获取应用路径
    def get_app_path(self):
        package_name, ok = QInputDialog.getText(self, "获取应用路径", "输入包名:")
        if ok and package_name:
            self.run_adb_command(f"shell pm path {package_name}")

    # 模拟文本输入
    def input_text(self):
        text, ok = QInputDialog.getText(self, "输入文本", "输入要输入的文本:")
        if ok and text:
            self.run_adb_command(f"shell input text '{text}'")

    # 获取应用版本号
    def get_app_version(self):
        try:
            self.logger.info("开始获取应用版本号")
            device_id = self.get_selected_device()
            if not device_id:
                raise ValueError("未选择设备")

            # 获取当前焦点的应用包名
            result = subprocess.run(f"adb -s {device_id} shell dumpsys window | findstr mCurrentFocus",
                                    shell=True, check=True, capture_output=True, text=True)
            package_name = result.stdout.split()[-1].split("/")[0]

            if not package_name:
                raise ValueError("无法获取当前应用包名")

            # 获取应用版本号
            result = subprocess.run(f"adb -s {device_id} shell dumpsys package {package_name} | findstr versionName",
                                    shell=True, check=True, capture_output=True, text=True)
            version = result.stdout.strip().split("=")[-1]

            if not version:
                raise ValueError(f"无法获取应用 {package_name} 的版本号")

            self.output.append(f"应用 {package_name} 的版本号: {version}")
            self.logger.info(f"成功获取应用 {package_name} 的版本号: {version}")
        except subprocess.CalledProcessError as e:
            error_msg = f"执行ADB命令时出错: {e}"
            self.log_error(error_msg)
        except ValueError as e:
            self.log_error(str(e))
        except Exception as e:
            error_msg = f"获取应用版本号时发生未知错误: {str(e)}"
            self.log_error(error_msg)

    # 获取所有日志
    def pull_all_logs(self):
        save_path, _ = QFileDialog.getSaveFileName(self, "保存日志文件", "", "Text Files (*.txt)")
        if save_path:
            self.run_adb_command(f"logcat -d > {save_path}")

    # 获取APK包名
    def get_apk_package_name(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择APK文件", "", "APK Files (*.apk)")
        if file_path:
            self.run_adb_command(f"shell pm dump {file_path} | grep package")

    # 清除应用缓存
    def clear_app_cache(self):
        try:
            device_id = self.get_selected_device()
            if not device_id:
                raise ValueError("未选择设备")

            # 获取当前焦点的应用包名
            result = subprocess.run(f"adb -s {device_id} shell dumpsys window | grep mCurrentFocus",
                                    shell=True, check=True, capture_output=True, text=True)
            package_name = result.stdout.split()[-1].split("/")[0]

            if not package_name:
                raise ValueError("无法获取当前应用包名")

            # 清除应用缓存
            result = subprocess.run(f"adb -s {device_id} shell pm clear {package_name}",
                                    shell=True, check=True, capture_output=True, text=True)

            if "Success" in result.stdout:
                self.output.append(f"已成功清除应用 {package_name} 的缓存")
            else:
                raise ValueError(f"清除应用 {package_name} 的缓存失败")

        except subprocess.CalledProcessError as e:
            error_msg = f"执行ADB命令时出错: {e}"
            self.log_error(error_msg)
        except ValueError as e:
            self.log_error(str(e))
        except Exception as e:
            error_msg = f"清除应用缓存时发生未知错误: {str(e)}"
            self.log_error(error_msg)

    # 获取当前应用信息
    def get_current_app_info(self):
        self.run_adb_command("shell dumpsys window | grep mCurrentFocus")

    # 关闭当前应用
    def close_current_app(self):
        try:
            device_id = self.get_selected_device()
            if not device_id:
                raise ValueError("未选择设备")

            # 获取当前焦点的应用包名
            result = subprocess.run(f"adb -s {device_id} shell dumpsys window | grep mCurrentFocus",
                                    shell=True, check=True, capture_output=True, text=True)
            package_name = result.stdout.split()[-1].split("/")[0]

            if not package_name:
                raise ValueError("无法获取当前应用包名")

            # 强制停止应用
            self.run_adb_command(f"shell am force-stop {package_name}")
            self.output.append(f"已尝试关闭应用: {package_name}")
            self.logger.info(f"已尝试关闭应用: {package_name}")

        except subprocess.CalledProcessError as e:
            error_msg = f"执行ADB命令时出错: {e}"
            self.log_error(error_msg)
        except ValueError as e:
            self.log_error(str(e))
        except Exception as e:
            error_msg = f"关闭当前应用时发生未知错误: {str(e)}"
            self.log_error(error_msg)

    def get_selected_device(self):
        return self.device_combo.currentText()

    def setup_logging(self):
        log_file = f"adb_gui_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        logging.basicConfig(filename=log_file, level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        self.logger.info("应用启动")

    def log_error(self, message):
        self.logger.error(message)
        self.output.append(f"错误: {message}")

    def process_output(self, text):
        # 用于存储提取的有用信息
        useful_info = []

        # 查找包名
        package_matches = re.findall(r'package:([^\s]+)', text)
        for match in package_matches:
            useful_info.append(f"包名: {match}")

        # 查找活动名
        activity_matches = re.findall(r'([^\s/]+)/([^\s]+)', text)
        for match in activity_matches:
            useful_info.append(f"包名/活动名: {match[0]}/{match[1]}")

        # 查找版本号
        version_matches = re.findall(r'versionName=([^\s]+)', text)
        for match in version_matches:
            useful_info.append(f"版本号: {match}")

        # 如果找到了有用信息，将其添加到输出中
        if useful_info:
            text += "\n\n提取的有用信息:\n" + "\n".join(useful_info)

        return text

    # def check_battery_status(self):  # 新增检查电池状态方法
    #     self.run_adb_command("shell dumpsys battery")


# 程序入口
if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        window = AdbUiAutomatorGUI()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logging.error(f"应用崩溃: {str(e)}", exc_info=True)
        print(f"应用发生错误，请查看日志文件获取详细信息。错误: {str(e)}")

