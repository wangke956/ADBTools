import time
from PyQt5.QtWidgets import (QMainWindow, QFileDialog, QInputDialog, QMessageBox)
import sys
import io
import subprocess
import threading
import queue

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
else:
    print("sys.stdout does not have a 'buffer' attribute.")
# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if hasattr(sys.stdout, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
else:
    print("sys.stdout does not have a 'buffer' attribute.")
# sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
import uiautomator2 as u2
import os
from ADB_module_UI import Ui_MainWindow

class TextEditOutputStream(io.TextIOBase):  # 继承 io.TextIOBase 类

    def __init__(self, textBrowser):
        super().__init__()  # 调用父类构造函数
        self.textBrowser = textBrowser  # 绑定 textEdit
        self.buffer = io.StringIO()  # 创建一个缓存区
        self.clear_before_write = False  # 添加一个标志来控制是否清空内容
    def write(self, s):
        if self.clear_before_write:
            self.textBrowser.clear()  # 如果标志为 True，则清空 textEdit 的内容
            self.clear_before_write = False  # 重置标志
        self.buffer.write(s)
        self.textBrowser.append(s)
        return len(s)

    def flush(self):
        self.buffer.flush()

    def set_clear_before_write(self, clear):
        self.clear_before_write = clear

def adb_root(device_id):
    """
    传入下拉框选择的设备 ID, 尝试以 root 权限运行 ADB 命令
    :param device_id: 设备 ID
    """
    device_ids = ADB_Mainwindow.get_new_device_lst()
    if device_id in device_ids:
        try:
            result = subprocess.run(f"adb -s {device_id} root", shell=True, check=True, capture_output=True, text=True)
            if "adbd is already running as root" in result.stdout:
                return "ADB 已成功以 root 权限运行"
            elif 'adbd cannot run as root in production builds'in result.stdout:
                return "设备不支持 ADB root，无法以 root 权限运行。"
            # 如果root成功则没有任何返回值，如果失败则会抛出异常
            elif result.returncode == 0:
                return "ADB root 成功"


        except subprocess.CalledProcessError as e:
            if "not found" in str(e):
                return "ADB 命令未找到，请确保 ADB 工具已正确安装并添加到系统路径中。"
            elif "permission denied" in str(e):
                return "权限被拒绝，请确保你有足够的权限执行 ADB root 命令。"
            elif "adbd cannot run as root" in str(e):
                return "设备不支持 ADB root，无法以 root 权限运行。"
            else:
                return f"ADB root 失败: {e}"
    else:
        return "设备未连接！"

def adb_cpu_info(device_id):
    """
    传入下拉框选择的设备 ID, 获取设备 CPU 信息
    :param device_id: 设备 ID
    :return: CPU 信息
    """
    try:
        cpu_info = subprocess.run(f'adb -s {device_id} shell cat /proc/cpuinfo', capture_output=True, text=True)  #
        return cpu_info.stdout
    except subprocess.CalledProcessError as e:
        return f"获取 CPU 信息失败: {e}"

def simulate_swipe(start_x, start_y, end_x, end_y, duration, device_id):
    """
    模拟滑动
    :param start_x: 起始 x 坐标
    :param start_y: 起始 y 坐标
    :param end_x: 终点 x 坐标
    :param end_y: 终点 y 坐标
    :param duration: 滑动持续时间
    :param device_id: 设备 ID
    :return: 滑动成功提示
    """
    command = f"adb -s {device_id} shell input swipe {start_x} {start_y} {end_x} {end_y} {duration}"
    try:
        subprocess.run(command, shell=True, check=True)
        return "滑动成功！"
    except subprocess.CalledProcessError as e:
        return f"滑动失败: {e}"


def input_text_via_adb(text_to_input, device_id):
    """
    传入文本内容，模拟输入
    :param text_to_input: 要输入的文本内容
    :param device_id: 设备 ID
    :return: 输入成功提示
    """
    command = f"adb -s {device_id} shell input text '{text_to_input}'"
    try:
        res = subprocess.run(command,
                             shell=True,
                             check=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             text=True)
        return f"文本输入成功！{res.stdout.strip()}"  # 获取输出并转为字符串
    except subprocess.CalledProcessError as e:
        return f"文本输入失败: {e}"



