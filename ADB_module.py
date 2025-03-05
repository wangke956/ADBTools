import time
from PyQt5.QtWidgets import (QMainWindow, QFileDialog, QInputDialog, QMessageBox)
import sys
import io
import subprocess
import threading
import queue
import logging

logger = logging.getLogger('ADBTools')

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
    logger.info(f'尝试以root权限运行ADB，设备ID：{device_id}')
    device_ids = ADB_Mainwindow.get_new_device_lst()
    if device_id in device_ids:
        try:
            result = subprocess.run(f"adb -s {device_id} root", shell=True, check=True, capture_output=True, text=True)
            if "adbd is already running as root" in result.stdout:
                logger.info('ADB已经以root权限运行')
                return "ADB 已成功以 root 权限运行"
            elif 'adbd cannot run as root in production builds'in result.stdout:
                logger.warning('设备不支持ADB root')
                return "设备不支持 ADB root，无法以 root 权限运行。"
            elif result.returncode == 0:
                logger.info('ADB root成功')
                return "ADB root 成功"
        except subprocess.CalledProcessError as e:
            error_msg = str(e)
            if "not found" in error_msg:
                logger.error('ADB命令未找到')
                return "ADB 命令未找到，请确保 ADB 工具已正确安装并添加到系统路径中。"
            elif "permission denied" in error_msg:
                logger.error('权限被拒绝')
                return "权限被拒绝，请确保你有足够的权限执行 ADB root 命令。"
            elif "adbd cannot run as root" in error_msg:
                logger.warning('设备不支持ADB root')
                return "设备不支持 ADB root，无法以 root 权限运行。"
            else:
                logger.error(f'ADB root失败：{e}')
                return f"ADB root 失败: {e}"
    else:
        logger.warning('设备未连接')
        return "设备未连接！"

# def adb_cpu_info(device_id):
#     try:
#         cpu_info = subprocess.run(f'adb -s {device_id} shell cat /proc/cpuinfo', capture_output=True, text=True)  #
#         return cpu_info.stdout
#     except subprocess.CalledProcessError as e:
#         return f"获取 CPU 信息失败: {e}"

def simulate_swipe(start_x, start_y, end_x, end_y, duration, device_id):
    command = f"adb -s {device_id} shell input swipe {start_x} {start_y} {end_x} {end_y} {duration}"
    try:
        subprocess.run(command, shell=True, check=True)
        return "滑动成功！"
    except subprocess.CalledProcessError as e:
        return f"滑动失败: {e}"


def input_text_via_adb(text_to_input, device_id):
    logger.info(f'尝试通过ADB输入文本，设备ID：{device_id}，文本：{text_to_input}')
    command = f"adb -s {device_id} shell input text '{text_to_input}'"
    try:
        res = subprocess.run(command,
                             shell=True,
                             check=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             text=True)
        logger.info('文本输入成功')
        return f"文本输入成功！{res.stdout.strip()}"  # 获取输出并转为字符串
    except subprocess.CalledProcessError as e:
        logger.error(f'文本输入失败：{e}')
        return f"文本输入失败: {e}"

def get_screenshot(file_path, device_id):
    logger.info(f'尝试获取截图，设备ID：{device_id}，保存路径：{file_path}')
    command = f"adb -s {device_id} shell screencap -p /sdcard/screenshot.png && adb -s {device_id} pull /sdcard/screenshot.png {file_path} && adb -s {device_id} shell rm /sdcard/screenshot.png"
    try:
        subprocess.run(command, shell=True, check=True)
        logger.info(f'截图已保存到：{file_path}')
        return f"截图已保存到 {file_path}"
    except subprocess.CalledProcessError as e:
        logger.error(f'截图失败：{e}')
        return f"截图失败: {e}"

def adb_uninstall(package_name, device_id):
    logger.info(f'尝试卸载应用，设备ID：{device_id}，包名：{package_name}')
    command = f"adb -s {device_id} uninstall {package_name}"
    try:
        subprocess.run(command, shell=True, check=True)
        logger.info(f'应用{package_name}已卸载')
        return f"应用 {package_name} 已卸载"
    except subprocess.CalledProcessError as e:
        logger.error(f'卸载应用失败：{e}')
        return f"卸载应用失败: {e}"

def adb_pull_file(file_path_on_device, local_path, device_id):
    logger.info(f'尝试拉取文件，设备ID：{device_id}，设备文件路径：{file_path_on_device}，本地保存路径：{local_path}')
    command = f"adb -s {device_id} pull {file_path_on_device} {local_path}"
    try:
        res = subprocess.run(command,
                             shell = True,
                             check = True,
                             stdout = subprocess.PIPE,
                             stderr = subprocess.PIPE,
                             text = True)
        string = res.stdout.strip()
        logger.info('文件拉取成功')
        return ["文件拉取成功！", string]
    except subprocess.CalledProcessError as e:
        logger.error(f'文件拉取失败：{e}')
        return f"文件拉取失败: {e}"

def simulate_long_press(x, y, duration, device_id):
    logger.info(f'尝试模拟长按，设备ID：{device_id}，坐标：({x}, {y})，持续时间：{duration}')
    command = f"adb -s {device_id} shell input swipe {x} {y} {x} {y} {duration}"
    try:
        subprocess.run(command, shell=True, check=True)
        logger.info('长按模拟成功')
        return "长按模拟成功！"
    except subprocess.CalledProcessError as e:
        logger.error(f'长按模拟失败：{e}')
        return f"长按模拟失败: {e}"
