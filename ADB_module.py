import time
from PyQt5.QtWidgets import (QMainWindow, QFileDialog, QInputDialog, QMessageBox)
import sys
import io
import subprocess
from Function_Moudle.adb_root_wrapper_thread import AdbRootWrapperThread

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
from PyQt5 import uic


# noinspection SpellCheckingInspection
class TextEditOutputStream(io.TextIOBase):  # 继承 io.TextIOBase 类

    def __init__(self, textbrowser):
        super().__init__()  # 调用父类构造函数
        self.textBrowser = textbrowser  # 绑定 textEdit
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


# noinspection DuplicatedCode,SpellCheckingInspection
class ADB_Mainwindow(QMainWindow):
    def __init__(self, parent=None):
        super(ADB_Mainwindow, self).__init__(parent)
        self.releasenote_package_version = None
        self.releasenote_dict = None
        self.app_version_check_thread = None
        self.releasenote_file = None
        self.voice_record_thread = None
        self.file_path = None
        self.PullLogSaveThread = None
        self.install_file_thread = None
        self.simulate_long_press_dialog_thread = None
        self.GetForegroundPackageThread = None
        self.input_text_thread = None
        self.Clear_app_cache_thread = None
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
        self.list_package_thread = None
        self.input_keyevent_287_thread = None
        self.engineering_thread = None
        self.app_action_thread = None

        # 动态加载ui文件
        uic.loadUi('adbtool.ui', self)
        # 假设这里是初始化UI控件的部分，使用findChild方法获取控件
        from PyQt5 import QtWidgets
        self.RefreshButton = self.findChild(QtWidgets.QPushButton, 'RefreshButton')
        self.ComboxButton = self.findChild(QtWidgets.QComboBox, 'ComboxButton')
        # 继续获取其他控件...
        # 添加按钮点击间隔控制和线程锁
        # self._last_click_time = {}
        # self._click_interval = 1.0  # 设置点击间隔为1秒
        # self._thread_locks = {}
        self.d = None

        # 重定向输出流为textBrowser
        self.text_edit_output_stream = TextEditOutputStream(self.textBrowser)
        # sys.stdout = self.text_edit_output_stream
        # sys.stderr = self.text_edit_output_stream
        if self.refresh_devices():  # 刷新设备列表
            self.d = u2.connect(self.get_selected_device())
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
        self.app_package_and_activity.clicked.connect(self.get_foreground_package)
        self.adb_push_file_button.clicked.connect(self.show_push_file_dialog)  # 推送文件
        self.button_reboot.clicked.connect(self.reboot_device)  # 重启设备
        self.RefreshButton.clicked.connect(self.refresh_devices)  # 刷新设备列表
        self.adb_root_button.clicked.connect(self.adb_root_wrapper)  # 以 root 权限运行 ADB
        self.start_app.clicked.connect(self.start_app_action)  # 启动应用
        self.get_running_app_info_button.clicked.connect(self.get_running_app_info)  # 获取当前运行的应用信息
        self.aapt_getpackagename_button.clicked.connect(self.aapt_getpackage_name_dilog)  # 获取apk包名
        self.textBrowser.textChanged.connect(self.scroll_to_bottom)  # 自动滚动到底部
        self.switch_vr_env_button.clicked.connect(self.switch_vr_env)  # 切换VR环境
        self.VR_nework_check_button.clicked.connect(self.check_vr_network)  # 检查VR网络
        self.activate_VR_button.clicked.connect(self.activate_vr)  # 激活VR
        self.list_package_button.clicked.connect(self.list_package)
        self.skipping_powerlimit_button.clicked.connect(self.skip_power_limit)  # 跳过电源挡位限制
        self.enter_engineering_mode_button.clicked.connect(self.enter_engineering_mode)  # 进入工程模式
        self.AS33_CR_enter_engineering_mode_button.clicked.connect(self.as33_cr_enter_engineering_mode)
        self.open_update_page_button.clicked.connect(self.open_update_page)  # 打开资源升级页面
        self.browse_log_save_path_button.clicked.connect(self.browse_log_save_path)  # 浏览日志保存路径
        self.pull_log_button.clicked.connect(self.pull_log)  # 拉取日志
        self.open_path_buttom.clicked.connect(self.open_path)  # 打开文件所在目录
        self.voice_start_record_button.clicked.connect(self.voice_start_record)  # 开始语音录制
        self.voice_stop_record_button.clicked.connect(self.voice_stop_record)  # 停止语音录制
        self.voice_pull_record_file_button.clicked.connect(self.voice_pull_record_file)  # 拉取录音文件
        self.remove_record_file_button.clicked.connect(self.remove_voice_record_file)  # 删除语音录制文件
        self.select_releasenote_excel_button.clicked.connect(self.select_releasenote_excel)  # 选择集成清单文件
        self.start_check_button.clicked.connect(self.app_version_check)

    def app_version_check(self):
        # 读取self.releasenote_file表格文件中的B8单元格是否等于packageName
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            try:
                from Function_Moudle.app_version_check_thread import AppVersionCheckThread
                self.releasenote_dict = {}
                self.app_version_check_thread = AppVersionCheckThread(self.d, self.releasenote_file)
                self.app_version_check_thread.progress_signal.connect(self.textBrowser.append)
                self.app_version_check_thread.error_signal.connect(self.textBrowser.append)
                self.app_version_check_thread.release_note_signal.connect(self.handle_progress)
                self.app_version_check_thread.start()
            except Exception as e:
                self.textBrowser.append(f"启动版本检查线程失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def handle_progress(self, result_dict):
        self.releasenote_dict.update(result_dict)  # 更新暂存字典
        self.releasenote_package_version = result_dict
        # 从字典result_dict中挨个读取packageName并用该包名取设备上获取该包名的版本号
        true_count = 0
        false_count = 0
        for i in result_dict.keys():
            if i is not None:
                app_info = self.d.app_info(i)
                if app_info is None:
                    break
                version_name = app_info.get('versionName', '未知版本')
                if str(version_name) == str(result_dict[i]):
                    self.textBrowser.append(f"包名: {i}, 已安装版本号: {version_name}， 集成清单版本号: {result_dict[i]}")
                    true_count += 1
                    self.textBrowser.append(f"版本号匹配成功！")
                else:
                    self.textBrowser.append(f"包名: {i}, 已安装版本号: {version_name}， 集成清单版本号: {result_dict[i]}")
                    false_count += 1
                    self.textBrowser.append(f"版本号匹配失败！")
        self.textBrowser.append(f"匹配成功数: {true_count}, 匹配失败数: {false_count}")



    def select_releasenote_excel(self):
        self.releasenote_file, _ = QFileDialog.getOpenFileName(self, "选择集成清单文件", "", "Excel Files (*.xlsx *.xls)")
        if self.releasenote_file is not None:
            # 显示文件名
            file_name = self.releasenote_file.split('/')[-1]
            self.releasenote_file_name_view.setText(file_name)


    def remove_voice_record_file(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        device_record_file_path = self.device_record_path.text()
        if self.d is not None:
            if device_id in devices_id_lst:
                try:
                    from Function_Moudle.remove_record_file_thread import RemoveRecordFileThread
                    self.voice_record_thread = RemoveRecordFileThread(self.d, device_record_file_path)
                    self.voice_record_thread.signal_remove_voice_record_file.connect(self.textBrowser.append)
                    self.voice_record_thread.start()
                except Exception as e:
                    self.textBrowser.append(f"启动删除语音录制文件线程失败: {e}")
            else:
                self.textBrowser.append("设备未连接！")
        else:
            self.textBrowser.append("设备未连接！")

    def voice_start_record(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            try:
                from Function_Moudle.voice_record_thread import VoiceRecordThread
                self.voice_record_thread = VoiceRecordThread(device_id)
                self.voice_record_thread.progress_signal.connect(self.textBrowser.append)
                self.voice_record_thread.record_signal.connect(self.textBrowser.append)
                self.voice_record_thread.start()
            except Exception as e:
                self.textBrowser.append(f"启动语音录制线程失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def voice_stop_record(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            try:
                from Function_Moudle.voice_stop_record_thread import VoiceStopRecordThread
                self.voice_record_thread = VoiceStopRecordThread(device_id)
                self.voice_record_thread.voice_stop_record_signal.connect(self.textBrowser.append)
                self.voice_record_thread.start()
            except Exception as e:
                self.textBrowser.append(f"启动语音录制线程失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def voice_pull_record_file(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        file_path = self.inputbox_log_path.text()
        device_record_file_path = self.device_record_path.text()
        # self.textBrowser.append(f"设备录音文件路径: {device_record_file_path}")
        if device_id in devices_id_lst:
            # 弹出目录选择弹窗
            if file_path is not None:
                try:
                    from Function_Moudle.voice_pull_record_file_thread import VoicePullRecordFileThread
                    self.voice_record_thread = VoicePullRecordFileThread(device_id, file_path, device_record_file_path)
                    self.voice_record_thread.signal_voice_pull_record_file.connect(self.textBrowser.append)
                    self.voice_record_thread.start()
                except Exception as e:
                    self.textBrowser.append(f"启动拉取录音文件线程失败: {e}")
            else:
                self.textBrowser.append("请选择保存路径！")
        else:
            self.textBrowser.append("设备未连接！")



    def open_path(self):
        # 使用资源管理器打开一个地址
        self.file_path = self.inputbox_log_path.text()
        try:
            if self.file_path is not None:
                os.startfile(self.file_path)
            else:
                self.textBrowser.append("路径不能为空！")
        except Exception as e:
            self.textBrowser.append(f"路径不存在！: {e}")

    def pull_log(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        self.file_path = self.inputbox_log_path.text()
        if device_id in devices_id_lst:
            try:
                if self.file_path is None:
                    self.textBrowser.append(f"路径不能为空！")
                elif os.path.exists(self.file_path):
                    from Function_Moudle.pull_log_thread import PullLogThread
                    self.PullLogSaveThread = PullLogThread(self.file_path, device_id)
                    self.PullLogSaveThread.progress_signal.connect(self.textBrowser.append)
                    self.PullLogSaveThread.error_signal.connect(self.textBrowser.append)
                    self.PullLogSaveThread.start()
                    # self.pull_log_button.setText("停止拉取")
                else:
                    self.textBrowser.append(f"路径不存在！")
            except Exception as e:
                self.textBrowser.append(f"启动拉取日志线程失败: {e}")

    # 调起资源升级页面
    def open_update_page(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            try:
                from Function_Moudle.update_thread import UpdateThread
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
        try:
            self.d = u2.connect(text)
            if self.d:
                self.textBrowser.append(f"已连接设备: {text}")
            else:
                self.textBrowser.append(f"连接设备 {text} 失败！")
        except Exception as e:
            self.textBrowser.append(f"连接设备 {text} 失败！: {e}")

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
                                                      '请输入应用包名')
                if ok and input_text:
                    package_name = input_text
                    from Function_Moudle.app_action_thread import AppActionThread
                    self.app_action_thread = AppActionThread(self.d, package_name)
                    self.app_action_thread.progress_signal.connect(self.textBrowser.append)
                    self.app_action_thread.error_signal.connect(self.textBrowser.append)
                    self.app_action_thread.start()
                else:
                    self.textBrowser.append("用户取消输入或输入为空")
            except Exception as e:
                self.textBrowser.append(f"启动应用失败: {e}")
        else:
            self.textBrowser.append("未连接设备！")

    def as33_cr_enter_engineering_mode(self):
        """AS33_CR进入工程模式"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            try:
                from Function_Moudle.engineering_mode_thread import EngineeringModeThread
                self.engineering_thread = EngineeringModeThread(self.d)
                self.engineering_thread.progress_signal.connect(self.textBrowser.append)
                self.engineering_thread.result_signal.connect(self.textBrowser.append)
                self.engineering_thread.error_signal.connect(self.textBrowser.append)
                self.engineering_thread.start()
            except Exception as e:
                self.textBrowser.append(f"启动工程模式线程失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")


    def enter_engineering_mode(self):

        """进入工程模式"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            try:
                from Function_Moudle.enter_engineering_mode_thread import enter_engineering_mode_thread
                self.engineering_thread = enter_engineering_mode_thread(self.d)
                self.engineering_thread.progress_signal.connect(self.textBrowser.append)
                self.engineering_thread.result_signal.connect(self.textBrowser.append)
                self.engineering_thread.error_signal.connect(self.textBrowser.append)
                self.engineering_thread.start()
            except Exception as e:
                self.textBrowser.append(f"启动工程模式线程失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")


    def skip_power_limit(self):
        """跳过电源挡位限制"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            try:
                from Function_Moudle.skip_power_limit_thread import SkipPowerLimitThread
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
                from Function_Moudle.list_package_thread import ListPackageThread
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
                from Function_Moudle.vr_thread import VRActivationThread
                self.vr_thread = VRActivationThread(device_id)
                self.vr_thread.progress_signal.connect(self.textBrowser.append)
                self.vr_thread.result_signal.connect(self.textBrowser.append)
                self.vr_thread.error_signal.connect(self.textBrowser.append)
                self.vr_thread.start()
            except Exception as e:
                self.textBrowser.append(f"启动VR激活线程失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def check_vr_network(self):
        """检查VR网络"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        if device_id in devices_id_lst:
            try:
                from Function_Moudle.check_vr_network_thread import CheckVRNetworkThread
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
                from Function_Moudle.switch_vr_env_thread import SwitchVrEnvThread
                self.check_vr_env_thread = SwitchVrEnvThread(self.d)
                self.check_vr_env_thread.progress_signal.connect(self.textBrowser.append)
                self.check_vr_env_thread.result_signal.connect(self.textBrowser.append)
                self.check_vr_env_thread.error_signal.connect(self.textBrowser.append)
                self.check_vr_env_thread.start()
            except Exception as e:
                self.textBrowser.append(f"切换VR环境失败: {e}")
        else:
            self.textBrowser.append("设备未连接！")

    def scroll_to_bottom(self):
        scrollbar = self.textBrowser.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def get_running_app_info(self):
        # 获取当前前景应用的版本号
        device_id = self.get_selected_device()  # 获取当前选定的设备ID
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            from Function_Moudle.get_running_app_info_thread import GetRunningAppInfoThread
            self.get_running_app_info_thread = GetRunningAppInfoThread(self.d)
            self.get_running_app_info_thread.progress_signal.connect(self.textBrowser.append)
            self.get_running_app_info_thread.result_signal.connect(self.textBrowser.append)
            self.get_running_app_info_thread.error_signal.connect(self.textBrowser.append)
            self.get_running_app_info_thread.start()
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
                from Function_Moudle.view_apk_path_wrapper_thread import ViewApkPathWrapperThread
                self.view_apk_thread = ViewApkPathWrapperThread(device_id, package_name)
                self.view_apk_thread.progress_signal.connect(self.textBrowser.append)
                self.view_apk_thread.result_signal.connect(self.textBrowser.append)
                self.view_apk_thread.error_signal.connect(self.textBrowser.append)
                self.view_apk_thread.start()
            else:
                self.textBrowser.append("未连接设备！")
        except Exception as e:
            self.textBrowser.append(f"初始化线程失败: {e}")

    # @staticmethod
    # def run_cmd():
    #     user_directory = os.path.expanduser("~")
    #     subprocess.Popen(["start", "cmd", "/k", "cd /d " + user_directory], shell=True)

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
                self.d = None
                self.d = u2.connect(self.get_selected_device())
                if self.d:
                    self.textBrowser.append(f"设备连接成功：{self.get_selected_device()}")
                else:
                    self.textBrowser.append(f"设备连接失败！")
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
                    from Function_Moudle.reboot_device_thread import RebootDeviceThread
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
                command = f"adb -s {device_id} shell screencap -p /sdcard/screenshot.png && adb -s {device_id} pull /sdcard/screenshot.png {file_path} && adb -s {device_id} shell rm /sdcard/screenshot.png"
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
                from Function_Moudle.show_uninstall_thread import ShowUninstallThread
                self.uninstall_thread = ShowUninstallThread(self.d, package_name)
                self.uninstall_thread.progress_signal.connect(self.textBrowser.append)
                self.uninstall_thread.result_signal.connect(self.textBrowser.append)
                self.uninstall_thread.error_signal.connect(self.textBrowser.append)
                self.uninstall_thread.start()
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
            package_path, ok = QFileDialog.getOpenFileName(self, "选择应用安装包", "",
                                                          "APK Files (*.apk);;All Files (*)")
            if ok:
                from Function_Moudle.install_file_thread import InstallFileThread
                self.install_file_thread = InstallFileThread(self.d, package_path)
                self.install_file_thread.progress_signal.connect(self.textBrowser.append)
                self.install_file_thread.signal_status.connect(self.textBrowser.append)
                self.install_file_thread.start()
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
        from Function_Moudle.simulate_long_press_dialog_thread import simulate_long_press_dialog_thread
        self.simulate_long_press_dialog_thread = simulate_long_press_dialog_thread(self.d)
        self.simulate_long_press_dialog_thread.result_signal.connect(self.textBrowser.append)
        self.simulate_long_press_dialog_thread.error_signal.connect(self.textBrowser.append)
        self.simulate_long_press_dialog_thread.start()

    def show_input_text_dialog(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            text_to_input, ok = QInputDialog.getText(self, "输入文本", "请输入要通过 ADB 输入的文本:")
            if ok and text_to_input:
                # self.textBrowser.append(text_to_input)
                from Function_Moudle.input_text_thread import InputTextThread
                self.input_text_thread = InputTextThread(self.d, text_to_input)
                self.input_text_thread.progress_signal.connect(self.textBrowser.append)
                self.input_text_thread.error_signal.connect(self.textBrowser.append)
                self.input_text_thread.start()
            else:
                self.textBrowser.append("已取消！")
        else:
            self.textBrowser.append("未连接设备！")

    def show_force_stop_app_dialog(self):
        try:
            device_id = self.get_selected_device()
            devices_id_lst = self.get_new_device_lst()
            if device_id in devices_id_lst:
                from Function_Moudle.force_stop_app_thread import ForceStopAppThread
                self.Force_app_thread = ForceStopAppThread(self.d)
                self.Force_app_thread.progress_signal.connect(self.textBrowser.append)
                self.Force_app_thread.error_signal.connect(self.textBrowser.append)
                self.Force_app_thread.start()
            else:
                self.textBrowser.append("未连接设备！")
        except Exception as e:
            self.textBrowser.append(f"强制停止应用失败: {e}")

    def show_clear_app_cache_dialog(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            from Function_Moudle.clear_app_cache_thread import ClearAppCacheThread
            self.Clear_app_cache_thread = ClearAppCacheThread(self.d)
            self.Clear_app_cache_thread.progress_signal.connect(self.textBrowser.append)
            self.Clear_app_cache_thread.error_signal.connect(self.textBrowser.append)
            self.Clear_app_cache_thread.start()
        else:
            self.textBrowser.append("设备未连接！")

    def get_foreground_package(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        try:
            if device_id in devices_id_lst:
                from Function_Moudle.get_foreground_package_thread import GetForegroundPackageThread
                self.GetForegroundPackageThread = GetForegroundPackageThread(self.d)
                self.GetForegroundPackageThread.signal_package.connect(self.textBrowser.append)
                self.GetForegroundPackageThread.start()
            else:
                self.textBrowser.append("设备连接失败")
        except Exception as e:
            self.textBrowser.append(f"获取前台正在运行的应用包名失败: {e}")

    @staticmethod
    def aapt_get_packagen_name(apk_path):
        quoted_apk_path = f'"{apk_path}"'
        command = f"aapt dump badging {quoted_apk_path} | findstr name"
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


    def browse_log_save_path(self):
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        if device_id in devices_id_lst:
            if hasattr(self, 'PullLogSaveThread') and self.PullLogSaveThread and self.PullLogSaveThread.isRunning():
                self.PullLogSaveThread.stop()
                self.pull_log_button.setText("拉取日志")
            else:
                #  弹出选择路径的窗口
                self.file_path = QFileDialog.getExistingDirectory(self, "选择保存路径", "")
                if self.file_path:
                    self.inputbox_log_path.setText(self.file_path)
                else:
                    self.textBrowser.append("已取消！")
        else:
            self.textBrowser.append("未连接设备！")
                
