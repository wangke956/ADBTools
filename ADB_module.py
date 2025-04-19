import time
from PyQt5.QtWidgets import (QMainWindow, QFileDialog, QInputDialog, QMessageBox)
import sys
import io
import subprocess
import queue
from PyQt5.QtCore import QThread, pyqtSignal
from adb_root_wrapper_thread import AdbRootWrapperThread

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


# noinspection DuplicatedCode
class ADB_Mainwindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(ADB_Mainwindow, self).__init__(parent)
        self.Force_app_thread = None
        self.uninstall_thread = None
        self.reboot_thread = None
        self.view_apk_thread = None
        self.skip_power_limit_thread = None
        self.upgrade_page_thread = None
        self.update_thread = None
        self.adb_root_thread = None
        self.get_running_app_info_thread = None
        self.check_vr_env_thread = None
        self.mzs3ett_thread = None
        self.check_vr_network_thread = None
        self.vr_thread = None
        self.setupUi(self)
        # 添加按钮点击间隔控制和线程锁
        self._last_click_time = {}
        self._click_interval = 1.0  # 设置点击间隔为1秒
        self._thread_locks = {}
        self.d = None
        self.list_package_thread = None
        self.input_keyevent_287_thread = None
        self.engineering_thread = None
        self.app_action_thread = None
        # 重定向输出流为textBrowser
        self.text_edit_output_stream = TextEditOutputStream(self.textBrowser)
        sys.stdout = self.text_edit_output_stream
        sys.stderr = self.text_edit_output_stream
        if self.refresh_devices():  # 刷新设备列表
            self.d = u2.connect(self.get_selected_device())
            self.textBrowser.append(f"已连接设备: {self.get_selected_device()}")
        else:
            pass
        self.ComboxButton.activated[str].connect(self.on_combobox_changed)
        self.view_apk_path.clicked.connect(self.view_apk_path_wrapper)  # 显示应用安装路径
        self.input_text_via_adb_button.clicked.connect(self.show_input_text_dialog)  # 输入文本
        self.get_screenshot_button.clicked.connect(self.show_screenshot_dialog)  # 截图
        self.force_stop_app.clicked.connect(self.show_force_stop_app_dialog)  # 强制停止应用
        self.adb_uninstall_button.clicked.connect(self.show_uninstall_dialog)  # 卸载应用
        self.adb_pull_file_button.clicked.connect(self.show_pull_file_dialog)  # 拉取文件
        self.reboot_adb_service_button.clicked.connect(self.show_simulate_long_press_dialog)  # 模拟长按

        self.adb_install_button.clicked.connect(self.show_install_file_dialog)  # 安装应用
        self.clear_app_cache_button.clicked.connect(self.show_clear_app_cache_dialog)  # 清除应用缓存
        self.app_package_and_activity.clicked.connect(lambda: self.get_foreground_package(is_direct_call=True))
        self.pull_log_without_clear.clicked.connect(self.show_pull_log_without_clear_dialog)  # 拉取日志（不清除）
        self.pull_log_with_clear_button.clicked.connect(self.show_pull_log_with_clear_dialog)  # 拉取日志（清除）
        self.simulate_click_button.clicked.connect(self.show_simulate_click_dialog)  # 模拟点击
        self.adb_push_file_button.clicked.connect(self.show_push_file_dialog)  # 推送文件
        self.adbbutton.clicked.connect(self.run_cmd)  # 执行 adb 命令
        self.button_reboot.clicked.connect(self.reboot_device)  # 重启设备
        self.RefreshButton.clicked.connect(self.refresh_devices)  # 刷新设备列表
        self.adb_root_button.clicked.connect(self.adb_root_wrapper)  # 以 root 权限运行 ADB
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
        self.upgrade_page_button_2.clicked.connect(self.as33_upgrade_page)  # 打开延峰升级页面
        self.MZS3E_TT_enter_engineering_mode_button.clicked.connect(
            self.MZS3E_TT_enter_engineering_mode)  # MZS3E_TT进入工程模式
        self.AS33_CR_enter_engineering_mode_button.clicked.connect(self.AS33_CR_enter_engineering_mode)
        self.open_update_page_button.clicked.connect(self.open_update_page)  # 打开资源升级页面
        # self.d_list()  # 设备列表初始化

    # 调起资源升级页面
    def open_update_page(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            try:
                from update_thread import UpdateThread
                self.update_thread = UpdateThread(self.d)
                self.update_thread.progress_signal.connect(self.textBrowser.append)
                self.update_thread.error_signal.connect(self.textBrowser.append)
                self.update_thread.start()
            except Exception as e:
                self.textBrowser.append(f"启动更新页面线程失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")
        return

    def on_combobox_changed(self, text):
        self.d = u2.connect(text)
        if self.d:
            self.textBrowser.append(f"已连接设备: {text}")
        else:
            self.textBrowser.append(f"连接设备 {text} 失败！")

    def get_selected_device(self):
        return self.ComboxButton.currentText()  # 返回的类型为str

    @staticmethod
    def get_new_device_lst():  # 静态方法，返回设备ID列表
        result = subprocess.run("adb devices", shell=True, check=True, capture_output=True,
                                text=True)  # 执行 adb devices 命令
        devices = result.stdout.strip().split('\n')[1:]  # 获取设备列表
        device_ids = [line.split('\t')[0] for line in devices if line]  # 提取设备ID
        return device_ids

    def start_app_action(self):
        device_ids = self.get_new_device_lst()
        device_id = self.get_selected_device()
        if device_id in device_ids:
            try:
                input_text, ok = QInputDialog.getText(self, '输入应用信息',
                                                      '请输入应用包名和活动名，格式为：包名: com.xxx.xxx, 活动名:.xxx')
                if ok and input_text:
                    parts = input_text.split(', ')
                    package_name = parts[0].split('包名: ')[1]
                    activity_name = parts[1].split('活动名: ')[1]
                    from app_action_thread import AppActionThread
                    self.app_action_thread = AppActionThread(self.d, package_name, activity_name)
                    self.app_action_thread.progress_signal.connect(self.textBrowser.append)
                    self.app_action_thread.error_signal.connect(self.textBrowser.append)
                    self.app_action_thread.start()
                else:
                    self.textBrowser.append("用户取消输入或输入为空")
            except Exception as e:
                self.textBrowser.append(f"启动应用失败: {e}")
        else:
            self.textBrowser.append("未连接设备！")

    def AS33_CR_enter_engineering_mode(self):
        """AS33_CR进入工程模式"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            try:
                from engineering_mode_thread import EngineeringModeThread
                self.engineering_thread = EngineeringModeThread(self.d)
                self.engineering_thread.progress_signal.connect(self.textBrowser.append)
                self.engineering_thread.result_signal.connect(self.textBrowser.append)
                self.engineering_thread.error_signal.connect(self.textBrowser.append)
                self.engineering_thread.start()
            except Exception as e:
                self.textBrowser.append(f"启动工程模式线程失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def MZS3E_TT_enter_engineering_mode(self):
        """MZS3E_TT进入工程模式"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            try:
                from mzs3e_tt_thread import MZS3E_TTEngineeringModeThread
                self.mzs3ett_thread = MZS3E_TTEngineeringModeThread(self.d)
                self.mzs3ett_thread.progress_signal.connect(self.textBrowser.append)
                self.mzs3ett_thread.error_signal.connect(self.textBrowser.append)
                self.mzs3ett_thread.start()
            except Exception as e:
                self.textBrowser.append(f"启动MZS3E_TT工程模式线程失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def enter_engineering_mode(self):

        """进入工程模式"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            try:
                from enter_engineering_mode_thread import enter_engineering_mode_thread
                self.engineering_thread = enter_engineering_mode_thread(self.d)
                self.engineering_thread.progress_signal.connect(self.textBrowser.append)
                self.engineering_thread.result_signal.connect(self.textBrowser.append)
                self.engineering_thread.error_signal.connect(self.textBrowser.append)
                self.engineering_thread.start()
            except Exception as e:
                self.textBrowser.append(f"启动工程模式线程失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

        # if device_id in devices_id_lst:
        #     try:
        #         d = u2.connect(device_id)
        #         result = d.app_start("com.saicmotor.hmi.engmode",
        #                              "com.saicmotor.hmi.engmode.home.ui.EngineeringModeActivity")
        #         return result
        #     except Exception as e:
        #         self.textBrowser.append(f"进入工程模式失败: {e}")
        # else:
        #     self.textBrowser.append("设备未连接！")

    def skip_power_limit(self):
        """跳过电源挡位限制"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            try:
                from skip_power_limit_thread import SkipPowerLimitThread
                self.skip_power_limit_thread = SkipPowerLimitThread(device_id)
                self.skip_power_limit_thread.progress_signal.connect(self.textBrowser.append)
                self.skip_power_limit_thread.error_signal.connect(self.textBrowser.append)
                self.skip_power_limit_thread.start()
            except Exception as e:
                self.textBrowser.append(f"启动跳过电源限制线程失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def list_package(self):
        """获取设备上安装的应用列表"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        findstr = self.Findstr.toPlainText()

        if device_id in devices_id_lst:
            try:
                from list_package_thread import ListPackageThread
                # 创建并启动线程
                self.list_package_thread = ListPackageThread(self.d, findstr)

                # 连接信号
                self.list_package_thread.progress_signal.connect(self.textBrowser.append)
                self.list_package_thread.result_signal.connect(
                    lambda results: self.textBrowser.append('\n'.join(results)))
                self.list_package_thread.finished_signal.connect(self.textBrowser.append)
                self.list_package_thread.error_signal.connect(self.textBrowser.append)

                # 启动线程
                self.list_package_thread.start()
            except Exception as e:
                self.textBrowser.append(f"启动应用列表获取线程失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def activate_vr(self):
        """激活VR"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            try:
                from vr_thread import VRActivationThread
                self.vr_thread = VRActivationThread(device_id)
                self.vr_thread.progress_signal.connect(self.textBrowser.append)
                self.vr_thread.result_signal.connect(self.textBrowser.append)
                self.vr_thread.error_signal.connect(self.textBrowser.append)
                self.vr_thread.start()
            except Exception as e:
                self.textBrowser.append(f"启动VR激活线程失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def as33_upgrade_page(self):
        """升级页面"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            try:
                from as33_upgrade_page_thread import AS33UpgradePageThread
                self.upgrade_page_thread = AS33UpgradePageThread(self.d)
                self.upgrade_page_thread.progress_signal.connect(self.textBrowser.append)
                self.upgrade_page_thread.error_signal.connect(self.textBrowser.append)
                self.upgrade_page_thread.start()
            except Exception as e:
                self.textBrowser.append(f"启动升级页面线程失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def check_vr_network(self):
        """检查VR网络"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            try:
                from check_vr_network_thread import CheckVRNetworkThread
                self.check_vr_network_thread = CheckVRNetworkThread(self.d)
                self.check_vr_network_thread.progress_signal.connect(self.textBrowser.append)
                self.check_vr_network_thread.result_signal.connect(self.textBrowser.append)
                self.check_vr_network_thread.error_signal.connect(self.textBrowser.append)
                self.check_vr_network_thread.start()
            except Exception as e:
                self.textBrowser.append(f"检查VR网络失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def switch_vr_env(self):
        """切换VR环境"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            try:
                from switch_vr_env_thread import SwitchVrEnvThread
                self.check_vr_env_thread = SwitchVrEnvThread(self.d)
                self.check_vr_env_thread.progress_signal.connect(self.textBrowser.append)
                self.check_vr_env_thread.result_signal.connect(self.textBrowser.append)
                self.check_vr_env_thread.error_signal.connect(self.textBrowser.append)
                self.check_vr_env_thread.start()
            except Exception as e:
                self.textBrowser.append(f"切换VR环境失败: {e}")
            #     self.d.shell('am start com.saicmotor.voiceservice/com.saicmotor.voiceagent.VREngineModeActivity')
            # except Exception as e:
            #     self.textBrowser.append(f"切换VR环境失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def scroll_to_bottom(self):
        scrollbar = self.textBrowser.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def get_running_app_info(self):
        # 获取当前前景应用的版本号
        device_id = self.get_selected_device()  # 获取当前选定的设备ID
        devices_id_lst = self.get_new_device_lst()
        package_name = self.get_foreground_package(is_direct_call=False)  # 传入 device_id 获取包名
        if device_id in devices_id_lst:
            from get_running_app_info_thread import GetRunningAppInfoThread
            self.get_running_app_info_thread = GetRunningAppInfoThread(self.d, package_name)
            self.get_running_app_info_thread.progress_signal.connect(self.textBrowser.append)
            self.get_running_app_info_thread.result_signal.connect(self.textBrowser.append)
            self.get_running_app_info_thread.error_signal.connect(self.textBrowser.append)
            self.get_running_app_info_thread.start()
            # if package_name:
            #     try:
            #         # 获取应用信息
            #         app_info = self.d.app_info(package_name)
            #         if app_info:
            #             version_name = app_info.get('versionName', '未知版本')
            #             self.textBrowser.append(f"应用 {package_name} 版本号: {version_name}")
            #         else:
            #             self.textBrowser.append("无法获取应用信息")
            #     except Exception as e:
            #         self.textBrowser.append(f"获取应用信息失败: {e}")
            # else:
            #     self.textBrowser.append("未获取到当前前景应用的包名")
        else:
            self.textBrowser.append("设备未连接！")

    def view_apk_path_wrapper(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        try:
            if device_id in devices_id_lst:
                package_name, ok = QInputDialog.getText(self, "输入应用包名", "请输入要查看安装路径的应用包名：")
                if not ok:
                    self.textBrowser.append("已取消！")
                    return
                from view_apk_path_wrapper_thread import ViewApkPathWrapperThread
                self.view_apk_thread = ViewApkPathWrapperThread(device_id, package_name)
                self.view_apk_thread.progress_signal.connect(self.textBrowser.append)
                self.view_apk_thread.result_signal.connect(self.textBrowser.append)
                self.view_apk_thread.error_signal.connect(self.textBrowser.append)
                self.view_apk_thread.start()
            else:
                self.textBrowser.append("未连接设备！")
        except Exception as e:
            self.textBrowser.append(f"初始化线程失败: {e}")

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
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            try:
                self.adb_root_thread = AdbRootWrapperThread(device_id)
                self.adb_root_thread.progress_signal.connect(self.textBrowser.append)
                self.adb_root_thread.error_signal.connect(self.textBrowser.append)
                self.adb_root_thread.start()
            except Exception as e:
                self.textBrowser.append(f"获取root权限失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def reboot_device(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            reply = QMessageBox.question(
                self, 
                '确认重启',
                '确定要重启设备吗？此操作不可逆！',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                try:
                    from reboot_device_thread import RebootDeviceThread
                    self.reboot_thread = RebootDeviceThread(device_id)
                    self.reboot_thread.progress_signal.connect(self.textBrowser.append)
                    self.reboot_thread.error_signal.connect(self.textBrowser.append)
                    self.reboot_thread.start()
                except Exception as e:
                    self.textBrowser.append(f"启动设备重启线程失败: {e}")
            else:
                self.textBrowser.append("用户取消重启操作")
        else:
            self.textBrowser.append("设备未连接！")

    @staticmethod
    def get_screenshot(file_path, device_id):
        command = f"adb -s {device_id} shell screencap -p /sdcard/screenshot.png && adb -s {device_id} pull /sdcard/screenshot.png {file_path} && adb -s {device_id} shell rm /sdcard/screenshot.png"
        try:
            subprocess.run(command, shell=True, check=True)
            return f"截图已保存到 {file_path}"
        except subprocess.CalledProcessError as e:
            return f"截图失败: {e}"

    def show_screenshot_dialog(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            file_path, _ = QFileDialog.getSaveFileName(self, "保存截图", "", "PNG Files (*.png);;All Files (*)")
            if file_path:
                # res = self.get_screenshot(file_path, device_id)
                command = f"adb -s {device_id} shell screencap -p /sdcard/screenshot.png && adb -s {device_id} pull /sdcard/screenshot.png {file_path} && adb -s {device_id} shell rm /sdcard/screenshot.png"
                # res = self.d.shell(command)
                res = subprocess.run(command, shell=True, check=True)
                self.textBrowser.append(res.stdout)
            else:
                self.textBrowser.append("已取消！")
        else:
            self.textBrowser.append("未连接设备！")

    @staticmethod
    def adb_uninstall(package_name, device_id):
        command = f"adb -s {device_id} uninstall {package_name}"
        try:
            subprocess.run(command, shell=True, check=True)
            return f"应用 {package_name} 已卸载"
        except subprocess.CalledProcessError as e:
            return f"卸载应用失败: {e}"

    def show_uninstall_dialog(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            package_name, ok = QInputDialog.getText(self, "输入应用包名", "请输入要卸载的应用包名：")
            if ok and package_name:
                from show_uninstall_thread import ShowUninstallThread
                self.uninstall_thread = ShowUninstallThread(self.d, package_name)
                self.uninstall_thread.progress_signal.connect(self.textBrowser.append)
                self.uninstall_thread.result_signal.connect(self.textBrowser.append)
                self.uninstall_thread.error_signal.connect(self.textBrowser.append)
                self.uninstall_thread.start()
                # res = self.adb_uninstall(package_name, device_id)
                # self.textBrowser.append(res)
            else:
                self.textBrowser.append("已取消！")
        else:
            self.textBrowser.append("未连接设备！")

    @staticmethod
    def adb_pull_file(file_path_on_device, local_path, device_id):
        command = f"adb -s {device_id} pull {file_path_on_device} {local_path}"
        res = subprocess.run(command,
                             shell=True,
                             check=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             text=True)
        try:
            string = res.stdout.strip()
            return ["文件拉取成功！", string]
        except subprocess.CalledProcessError as e:
            return f"文件拉取失败: {e}"

    def show_pull_file_dialog(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            file_path_on_device, ok = QInputDialog.getText(self, "输入设备文件路径", "请输入车机上的文件路径:")
            if ok and file_path_on_device:
                local_path, _ = QFileDialog.getSaveFileName(self, "保存文件", "", "All Files (*)")
                if local_path:
                    # res = self.adb_pull_file(file_path_on_device, local_path, device_id)
                    res = self.d.pull(file_path_on_device, local_path)
                    self.textBrowser.append(" ".join(res))
                else:
                    self.textBrowser.append("已取消！")
            else:
                self.textBrowser.append("已取消！")
        else:
            self.textBrowser.append("未连接设备！")

    @staticmethod
    def adb_install(package_path, device_id):
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
                return f"应用安装成功！{res.stdout.strip()}"
            except subprocess.CalledProcessError as e:
                return f"应用安装失败: {e.stderr.strip()}"
        else:
            return "设备未连接！"

    def show_install_file_dialog(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            package_path, _ = QFileDialog.getOpenFileName(self, "选择应用安装包", "",
                                                          "APK Files (*.apk);;All Files (*)")
            if package_path:
                res = self.adb_install(package_path, device_id)
                self.textBrowser.append(res)
                self.textBrowser.append("即将开始安装应用，请耐心等待...")
            else:
                self.textBrowser.append("已取消！")
        else:
            self.textBrowser.append("未连接设备！")

    def show_pull_log_without_clear_dialog(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            self.textBrowser.append("即将开始拉取 log，如需停止，请手动关闭此窗口。")
            file_path, _ = QFileDialog.getSaveFileName(self, "保存 log", "", "txt Files (*.txt);;All Files (*)")
            if file_path:
                self.pull_log_without_clear(file_path, device_id)
            else:
                self.textBrowser.append("已取消！")
        else:
            self.textBrowser.append("未连接设备！")

    @staticmethod
    def pull_log_with_clear(file_path, device_id):
        subprocess.run(f'adb -s {device_id} logcat -c', shell=True)
        command = f'cmd /k "adb -s {device_id} shell logcat > {file_path}"'
        process = subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE)
        while True:
            if process.poll() is not None:
                break

    def show_pull_log_with_clear_dialog(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            file_path, _ = QFileDialog.getSaveFileName(self, "保存 log", "", "txt Files (*.txt);;All Files (*)")
            if file_path:
                self.pull_log_with_clear(file_path, device_id)
            else:
                self.textBrowser.append("已取消！")
        else:
            self.textBrowser.append("未连接设备！")

    @staticmethod
    def adb_push_file(local_file_path, target_path_on_device, device_id):
        command = f"adb -s {device_id} push {local_file_path} {target_path_on_device}"
        try:
            subprocess.run(command, shell=True, check=True)
            return "文件推送成功！"
        except subprocess.CalledProcessError as e:
            return f"文件推送失败: {e}"

    def show_push_file_dialog(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            local_file_path, _ = QFileDialog.getOpenFileName(self, "选择本地文件", "", "All Files (*)")
            if local_file_path:
                target_path_on_device, ok = QInputDialog.getText(self, "输入设备文件路径",
                                                                 "请输入车机上的目标路径:")
                if ok and target_path_on_device:
                    res = self.adb_push_file(local_file_path, target_path_on_device, device_id)
                    self.textBrowser.append(res)
                else:
                    self.textBrowser.append("已取消！")
            else:
                self.textBrowser.append("已取消！")
        else:
            self.textBrowser.append("未连接设备！")

    @staticmethod
    def simulate_click(x, y, device_id):
        command = f"adb -s {device_id} shell input tap {x} {y}"
        try:
            subprocess.run(command, shell=True, check=True)
            return "点击成功！"
        except subprocess.CalledProcessError as e:
            return f"点击失败: {e}"

    def show_simulate_click_dialog(self):  # 模拟点击
        device_id = self.get_selected_device()
        device_id_lst = self.get_new_device_lst()
        if device_id in device_id_lst:
            x, ok = QInputDialog.getInt(self, "输入 X 坐标", "请输入点击的 X 坐标:")
            if ok:
                y, ok = QInputDialog.getInt(self, "输入 Y 坐标", "请输入点击的 Y 坐标:")
                if ok:
                    res = self.simulate_click(x, y, device_id)
                    self.textBrowser.append(res)
                else:
                    self.textBrowser.append("已取消！")
            else:
                self.textBrowser.append("已取消！")
        else:
            self.textBrowser.append("未连接设备！")

    @staticmethod
    def simulate_long_press(x, y, duration, device_id):
        command = f"adb -s {device_id} shell input swipe {x} {y} {x} {y} {duration}"
        try:
            subprocess.run(command, shell=True, check=True)
            return "长按模拟成功！"
        except subprocess.CalledProcessError as e:
            return f"长按模拟失败: {e}"


    def show_simulate_long_press_dialog(self):
        # 执行adb kill-server
        # 执行adb start-server
        result = subprocess.run("adb kill-server", capture_output=True, text=True)
        if result.returncode == 0:
            self.textBrowser.append("杀死ADB服务成功！")
            self.textBrowser.append(result.stdout)
        else:
            self.textBrowser.append("命令执行失败，标准错误输出如下：")
            self.textBrowser.append(result.stderr)
        result_2 = subprocess.run("adb start-server", capture_output=True, text=True)
        if result_2.returncode == 0:
            self.textBrowser.append("ADB服务启动成功，标准输出如下：")
            self.textBrowser.append(result.stdout)
        else:
            self.textBrowser.append("ADB服务启动失败，标准错误输出如下：")
            self.textBrowser.append(result.stderr)


    @staticmethod
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

    def show_input_text_dialog(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            text_to_input, ok = QInputDialog.getText(self, "输入文本", "请输入要通过 ADB 输入的文本:")
            if ok and text_to_input:
                lst = self.input_text_via_adb(text_to_input, device_id)
                self.textBrowser.append(lst)
            else:
                self.textBrowser.append("已取消！")
        else:
            self.textBrowser.append("未连接设备！")

    def show_force_stop_app_dialog(self):
        try:
            device_id = self.get_selected_device()
            devices_id_lst = self.get_new_device_lst()
            if device_id in devices_id_lst:
                from force_stop_app_thread import ForceStopAppThread
                self.Force_app_thread = ForceStopAppThread(self.d)
                self.Force_app_thread.progress_signal.connect(self.textBrowser.append)
                self.Force_app_thread.error_signal.connect(self.textBrowser.append)
                self.Force_app_thread.start()
                # package_name = self.get_foreground_package(is_direct_call=False)
                # if package_name:
                #     adb_command = f"am force-stop {package_name}"
                #     try:
                #         # subprocess.run(adb_command, shell=True, check=True)
                #         self.d.shell(adb_command)
                #         self.textBrowser.append(f"成功强制停止 {package_name} 应用在设备 {device_id} 上")
                #     except subprocess.CalledProcessError as e:
                #         self.textBrowser.append(f"强制停止 {package_name} 应用在设备 {device_id} 上失败: {e}")
                # else:
                #     self.textBrowser.append("未获取到前台应用包名")
            else:
                self.textBrowser.append("未连接设备！")
        except Exception as e:
            self.textBrowser.append(f"强制停止应用失败: {e}")

    @staticmethod
    def clear_app_cache(device, package_name):
        if device is not None:
            try:
                device.app_clear(package_name)
                return f"应用 {package_name} 的缓存已清除"
            except Exception as e:
                return f"清除应用缓存失败: {e}"
        else:
            return "设备未连接！"

    def show_clear_app_cache_dialog(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            package_name = self.get_foreground_package(is_direct_call=False)
            if package_name:
                result = self.clear_app_cache(self.d, package_name)
                self.textBrowser.append(result)
            else:
                self.textBrowser.append("未获取到前台应用包名")
        else:
            self.textBrowser.append("设备未连接！")

    def get_foreground_package(self, is_direct_call=True):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        try:
            if device_id in devices_id_lst:
                current_app = self.d.app_current()  # 获取当前正在运行的应用
                if current_app:
                    package_name = current_app['package']
                    activity_name = current_app['activity']
                    if is_direct_call:  # 如果是直接调用
                        self.textBrowser.append(f"包名: {package_name}, 活动名: {activity_name}")
                    else:
                        return package_name  # 返回包名
                else:
                    self.textBrowser.append("未找到正在运行的应用包名")
            else:
                self.textBrowser.append("设备连接失败")
        except Exception as e:
            self.textBrowser.append(f"获取前台正在运行的应用包名失败: {e}")

    @staticmethod
    def aapt_get_packagen_name(apk_path):
        command = f"aapt dump badging {apk_path} | findstr name"
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            package_name = result.stdout.strip().split('\'')[1]
            return package_name
        except subprocess.CalledProcessError as e:
            return f"获取包名失败: {e}"

    def aapt_getpackage_name_dilog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择APK文件", "", "APK文件 (*.apk)")
        if file_path:
            package_name = self.aapt_get_packagen_name(file_path)
            self.textBrowser.append(f"包名: {package_name}")
        else:
            self.textBrowser.append("未选择APK文件")

    def d_list(self):
        devices_id_lst = self.get_new_device_lst()
        if devices_id_lst:
            for device_id in devices_id_lst:
                try:
                    d = u2.connect(device_id)
                except Exception as e:
                    self.textBrowser.append(f"设备 {device_id} 连接失败: {e}")
        else:
            self.textBrowser.append("未连接设备！")

    @staticmethod
    def stop_program():
        sys.exit()