def adb_install(package_path, device_id):
    logger.info(f'尝试安装应用，设备ID：{device_id}，安装包路径：{package_path}')
    devices_id_lst = ADB_Mainwindow.get_new_device_lst()
    if device_id in devices_id_lst:
        command = f"adb -s {device_id} install {package_path}"
        try:
            res = subprocess.run(command,
                                 shell=True,
                                 check=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 text=True)
            time.sleep(8)
            logger.info('应用安装成功')
            return f"应用安装成功！{res.stdout.strip()}"
        except subprocess.CalledProcessError as e:
            logger.error(f'应用安装失败：{e.stderr.strip()}')
            return f"应用安装失败: {e.stderr.strip()}"
    else:
        logger.warning('设备未连接')
        return "设备未连接！"
def clear_app_cache(device, package_name):
    logger.info(f'尝试清除应用缓存，包名：{package_name}')
    if device is not None:
        try:
            device.app_clear(package_name)
            logger.info(f'应用{package_name}的缓存已清除')
            return f"应用 {package_name} 的缓存已清除"
        except Exception as e:
            logger.error(f'清除应用缓存失败：{e}')
            return f"清除应用缓存失败: {e}"
    else:
        logger.warning('设备未连接')
        return "设备未连接！"
def pull_log_without_clear(file_path, device_id):
    logger.info(f'尝试拉取日志（不清除），设备ID：{device_id}，保存路径：{file_path}')
    command = f'cmd /k "adb -s {device_id} shell logcat > {file_path}"'
    process = subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE)
    while True:
        if process.poll() is not None:
            break
def pull_log_with_clear(file_path, device_id):
    logger.info(f'尝试拉取日志（清除），设备ID：{device_id}，保存路径：{file_path}')
    subprocess.run(f'adb -s {device_id} logcat -c', shell=True)
    command = f'cmd /k "adb -s {device_id} shell logcat > {file_path}"'
    process = subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE)
    while True:
        if process.poll() is not None:
            break
def simulate_click(x, y, device_id):
    logger.info(f'尝试模拟点击，设备ID：{device_id}，坐标：({x}, {y})')
    command = f"adb -s {device_id} shell input tap {x} {y}"
    try:
        subprocess.run(command, shell=True, check=True)
        logger.info('点击成功')
        return "点击成功！"
    except subprocess.CalledProcessError as e:
        logger.error(f'点击失败：{e}')
        return f"点击失败: {e}"
def adb_push_file(local_file_path, target_path_on_device, device_id):
    logger.info(f'尝试推送文件，设备ID：{device_id}，本地文件路径：{local_file_path}，目标路径：{target_path_on_device}')
    command = f"adb -s {device_id} push {local_file_path} {target_path_on_device}"
    try:
        subprocess.run(command, shell=True, check=True)
        logger.info('文件推送成功')
        return "文件推送成功！"
    except subprocess.CalledProcessError as e:
        logger.error(f'文件推送失败：{e}')
        return f"文件推送失败: {e}"
def aapt_get_packagen_name(apk_path):
    logger.info(f'尝试获取APK包名，APK路径：{apk_path}')
    command = f"aapt dump badging {apk_path} | findstr name"
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        package_name = result.stdout.strip().split('\'')[1]
        logger.info(f'获取到包名：{package_name}')
        return package_name
    except subprocess.CalledProcessError as e:
        logger.error(f'获取包名失败：{e}')
        return f"获取包名失败: {e}"
