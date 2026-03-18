#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VR功能控制器

从 ADB_module.py 中拆分出的VR功能模块
"""

from logger_manager import (
    get_logger, log_button_click, log_method_result
)

# 创建日志记录器
logger = get_logger("ADBTools.VRController")


class VRController:
    """VR功能控制器
    
    处理VR相关功能：
    - VR激活
    - VR网络检查
    - VR环境切换
    - VR超时设置
    - 电源挡位限制
    """
    
    def __init__(self, main_window):
        """
        初始化VR控制器
        
        Args:
            main_window: 主窗口实例，用于获取设备和UI控件
        """
        self.main_window = main_window
    
    # ========== 设备和连接信息 ==========
    
    def _get_selected_device(self):
        """获取当前选中的设备ID"""
        return self.main_window.get_selected_device()
    
    def _get_device_list(self):
        """获取设备列表"""
        return self.main_window.get_new_device_lst()
    
    def _get_connection_mode(self):
        """获取当前连接模式"""
        return self.main_window.connection_mode
    
    def _get_u2_device(self):
        """获取U2设备对象"""
        return self.main_window.d
    
    def _is_device_connected(self):
        """检查设备是否已连接"""
        device_id = self._get_selected_device()
        devices = self._get_device_list()
        return device_id in devices
    
    def _append_output(self, text):
        """输出文本到主窗口"""
        self.main_window.textBrowser.append(text)
    
    def _connect_thread_signals(self, thread):
        """连接线程的通用信号（安全模式：检查信号是否存在）"""
        if hasattr(thread, 'progress_signal'):
            thread.progress_signal.connect(self._append_output)
        if hasattr(thread, 'error_signal'):
            thread.error_signal.connect(self._append_output)
        if hasattr(thread, 'result_signal'):
            thread.result_signal.connect(self._append_output)
        # 兼容旧的信号名称
        if hasattr(thread, 'signal_timeout'):
            thread.signal_timeout.connect(self._append_output)
    
    # ========== VR激活 ==========
    
    def activate_vr(self):
        """激活VR"""
        device_id = self._get_selected_device()
        
        # 获取keyevent值
        keyevent_value = self.main_window.vr_keyevent_combo.currentText()
        log_button_click("activate_VR_button", "激活VR", f"Keyevent: {keyevent_value}")
        
        if not self._is_device_connected():
            log_method_result("activate_vr", False, "设备未连接")
            self._append_output("设备未连接！")
            return
        
        try:
            from Function_Moudle.activate_vr_thread import ActivateVrThread
            
            connection_mode = self._get_connection_mode()
            
            if connection_mode == 'u2':
                u2_device = self._get_u2_device()
                if not u2_device:
                    log_method_result("activate_vr", False, "U2设备连接失败")
                    self._append_output("U2设备连接失败！")
                    return
                self.activate_vr_thread = ActivateVrThread(
                    device_id,
                    keyevent_value,
                    connection_mode='u2',
                    u2_device=u2_device
                )
            elif connection_mode == 'adb':
                self.activate_vr_thread = ActivateVrThread(
                    device_id,
                    keyevent_value,
                    connection_mode='adb'
                )
            else:
                log_method_result("activate_vr", False, "设备连接失败")
                self._append_output("设备连接失败或模式不支持！")
                return
            
            self._connect_thread_signals(self.activate_vr_thread)
            self.activate_vr_thread.start()
            log_method_result("activate_vr", True, f"线程已启动 (Keyevent: {keyevent_value})")
            
        except Exception as e:
            log_method_result("activate_vr", False, str(e))
            self._append_output(f"执行VR唤醒命令失败: {e}")
    
    # ========== VR网络检查 ==========
    
    def check_vr_network(self):
        """检查VR网络"""
        log_button_click("VR_nework_check_button", "检查VR网络")
        
        if not self._is_device_connected():
            log_method_result("check_vr_network", False, "设备未连接")
            self._append_output("设备未连接！")
            return
        
        device_id = self._get_selected_device()
        connection_mode = self._get_connection_mode()
        
        try:
            if connection_mode == 'u2':
                u2_device = self._get_u2_device()
                from Function_Moudle.check_vr_network_thread import CheckVRNetworkThread
                self.check_vr_network_thread = CheckVRNetworkThread(u2_device)
            elif connection_mode == 'adb':
                from Function_Moudle.adb_check_vr_network_thread import ADBCheckVRNetworkThread
                self.check_vr_network_thread = ADBCheckVRNetworkThread(device_id)
            else:
                log_method_result("check_vr_network", False, "设备未连接")
                self._append_output("设备未连接！")
                return
            
            self._connect_thread_signals(self.check_vr_network_thread)
            self.check_vr_network_thread.start()
            log_method_result("check_vr_network", True, "线程已启动")
            
        except Exception as e:
            log_method_result("check_vr_network", False, str(e))
            self._append_output(f"检查VR网络失败: {e}")
    
    # ========== VR环境切换 ==========
    
    def switch_vr_env(self):
        """切换VR环境"""
        log_button_click("switch_vr_env_button", "切换VR环境")
        
        if not self._is_device_connected():
            log_method_result("switch_vr_env", False, "设备未连接")
            self._append_output("设备未连接！")
            return
        
        device_id = self._get_selected_device()
        connection_mode = self._get_connection_mode()
        
        try:
            if connection_mode == 'u2':
                u2_device = self._get_u2_device()
                from Function_Moudle.switch_vr_env_thread import SwitchVrEnvThread
                self.switch_vr_env_thread = SwitchVrEnvThread(u2_device)
            elif connection_mode == 'adb':
                from Function_Moudle.adb_switch_vr_env_thread import ADBSwitchVrEnvThread
                self.switch_vr_env_thread = ADBSwitchVrEnvThread(device_id)
            else:
                log_method_result("switch_vr_env", False, "设备未连接")
                self._append_output("设备未连接！")
                return
            
            self._connect_thread_signals(self.switch_vr_env_thread)
            self.switch_vr_env_thread.start()
            log_method_result("switch_vr_env", True, "线程已启动")
            
        except Exception as e:
            log_method_result("switch_vr_env", False, str(e))
            self._append_output(f"切换VR环境失败: {e}")
    
    # ========== VR超时设置 ==========
    
    def set_vr_timeout(self):
        """设置VR服务器超时"""
        log_button_click("set_vr_server_timout", "设置VR服务器超时")
        
        if not self._is_device_connected():
            log_method_result("set_vr_timeout", False, "设备未连接")
            self._append_output("设备未连接！")
            return
        
        device_id = self._get_selected_device()
        connection_mode = self._get_connection_mode()
        
        try:
            if connection_mode == 'u2':
                u2_device = self._get_u2_device()
                from Function_Moudle.set_vr_timeout_thread import SetVrTimeoutThread
                self.vr_timeout_thread = SetVrTimeoutThread(u2_device)
            elif connection_mode == 'adb':
                from Function_Moudle.adb_set_vr_timeout_thread import ADBSetVrTimeoutThread
                self.vr_timeout_thread = ADBSetVrTimeoutThread(device_id)
            else:
                log_method_result("set_vr_timeout", False, "设备未连接")
                self._append_output("设备未连接！")
                return
            
            self._connect_thread_signals(self.vr_timeout_thread)
            self.vr_timeout_thread.start()
            log_method_result("set_vr_timeout", True, "线程已启动")
            
        except Exception as e:
            log_method_result("set_vr_timeout", False, str(e))
            self._append_output(f"设置VR超时失败: {e}")
    
    # ========== 电源挡位限制 ==========
    
    def skip_power_limit(self):
        """跳过电源挡位限制"""
        log_button_click("skipping_powerlimit_button", "跳过电源挡位限制")
        
        if not self._is_device_connected():
            log_method_result("skip_power_limit", False, "设备未连接")
            self._append_output("设备未连接！")
            return
        
        device_id = self._get_selected_device()
        
        try:
            from Function_Moudle.skip_power_limit_thread import SkipPowerLimitThread
            self.skip_power_limit_thread = SkipPowerLimitThread(device_id)
            self._connect_thread_signals(self.skip_power_limit_thread)
            self.skip_power_limit_thread.start()
            log_method_result("skip_power_limit", True, "线程已启动")
            
        except Exception as e:
            log_method_result("skip_power_limit", False, str(e))
            self._append_output(f"启动跳过电源限制线程失败: {e}")
