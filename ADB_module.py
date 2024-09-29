import time

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (QMainWindow, QFileDialog, QInputDialog)
import sys
import io
import subprocess

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

    def __init__(self, text_edit):
        super().__init__()  # 调用父类构造函数
        self.text_edit = text_edit  # 绑定 textEdit
        self.buffer = io.StringIO()  # 创建一个缓存区
        self.clear_before_write = False  # 添加一个标志来控制是否清空内容
    def write(self, s):
        if self.clear_before_write:
            self.text_edit.clear()  # 如果标志为 True，则清空 textEdit 的内容
            self.clear_before_write = False  # 重置标志
        self.buffer.write(s)
        self.text_edit.append(s)
        return len(s)

    def flush(self):
        self.buffer.flush()

    def set_clear_before_write(self, clear):
        self.clear_before_write = clear


def connect_device():
    try:
        result = subprocess.run("adb devices", shell=True, check=True, capture_output=True, text=True)
        devices = result.stdout.strip().split('\n')[1:]
        if not devices:
            return None
        return devices[0].split('\t')[0]
    except subprocess.CalledProcessError as e:
        print(f"设备连接失败: {e}")
        return None


def adb_root(device_id):
    device_ids = ADB_Mainwindow.refresh_devices(self=ADB_Mainwindow())
    if device_id in device_ids:
        try:
            result = subprocess.run(f"adb -s {device_id} root", shell=True, check=True, capture_output=True, text=True)
            # print(result.stdout)
            if "adbd is already running as root" in result.stdout:
                # print("ADB 已成功以 root 权限运行")
                return "ADB 已成功以 root 权限运行"
            elif 'adbd cannot run as root in production builds'in result.stdout:
                # print("设备不支持 ADB root，无法以 root 权限运行。")
                return "设备不支持 ADB root，无法以 root 权限运行。"
            # 如果root成功则没有任何返回值，如果失败则会抛出异常
            elif result.returncode == 0:
                return "ADB root 成功"


        except subprocess.CalledProcessError as e:
            if "not found" in str(e):
                return "ADB 命令未找到，请确保 ADB 工具已正确安装并添加到系统路径中。"
                # print("ADB 命令未找到，请确保 ADB 工具已正确安装并添加到系统路径中。")
            elif "permission denied" in str(e):
                return "权限被拒绝，请确保你有足够的权限执行 ADB root 命令。"
                # print("权限被拒绝，请确保你有足够的权限执行 ADB root 命令。")
            elif "adbd cannot run as root" in str(e):
                return "设备不支持 ADB root，无法以 root 权限运行。"
                # print("设备不支持 ADB root，无法以 root 权限运行。")
            else:
                print(f"ADB root 失败: {e}")
    else:
        # print("设备未连接！")
        return "设备未连接！"

def adb_cpu_info(device_id):
    try:
        cpu_info = subprocess.run(f'adb -s {device_id} shell cat /proc/cpuinfo', capture_output=True, text=True)
        print(cpu_info.stdout)
    except subprocess.CalledProcessError as e:
        print(f"获取 CPU 信息失败: {e}")


def simulate_swipe(start_x, start_y, end_x, end_y, duration, device_id):
    command = f"adb -s {device_id} shell input swipe {start_x} {start_y} {end_x} {end_y} {duration}"
    try:
        subprocess.run(command, shell=True, check=True)
        print("滑动成功！")
    except subprocess.CalledProcessError as e:
        print(f"滑动失败: {e}")


def input_text_via_adb(text_to_input, device_id):
    command = f"adb -s {device_id} shell input text '{text_to_input}'"
    try:
        subprocess.run(command, shell=True, check=True)
        print("文本输入成功！")
    except subprocess.CalledProcessError as e:
        print(f"文本输入失败: {e}")


def get_screenshot(file_path, device_id):
    command = f"adb -s {device_id} shell screencap -p /sdcard/screenshot.png && adb -s {device_id} pull /sdcard/screenshot.png {file_path} && adb -s {device_id} shell rm /sdcard/screenshot.png"
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"截图已保存到 {file_path}")
    except subprocess.CalledProcessError as e:
        print(f"截图失败: {e}")


def adb_uninstall(package_name, device_id):
    command = f"adb -s {device_id} uninstall {package_name}"
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"应用 {package_name} 已卸载")
    except subprocess.CalledProcessError as e:
        print(f"卸载应用失败: {e}")


