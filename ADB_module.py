import time
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

def adb_root(device_id):
    # 传入下拉框选择的设备 ID
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
    try:
        cpu_info = subprocess.run(f'adb -s {device_id} shell cat /proc/cpuinfo', capture_output=True, text=True)
        return cpu_info.stdout
    except subprocess.CalledProcessError as e:
        return f"获取 CPU 信息失败: {e}"


def simulate_swipe(start_x, start_y, end_x, end_y, duration, device_id):
    command = f"adb -s {device_id} shell input swipe {start_x} {start_y} {end_x} {end_y} {duration}"
    try:
        subprocess.run(command, shell=True, check=True)
        return "滑动成功！"
    except subprocess.CalledProcessError as e:
        return f"滑动失败: {e}"


def input_text_via_adb(text_to_input, device_id):
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
    command = f"adb -s {device_id} shell screencap -p /sdcard/screenshot.png && adb -s {device_id} pull /sdcard/screenshot.png {file_path} && adb -s {device_id} shell rm /sdcard/screenshot.png"
    try:
        subprocess.run(command, shell=True, check=True)
        return f"截图已保存到 {file_path}"
    except subprocess.CalledProcessError as e:
        return f"截图失败: {e}"


def adb_uninstall(package_name, device_id):
    command = f"adb -s {device_id} uninstall {package_name}"
    try:
        subprocess.run(command, shell=True, check=True)
        return f"应用 {package_name} 已卸载"
    except subprocess.CalledProcessError as e:
        return f"卸载应用失败: {e}"


def adb_pull_file(file_path_on_device, local_path, device_id):
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
    command = f"adb -s {device_id} shell input swipe {x} {y} {x} {y} {duration}"
    try:
        subprocess.run(command, shell=True, check=True)
        return "长按模拟成功！"
    except subprocess.CalledProcessError as e:
        return f"长按模拟失败: {e}"


def adb_install(package_path, device_id):
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
    if device is not None:
        try:
            device.app_clear(package_name)
            return f"应用 {package_name} 的缓存已清除"
        except Exception as e:
            return f"清除应用缓存失败: {e}"
    else:
        return "设备未连接！"


def pull_log_without_clear(file_path, device_id):
    command = f'cmd /k "adb -s {device_id} shell logcat > {file_path}"'
    process = subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE)
    while True:
        if process.poll() is not None:
            break


def pull_log_with_clear(file_path, device_id):
    subprocess.run(f'adb -s {device_id} logcat -c', shell=True)
    command = f'cmd /k "adb -s {device_id} shell logcat > {file_path}"'
    process = subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE)
    while True:
        if process.poll() is not None:
            break



def simulate_click(x, y, device_id):
    command = f"adb -s {device_id} shell input tap {x} {y}"
    try:
        subprocess.run(command, shell=True, check=True)
        return "点击成功！"
    except subprocess.CalledProcessError as e:
        return f"点击失败: {e}"