def get_screenshot(file_path, device_id):
    """
    传入文件路径，获取设备截图并保存到本地
    :param file_path: 保存截图的本地路径
    :param device_id: 设备 ID
    :return: 截图保存成功提示
    """
    command = f"adb -s {device_id} shell screencap -p /sdcard/screenshot.png && adb -s {device_id} pull /sdcard/screenshot.png {file_path} && adb -s {device_id} shell rm /sdcard/screenshot.png"
    try:
        subprocess.run(command, shell=True, check=True)
        return f"截图已保存到 {file_path}"
    except subprocess.CalledProcessError as e:
        return f"截图失败: {e}"


def adb_uninstall(package_name, device_id):
    """
    传入包名，卸载应用
    :param package_name: 应用包名
    :param device_id: 设备 ID
    :return: 卸载成功提示
    """
    command = f"adb -s {device_id} uninstall {package_name}"
    try:
        subprocess.run(command, shell=True, check=True)
        return f"应用 {package_name} 已卸载"
    except subprocess.CalledProcessError as e:
        return f"卸载应用失败: {e}"


def adb_pull_file(file_path_on_device, local_path, device_id):
    """
    传入设备上的文件路径和本地保存路径，拉取文件
    :param file_path_on_device: 设备上的文件路径
    :param local_path: 本地保存路径
    :param device_id: 设备 ID
    :return: 成功提示
    """
    command = f"adb -s {device_id} pull {file_path_on_device} {local_path}"
    try:
        res = subprocess.run(command,
                             shell = True,
                             check = True,
                             stdout = subprocess.PIPE,
                             stderr = subprocess.PIPE,
                             text = True)
        string = res.stdout.strip()
        return ["文件拉取成功！", string]
    except subprocess.CalledProcessError as e:
        return f"文件拉取失败: {e}"


def simulate_long_press(x, y, duration, device_id):
    """
    模拟长按
    :param x: 按压点的 x 坐标
    :param y: 按压点的 y 坐标
    :param duration: 按压持续时间
    :param device_id: 设备 ID
    :return: 长按模拟成功提示
    """
    command = f"adb -s {device_id} shell input swipe {x} {y} {x} {y} {duration}"
    try:
        subprocess.run(command, shell=True, check=True)
        return "长按模拟成功！"
    except subprocess.CalledProcessError as e:
        return f"长按模拟失败: {e}"


def adb_install(package_path, device_id):
    """
    传入安装包路径，安装应用
    :param package_path: 安装包路径
    :param device_id: 设备 ID
    :return: 安装成功提示
    """
    devices_id_lst = ADB_Mainwindow.get_new_device_lst()
    # 传入下拉框选择的设备 ID：device_id
    if device_id in devices_id_lst:
        command = f"adb -s {device_id} install {package_path}"
        try:
            res = subprocess.run(command,
                                 shell=True,
                                 check=True,
                                 stdout=subprocess.PIPE,  # 捕获标准输出
                                 stderr=subprocess.PIPE,   # 捕获标准错误
                                 text=True)                # 返回字符串而不是字节
            time.sleep(8)
            return f"应用安装成功！{res.stdout.strip()}"  # 获取输出并返回
        except subprocess.CalledProcessError as e:
            return f"应用安装失败: {e.stderr.strip()}"  # 捕获并返回标准错误信息
    else:
        return "设备未连接！"


def clear_app_cache(device, package_name):
    """
    清除应用缓存
    :param device: 设备对象
    :param package_name: 应用包名
    :return: 清除成功提示
    """
    if device is not None:
        try:
            device.app_clear(package_name)
            return f"应用 {package_name} 的缓存已清除"
        except Exception as e:
            return f"清除应用缓存失败: {e}"
    else:
        return "设备未连接！"


def pull_log_without_clear(file_path, device_id):
    """
    拉取日志（不清除）
    :param file_path: 日志保存路径
    :param device_id: 设备 ID
    :return: 日志拉取成功提示
    """
    command = f'cmd /k "adb -s {device_id} shell logcat > {file_path}"'
    process = subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE)
    while True:
        if process.poll() is not None:
            break


def pull_log_with_clear(file_path, device_id):
    """
    拉取日志（清除）
    :param file_path: 日志保存路径
    :param device_id: 设备 ID
    :return: 日志拉取成功提示
    """
    subprocess.run(f'adb -s {device_id} logcat -c', shell=True)
    command = f'cmd /k "adb -s {device_id} shell logcat > {file_path}"'
    process = subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE)
    while True:
        if process.poll() is not None:
            break


def simulate_click(x, y, device_id):
    """
    模拟点击
    :param x: 点击点的 x 坐标
    :param y: 点击点的 y 坐标
    :param device_id: 设备 ID
    :return:
    """
    command = f"adb -s {device_id} shell input tap {x} {y}"
    try:
        subprocess.run(command, shell=True, check=True)
        return "点击成功！"
    except subprocess.CalledProcessError as e:
        return f"点击失败: {e}"