# noinspection PyShadowingNames
class ADB_Mainwindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        logger.info('初始化ADB_Mainwindow类')
        super(ADB_Mainwindow, self).__init__(parent)
        self.setupUi(self)
        # 添加按钮点击间隔控制和线程锁
        logger.debug('初始化按钮点击间隔控制和线程锁')
        self._last_click_time = {}
        self._click_interval = 1.0  # 设置点击间隔为1秒
        self._thread_locks = {}
        
        # 重定向输出流为textBrowser
        logger.debug('设置输出重定向到textBrowser')
        self.text_edit_output_stream = TextEditOutputStream(self.textBrowser)
        sys.stdout = self.text_edit_output_stream
        sys.stderr = self.text_edit_output_stream
        logger.info('开始刷新设备列表')
        self.refresh_devices()  # 刷新设备列表
        # self.adb_cpu_info.clicked.connect(self.adb_cpu_info_wrapper)  # 显示CPU信息
        # self.simulate_swipe.clicked.connect(self.show_simulate_swipe_dialog)  # 模拟滑动
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
        # self.pull_hulog.clicked.connect(self.show_pull_hulog_dialog)  # 拉取hulog
        self.pull_log_without_clear.clicked.connect(self.show_pull_log_without_clear_dialog)  # 拉取日志（不清除）
        self.pull_log_with_clear.clicked.connect(self.show_pull_log_with_clear_dialog)  # 拉取日志（清除）
        self.simulate_click.clicked.connect(self.show_simulate_click_dialog)  # 模拟点击
        self.adb_push_file.clicked.connect(self.show_push_file_dialog)  # 推送文件
        # self.close.clicked.connect(self.stop_program)  # 关闭程序
        self.adbbutton.clicked.connect(ADB_Mainwindow.run_cmd)  # 执行 adb 命令
        self.button_reboot.clicked.connect(self.reboot_device)  # 重启设备
        self.RefreshButton.clicked.connect(self.refresh_devices)  # 刷新设备列表
        self.adb_root.clicked.connect(self.adb_root_wrapper)  # 以 root 权限运行 ADB
        self.start_app.clicked.connect(self.start_app_action)  # 启动应用
        self.get_running_app_info_button.clicked.connect(self.get_running_app_info)  # 获取当前运行的应用信息
        self.aapt_getpackagename_button.clicked.connect(self.aapt_getpackage_name_dilog)  # 获取apk包名
        self.textBrowser.textChanged.connect(self.scroll_to_bottom)  # 自动滚动到底部
        self.switch_vr_env_button.clicked.connect(self.switch_vr_env)  # 切换VR环境
        self.VR_nework_check_button.clicked.connect(self.check_vr_network)  # 检查VR网络
        self.upgrade_page_button.clicked.connect(self.as33_upgrade_page)  # 打开延峰升级页面
        self.activate_VR_button.clicked.connect(self.activate_vr)  # 激活VR
        self.list_package_button.clicked.connect(self.list_package)
        self.skipping_powerlimit_button.clicked.connect(self.skip_power_limit)  # 跳过电源挡位限制
        self.enter_engineering_mode_button.clicked.connect(self.enter_engineering_mode)  # 进入工程模式
        self.upgrade_page_button_2.clicked.connect(self.as33_upgrade_page) # 打开延峰升级页面
        self.MZS3E_TT_enter_engineering_mode_button.clicked.connect(self.MZS3E_TT_enter_engineering_mode)  # MZS3E_TT进入工程模式
        # self.d_list()  # 设备列表初始化

    def MZS3E_TT_enter_engineering_mode(self):
        """MZS3E_TT进入工程模式"""
        logger.info('尝试进入MZS3E_TT工程模式')
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        def inner():
            if device_id in devices_id_lst:
                try:
                    logger.debug(f'连接设备：{device_id}')
                    d = u2.connect(device_id)
                    # 包名: com.saicmotor.diag, 活动名: .ui.main.MainActivity
                    logger.info('启动工程模式应用')
                    result = d.app_start("com.saicmotor.diag", ".ui.main.MainActivity")
                    logger.info('工程模式应用启动成功')
                    return result
                except Exception as e:
                    logger.error(f'MZS3E_TT进入工程模式失败：{e}')
                    self.textBrowser.append(f"MZS3E_TT进入工程模式失败: {e}")
            else:
                logger.warning('设备未连接')
                self.textBrowser.append("设备未连接！")
        threading.Thread(target=inner).start()

    def enter_engineering_mode(self):
        """进入工程模式"""
        logger.info('尝试进入工程模式')
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        def inner():
            if device_id in devices_id_lst:
                try:
                    logger.debug(f'连接设备：{device_id}')
                    d = u2.connect(device_id)
                    logger.info('启动工程模式应用')
                    result = d.app_start("com.saicmotor.hmi.engmode", "com.saicmotor.hmi.engmode.home.ui.EngineeringModeActivity")
                    logger.info('工程模式应用启动成功')
                    return result
                except Exception as e:
                    logger.error(f'进入工程模式失败：{e}')
                    self.textBrowser.append(f"进入工程模式失败: {e}")
            else:
                logger.warning('设备未连接')
                self.textBrowser.append("设备未连接！")
        threading.Thread(target=inner).start()

    def skip_power_limit(self):
        """跳过电源挡位限制"""
        logger.info('尝试跳过电源挡位限制')
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        def inner():
            if device_id in devices_id_lst:
                try:
                    logger.debug(f'连接设备：{device_id}')
                    d = u2.connect(device_id)
                    logger.info('执行root命令')
                    result = d.shell('adb root')
                    logger.debug(f'root命令结果：{result}')
                    logger.info('设置系统属性')
                    d.shell('setprop persist.update.enable 1')
                    logger.info('电源挡位限制已跳过')
                except Exception as e:
                    logger.error(f'跳过电源挡位限制失败：{e}')
                    self.textBrowser.append(f"跳过电源挡位限制失败: {e}")
            else:
                logger.warning('设备未连接')
                self.textBrowser.append("设备未连接！")
        threading.Thread(target=inner).start()



    def list_package(self):
        """获取设备上安装的应用列表"""
        logger.info('开始获取设备上的应用列表')
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        findstr = self.Findstr.toPlainText()
        logger.debug(f'搜索关键字：{findstr}')
        def inner():
            if device_id in devices_id_lst:
                try:
                    logger.debug(f'连接设备：{device_id}')
                    d = u2.connect(device_id)
                    logger.info('获取应用列表')
                    app_list = d.app_list(findstr)
                    total_apps = len(app_list)
                    logger.info(f'找到{total_apps}个应用')
                    if findstr:
                        self.textBrowser.append(f"设备 {device_id} 上共有 {total_apps} 个应用，包含关键字 {findstr}")
                        self.textBrowser.append("正在获取应用信息...")

                    else:
                        self.textBrowser.append(f"设备 {device_id} 上共有 {total_apps} 个应用")
                        self.textBrowser.append("正在获取应用信息...")

                    # 使用队列来管理输出，避免内存占用过大
                    output_queue = queue.Queue()
                    batch_size = 100  # 增加每批处理数量到100个应用
                    last_progress_line = None  # 记录上一次的进度行

                    def process_app_batch(apps_batch):
                        batch_output = []
                        for app in apps_batch:
                            try:
                                app_info = d.app_info(app)
                                version_name = app_info.get('versionName', '未知版本')
                                batch_output.append(f"{app}, 版本号: {version_name}")
                            except Exception as e:
                                batch_output.append(f"获取应用 {app} 信息失败: {str(e)}")
                        return batch_output

                    # 分批处理应用
                    current_batch = []
                    for i, app in enumerate(app_list):
                        current_batch.append(app)

                        if len(current_batch) >= batch_size or i == len(app_list) - 1:
                            # 处理当前批次
                            batch_results = process_app_batch(current_batch)
                            output_queue.put(batch_results)

                            # 显示当前批次结果
                            self.textBrowser.append('\n'.join(batch_results))

                            # 更新进度 - 如果存在上一次的进度行，先清除它
                            if last_progress_line:
                                self.text_edit_output_stream.set_clear_before_write(True)
                            progress = (i + 1) / total_apps * 100
                            progress_text = f"处理进度: {progress:.1f}% ({i + 1}/{total_apps})"
                            self.textBrowser.append(progress_text)
                            last_progress_line = progress_text

                            # 清空当前批次
                            current_batch = []

                    # 处理队列中剩余的结果
                    while not output_queue.empty():
                        batch_results = output_queue.get()
                        self.textBrowser.append('\n'.join(batch_results))

                    self.textBrowser.append(f"\n完成! 共处理 {total_apps} 个应用")

                except Exception as e:
                    self.textBrowser.append(f"获取应用列表失败: {e}")
            else:
                self.textBrowser.append("设备未连接！")
        threading.Thread(target=inner).start()

    def activate_vr(self):
        """激活VR"""
        logger.info('尝试激活VR')
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        def inner():
            if device_id in devices_id_lst:
                try:
                    logger.debug(f'连接设备：{device_id}')
                    d = u2.connect(device_id)
                    logger.info('发送激活VR按键事件')
                    d.shell('input keyevent 287')
                    logger.info('VR激活成功')
                except Exception as e:
                    logger.error(f'激活VR失败：{e}')
                    self.textBrowser.append(f"激活VR失败: {e}")
            else:
                logger.warning('设备未连接')
                self.textBrowser.append("设备未连接！")
        threading.Thread(target=inner).start()

    def as33_upgrade_page(self):
        """升级页面"""
        logger.info('尝试打开升级页面')
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        def inner():
            if device_id in devices_id_lst:
                try:
                    logger.debug(f'连接设备：{device_id}')
                    d = u2.connect(device_id)
                    logger.info('启动升级页面')
                    d.shell('am start com.yfve.usbupdate/.MainActivity')
                    logger.info('升级页面启动成功')
                except Exception as e:
                    logger.error(f'打开升级页面失败：{e}')
                    self.textBrowser.append(f"升级页面失败: {e}")
            else:
                logger.warning('设备未连接')
                self.textBrowser.append("设备未连接！")
        threading.Thread(target=inner).start()

    def check_vr_network(self):
        """检查VR网络"""
        logger.info('开始检查VR网络')
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        def inner():
            if device_id in devices_id_lst:
                try:
                    logger.debug(f'连接设备：{device_id}')
                    d = u2.connect(device_id)
                    logger.info('启动VR助手应用')
                    result = d.shell('am start -n com.microsoft.assistant.client/com.microsoft.assistant.client.MainActivity')
                    if result:
                        logger.info('VR助手页面打开成功')
                        self.textBrowser.append("页面打开成功！")
                    else:
                        logger.warning('VR助手页面打开失败')
                        self.textBrowser.append("页面打开失败！")
                except Exception as e:
                    logger.error(f'检查VR网络失败：{e}')
                    self.textBrowser.append(f"检查VR网络失败: {e}")
            else:
                logger.warning('设备未连接')
                self.textBrowser.append("设备未连接！")
        threading.Thread(target=inner).start()



    def switch_vr_env(self):
        """切换VR环境"""
        logger.info('尝试切换VR环境')
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        def inner():
            if device_id in devices_id_lst:
                try:
                    logger.debug(f'连接设备：{device_id}')
                    d = u2.connect(device_id)
                    logger.info('启动VR引擎模式活动')
                    d.shell('am start com.saicmotor.voiceservice/com.saicmotor.voiceagent.VREngineModeActivity')
                    logger.info('VR环境切换成功')
                except Exception as e:
                    logger.error(f'切换VR环境失败：{e}')
                    self.textBrowser.append(f"切换VR环境失败: {e}")
            else:
                logger.warning('设备未连接')
                self.textBrowser.append("设备未连接！")
        threading.Thread(target=inner).start()


    def scroll_to_bottom(self):
        scrollbar = self.textBrowser.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    @staticmethod
    def get_new_device_lst():  # 静态方法，返回设备ID列表
        result = subprocess.run("adb devices", shell=True, check=True, capture_output=True,
                                text=True)  # 执行 adb devices 命令
        devices = result.stdout.strip().split('\n')[1:]  # 获取设备列表
        device_ids = [line.split('\t')[0] for line in devices if line]  # 提取设备ID
        return device_ids

    # def show_pull_hulog_dialog(self):
    #     def run_commands_and_update(device_id, file_path):
    #         if device_id:
    #             command = f'adb -s {device_id} root && adb -s {device_id} shell "setprop bmi.service.adb.root 1" && adb -s {device_id} pull log {file_path}'
    #             process = subprocess.Popen(command, shell = True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
    #             for line in iter(process.stdout.readline, b''):  # 逐行读取输出
    #                 if line:
    #                     self.textBrowser.append(line.decode())
    #             return_code = process.wait()
    #             if return_code != 0:
    #                 self.textBrowser.append("日志文件拉取失败.")
    #             else:
    #                 self.textBrowser.append(f"日志文件已保存到 {file_path}")
    #         else:
    #             self.textBrowser.append("设备未连接！")
    #
    #     device_ids = self.get_new_device_lst()
    #     device_id = self.get_selected_device()
    #     if device_id in device_ids:
    #         file_path = QFileDialog.getExistingDirectory(self, "选择保存路径", os.getcwd())
    #         if file_path:
    #             threading.Thread(target = run_commands_and_update, args = (device_id, file_path)).start()
    #         else:
    #             self.textBrowser.append("已取消！")
    #     else:
    #         self.textBrowser.append("设备未连接！")


    def start_app_action(self):
        """启动应用"""
        logger.info('尝试启动应用')
        device_ids = self.get_new_device_lst()
        device_id = self.get_selected_device()
        if device_id in device_ids:
            logger.debug(f'连接设备：{device_id}')
            device = u2.connect(device_id)
            try:
                # 弹出对话框，请用户输入应用包名和活动名，格式为：包名: com.android.settings, 活动名:.MainSettings
                logger.debug('显示输入对话框')
                input_text, ok = QInputDialog.getText(self, '输入应用信息',
                                                      '请输入应用包名和活动名，格式为：包名: com.xxx.xxx, 活动名:.xxx')
                if ok and input_text:
                    # 解析输入的文本，获取包名和活动名
                    logger.debug(f'用户输入：{input_text}')
                    parts = input_text.split(', ')
                    package_name = parts[0].split('包名: ')[1]
                    activity_name = parts[1].split('活动名: ')[1]
                    if len(parts) >= 2:
                        logger.info(f'启动应用：{package_name}')
                        device.app_start(package_name, activity_name)
                        logger.info('应用启动成功')
                        self.textBrowser.append(f"应用 {package_name} 已启动")
                    else:
                        logger.warning('用户输入格式不正确')
                        self.textBrowser.append("输入的格式不正确，请按照格式输入：包名: com.xxx.xxx, 活动名:.xxx")
                else:
                    logger.info('用户取消输入或输入为空')
                    self.textBrowser.append("用户取消输入或输入为空")
            except Exception as e:
                logger.error(f'启动应用失败：{e}')
                self.textBrowser.append(f"启动应用失败: {e}")
        else:
            logger.warning('设备未连接')
            self.textBrowser.append("未连接设备！")


    def get_running_app_info(self):
        # 获取当前前景应用的版本号
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


    def view_apk_path_wrapper(self):
        logger.info('尝试查看应用安装路径')
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        try:
            if device_id in devices_id_lst:
                # 弹窗获取用户输入包名
                logger.debug('显示输入包名对话框')
                package_name, ok = QInputDialog.getText(self, "输入应用包名", "请输入要查看安装路径的应用包名：")
                if not ok:
                    logger.info('用户取消操作')
                    self.textBrowser.append("已取消！")
                else:
                    logger.info(f'查询应用 {package_name} 的安装路径')
                    cmd = f'pm path {package_name}'
                    logger.debug(f'连接设备：{device_id}')
                    d = u2.connect(device_id)
                    result = d.shell(cmd)
                    path = result.output.split('package:')[1].strip()
                    logger.info(f'获取到应用安装路径：{path}')
                    self.textBrowser.append(f"应用安装路径: {path}")
            else:
                logger.warning('设备未连接')
                self.textBrowser.append("未连接设备！")
        except Exception as e:
            logger.error(f'获取应用安装路径失败：{e}')
            self.textBrowser.append(f"获取应用安装路径失败: {e}")

    @staticmethod
    def run_cmd():
        user_directory = os.path.expanduser("~")
        subprocess.Popen(["start", "cmd", "/k", "cd /d " + user_directory], shell=True)

    def refresh_devices(self):
        # 刷新设备列表并添加到下拉框
        logger.info('开始刷新设备列表')
        def inner():
            try:
                # 执行 adb devices 命令
                logger.debug('执行adb devices命令')
                result = subprocess.run("adb devices", shell=True, check=True, capture_output=True, text=True)
                devices = result.stdout.strip().split('\n')[1:]  # 获取设备列表
                device_ids = [line.split('\t')[0] for line in devices if line]  # 提取设备ID
                logger.debug(f'找到的设备：{device_ids}')

                # 清空 ComboxButton 并添加新的设备ID
                logger.debug('更新设备列表下拉框')
                self.ComboxButton.clear()
                for device_id in device_ids:
                    self.ComboxButton.addItem(device_id)

                # 将设备ID列表转换为字符串并更新到textBrowser
                device_ids_str = ", ".join(device_ids)
                if device_ids_str:
                    logger.info(f'设备列表刷新成功：{device_ids_str}')
                    self.textBrowser.append(f"设备列表已刷新：\n{device_ids_str}")
                    return device_ids  # 返回设备ID列表
                else:
                    logger.warning('未发现已连接的设备')
                    self.textBrowser.append(f"未连接设备！")
                    return device_ids  # 返回设备ID列表
            except subprocess.CalledProcessError as e:
                logger.error(f'刷新设备列表失败：{e}')
                self.textBrowser.append(f"刷新设备列表失败: {e}")
                return []  # 返回空列表表示刷新失败
        threading.Thread(target=inner).start()  # 异步执行

    def adb_root_wrapper(self):
        logger.info('尝试执行ADB root操作')
        def inner():
            device_id = self.get_selected_device()
            if device_id:
                logger.debug(f'对设备 {device_id} 执行root操作')
                res = adb_root(device_id)  # 传入下拉框选择的设备ID
                self.textBrowser.append(res)
            else:
                logger.warning('设备未连接')
                self.textBrowser.append("设备未连接！")
        threading.Thread(target=inner).start()  # 异步执行

    def reboot_device(self):
        logger.info('尝试重启设备')
        device_id = self.get_selected_device()
        device_ids = self.get_new_device_lst()
        if device_id in device_ids:
            # 弹出对话框询问是否要重启设备
            logger.debug('显示重启确认对话框')
            dig = QMessageBox.question(self, "重启设备", "是否要重启设备？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if dig == QMessageBox.Yes:
                logger.info('用户确认重启设备')
                def inner():
                    try:
                        # 执行 adb reboot 命令
                        logger.debug(f'执行重启命令：adb -s {device_id} reboot')
                        result = subprocess.run(
                            f"start /b adb -s {device_id} reboot",
                            shell = True,  # 执行命令
                            check = True,  # 检查命令是否成功
                            stdout = subprocess.PIPE,  # 捕获输出
                            stderr = subprocess.PIPE  # 捕获错误
                        )
                        # 不要用print，会导致UI卡死，用textBrowser.append
                        if "not found" not in str(result.stdout.decode('utf-8')):
                            logger.info(f'设备 {device_id} 重启成功')
                            self.textBrowser.append(f"设备 {device_id} 已重启！")
                        elif "not found" in result.stdout.decode('utf-8'):
                            logger.warning('需要先执行root操作')
                            self.adb_root_wrapper()
                            self.reboot_device()
                    except Exception as e:
                        logger.error(f'重启设备失败：{e}')
                        self.textBrowser.append(f"重启设备失败: {e}")
                threading.Thread(target=inner).start()  # 异步执行
            else:
                logger.info('用户取消重启操作')
        else:
            logger.warning('设备未连接')
            self.textBrowser.append("未连接设备！")

    def show_screenshot_dialog(self):
        logger.info('尝试获取设备截图')
        def inner():
            device_id = self.get_selected_device()
            devices_id_lst = self.get_new_device_lst()
            if device_id in devices_id_lst:
                logger.debug('显示保存截图对话框')
                file_path, _ = QFileDialog.getSaveFileName(self, "保存截图", "", "PNG Files (*.png);;All Files (*)")
                if file_path:
                    logger.info(f'开始获取截图，保存路径：{file_path}')
                    res = get_screenshot(file_path, device_id)
                    self.textBrowser.append(res)
                else:
                    logger.info('用户取消保存截图')
            else:
                logger.warning('设备未连接')
                self.textBrowser.append("未连接设备！")
        threading.Thread(target=inner).start()  # 异步执行


    def show_uninstall_dialog(self):
        logger.info('尝试卸载应用')
        def inner():
            device_id = self.get_selected_device()
            devices_id_lst = self.get_new_device_lst()
            if device_id in devices_id_lst:
                logger.debug('显示输入包名对话框')
                package_name, ok = QInputDialog.getText(self, "输入应用包名", "请输入要卸载的应用包名：")
                if ok and package_name:
                    logger.info(f'开始卸载应用：{package_name}')
                    res = adb_uninstall(package_name, device_id)
                    self.textBrowser.append(res)
                else:
                    logger.info('用户取消卸载操作')
            else:
                logger.warning('设备未连接')
                self.textBrowser.append("未连接设备！")
        threading.Thread(target=inner).start()  # 异步执行

    def show_pull_file_dialog(self):
        logger.info('尝试从设备拉取文件')
        def inner():
            device_id = self.get_selected_device()
            devices_id_lst = self.get_new_device_lst()
            if device_id in devices_id_lst:
                logger.debug('显示输入文件路径对话框')
                file_path_on_device, ok = QInputDialog.getText(self, "输入设备文件路径", "请输入车机上的文件路径:")
                if ok and file_path_on_device:
                    logger.debug('显示保存文件对话框')
                    local_path, _ = QFileDialog.getSaveFileName(self, "保存文件", "", "All Files (*)")
                    if local_path:
                        logger.info(f'开始拉取文件，设备路径：{file_path_on_device}，本地路径：{local_path}')
                        res = adb_pull_file(file_path_on_device, local_path, device_id)
                        self.textBrowser.append(" ".join(res))
                    else:
                        logger.info('用户取消选择保存路径')
                else:
                    logger.info('用户取消输入文件路径')
            else:
                logger.warning('设备未连接')
                self.textBrowser.append("未连接设备！")
        threading.Thread(target=inner).start()  # 异步执行


    def show_install_file_dialog(self):
        logger.info('尝试安装应用')
        def inner():
            device_id = self.get_selected_device()
            devices_id_lst = self.get_new_device_lst()
            if device_id in devices_id_lst:
                logger.debug('显示选择安装包对话框')
                package_path, _ = QFileDialog.getOpenFileName(self, "选择应用安装包", "",
                                                              "APK Files (*.apk);;All Files (*)")
                if package_path:
                    logger.info(f'选择的安装包路径：{package_path}')
                    def inner():
                        logger.debug(f'开始安装应用到设备：{device_id}')
                        res = adb_install(package_path, device_id)
                        self.textBrowser.append(res)
                    threading.Thread(target=inner).start()  # 异步执行
                    self.textBrowser.append("即将开始安装应用，请耐心等待...")
                else:
                    logger.info('用户取消选择安装包')
            else:
                logger.warning('设备未连接')
                self.textBrowser.append("未连接设备！")
        threading.Thread(target=inner).start()  # 异步执行

    def show_pull_log_without_clear_dialog(self):
        logger.info('尝试拉取日志（不清除）')
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            logger.info('开始拉取日志')
            self.textBrowser.append("即将开始拉取 log，如需停止，请手动关闭此窗口。")
            logger.debug('显示保存日志对话框')
            file_path, _ = QFileDialog.getSaveFileName(self, "保存 log", "", "txt Files (*.txt);;All Files (*)")
            if file_path:
                logger.info(f'开始拉取日志到：{file_path}')
                pull_log_without_clear(file_path, device_id)
            else:
                logger.info('用户取消保存日志')
        else:
            logger.warning('设备未连接')
            self.textBrowser.append("未连接设备！")

    def show_pull_log_with_clear_dialog(self):
        logger.info('尝试拉取日志（清除）')
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            logger.debug('显示保存日志对话框')
            file_path, _ = QFileDialog.getSaveFileName(self, "保存 log", "", "txt Files (*.txt);;All Files (*)")
            if file_path:
                logger.info(f'开始拉取日志到：{file_path}')
                pull_log_with_clear(file_path, device_id)
            else:
                logger.info('用户取消保存日志')
        else:
            logger.warning('设备未连接')
            self.textBrowser.append("未连接设备！")

    def show_push_file_dialog(self):
        logger.info('尝试推送文件到设备')
        def inner():
            device_id = self.get_selected_device()
            devices_id_lst = self.get_new_device_lst()
            if device_id in devices_id_lst:
                logger.debug('显示选择本地文件对话框')
                local_file_path, _ = QFileDialog.getOpenFileName(self, "选择本地文件", "", "All Files (*)")
                if local_file_path:
                    logger.debug('显示输入设备路径对话框')
                    target_path_on_device, ok = QInputDialog.getText(self, "输入设备文件路径",
                                                                     "请输入车机上的目标路径:")
                    if ok and target_path_on_device:
                        logger.info(f'开始推送文件，本地路径：{local_file_path}，设备路径：{target_path_on_device}')
                        res = adb_push_file(local_file_path, target_path_on_device, device_id)
                        self.textBrowser.append(res)
                    else:
                        logger.info('用户取消输入设备路径')
                else:
                    logger.info('用户取消选择本地文件')
            else:
                logger.warning('设备未连接')
                self.textBrowser.append("未连接设备！")
        threading.Thread(target=inner).start()  # 异步执行

    def show_simulate_click_dialog(self):  # 模拟点击
        logger.info('尝试模拟点击操作')
        def inner():
            device_id = self.get_selected_device()
            device_id_lst = self.get_new_device_lst()
            if device_id in device_id_lst:
                logger.debug('显示输入X坐标对话框')
                x, ok = QInputDialog.getInt(self, "输入 X 坐标", "请输入点击的 X 坐标:")
                if ok:
                    logger.debug('显示输入Y坐标对话框')
                    y, ok = QInputDialog.getInt(self, "输入 Y 坐标", "请输入点击的 Y 坐标:")
                    if ok:
                        logger.info(f'执行点击操作，坐标：({x}, {y})')
                        res = simulate_click(x, y, device_id)
                        self.textBrowser.append(res)
                    else:
                        logger.info('用户取消输入Y坐标')
                else:
                    logger.info('用户取消输入X坐标')
            else:
                logger.warning('设备未连接')
                self.textBrowser.append("未连接设备！")
        threading.Thread(target=inner).start()  # 异步执行

    # def show_simulate_swipe_dialog(self):  # 模拟滑动
    #     def inner():
    #         try:
    #             device_id = self.get_selected_device()
    #             devices_id_lst = self.get_new_device_lst()
    #             if device_id in devices_id_lst:
    #                 # 弹出一个输入框让用户一次性输入所有坐标共四个整数
    #                 input_text, ok = QInputDialog.getText(self, "输入坐标", "请输入滑动的起始坐标和终止坐标，格式为：x1,y1,x2,y2:")
    #                 if ok and input_text:
    #                     parts = input_text.split(',')
    #                     if len(parts) == 4:
    #                         x1, y1, x2, y2 = [int(part) for part in parts]
    #                         res = simulate_swipe(x1, y1, x2, y2, 500, device_id)
    #                         self.textBrowser.append(res)
    #             else:
    #                 self.textBrowser.append("未连接设备！")
    #         except Exception as e:
    #             self.textBrowser.append(f"模拟滑动失败: {e}")
    #     threading.Thread(target=inner).start()  # 异步执行

    def show_simulate_long_press_dialog(self):
        logger.info('尝试模拟长按操作')
        def inner():
            device_id = self.get_selected_device()
            devices_id_lst = self.get_new_device_lst()
            if device_id in devices_id_lst:
                logger.debug('显示输入坐标和时间对话框')
                input_text, ok = QInputDialog.getText(self, "输入坐标和长按时间", "请输入长按的坐标和长按时间，格式为：x,y,时间:")
                if ok and input_text:
                    logger.debug(f'用户输入：{input_text}')
                    parts = input_text.split(',')
                    if len(parts) == 3:
                        x, y, duration = [int(part) for part in parts]
                        logger.info(f'执行长按操作，坐标：({x}, {y})，持续时间：{duration}ms')
                        res = simulate_long_press(x, y, duration, device_id)
                        self.textBrowser.append(res)
                    else:
                        logger.warning('输入格式不正确')
                else:
                    logger.info('用户取消输入')
            else:
                logger.warning('设备未连接')
                self.textBrowser.append("未连接设备！")
        threading.Thread(target=inner).start()  # 异步执行

    def show_input_text_dialog(self):
        logger.info('尝试通过ADB输入文本')
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            logger.debug('显示输入文本对话框')
            text_to_input, ok = QInputDialog.getText(self, "输入文本", "请输入要通过 ADB 输入的文本:")
            if ok and text_to_input:
                logger.info(f'开始输入文本：{text_to_input}')
                lst = input_text_via_adb(text_to_input, device_id)
                self.textBrowser.append(lst)
            else:
                logger.info('用户取消输入文本')
        else:
            logger.warning('设备未连接')
            self.textBrowser.append("未连接设备！")

    def show_force_stop_app_dialog(self):
        logger.info('尝试强制停止应用')
        def inner():
            try:
                device_id = self.get_selected_device()
                devices_id_lst = self.get_new_device_lst()
                if device_id in devices_id_lst:
                    logger.debug('获取前台应用包名')
                    package_name = self.get_foreground_package(is_direct_call=False)
                    if package_name:
                        logger.info(f'准备强制停止应用：{package_name}')
                        adb_command = f"adb -s {device_id} shell am force-stop {package_name}"
                        try:
                            subprocess.run(adb_command, shell=True, check=True)
                            logger.info(f'成功强制停止应用：{package_name}')
                            self.textBrowser.append(f"成功强制停止 {package_name} 应用在设备 {device_id} 上")
                        except subprocess.CalledProcessError as e:
                            logger.error(f'强制停止应用失败：{e}')
                            self.textBrowser.append(f"强制停止 {package_name} 应用在设备 {device_id} 上失败: {e}")
                    else:
                        logger.warning('未获取到前台应用包名')
                else:
                    logger.warning('设备未连接')
                    self.textBrowser.append("未连接设备！")
            except Exception as e:
                logger.error(f'强制停止应用失败：{e}')
                self.textBrowser.append(f"强制停止应用失败: {e}")
        threading.Thread(target=inner).start()  # 异步执行

    def show_clear_app_cache_dialog(self):
        logger.info('显示清除应用缓存对话框')
        device_id = self.get_selected_device()
        logger.debug(f'获取到设备ID：{device_id}')
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            logger.debug(f'尝试连接设备：{device_id}')
            d = u2.connect(device_id)
            package_name = self.get_foreground_package(is_direct_call=False)
            logger.debug(f'获取到前台应用包名：{package_name}')
            if package_name:
                result = clear_app_cache(d, package_name)
                logger.info(f'清除缓存结果：{result}')
                self.textBrowser.append(result)
            else:
                logger.warning('未获取到前台应用包名')
                self.textBrowser.append("未获取到前台应用包名")
        else:
            logger.warning('设备未连接')
            self.textBrowser.append("设备未连接！")

    def get_foreground_package(self, is_direct_call = True):
        logger.info('开始获取前台应用包名')
        result_queue = queue.Queue()  # 创建一个队列用于存储结果
        def inner():
            device_id = self.get_selected_device()
            logger.debug(f'获取到设备ID：{device_id}')
            devices_id_lst = self.get_new_device_lst()
            if device_id in devices_id_lst:  # 检查选择的设备是否在设备列表中
                try:
                    logger.debug(f'尝试连接设备：{device_id}')
                    device = u2.connect(device_id)
                    if device:
                        logger.info('设备连接成功，获取当前应用信息')
                        current_app = device.app_current()  # 获取当前正在运行的应用
                        if current_app:
                            package_name = current_app['package']
                            activity_name = current_app['activity']
                            logger.info(f'获取到应用信息：包名={package_name}, 活动名={activity_name}')
                            if is_direct_call:  # 如果是直接调用
                                self.textBrowser.append(f"包名: {package_name}, 活动名: {activity_name}")
                            result_queue.put(package_name)  # 将结果放入队列
                        else:
                            logger.warning('未找到正在运行的应用')
                            self.textBrowser.append("未找到正在运行的应用包名")
                            result_queue.put(None)  # 将结果放入队列，表示未找到
                    else:
                        logger.error('设备连接失败')
                        self.textBrowser.append("设备连接失败")
                        result_queue.put(None)  # 将结果放入队列，表示连接失败
                except Exception as e:
                    logger.error(f'获取前台应用信息失败：{str(e)}')
                    self.textBrowser.append(f"获取前台正在运行的应用包名失败: {e}")
                    result_queue.put(None)  # 将结果放入队列，表示获取失败
            else:
                logger.warning('设备未连接')
                self.textBrowser.append("未连接设备！")
                result_queue.put(None)  # 将结果放入队列，表示设备断开

        threading.Thread(target = inner).start()
        return result_queue.get()  # 在主线程中获取队列中的结果


    def aapt_getpackage_name_dilog(self):
        logger.info('显示获取APK包名对话框')
        file_path, _ = QFileDialog.getOpenFileName(self, "选择APK文件", "", "APK文件 (*.apk)")
        logger.debug(f'选择的APK文件路径：{file_path}')
        if file_path:
            package_name = aapt_get_packagen_name(file_path)
            logger.info(f'获取到包名：{package_name}')
            self.textBrowser.append(f"包名: {package_name}")
        else:
            logger.warning('未选择APK文件')
            self.textBrowser.append("未选择APK文件")

    def d_list(self):
        logger.info('初始化设备列表')
        devices_id_lst = self.get_new_device_lst()
        logger.debug(f'获取到设备列表：{devices_id_lst}')
        if devices_id_lst:
            for device_id in devices_id_lst:
                logger.debug(f'尝试连接设备：{device_id}')
                try:
                    d = u2.connect(device_id)
                    logger.info(f'设备{device_id}连接成功')
                except Exception as e:
                    logger.error(f'设备{device_id}连接失败：{str(e)}')
        else:
            logger.warning('未找到任何设备')


    @staticmethod
    def stop_program():
        sys.exit()

if __name__ == '__main__':
    app = ADB_Mainwindow().MZS3E_TT_enter_engineering_mode()