def adb_pull_file(file_path_on_device, local_path, device_id):
    command = f"adb -s {device_id} pull {file_path_on_device} {local_path}"
    try:
        subprocess.run(command, shell=True, check=True)
        print("文件拉取成功！")
    except subprocess.CalledProcessError as e:
        print(f"文件拉取失败: {e}")


def simulate_long_press(x, y, duration, device_id):
    command = f"adb -s {device_id} shell input swipe {x} {y} {x} {y} {duration}"
    try:
        subprocess.run(command, shell=True, check=True)
        print("长按模拟成功！")
    except subprocess.CalledProcessError as e:
        print(f"长按模拟失败: {e}")


def adb_install(package_path, device_id):
    devices_id_lst = ADB_Mainwindow.refresh_devices(ADB_Mainwindow())
    devices_id = ADB_Mainwindow.get_selected_device(ADB_Mainwindow())
    if devices_id in devices_id_lst:
        command = f"adb -s {device_id} install {package_path}"
        try:
            subprocess.run(command, shell=True, check=True)
            print("应用安装成功！")
        except subprocess.CalledProcessError as e:
            print(f"应用安装失败: {e}")
    else:
        print("设备已断开！")

def clear_app_cache(device, package_name):
    if device is not None:
        # print(device)
        try:
            device.app_clear(package_name)
            print(f"应用 {package_name} 的缓存已清除")
        except Exception as e:
            print(f"清除应用缓存失败: {e}")
    else:
        print("设备未连接")


def pull_log_without_clear(file_path, device_id):
    command = f'cmd /k "adb -s {device_id} shell logcat > {file_path}"'
    process = subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE)
    print("已开始拉取 log，如需停止，请手动关闭此窗口。")
    while True:
        if process.poll() is not None:
            break


def pull_log_with_clear(file_path, device_id):
    subprocess.run(f'adb -s {device_id} logcat -c', shell=True)
    command = f'cmd /k "adb -s {device_id} shell logcat > {file_path}"'
    process = subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE)
    print("已开始拉取 log，如需停止，请手动关闭此窗口。")
    while True:
        if process.poll() is not None:
            break



def simulate_click(x, y, device_id):
    command = f"adb -s {device_id} shell input tap {x} {y}"
    try:
        subprocess.run(command, shell=True, check=True)
        print("点击成功！")
    except subprocess.CalledProcessError as e:
        print(f"点击失败: {e}")


def adb_push_file(local_file_path, target_path_on_device, device_id):
    command = f"adb -s {device_id} push {local_file_path} {target_path_on_device}"
    try:
        subprocess.run(command, shell=True, check=True)
        print("文件推送成功！")
    except subprocess.CalledProcessError as e:
        print(f"文件推送失败: {e}")

def aapt_get_packagen_name(apk_path):
    """
    通过aapt命令获取apk包名
    """
    command = f"aapt dump badging {apk_path} | findstr name"
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        package_name = result.stdout.strip().split('\'')[1]
        return package_name
    except subprocess.CalledProcessError as e:
        print(f"获取包名失败: {e}")
        return None

class Worker(QThread):
    update_ui = pyqtSignal(str)  # 定义一个信号用于更新UI，传递字符串消息

    def __init__(self, func, *args):
        super().__init__()
        self.func = func  # 将要在新线程中运行的函数
        self.args = args  # 传递给函数的参数

    def run(self):
        """在新线程中执行"""
        try:
            result = self.func(*self.args)  # 调用指定的函数并传递参数
            self.update_ui.emit(str(result))  # 将结果发送到主线程以更新UI
        except Exception as e:
            self.update_ui.emit(f"执行命令失败: {e}")  # 捕获异常并通知主线程