def adb_push_file(local_file_path, target_path_on_device, device_id):
    command = f"adb -s {device_id} push {local_file_path} {target_path_on_device}"
    try:
        subprocess.run(command, shell=True, check=True)
        return "文件推送成功！"
    except subprocess.CalledProcessError as e:
        return f"文件推送失败: {e}"

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
        return f"获取包名失败: {e}"


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

    @staticmethod
    def get_new_device_lst():  # 静态方法，返回设备ID列表
        result = subprocess.run("adb devices", shell=True, check=True, capture_output=True,
                                text=True)  # 执行 adb devices 命令
        devices = result.stdout.strip().split('\n')[1:]  # 获取设备列表
        device_ids = [line.split('\t')[0] for line in devices if line]  # 提取设备ID
        return device_ids

    def show_pull_hulog_dialog(self):
        """
        执行以下命令：
        adb root
        adb shell setprop bmi.service.adb.root 1
        adb pull log
        """
        device_ids = self.get_new_device_lst()
        device_id = self.get_selected_device()
        if device_id in device_ids:
            # 弹出对话框请用户选择文件夹
            file_path = QFileDialog.getExistingDirectory(self, "选择保存路径", os.getcwd())
            if file_path:
                # 运行上述三条命令
                try:
                    # 创建一个命令行窗口，执行命令
                    command = f'adb -s {device_id} root && adb -s {device_id} shell "setprop bmi.service.adb.root 1" && adb -s {device_id} pull log {file_path}'
                    subprocess.run(command, shell= True, check=True)
                    self.textBrowser.append(f"日志文件已保存到 {file_path}")
                except subprocess.CalledProcessError as e:
                    self.textBrowser.append(f"日志文件拉取失败: {e}")
            else:
                self.textBrowser.append("已取消！")
        else:
            self.textBrowser.append("设备未连接！")




    def start_app_action(self):
        """启动应用"""
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
                    if len(parts) >= 2:
                        self.device = u2.connect(device_id)
                        self.device.app_start(package_name, activity_name)
                        self.textBrowser.append(f"应用 {package_name} 已启动")
                    else:
                        self.textBrowser.append("输入的格式不正确，请按照格式输入：包名: com.xxx.xxx, 活动名:.xxx")
                else:
                    self.textBrowser.append("用户取消输入或输入为空")
            except Exception as e:
                self.textBrowser.append(f"启动应用失败: {e}")
        else:
            self.textBrowser.append("未连接设备！")


    def get_running_app_info(self):
        # 获取当前前景应用的包名
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


    def get_selected_device(self):
        return self.ComboxButton.currentText()  # 返回的类型为str

    def adb_cpu_info_wrapper(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            # device_id:下拉框选择的设备ID
            res = adb_cpu_info(device_id)
            self.textBrowser.append(res)
        else:
            self.textBrowser.append("设备已断开！")

    def view_apk_path_wrapper(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
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
                parts = apk_path.split(":")
                self.textBrowser.append(f"应用安装路径: {parts[1]}")
                return parts[1]
        else:
            self.textBrowser.append("设备已断开！")

    @staticmethod
    def run_cmd():
        user_directory = os.path.expanduser("~")
        subprocess.Popen(["start", "cmd", "/k", "cd /d " + user_directory], shell=True)

    def refresh_devices(self):
        # 刷新设备列表并添加到下拉框
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

    def adb_root_wrapper(self):
        device_id = self.get_selected_device()
        if device_id:
            res = adb_root(device_id)  # 传入下拉框选择的设备ID
            self.textBrowser.append(res)
        else:
            self.textBrowser.append("未连接设备！")

    def reboot_device(self):
        try:
            device_id = self.get_selected_device()
            device_ids = self.get_new_device_lst()
            if device_id in device_ids:
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
                    # self.textBrowser.append(result.stdout.decode('utf-8'))
                elif "not found" in result.stdout.decode('utf-8'):
                    self.adb_root_wrapper()
                    self.reboot_device()
            else:
                self.textBrowser.append(f"设备已断开！")
        except Exception as e:
            self.textBrowser.append(f"重启设备失败: {e}")

    def show_screenshot_dialog(self):
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


    def show_uninstall_dialog(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            package_name, ok = QInputDialog.getText(self, "输入应用包名", "请输入要卸载的应用包名：")
            if ok and package_name:
                res = adb_uninstall(package_name, device_id)
                self.textBrowser.append(res)
        else:
            self.textBrowser.append("未连接设备！")

    def show_pull_file_dialog(self):
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

    def show_install_file_dialog(self):
        device_id = self.get_selected_device()
        if device_id:
            package_path, _ = QFileDialog.getOpenFileName(self, "选择应用安装包", "",
                                                          "APK Files (*.apk);;All Files (*)")
            if package_path:
                # 传入下拉框选择的设备ID
                res = adb_install(package_path, device_id)
                self.textBrowser.append(res)

    def show_pull_log_without_clear_dialog(self):

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
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            file_path, _ = QFileDialog.getSaveFileName(self, "保存 log", "", "txt Files (*.txt);;All Files (*)")
            if file_path:
                pull_log_with_clear(file_path, device_id)
        else:
            self.textBrowser.append("未连接设备！")

    def show_push_file_dialog(self):
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

    def show_simulate_click_dialog(self):
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

    def show_simulate_swipe_dialog(self):
        device_id = self.get_selected_device()
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
                                res = simulate_swipe(start_x, start_y, end_x, end_y, duration, device_id)
                                self.textBrowser.append(res)
        else:
            self.textBrowser.append("未连接设备！")

    def show_simulate_long_press_dialog(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            x, ok = QInputDialog.getInt(self, "输入 X 坐标", "请输入长按的 X 坐标:")
            if ok:
                y, ok = QInputDialog.getInt(self, "输入 Y 坐标", "请输入长按的 Y 坐标:")
                if ok:
                    duration, ok = QInputDialog.getInt(self, "输入长按持续时间",
                                                       "请输入长按的持续时间（毫秒，默认为 2000 毫秒）:")
                    if ok:
                        result = simulate_long_press(x, y, duration, device_id)
                        self.textBrowser.append(result)
        else:
            self.textBrowser.append("未连接设备！")

    def show_input_text_dialog(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            text_to_input, ok = QInputDialog.getText(self, "输入文本", "请输入要通过 ADB 输入的文本:")
            if ok and text_to_input:
                lst = input_text_via_adb(text_to_input, device_id)
                self.textBrowser.append(lst)
        else:
            self.textBrowser.append("未连接设备！")

    def show_force_stop_app_dialog(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            package_name = self.get_foreground_package()
            self.textBrowser.append(f"当前前台应用包名: {package_name}")
            if package_name:
                adb_command = f"adb -s {device_id} shell am force-stop {package_name}"
                try:
                    subprocess.run(adb_command, shell=True, check=True)
                    self.textBrowser.append(f"成功强制停止 {package_name} 应用在设备 {device_id} 上")
                except subprocess.CalledProcessError as e:
                    self.textBrowser.append(f"强制停止 {package_name} 应用在设备 {device_id} 上失败: {e}")
        else:
            self.textBrowser.append("设备已断开！")


    def show_clear_app_cache_dialog(self):
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


    def get_foreground_package(self, is_direct_call=True):
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
                        if is_direct_call:  # 如果是直接调用
                            self.textBrowser.append(f"包名: {package_name}, 活动名: {activity_name}")
                        return package_name
                    else:
                        self.textBrowser.append("未找到正在运行的应用包名")
                        return None
                else:

                    self.textBrowser.append("设备连接失败")
                    return None
            except Exception as e:
                self.textBrowser.append(f"获取前台正在运行的应用包名失败: {e}")
                return None
        else:
            self.textBrowser.append("设备已断开！")
            return None


    def aapt_getpackage_name_dilog(self):
        """弹出文件选择框让用户选择apk文件，获取到的apk_path传入到aapt_get_package_name()函数中获取包名"""
        apk_path, _ = QFileDialog.getOpenFileName(self, "选择APK文件", "", "APK Files (*.apk)")
        if apk_path:
            package_name = aapt_get_packagen_name(apk_path)
            # 从apk_path中提取出文件名
            apk_name = os.path.basename(apk_path)
            if package_name:
                self.textBrowser.append(f"{apk_name}文件的包名: {package_name}")
            else:
                self.textBrowser.append(f"无法获取{apk_name}文件的包名")
        else:
            self.textBrowser.append("未选择apk文件!")

    @staticmethod
    def stop_program():
        sys.exit()