def adb_push_file(local_file_path, target_path_on_device, device_id):
    """
    传入本地文件路径和设备上的目标路径，推送文件
    :param local_file_path: 本地文件路径
    :param target_path_on_device: 设备上的目标路径
    :param device_id: 设备 ID
    :return: 成功提示
    """
    command = f"adb -s {device_id} push {local_file_path} {target_path_on_device}"
    try:
        subprocess.run(command, shell=True, check=True)
        return "文件推送成功！"
    except subprocess.CalledProcessError as e:
        return f"文件推送失败: {e}"


def aapt_get_packagen_name(apk_path):
    """
    传入apk路径，获取包名
    :param apk_path: apk路径
    :return: 包名
    """
    command = f"aapt dump badging {apk_path} | findstr name"
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        package_name = result.stdout.strip().split('\'')[1]
        return package_name
    except subprocess.CalledProcessError as e:
        return f"获取包名失败: {e}"


# noinspection PyShadowingNames
class ADB_Mainwindow(QMainWindow, Ui_MainWindow):
    # device_check_timer = QTimer()  # 设备连接状态检查定时器
    def __init__(self, parent=None):
        super(ADB_Mainwindow, self).__init__(parent)
        self.setupUi(self)
        """print重定向到textEdit、textBrowser"""
        # self.device = u2.connect(device_id)

        self.text_edit_output_stream = TextEditOutputStream(self.textBrowser)  # 创建一个 TextEditOutputStream 对象
        sys.stdout = self.text_edit_output_stream  # 绑定到 sys.stdout
        sys.stderr = self.text_edit_output_stream  # 绑定到 sys.stderr
        self.refresh_devices()  # 刷新设备列表
        self.adb_cpu_info.clicked.connect(self.adb_cpu_info_wrapper)  # 显示CPU信息
        self.simulate_swipe.clicked.connect(self.show_simulate_swipe_dialog)  # 模拟滑动
        self.view_apk_path.clicked.connect(self.view_apk_path_wrapper)  # 显示应用安装路径
        self.input_text_via_adb.clicked.connect(self.show_input_text_dialog)  # 输入文本
        self.get_screenshot.clicked.connect(self.show_screenshot_dialog)  # 截图
        self.force_stop_app.clicked.connect(self.show_force_stop_app_dialog)  # 强制停止应用
        self.adb_uninstall.clicked.connect(self.show_uninstall_dialog)  # 卸载应用
        self.adb_pull_file.clicked.connect(self.show_pull_file_dialog)  # 拉取文件
        self.simulate_long_press.clicked.connect(self.show_simulate_long_press_dialog)  # 模拟长按
        self.adb_install.clicked.connect(self.show_install_file_dialog)  # 安装应用
        self.clear_app_cache.clicked.connect(self.show_clear_app_cache_dialog)  # 清除应用缓存
        self.app_package_and_activity.clicked.connect(lambda: self.get_foreground_package(is_direct_call = True))
        self.pull_hulog.clicked.connect(self.show_pull_hulog_dialog)  # 拉取hulog
        self.pull_log_without_clear.clicked.connect(self.show_pull_log_without_clear_dialog)  # 拉取日志（不清除）
        self.pull_log_with_clear.clicked.connect(self.show_pull_log_with_clear_dialog)  # 拉取日志（清除）
        self.simulate_click.clicked.connect(self.show_simulate_click_dialog)  # 模拟点击
        self.adb_push_file.clicked.connect(self.show_push_file_dialog)  # 推送文件
        self.close.clicked.connect(self.stop_program)  # 关闭程序
        self.adbbutton.clicked.connect(ADB_Mainwindow.run_cmd)  # 执行 adb 命令
        self.button_reboot.clicked.connect(self.reboot_device)  # 重启设备
        self.RefreshButton.clicked.connect(self.refresh_devices)  # 刷新设备列表
        self.adb_root.clicked.connect(self.adb_root_wrapper)  # 以 root 权限运行 ADB
        self.start_app.clicked.connect(self.start_app_action)  # 启动应用
        self.get_running_app_info_button.clicked.connect(self.get_running_app_info)  # 获取当前运行的应用信息
        self.aapt_getpackagename_button.clicked.connect(self.aapt_getpackage_name_dilog)  # 获取apk包名
        self.textBrowser.textChanged.connect(self.scroll_to_bottom)  # 自动滚动到底部
        # self.check_device_status()

    # def check_device_status(self):
    #     def inner():
    #         while True:
    #             """检查设备连接状态，如果没有设备连接则输出提示信息"""
    #             result = subprocess.run("adb devices", shell = True, capture_output = True, text = True)
    #             devices = result.stdout.strip().split('\n')[1:]  # 获取设备列表
    #             device_ids = [line.split('\t')[0] for line in devices if line]  # 提取设备ID
    #
    #             if not device_ids:
    #                 self.textBrowser.append("未连接设备！")  # 输出未连接设备的提示信息
    #             else:
    #                 break
    #             time.sleep(0.5)
    #
    #     threading.Thread(target=inner).start()  # 异步执行


    def scroll_to_bottom(self):
        scrollbar = self.textBrowser.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def show_pull_hulog_dialog(self):
        def run_commands_and_update(device_id, file_path):
            if device_id:
                command = f'adb -s {device_id} root && adb -s {device_id} shell "setprop bmi.service.adb.root 1" && adb -s {device_id} pull log {file_path}'
                process = subprocess.Popen(command, shell = True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
                for line in iter(process.stdout.readline, b''):  # 逐行读取输出
                    if line:
                        self.textBrowser.append(line.decode())
                return_code = process.wait()
                if return_code != 0:
                    self.textBrowser.append("日志文件拉取失败.")
                else:
                    self.textBrowser.append(f"日志文件已保存到 {file_path}")
            else:
                self.textBrowser.append("设备未连接！")

        device_ids = self.get_new_device_lst()
        device_id = self.get_selected_device()
        if device_id in device_ids:
            file_path = QFileDialog.getExistingDirectory(self, "选择保存路径", os.getcwd())
            if file_path:
                threading.Thread(target = run_commands_and_update, args = (device_id, file_path)).start()
            else:
                self.textBrowser.append("已取消！")
        else:
            self.textBrowser.append("设备未连接！")


    def start_app_action(self):
        """
        启动应用
        """
        def inner():
            device_ids = self.get_new_device_lst()
            device_id = self.get_selected_device()
            device = u2.connect(device_id)
            if device_id in device_ids:
                try:
                    # 弹出对话框，请用户输入应用包名和活动名，格式为：包名: com.android.settings, 活动名:.MainSettings
                    input_text, ok = QInputDialog.getText(self, '输入应用信息',
                                                          '请输入应用包名和活动名，格式为：包名: com.xxx.xxx, 活动名:.xxx')
                    if ok and input_text:
                        # 解析输入的文本，获取包名和活动名
                        parts = input_text.split(', ')
                        package_name = parts[0].split('包名: ')[1]
                        activity_name = parts[1].split('活动名: ')[1]
                        if len(parts) >= 2:
                            device.app_start(package_name, activity_name)
                            self.textBrowser.append(f"应用 {package_name} 已启动")
                        else:
                            self.textBrowser.append("输入的格式不正确，请按照格式输入：包名: com.xxx.xxx, 活动名:.xxx")
                    else:
                        self.textBrowser.append("用户取消输入或输入为空")
                except Exception as e:
                    self.textBrowser.append(f"启动应用失败: {e}")
            else:
                self.textBrowser.append("未连接设备！")
        threading.Thread(target=inner).start()  # 异步执行


    def get_running_app_info(self):
        """
        获取当前前景应用的版本号
        """
        def inner():
            device_id = self.get_selected_device()  # 获取当前选定的设备ID
            devices_id_lst = self.get_new_device_lst()
            package_name = self.get_foreground_package(is_direct_call=False)  # 传入 device_id 获取包名
            if device_id in devices_id_lst:
                if package_name:
                    try:
                        # 连接到设备
                        d = u2.connect(device_id)  # 使用获取的设备ID
                        # 获取应用信息
                        app_info = d.app_info(package_name)
                        if app_info:
                            version_name = app_info.get('versionName', '未知版本')
                            self.textBrowser.append(f"应用 {package_name} 版本号: {version_name}")
                        else:
                            self.textBrowser.append("无法获取应用信息")
                    except Exception as e:
                        self.textBrowser.append(f"获取应用信息失败: {e}")
                else:
                    self.textBrowser.append("未获取到当前前景应用的包名")
            else:
                pass
        threading.Thread(target=inner).start()


    def get_selected_device(self):
        return self.ComboxButton.currentText()  # 返回的类型为str

    def adb_cpu_info_wrapper(self):
        """
        显示CPU信息
        """
        def inner():
            device_id = self.get_selected_device()
            devices_id_lst = self.get_new_device_lst()
            if device_id in devices_id_lst:
                res = adb_cpu_info(device_id)  # 传入下拉框选择的设备ID, 并返回cpu_info.stdout
                self.textBrowser.append(res)
            else:
                self.textBrowser.append("设备已断开！")
        threading.Thread(target=inner).start()  # 异步执行


    def view_apk_path_wrapper(self, package_name):
        """
        显示应用安装路径
        """
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            if package_name:
                cmd = f'adb -s {device_id} shell pm path {package_name}'
                result = subprocess.run(cmd, shell = True, check = True, capture_output = True, text = True)
                apk_path = result.stdout.strip()
                parts = apk_path.split(":")[1]
                return parts  # 返回安装路径
            else:
                # 弹窗获取用户输入包名,
                package_name, ok = QInputDialog.getText(self, "输入应用包名", "请输入要查看安装路径的应用包名：")
                if not ok:
                    # 点击取消，输出提示信息
                    self.textBrowser.append("已取消！")
                else:
                    # 点击确认，执行 adb shell pm path 命令获取安装路径
                    cmd = f'adb -s {device_id} shell pm path {package_name}'
                    # cmd = f'adb -s {device_id} shell pm path {package_name}'
                    result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
                    # 输出安装目录
                    apk_path = result.stdout.strip()
                    parts = apk_path.split(":")[1]
                    self.textBrowser.append(f"应用安装路径: {parts}")
                    return parts  # 返回安装路径
        else:
            self.textBrowser.append("设备已断开！")


    def refresh_devices(self):
        """
        刷新设备列表
        """
        def inner():
            try:
                # 执行 adb devices 命令
                result = subprocess.run("adb devices", shell=True, check=True, capture_output=True, text=True)
                devices = result.stdout.strip().split('\n')[1:]  # 获取设备列表
                device_ids = [line.split('\t')[0] for line in devices if line]  # 提取设备ID

                # 清空 ComboxButton 并添加新的设备ID
                self.ComboxButton.clear()
                for device_id in device_ids:
                    self.ComboxButton.addItem(device_id)

                # 将设备ID列表转换为字符串并更新到textBrowser
                device_ids_str = ", ".join(device_ids)
                if device_ids_str:
                    self.textBrowser.append(f"设备列表已刷新：\n{device_ids_str}")
                    return device_ids  # 返回设备ID列表
                else:
                    self.textBrowser.append(f"未连接设备！")
                    return device_ids  # 返回设备ID列表
            except subprocess.CalledProcessError as e:
                self.textBrowser.append(f"刷新设备列表失败: {e}")
                return []  # 返回空列表表示刷新失败
        threading.Thread(target=inner).start()  # 异步执行

    def adb_root_wrapper(self):
        """
        以 root 权限运行 ADB
        """
        def inner():
            device_id = self.get_selected_device()
            if device_id:
                res = adb_root(device_id)  # 传入下拉框选择的设备ID
                self.textBrowser.append(res)
            else:
                self.textBrowser.append("未连接设备！")
        threading.Thread(target=inner).start()  # 异步执行

    def reboot_device(self):
        """
        重启设备
        """
        dig = QMessageBox.question(self, "重启设备", "是否要重启设备？", QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        if dig == QMessageBox.Yes:
            def inner():
                try:
                    device_id = self.get_selected_device()
                    device_ids = self.get_new_device_lst()

                    # 重新检查设备的连接状态
                    if device_id not in device_ids:
                        self.textBrowser.append("设备已断开！")
                        return  # 直接返回，避免后续执行无效的命令

                    # 执行 adb reboot 命令
                    result = subprocess.run(
                        f"start /b adb -s {device_id} reboot",
                        shell = True,  # 执行命令
                        check = True,  # 检查命令是否成功
                        stdout = subprocess.PIPE,  # 捕获输出
                        stderr = subprocess.PIPE  # 捕获错误
                    )

                    # 不要用print，会导致UI卡死，用textBrowser.append
                    if "not found" not in str(result.stdout.decode('utf-8')):
                        self.textBrowser.append(f"设备 {device_id} 已重启！")
                    elif "not found" in result.stdout.decode('utf-8'):
                        self.adb_root_wrapper()
                        self.reboot_device()
                except Exception as e:
                    self.textBrowser.append(f"重启设备失败: {e}")

            threading.Thread(target = inner).start()  # 异步执行

    def show_screenshot_dialog(self):
        """
        截图
        """
        def inner():
            device_id = self.get_selected_device()
            devices_id_lst = self.get_new_device_lst()
            if device_id in devices_id_lst:
                file_path, _ = QFileDialog.getSaveFileName(self, "保存截图", "", "PNG Files (*.png);;All Files (*)")
                if file_path:
                    # 传入下拉框选择的设备ID
                    res = get_screenshot(file_path, device_id)
                    self.textBrowser.append(res)
            else:
                self.textBrowser.append("未连接设备！")
        threading.Thread(target=inner).start()  # 异步执行


    def show_uninstall_dialog(self):
        """
        卸载应用
        """
        def inner():
            device_id = self.get_selected_device()
            devices_id_lst = self.get_new_device_lst()
            if device_id in devices_id_lst:
                package_name, ok = QInputDialog.getText(self, "输入应用包名", "请输入要卸载的应用包名：")
                if ok and package_name:
                    res = adb_uninstall(package_name, device_id)
                    self.textBrowser.append(res)
            else:
                self.textBrowser.append("未连接设备！")
        threading.Thread(target=inner).start()  # 异步执行

    def show_pull_file_dialog(self):
        """
        拉取文件
        """
        def inner():
            device_id = self.get_selected_device()
            devices_id_lst = self.get_new_device_lst()
            if device_id in devices_id_lst:
                file_path_on_device, ok = QInputDialog.getText(self, "输入设备文件路径", "请输入车机上的文件路径:")
                if ok and file_path_on_device:
                    local_path, _ = QFileDialog.getSaveFileName(self, "保存文件", "", "All Files (*)")
                    if local_path:
                        res = adb_pull_file(file_path_on_device, local_path, device_id)
                        self.textBrowser.append(" ".join(res))  # 使用 " | " 作为分隔符
            else:
                self.textBrowser.append("未连接设备！")
        threading.Thread(target=inner).start()  # 异步执行


    def show_install_file_dialog(self):
        """
        安装应用
        """
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            package_path, _ = QFileDialog.getOpenFileName(self, "选择应用安装包", "",
                                                          "APK Files (*.apk);;All Files (*)")
            if package_path:
                def inner():
                    # 传入下拉框选择的设备ID
                    res = adb_install(package_path, device_id)
                    self.textBrowser.append(res)
                threading.Thread(target=inner).start()  # 异步执行
            self.textBrowser.append("即将开始安装应用，请耐心等待...")
        elif not device_id:
            self.textBrowser.append("未连接设备！")

    def show_pull_log_without_clear_dialog(self):
        """
        拉取 log 但不清空
        """
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            self.textBrowser.append("即将开始拉取 log，如需停止，请手动关闭此窗口。")
            file_path, _ = QFileDialog.getSaveFileName(self, "保存 log", "", "txt Files (*.txt);;All Files (*)")
            if file_path:
                pull_log_without_clear(file_path, device_id)
        else:
            self.textBrowser.append("未连接设备！")

    def show_pull_log_with_clear_dialog(self):
        """
        拉取 log 并清空
        """
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            file_path, _ = QFileDialog.getSaveFileName(self, "保存 log", "", "txt Files (*.txt);;All Files (*)")
            if file_path:
                pull_log_with_clear(file_path, device_id)
        else:
            self.textBrowser.append("未连接设备！")

    def show_push_file_dialog(self):
        """
        推送文件
        """
        def inner():
            device_id = self.get_selected_device()
            devices_id_lst = self.get_new_device_lst()
            if device_id in devices_id_lst:
                local_file_path, _ = QFileDialog.getOpenFileName(self, "选择本地文件", "", "All Files (*)")
                if local_file_path:
                    target_path_on_device, ok = QInputDialog.getText(self, "输入设备文件路径",
                                                                     "请输入车机上的目标路径:")
                    if ok and target_path_on_device:
                        # 传入下拉框选择的设备ID
                        res = adb_push_file(local_file_path, target_path_on_device, device_id)
                        self.textBrowser.append(res)
            else:
                self.textBrowser.append("未连接设备！")
        threading.Thread(target=inner).start()  # 异步执行

    def show_simulate_click_dialog(self):  # 模拟点击
        """
        弹出输入框让用户输入 X 坐标和 Y 坐标，模拟点击
        """
        def inner():
            device_id = self.get_selected_device()
            device_id_lst = self.get_new_device_lst()
            if device_id in device_id_lst:
                x, ok = QInputDialog.getInt(self, "输入 X 坐标", "请输入点击的 X 坐标:")
                if ok:
                    y, ok = QInputDialog.getInt(self, "输入 Y 坐标", "请输入点击的 Y 坐标:")
                    if ok:
                        res = simulate_click(x, y, device_id)
                        self.textBrowser.append(res)
            else:
                self.textBrowser.append("未连接设备！")
        threading.Thread(target=inner).start()  # 异步执行

    def show_simulate_swipe_dialog(self):  # 模拟滑动
        """
        弹出输入框让用户输入起始坐标和终止坐标，模拟滑动
        """
        def inner():
            try:
                device_id = self.get_selected_device()
                devices_id_lst = self.get_new_device_lst()
                if device_id in devices_id_lst:
                    # 弹出一个输入框让用户一次性输入所有坐标共四个整数
                    input_text, ok = QInputDialog.getText(self, "输入坐标", "请输入滑动的起始坐标和终止坐标，格式为：x1,y1,x2,y2:")
                    if ok and input_text:
                        parts = input_text.split(',')
                        if len(parts) == 4:
                            x1, y1, x2, y2 = [int(part) for part in parts]
                            res = simulate_swipe(x1, y1, x2, y2, 500, device_id)  # 传入滑动起始坐标和终止坐标，滑动时间为500ms，并传入设备ID，并返回结果
                            self.textBrowser.append(res)
                else:
                    self.textBrowser.append("未连接设备！")
            except Exception as e:
                self.textBrowser.append(f"模拟滑动失败: {e}")
        threading.Thread(target=inner).start()  # 异步执行

    def show_simulate_long_press_dialog(self):
        """
        弹出输入框让用户输入坐标和长按时间，模拟长按
        """
        def inner():
            device_id = self.get_selected_device()
            devices_id_lst = self.get_new_device_lst()
            if device_id in devices_id_lst:
                # 弹出输入框一次性坐标和长按时间
                input_text, ok = QInputDialog.getText(self, "输入坐标和长按时间", "请输入长按的坐标和长按时间，格式为：x,y,时间:")
                if ok and input_text:
                    parts = input_text.split(',')
                    if len(parts) == 3:
                        x, y, duration = [int(part) for part in parts]
                        res = simulate_long_press(x, y, duration, device_id)
                        self.textBrowser.append(res)
            else:
                self.textBrowser.append("未连接设备！")
        threading.Thread(target=inner).start()  # 异步执行

    def show_input_text_dialog(self):
        """
        弹出输入框让用户输入文本，通过 ADB 输入到设备上
        """
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            text_to_input, ok = QInputDialog.getText(self, "输入文本", "请输入要通过 ADB 输入的文本:")
            if ok and text_to_input:
                lst = input_text_via_adb(text_to_input, device_id)  # 传入要输入的文本和设备ID，并返回结果列表
                self.textBrowser.append(lst)
        else:
            self.textBrowser.append("未连接设备！")

    def show_force_stop_app_dialog(self):
        """
        弹出输入框让用户输入应用包名，强制停止应用
        """
        def inner():
            try:
                device_id = self.get_selected_device()
                devices_id_lst = self.get_new_device_lst()
                if device_id in devices_id_lst:
                    package_name = self.get_foreground_package(is_direct_call=False)
                    # self.textBrowser.append(f"当前前台应用包名: {package_name}")
                    if package_name:
                        adb_command = f"adb -s {device_id} shell am force-stop {package_name}"
                        try:
                            subprocess.run(adb_command, shell=True, check=True)
                            self.textBrowser.append(f"成功强制停止 {package_name} 应用在设备 {device_id} 上")
                        except subprocess.CalledProcessError as e:
                            self.textBrowser.append(f"强制停止 {package_name} 应用在设备 {device_id} 上失败: {e}")
                else:
                    self.textBrowser.append("设备已断开！")
            except Exception as e:
                self.textBrowser.append(f"强制停止应用失败: {e}")
        threading.Thread(target=inner).start()  # 异步执行

    def show_clear_app_cache_dialog(self):
        """
        清除应用缓存
        """
        def inner():
            device_id = self.get_selected_device()  # 获取用户选择的设备ID
            if device_id:
                package_name = self.get_foreground_package()
                if package_name:
                    res = clear_app_cache(u2.connect(device_id), package_name)  # 清除应用缓存
                    self.textBrowser.append(res)
                else:
                    self.textBrowser.append("未找到正在运行的应用包名")
            else:
                self.textBrowser.append("未选择设备")
        threading.Thread(target=inner).start()  # 异步执行

    def get_foreground_package(self, is_direct_call = True):
        """
        获取当前正在运行的应用包名
        """
        result_queue = queue.Queue()  # 创建一个队列用于存储结果
        def inner():
            device_id = self.get_selected_device()
            devices_id_lst = self.get_new_device_lst()
            if device_id in devices_id_lst:  # 检查选择的设备是否在设备列表中
                try:
                    device = u2.connect(device_id)
                    if device:
                        current_app = device.app_current()  # 获取当前正在运行的应用
                        if current_app:
                            package_name = current_app['package']
                            activity_name = current_app['activity']
                            if is_direct_call:  # 如果是直接调用
                                self.textBrowser.append(f"包名: {package_name}, 活动名: {activity_name}")
                            result_queue.put(package_name)  # 将结果放入队列
                        else:
                            self.textBrowser.append("未找到正在运行的应用包名")
                            result_queue.put(None)  # 将结果放入队列，表示未找到
                    else:
                        self.textBrowser.append("设备连接失败")
                        result_queue.put(None)  # 将结果放入队列，表示连接失败
                except Exception as e:
                    self.textBrowser.append(f"获取前台正在运行的应用包名失败: {e}")
                    result_queue.put(None)  # 将结果放入队列，表示获取失败
            else:
                self.textBrowser.append("设备已断开！")
                result_queue.put(None)  # 将结果放入队列，表示设备断开

        threading.Thread(target = inner).start()  # 异步执行
        return result_queue.get()  # 在主线程中获取队列中的结果


    def aapt_getpackage_name_dilog(self):
        """
        弹出文件选择框让用户选择apk文件，获取到的apk_path传入到aapt_get_package_name()函数中获取包名
        """

        # 弹窗获取apk文件
        apk_path, _ = QFileDialog.getOpenFileName(self,
                                                  "选择APK文件",
                                                  "",
                                                  "apk Files (*.apk)",
                                                  options=QFileDialog.DontUseNativeDialog
                                                  )
        if apk_path:
            package_name = aapt_get_packagen_name(apk_path)
            # 从apk_path中提取出文件名
            apk_name = os.path.basename(apk_path)
            if package_name:
                self.textBrowser.append(f"{apk_name}文件的包名: {package_name}")

                # 弹框询问用户是否查看该应用的安装位置，也就是是否执行adb pm path 命令
                if QMessageBox.question(self, "查看安装位置", f"是否查看{apk_name}文件的安装位置?", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes) == QMessageBox.Yes:
                    try:

                        apk_device_path = self.view_apk_path_wrapper(package_name)
                        self.textBrowser.append(f"{apk_name}文件的安装位置: {apk_device_path}")
                        # 弹框询问用户是否执行adb push 该apk文件到刚获得的安装位置
                        if QMessageBox.question(self, "推送到设备", f"是否推送{apk_name}文件到设备的{apk_device_path}位置?", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes) == QMessageBox.Yes:
                            try:
                                subprocess.run(f"adb push {apk_path} {apk_device_path}", shell=True, check=True)
                                self.textBrowser.append(f"成功推送{apk_name}文件到设备的{apk_device_path}位置")

                                # 弹框询问用户是否重启设备，重启设备或不重启
                                if QMessageBox.question(self, "重启设备", "是否重启设备?", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes) == QMessageBox.Yes:
                                    try:
                                        # 调用reboot方法
                                        self.reboot_device()
                                        self.textBrowser.append("设备重启成功")
                                    except Exception as e:
                                        self.textBrowser.append(f"重启设备失败: {e}")
                            except subprocess.CalledProcessError as e:
                                self.textBrowser.append(f"推送{apk_name}文件到设备的{apk_device_path}位置失败: {e}")
                    except subprocess.CalledProcessError as e:
                        self.textBrowser.append(f"获取{apk_name}文件的安装位置失败: {e}")
            else:
                self.textBrowser.append(f"无法获取{apk_name}文件的包名")
        else:
            self.textBrowser.append("未选择apk文件!")


    @staticmethod
    def stop_program():
        sys.exit()


    @staticmethod
    def get_new_device_lst():  # 静态方法，返回设备ID列表
        result = subprocess.run("adb devices", shell=True, check=True, capture_output=True,
                                text=True)  # 执行 adb devices 命令
        devices = result.stdout.strip().split('\n')[1:]  # 获取设备列表
        device_ids = [line.split('\t')[0] for line in devices if line]  # 提取设备ID
        return device_ids


    @staticmethod
    def run_cmd():
        user_directory = os.path.expanduser("~")
        subprocess.Popen(["start", "cmd", "/k", "cd /d " + user_directory], shell = True)