# noinspection PyShadowingNames
class ADB_Mainwindow(QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        super(ADB_Mainwindow, self).__init__(parent)
        self.setupUi(self)
        """print重定向到textEdit、textBrowser"""

        # 重定向输出流为textBrowser
        self.text_edit_output_stream = TextEditOutputStream(self.textBrowser)
        sys.stdout = self.text_edit_output_stream
        sys.stderr = self.text_edit_output_stream

        self.device_id = connect_device()

        if self.device_id:
            self.device = u2.connect(self.device_id)
        else:
            self.device = None  # 类型为 u2.Device 或 None


        self.refresh_devices()  # 刷新设备列表
        self.adb_cpu_info.clicked.connect(self.adb_cpu_info_wrapper)  # 显示CPU信息
        self.simulate_swipe.clicked.connect(self.show_simulate_swipe_dialog)  # 模拟滑动
        # self.adb_operation.clicked.connect(self.adb_operation_wrapper)  # 显示设备号
        self.view_apk_path.clicked.connect(self.view_apk_path_wrapper)  # 显示应用安装路径
        self.input_text_via_adb.clicked.connect(self.show_input_text_dialog)  # 输入文本
        self.get_screenshot.clicked.connect(self.show_screenshot_dialog)  # 截图
        self.force_stop_app.clicked.connect(self.show_force_stop_app_dialog)  # 强制停止应用
        self.adb_uninstall.clicked.connect(self.show_uninstall_dialog)  # 卸载应用
        self.adb_pull_file.clicked.connect(self.show_pull_file_dialog)  # 拉取文件
        self.simulate_long_press.clicked.connect(self.show_simulate_long_press_dialog)  # 模拟长按
        self.adb_install.clicked.connect(self.show_install_file_dialog)  # 安装应用
        self.clear_app_cache.clicked.connect(self.show_clear_app_cache_dialog)  # 清除应用缓存
        self.app_package_and_activity.clicked.connect(self.get_foreground_package)  # 获取前台应用包名和活动名
        self.pull_log_without_clear.clicked.connect(self.show_pull_log_without_clear_dialog)  # 拉取日志（不清除）
        self.pull_log_with_clear.clicked.connect(self.show_pull_log_with_clear_dialog)  # 拉取日志（清除）
        self.simulate_click.clicked.connect(self.show_simulate_click_dialog)  # 模拟点击
        self.adb_push_file.clicked.connect(self.show_push_file_dialog)  # 推送文件
        self.install_system.clicked.connect(self.install_system_action)  # 安装系统应用
        self.close.clicked.connect(self.stop_program)  # 关闭程序
        self.adbbutton.clicked.connect(ADB_Mainwindow.run_cmd)  # 执行 adb 命令
        self.button_reboot.clicked.connect(self.reboot_device)  # 重启设备
        self.RefreshButton.clicked.connect(self.refresh_devices)  # 刷新设备列表
        self.adb_root.clicked.connect(self.adb_root_wrapper)  # 以 root 权限运行 ADB
        self.start_app.clicked.connect(self.start_app_action)  # 启动应用
        self.get_running_app_info_button.clicked.connect(self.get_running_app_info)  # 获取当前运行的应用信息
        self.aapt_getpackagename_button.clicked.connect(self.aapt_getpackage_name_dilog)  # 获取apk包名

    @staticmethod
    def get_new_device_lst():  # 静态方法，返回设备ID列表
        # device_id = self.get_selected_device()
        result = subprocess.run("adb devices", shell=True, check=True, capture_output=True,
                                text=True)  # 执行 adb devices 命令
        devices = result.stdout.strip().split('\n')[1:]  # 获取设备列表
        device_ids = [line.split('\t')[0] for line in devices if line]  # 提取设备ID
        return device_ids

    def start_app_action(self):
        """启动应用"""
        # device_id_lst = self.refresh_devices()
        device_ids = self.get_new_device_lst()

        device_id = self.get_selected_device()
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
                    print(package_name)
                    print(activity_name)
                    if len(parts) >= 2:
                        self.device = u2.connect(device_id)
                        self.device.app_start(package_name, activity_name)
                        print(f"应用 {package_name} 已启动")
                    else:
                        print("输入的格式不正确，请按照格式输入：包名: com.xxx.xxx, 活动名:.xxx")
                else:
                    print("用户取消输入或输入为空")
            except Exception as e:
                # print(package_name)
                # print(activity_name)
                print(f"启动应用失败: {e}")
        else:
            print("未连接设备！", end="")


    def get_running_app_info(self):
        # 获取当前前景应用的包名
        device_id = self.get_selected_device()  # 获取当前选定的设备ID
        devices_id_lst = self.get_new_device_lst()
        package_name = self.get_foreground_package()  # 传入 device_id 获取包名
        if device_id in devices_id_lst:
            if package_name:
                try:
                    # 连接到设备
                    d = u2.connect(device_id)  # 使用获取的设备ID

                    # 获取应用信息
                    app_info = d.app_info(package_name)

                    if app_info:
                        version_name = app_info.get('versionName', '未知版本')
                        # print(f"当前运行的应用包名: {package_name}")
                        print(f"当前运行的应用版本号: {version_name}")
                    else:
                        print("无法获取应用信息")
                except Exception as e:
                    print(f"获取应用信息失败: {e}")
            else:
                print("未获取到当前前景应用的包名")
        else:
            print("设备已断开！")

    def get_selected_device(self):
        return self.ComboxButton.currentText()  # 返回的类型为str

    def adb_cpu_info_wrapper(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            adb_cpu_info(device_id)
        else:
            print("设备已断开！", end="")

    def view_apk_path_wrapper(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            # 获取当前应用包名
            package_name = self.get_foreground_package()
            cmd = f'adb -s {device_id} shell pm path {package_name}'
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            # 输出安装目录
            apk_path = result.stdout.strip()
            parts = apk_path.split(":")
            print(f"应用安装路径: {parts[1]}")
        else:
            print("设备已断开！", end="")

    @staticmethod
    def run_cmd():
        user_directory = os.path.expanduser("~")
        subprocess.Popen(["start", "cmd", "/k", "cd /d " + user_directory], shell=True)

    def refresh_devices(self):
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
                print("未连接设备！", end="")
                # self.textBrowser.append("append:未连接设备！")
                return device_ids  # 返回设备ID列表



        except subprocess.CalledProcessError as e:
            self.textBrowser.append(f"刷新设备列表失败: {e}")
            return []  # 返回空列表表示刷新失败

    def adb_root_wrapper(self):
        device_id = self.get_selected_device()
        if device_id:
            self.textBrowser.append(adb_root(device_id))
            # print("获取Root成功！")
        else:
            print("未连接设备！", end="")

    def reboot_device(self):
        try:
            device_id = self.get_selected_device()
            device_ids = self.get_new_device_lst()
            if device_id in device_ids:
                # 执行 adb reboot 命令
                result = subprocess.run(
                    f"adb -s {device_id} reboot",
                    shell = True,  # 执行命令
                    check = True,  # 检查命令是否成功
                    stdout = subprocess.PIPE,  # 捕获输出
                    stderr = subprocess.PIPE  # 捕获错误
                )
                # 不要用print，会导致UI卡死，用textBrowser.append
                if result.returncode == 0:
                    # self.textBrowser.append(str(result))
                    self.textBrowser.append(f"设备 {device_id} 已重启！")
                else:
                    self.textBrowser.append(f"设备 {device_id} 已重启！")
                    self.textBrowser.append(f"错误信息：", str(result))
            else:
                self.textBrowser.append(f"设备已断开！")
        except Exception as e:
            self.textBrowser.append(f"重启设备失败: {e}")

    def show_screenshot_dialog(self):
        device_id = self.get_selected_device()
        # devices_id_lst = self.refresh_devices()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            file_path, _ = QFileDialog.getSaveFileName(self, "保存截图", "", "PNG Files (*.png);;All Files (*)")
            if file_path:
                get_screenshot(file_path, device_id)
        else:
            print("设备已断开！", end="")


    def show_uninstall_dialog(self):
        device_id = self.get_selected_device()
        # devices_id_lst = self.refresh_devices()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            package_name, ok = QInputDialog.getText(self, "输入应用包名", "请输入要卸载的应用包名：")
            if ok and package_name:
                adb_uninstall(package_name, device_id)
        else:
            # print("未连接设备！")
            pass

    def show_pull_file_dialog(self):
        device_id = self.get_selected_device()
        # device_id_lst = self.refresh_devices()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            file_path_on_device, ok = QInputDialog.getText(self, "输入设备文件路径", "请输入车机上的文件路径:")
            if ok and file_path_on_device:
                local_path, _ = QFileDialog.getSaveFileName(self, "保存文件", "", "All Files (*)")
                if local_path:
                    adb_pull_file(file_path_on_device, local_path, device_id)
        else:
            print("未连接设备！", end="")

    def show_install_file_dialog(self):
        device_id = self.get_selected_device()
        if device_id:
            package_path, _ = QFileDialog.getOpenFileName(self, "选择应用安装包", "",
                                                          "APK Files (*.apk);;All Files (*)")
            if package_path:
                adb_install(package_path, device_id)

    def show_pull_log_without_clear_dialog(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            file_path, _ = QFileDialog.getSaveFileName(self, "保存 log", "", "txt Files (*.txt);;All Files (*)")
            if file_path:
                pull_log_without_clear(file_path, device_id)
        else:
            print("未连接设备！", end="")

    def show_pull_log_with_clear_dialog(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            file_path, _ = QFileDialog.getSaveFileName(self, "保存 log", "", "txt Files (*.txt);;All Files (*)")
            if file_path:
                pull_log_with_clear(file_path, device_id)
        else:
            print("未连接设备！")

    def show_push_file_dialog(self):
        device_id = self.get_selected_device()
        # device_id_lst = self.refresh_devices()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            local_file_path, _ = QFileDialog.getOpenFileName(self, "选择本地文件", "", "All Files (*)")
            if local_file_path:
                target_path_on_device, ok = QInputDialog.getText(self, "输入设备文件路径",
                                                                 "请输入车机上的目标路径:")
                if ok and target_path_on_device:
                    adb_push_file(local_file_path, target_path_on_device, device_id)
        else:
            print("未连接设备！")

    def show_simulate_click_dialog(self):
        device_id = self.get_selected_device()
        # device_id_lst = self.refresh_devices()
        device_id_lst = self.get_new_device_lst()
        if device_id in device_id_lst:
            x, ok = QInputDialog.getInt(self, "输入 X 坐标", "请输入点击的 X 坐标:")
            if ok:
                y, ok = QInputDialog.getInt(self, "输入 Y 坐标", "请输入点击的 Y 坐标:")
                if ok:
                    simulate_click(x, y, device_id)
        else:
            print("未连接设备！")

    def show_simulate_swipe_dialog(self):
        device_id = self.get_selected_device()
        # device_id_lst = self.refresh_devices()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            start_x, ok = QInputDialog.getInt(self, "输入起始 X 坐标", "请输入滑动起始的 X 坐标:")
            if ok:
                start_y, ok = QInputDialog.getInt(self, "输入起始 Y 坐标", "请输入滑动起始的 Y 坐标:")
                if ok:
                    end_x, ok = QInputDialog.getInt(self, "输入结束 X 坐标", "请输入滑动结束的 X 坐标:")
                    if ok:
                        end_y, ok = QInputDialog.getInt(self, "输入结束 Y 坐标", "请输入滑动结束的 Y 坐标:")
                        if ok:
                            duration, ok = QInputDialog.getInt(self, "输入滑动持续时间",
                                                               "请输入滑动的持续时间（毫秒，默认为 200 毫秒）:")
                            if ok:
                                simulate_swipe(start_x, start_y, end_x, end_y, duration, device_id)
        else:
            print("未连接设备！")

    def show_simulate_long_press_dialog(self):
        device_id = self.get_selected_device()
        # device_id_lst = self.refresh_devices()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            x, ok = QInputDialog.getInt(self, "输入 X 坐标", "请输入长按的 X 坐标:")
            if ok:
                y, ok = QInputDialog.getInt(self, "输入 Y 坐标", "请输入长按的 Y 坐标:")
                if ok:
                    duration, ok = QInputDialog.getInt(self, "输入长按持续时间",
                                                       "请输入长按的持续时间（毫秒，默认为 2000 毫秒）:")
                    if ok:
                        simulate_long_press(x, y, duration, device_id)
        else:
            # print("未连接设备！")
            pass

    def show_input_text_dialog(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            text_to_input, ok = QInputDialog.getText(self, "输入文本", "请输入要通过 ADB 输入的文本:")
            if ok and text_to_input:
                input_text_via_adb(text_to_input, device_id)
        else:
            print("未连接设备！", end="")

    def show_force_stop_app_dialog(self):
        device_id = self.get_selected_device()
        # if device_id:
        #     print(f"选择的设备ID: {device_id}")

        if device_id != "":
            package_name = self.get_foreground_package()
            print(f"当前前台应用包名: {package_name}")
            if package_name:
                # 使用ADB命令强制停止应用
                adb_command = f"adb -s {device_id} shell am force-stop {package_name}"
                try:
                    subprocess.run(adb_command, shell=True, check=True)
                    print(f"成功强制停止 {package_name} 应用在设备 {device_id} 上")
                except subprocess.CalledProcessError as e:
                    print(f"无法强制停止 {package_name} 应用在设备 {device_id} 上: {e}")
        elif not device_id:
            print("未选择设备", end="")


    def show_clear_app_cache_dialog(self):
        device_id = self.get_selected_device()  # 获取用户选择的设备ID
        if device_id:
            package_name = self.get_foreground_package()
            if package_name:
                clear_app_cache(u2.connect(device_id), package_name)  # 清除应用缓存
            else:
                print("未找到正在运行的应用包名")
        else:
            print("未选择设备", end="")

    """install_system_action()函数"""
    @staticmethod
    def install_system_action():
        print("功能待定")
        # device_id = self.get_selected_device()
        #
        # def get_package_name_from_apk(apk_path):
        #     aapt_path = "aapt"  # 假设 aapt 在 PATH 中，如果没有，请指定完整路径
        #     if not shutil.which(aapt_path):
        #         print(f"错误: 找不到 aapt 工具，请检查 Android SDK 是否正确安装")
        #         return None
        #
        #     try:
        #         # 使用 aapt 获取 APK 的包名
        #         result = subprocess.run([aapt_path, 'dump', 'badging', apk_path], capture_output=True, text=True,
        #                                 check=True)
        #         for line in result.stdout.splitlines():
        #             if line.startswith('package: name='):
        #                 # 提取包名
        #                 package_name = line.split("'")[1]
        #                 return package_name
        #     except subprocess.CalledProcessError as e:
        #         print(f"获取包名失败: {e}")
        #         return None
        #     except FileNotFoundError:
        #         print(f"错误: 未找到 aapt 工具")
        #         return None
        #
        # if device_id:
        #     try:
        #         # 弹出文件选择对话框，选择APK文件
        #         apk_path, _ = QFileDialog.getOpenFileName(self, "Select APK", "", "APK Files (*.apk)")
        #
        #         if apk_path:
        #             # 获取APK文件的包名
        #             package_name = get_package_name_from_apk(apk_path)
        #             if not package_name:
        #                 print("无法获取APK的包名")
        #                 return
        #
        #             # 连接设备
        #             device = u2.connect(device_id)
        #
        #             # 运行adb disable-verity命令
        #             subprocess.run(['adb', '-s', device_id, 'disable-verity'], check=True)
        #             print(f"已禁用verity")
        #
        #             # 运行adb remount命令
        #             subprocess.run(['adb', '-s', device_id, 'remount'], check=True)
        #             print(f"已重新挂载")
        #
        #             # 获取应用包路径
        #             result = subprocess.run(['adb', '-s', device_id, 'shell', 'pm', 'path', package_name],
        #                                     capture_output=True, text=True, check=True)
        #             print(f"获取到应用包路径: {result.stdout.strip()}")
        #             path = result.stdout.strip().split(':')[-1]
        #
        #             # 向设备推送apk文件
        #             subprocess.run(['adb', '-s', device_id, 'push', apk_path, path], check=True)
        #
        #             # 安装apk
        #             subprocess.run(['adb', '-s', device_id, 'install', apk_path], check=True)
        #
        #     except subprocess.CalledProcessError as e:
        #         print(f"操作失败: {e}")
        #     except Exception as e:
        #         print(f"发生错误: {e}")

    def get_foreground_package(self):
        # 刷新设备列表
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
                        print(f"包名: {package_name}, 活动名: {activity_name}")
                        return package_name
                    else:
                        print("未找到正在运行的应用包名")
                        return None
                else:
                    print("设备连接失败")
                    return None
            except Exception as e:
                print(f"获取前台正在运行的应用包名失败: {e}")
                return None
        else:
            print("设备已断开！")
            # return None


    def aapt_getpackage_name_dilog(self):
        """弹出文件选择框让用户选择apk文件，获取到的apk_path传入到aapt_get_package_name()函数中获取包名"""
        apk_path, _ = QFileDialog.getOpenFileName(self, "选择APK文件", "", "APK Files (*.apk)")
        if apk_path:
            package_name = aapt_get_packagen_name(apk_path)
            # 从apk_path中提取出文件名
            apk_name = os.path.basename(apk_path)
            if package_name:
                print(f"{apk_name}文件的包名: {package_name}")
            else:
                print(f"无法获取{apk_name}文件的包名")
        else:
            print("未选择apk文件!", end="")

            # if package_name:
            #     QMessageBox.information(self, "提示", f"包名: {package_name}")
            # else:
            #     QMessageBox.warning(self, "警告", "无法获取APK的包名")

    @staticmethod
    def stop_program():
        sys.exit()
