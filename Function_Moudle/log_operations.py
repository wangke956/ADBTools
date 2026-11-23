#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""日志操作管理器 - 处理日志拉取、语音录制等功能"""

import os
from PyQt6.QtWidgets import QFileDialog

from logger_manager import (
    get_logger, log_operation, log_exception,
    log_button_click, log_method_result, log_device_operation
)

logger = get_logger("ADBTools.LogManager")


class LogManager:
    """日志操作管理器 - 处理日志拉取、语音录制等功能"""
    
    def __init__(self, main_window, device_id, connection_mode="adb", u2_device=None):
        """
        初始化日志管理器
        
        Args:
            main_window: 主窗口实例 (ADB_Mainwindow)
            device_id: 设备ID
            connection_mode: 连接模式 ('u2' 或 'adb')，默认为 'adb'
            u2_device: U2设备对象
        """
        self.main_window = main_window
        self.device_id = device_id
        # 确保connection_mode不为None，如果为None则使用默认值'adb'
        self.connection_mode = connection_mode if connection_mode else "adb"
        self.u2_device = u2_device

    def get_selected_device(self):
        """获取当前选中的设备ID"""
        return self.main_window.ComboxButton.currentText()
    
    def get_new_device_lst(self):
        """获取设备ID列表"""
        from adb_utils import adb_utils
        return adb_utils.get_device_list()
    
    def pull_log(self):
        """拉取设备日志"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        file_path = self.main_window.inputbox_log_path.text()
        
        log_button_click("pull_log_button", "拉取设备日志", f"保存路径: {file_path}")
        
        if device_id in devices_id_lst:
            try:
                if not file_path:
                    log_method_result("pull_log", False, "路径不能为空")
                    self.main_window.textBrowser.append("路径不能为空！")
                elif os.path.exists(file_path):
                    from Function_Moudle.pull_log_thread import PullLogThread
                    self.main_window.PullLogSaveThread = PullLogThread(file_path, device_id)
                    self.main_window.PullLogSaveThread.progress_signal.connect(self.main_window.textBrowser.append)
                    self.main_window.PullLogSaveThread.error_signal.connect(self.main_window.textBrowser.append)
                    self.main_window.PullLogSaveThread.start()
                    log_method_result("pull_log", True, "拉取日志线程已启动")
                else:
                    log_method_result("pull_log", False, "路径不存在")
                    self.main_window.textBrowser.append("路径不存在！")
            except Exception as e:
                log_method_result("pull_log", False, str(e))
                self.main_window.textBrowser.append(f"启动拉取日志线程失败: {e}")
        else:
            log_method_result("pull_log", False, "设备未连接")
            self.main_window.textBrowser.append("设备未连接！")
    
    def browse_log_save_path(self):
        """浏览日志保存路径"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("browse_log_save_path_button", "浏览日志保存路径")
        
        if device_id in devices_id_lst:
            if hasattr(self.main_window, 'PullLogSaveThread') and self.main_window.PullLogSaveThread and self.main_window.PullLogSaveThread.isRunning():
                self.main_window.PullLogSaveThread.stop()
                self.main_window.pull_log_button.setText("拉取日志")
                logger.info("停止拉取日志")
            else:
                file_path = QFileDialog.getExistingDirectory(self.main_window, "选择保存路径", "")
                if file_path:
                    self.main_window.inputbox_log_path.setText(file_path)
                    logger.info(f"选择路径: {file_path}")
                else:
                    logger.info("用户取消选择")
                    self.main_window.textBrowser.append("已取消！")
        else:
            log_method_result("browse_log_save_path", False, "设备未连接")
            self.main_window.textBrowser.append("未连接设备！")
    
    def open_path(self):
        """打开文件所在目录"""
        log_button_click("open_path_buttom", "打开文件所在目录")
        
        file_path = self.main_window.inputbox_log_path.text()
        
        try:
            if file_path:
                logger.info(f"打开路径: {file_path}")
                os.startfile(file_path)
                log_method_result("open_path", True, f"已打开: {file_path}")
            else:
                log_method_result("open_path", False, "路径不能为空")
                self.main_window.textBrowser.append("路径不能为空！")
        except Exception as e:
            log_method_result("open_path", False, str(e))
            self.main_window.textBrowser.append(f"路径不存在！: {e}")
    
    def voice_start_record(self):
        """开始语音录制"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("voice_start_record_button", "开始语音录制")

        if device_id in devices_id_lst:
            try:
                # 动态获取当前的连接模式和u2设备
                current_connection_mode = getattr(self.main_window, 'connection_mode', 'adb') or 'adb'
                current_u2_device = getattr(self.main_window, 'd', None)
                
                from Function_Moudle.voice_record_thread import VoiceRecordThread
                self.main_window.voice_record_thread = VoiceRecordThread(
                    device_id=device_id,
                    connection_mode=current_connection_mode,
                    u2_device=current_u2_device
                )
                self.main_window.voice_record_thread.progress_signal.connect(self.main_window.textBrowser.append)
                self.main_window.voice_record_thread.record_signal.connect(self.main_window.textBrowser.append)
                self.main_window.voice_record_thread.start()
                
                log_method_result("voice_start_record", True, "录制线程已启动")
            except Exception as e:
                log_method_result("voice_start_record", False, str(e))
                self.main_window.textBrowser.append(f"启动语音录制线程失败: {e}")
        else:
            log_method_result("voice_start_record", False, "设备未连接")
            self.main_window.textBrowser.append("设备未连接！")
    
    def voice_stop_record(self):
        """停止语音录制"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("voice_stop_record_button", "停止语音录制")

        if device_id in devices_id_lst:
            try:
                # 动态获取当前的连接模式和u2设备
                current_connection_mode = getattr(self.main_window, 'connection_mode', 'adb') or 'adb'
                current_u2_device = getattr(self.main_window, 'd', None)
                
                from Function_Moudle.voice_stop_record_thread import VoiceStopRecordThread
                self.main_window.voice_record_thread = VoiceStopRecordThread(
                    device_id=device_id,
                    connection_mode=current_connection_mode,
                    u2_device=current_u2_device
                )
                self.main_window.voice_record_thread.voice_stop_record_signal.connect(self.main_window.textBrowser.append)
                self.main_window.voice_record_thread.start()
                
                log_method_result("voice_stop_record", True, "停止录制线程已启动")
            except Exception as e:
                log_method_result("voice_stop_record", False, str(e))
                self.main_window.textBrowser.append(f"停止语音录制失败: {e}")
        else:
            log_method_result("voice_stop_record", False, "设备未连接")
            self.main_window.textBrowser.append("设备未连接！")
    
    def voice_pull_record_file(self):
        """拉取录音文件"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("voice_pull_record_file_button", "拉取录音文件")

        if device_id in devices_id_lst:
            try:
                # 从控件中获取设备录音文件路径
                device_record_file_path = self.main_window.device_record_path.text().strip()
                if not device_record_file_path:
                    log_method_result("voice_pull_record_file", False, "设备录音文件路径不能为空")
                    self.main_window.textBrowser.append("设备录音文件路径不能为空！")
                    return
                
                # 获取本地保存路径（使用日志保存路径输入框）
                local_save_path = self.main_window.inputbox_log_path.text().strip()
                if not local_save_path:
                    log_method_result("voice_pull_record_file", False, "本地保存路径不能为空")
                    self.main_window.textBrowser.append("请先设置本地保存路径！")
                    return
                
                from Function_Moudle.voice_pull_record_file_thread import VoicePullRecordFileThread
                # 动态获取当前的连接模式和u2设备
                current_connection_mode = getattr(self.main_window, 'connection_mode', 'adb') or 'adb'
                current_u2_device = getattr(self.main_window, 'd', None)
                
                self.main_window.voice_pull_record_file_thread = VoicePullRecordFileThread(
                    device_id=device_id,
                    file_path=local_save_path,
                    device_record_file_path=device_record_file_path,
                    connection_mode=current_connection_mode,
                    u2_device=current_u2_device
                )
                self.main_window.voice_pull_record_file_thread.progress_signal.connect(self.main_window.textBrowser.append)
                self.main_window.voice_pull_record_file_thread.result_signal.connect(self.main_window.textBrowser.append)
                self.main_window.voice_pull_record_file_thread.start()
                
                log_method_result("voice_pull_record_file", True, "拉取线程已启动")
            except Exception as e:
                log_method_result("voice_pull_record_file", False, str(e))
                self.main_window.textBrowser.append(f"拉取录音文件失败: {e}")
        else:
            log_method_result("voice_pull_record_file", False, "设备未连接")
            self.main_window.textBrowser.append("设备未连接！")
    
    def remove_voice_record_file(self):
        """删除语音录制文件"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        log_button_click("remove_record_file_button", "删除语音录制文件")

        if device_id in devices_id_lst:
            try:
                # 从控件中获取设备录音文件路径
                device_record_file_path = self.main_window.device_record_path.text().strip()
                if not device_record_file_path:
                    log_method_result("remove_voice_record_file", False, "设备录音文件路径不能为空")
                    self.main_window.textBrowser.append("设备录音文件路径不能为空！")
                    return
                
                # 动态获取当前的连接模式和u2设备（确保使用最新的状态）
                current_connection_mode = getattr(self.main_window, 'connection_mode', 'adb') or 'adb'
                current_u2_device = getattr(self.main_window, 'd', None)
                
                from Function_Moudle.remove_record_file_thread import RemoveRecordFileThread
                self.main_window.remove_record_file_thread = RemoveRecordFileThread(
                    device_id=device_id,
                    device_record_file_path=device_record_file_path,
                    connection_mode=current_connection_mode,
                    u2_device=current_u2_device
                )
                self.main_window.remove_record_file_thread.progress_signal.connect(self.main_window.textBrowser.append)
                self.main_window.remove_record_file_thread.result_signal.connect(self.main_window.textBrowser.append)
                self.main_window.remove_record_file_thread.signal_remove_voice_record_file.connect(self.main_window.textBrowser.append)
                self.main_window.remove_record_file_thread.start()
                
                log_method_result("remove_voice_record_file", True, "删除线程已启动")
            except Exception as e:
                log_method_result("remove_voice_record_file", False, str(e))
                self.main_window.textBrowser.append(f"删除录音文件失败: {e}")
        else:
            log_method_result("remove_voice_record_file", False, "设备未连接")
            self.main_window.textBrowser.append("设备未连接！")
    
    def voice_asr_test(self):
        """语音识别测试"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()
        
        log_button_click("voice_asr_test_button", "语音识别测试")

        if device_id in devices_id_lst:
            try:
                # 从输入框获取ASR测试文本
                asr_text = self.main_window.asr_test_text_input.text().strip()
                if not asr_text:
                    log_method_result("voice_asr_test", False, "测试文本不能为空")
                    self.main_window.textBrowser.append("请输入语音识别测试文本！")
                    return
                
                # 动态获取当前的连接模式和u2设备
                current_connection_mode = getattr(self.main_window, 'connection_mode', 'adb') or 'adb'
                current_u2_device = getattr(self.main_window, 'd', None)
                
                from Function_Moudle.voice_asr_test_thread import VoiceAsrTestThread
                self.main_window.voice_asr_test_thread = VoiceAsrTestThread(
                    device_id=device_id,
                    asr_text=asr_text,
                    connection_mode=current_connection_mode,
                    u2_device=current_u2_device
                )
                self.main_window.voice_asr_test_thread.progress_signal.connect(self.main_window.textBrowser.append)
                self.main_window.voice_asr_test_thread.result_signal.connect(self.main_window.textBrowser.append)
                self.main_window.voice_asr_test_thread.start()
                
                log_method_result("voice_asr_test", True, "语音识别测试线程已启动")
            except Exception as e:
                log_method_result("voice_asr_test", False, str(e))
                self.main_window.textBrowser.append(f"语音识别测试失败: {e}")
        else:
            log_method_result("voice_asr_test", False, "设备未连接")
            self.main_window.textBrowser.append("设备未连接！")

    def voice3_execute_query(self):
        """语音3.0 指令下发

        将用户输入的普通文本指令转为 VOICELESS_QUERY 广播命令，对当前选中设备执行。
        命令模板：
            adb -s <device> shell am broadcast \
                -n com.saicmotor.voiceservice/com.google.cloud.ml.api.cca.sample.debug.RemoteCommandReceiver \
                -a com.google.cloud.ml.api.cca.sample.VOICELESS_QUERY \
                --es query "<空格已转义的文本>"
        """
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        log_button_click("voice3_execute_button", "语音3.0指令下发")

        if device_id not in devices_id_lst:
            log_method_result("voice3_execute_query", False, "设备未连接")
            self.main_window.textBrowser.append("设备未连接！")
            return

        try:
            # 从输入框获取指令文本
            query_text = self.main_window.voice3_query_input.text().strip()
            if not query_text:
                log_method_result("voice3_execute_query", False, "指令文本不能为空")
                self.main_window.textBrowser.append("请输入语音3.0指令文本！")
                return

            # 动态获取当前的连接模式和 u2 设备
            current_connection_mode = getattr(self.main_window, 'connection_mode', 'adb') or 'adb'
            current_u2_device = getattr(self.main_window, 'd', None)

            from Function_Moudle.voice3_query_thread import Voice3QueryThread
            self.main_window.voice3_query_thread = Voice3QueryThread(
                device_id=device_id,
                query_text=query_text,
                connection_mode=current_connection_mode,
                u2_device=current_u2_device
            )
            self.main_window.voice3_query_thread.progress_signal.connect(self.main_window.textBrowser.append)
            self.main_window.voice3_query_thread.result_signal.connect(self.main_window.textBrowser.append)
            self.main_window.voice3_query_thread.start()

            log_method_result(
                "voice3_execute_query", True,
                f"语音3.0指令下发线程已启动 | 设备: {device_id} | 指令: {query_text}"
            )
        except Exception as e:
            log_method_result("voice3_execute_query", False, str(e))
            self.main_window.textBrowser.append(f"语音3.0指令下发失败: {e}")

    def voice3_update_preview(self, text=None):
        """实时刷新语音3.0命令预览框

        可由输入框 textChanged 或设备下拉框 currentTextChanged 触发；
        text 参数仅为兼容 Qt 信号，实际以控件当前内容为准。
        """
        try:
            from Function_Moudle.voice3_query_thread import Voice3QueryThread
            preview_widget = getattr(self.main_window, 'voice3_command_preview', None)
            input_widget = getattr(self.main_window, 'voice3_query_input', None)
            if preview_widget is None or input_widget is None:
                return
            query_text = input_widget.text().strip()
            if not query_text:
                preview_widget.setPlainText("")
                return
            # 使用与线程一致的构造逻辑，避免预览与实际执行命令不一致
            dummy = Voice3QueryThread(device_id=None, query_text=query_text)
            shell_cmd = dummy.build_shell_command()
            device_id = self.get_selected_device() or "<device>"
            preview_widget.setPlainText(f"adb -s {device_id} shell {shell_cmd}")
        except Exception as e:
            logger.warning(f"刷新语音3.0命令预览失败: {e}")

    # ==================== VHAL 告警注入（ZXD项目 Inbox 告警测试）====================
    def _vhal_read_inputs(self):
        """读取并解析 VHAL 告警注入输入框

        Returns:
            (warning_id, sub_status, err_msg)
            成功时 err_msg 为 None；失败时 warning_id/sub_status 为 None，err_msg 为错误提示。
        """
        from Function_Moudle.vhal_warning_inject_thread import VhalWarningInjectThread

        warning_id_widget = getattr(self.main_window, 'vhal_warning_id_input', None)
        sub_status_widget = getattr(self.main_window, 'vhal_sub_status_input', None)
        if warning_id_widget is None or sub_status_widget is None:
            return None, None, "VHAL 告警注入控件未初始化"

        warning_id_text = warning_id_widget.text().strip()
        sub_status_text = sub_status_widget.text().strip()

        # subStatus 为空时默认 0
        if not sub_status_text:
            sub_status_text = "0"

        warning_id, err = VhalWarningInjectThread.parse_number(warning_id_text, "WarningID")
        if err:
            return None, None, err
        sub_status, err = VhalWarningInjectThread.parse_number(sub_status_text, "subStatus")
        if err:
            return None, None, err

        err = VhalWarningInjectThread.validate_range(warning_id, "WarningID")
        if err:
            return None, None, err
        err = VhalWarningInjectThread.validate_range(sub_status, "subStatus")
        if err:
            return None, None, err

        return warning_id, sub_status, None

    def _vhal_render_preview(self, warning_id, sub_status, vhal_value):
        """渲染 VHAL 告警注入结果预览框"""
        from Function_Moudle.vhal_warning_inject_thread import VhalWarningInjectThread
        preview_widget = getattr(self.main_window, 'vhal_result_preview', None)
        if preview_widget is None:
            return
        device_id = self.get_selected_device() or "<device>"
        dummy = VhalWarningInjectThread(device_id=None)
        shell_cmd = dummy.build_shell_command(vhal_value)
        text = (
            f"WarningID  十进制 : {warning_id}\n"
            f"WarningID  十六进制: 0x{warning_id:04X}\n"
            f"subStatus  十进制 : {sub_status}\n"
            f"subStatus  十六进制: 0x{sub_status:04X}\n"
            f"vhalValue  十进制 : {vhal_value}\n"
            f"vhalValue  十六进制: 0x{vhal_value:08X}\n"
            f"\n"
            f"完整 adb 命令：\n"
            f"adb -s {device_id} shell {shell_cmd}"
        )
        preview_widget.setPlainText(text)

    def vhal_warning_generate_command(self):
        """【生成命令】按钮：解析输入、计算 vhalValue、展示预览（不执行）"""
        log_button_click("vhal_generate_command_button", "VHAL 告警注入-生成命令")
        try:
            warning_id, sub_status, err = self._vhal_read_inputs()
            if err:
                log_method_result("vhal_warning_generate_command", False, err)
                self.main_window.textBrowser.append(f"[VHAL] 输入错误: {err}")
                preview_widget = getattr(self.main_window, 'vhal_result_preview', None)
                if preview_widget is not None:
                    preview_widget.setPlainText(f"输入错误：{err}")
                return

            from Function_Moudle.vhal_warning_inject_thread import VhalWarningInjectThread
            vhal_value = VhalWarningInjectThread.compute_vhal_value(warning_id, sub_status)
            self._vhal_render_preview(warning_id, sub_status, vhal_value)

            # 在主日志区简要回显
            self.main_window.textBrowser.append(
                f"[VHAL] 生成命令 | WarningID=0x{warning_id:04X}({warning_id}) "
                f"subStatus=0x{sub_status:04X}({sub_status}) "
                f"=> vhalValue=0x{vhal_value:08X}({vhal_value})"
            )
            log_method_result(
                "vhal_warning_generate_command", True,
                f"WarningID={warning_id} subStatus={sub_status} vhalValue={vhal_value}"
            )
        except Exception as e:
            log_method_result("vhal_warning_generate_command", False, str(e))
            self.main_window.textBrowser.append(f"[VHAL] 生成命令失败: {e}")

    def vhal_warning_execute_command(self):
        """【执行命令】按钮：解析输入、计算 vhalValue 并下发到设备"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        log_button_click("vhal_execute_command_button", "VHAL 告警注入-执行命令")

        if device_id not in devices_id_lst:
            log_method_result("vhal_warning_execute_command", False, "设备未连接")
            self.main_window.textBrowser.append("设备未连接！")
            return

        try:
            warning_id, sub_status, err = self._vhal_read_inputs()
            if err:
                log_method_result("vhal_warning_execute_command", False, err)
                self.main_window.textBrowser.append(f"[VHAL] 输入错误: {err}")
                return

            from Function_Moudle.vhal_warning_inject_thread import VhalWarningInjectThread
            vhal_value = VhalWarningInjectThread.compute_vhal_value(warning_id, sub_status)
            # 同步刷新预览，避免用户看到的与实际执行不一致
            self._vhal_render_preview(warning_id, sub_status, vhal_value)

            current_connection_mode = getattr(self.main_window, 'connection_mode', 'adb') or 'adb'
            current_u2_device = getattr(self.main_window, 'd', None)

            self.main_window.vhal_warning_inject_thread = VhalWarningInjectThread(
                device_id=device_id,
                warning_id=warning_id,
                sub_status=sub_status,
                connection_mode=current_connection_mode,
                u2_device=current_u2_device,
                action='inject'
            )
            self.main_window.vhal_warning_inject_thread.progress_signal.connect(self.main_window.textBrowser.append)
            self.main_window.vhal_warning_inject_thread.result_signal.connect(self.main_window.textBrowser.append)
            self.main_window.vhal_warning_inject_thread.start()

            log_method_result(
                "vhal_warning_execute_command", True,
                f"VHAL 告警注入线程已启动 | 设备: {device_id} | vhalValue={vhal_value}"
            )
        except Exception as e:
            log_method_result("vhal_warning_execute_command", False, str(e))
            self.main_window.textBrowser.append(f"[VHAL] 执行命令失败: {e}")

    def vhal_warning_clear_warning(self):
        """【清除告警】按钮：直接下发 vhalValue=0 的注入命令"""
        device_id = self.get_selected_device()
        devices_id_lst = self.get_new_device_lst()

        log_button_click("vhal_clear_warning_button", "VHAL 告警注入-清除告警")

        if device_id not in devices_id_lst:
            log_method_result("vhal_warning_clear_warning", False, "设备未连接")
            self.main_window.textBrowser.append("设备未连接！")
            return

        try:
            from Function_Moudle.vhal_warning_inject_thread import VhalWarningInjectThread

            current_connection_mode = getattr(self.main_window, 'connection_mode', 'adb') or 'adb'
            current_u2_device = getattr(self.main_window, 'd', None)

            # 清除告警时 warning_id/sub_status 不参与计算，vhalValue 固定为 0
            self.main_window.vhal_warning_inject_thread = VhalWarningInjectThread(
                device_id=device_id,
                warning_id=0,
                sub_status=0,
                connection_mode=current_connection_mode,
                u2_device=current_u2_device,
                action='clear'
            )
            self.main_window.vhal_warning_inject_thread.progress_signal.connect(self.main_window.textBrowser.append)
            self.main_window.vhal_warning_inject_thread.result_signal.connect(self.main_window.textBrowser.append)
            self.main_window.vhal_warning_inject_thread.start()

            # 同步刷新预览为清除告警命令
            preview_widget = getattr(self.main_window, 'vhal_result_preview', None)
            if preview_widget is not None:
                dummy = VhalWarningInjectThread(device_id=None)
                shell_cmd = dummy.build_shell_command(0)
                preview_widget.setPlainText(
                    f"[清除告警] vhalValue = 0\n"
                    f"\n"
                    f"完整 adb 命令：\n"
                    f"adb -s {device_id} shell {shell_cmd}"
                )

            log_method_result(
                "vhal_warning_clear_warning", True,
                f"VHAL 清除告警线程已启动 | 设备: {device_id}"
            )
        except Exception as e:
            log_method_result("vhal_warning_clear_warning", False, str(e))
            self.main_window.textBrowser.append(f"[VHAL] 清除告警失败: {e}")

    def vhal_warning_update_preview(self, *args):
        """输入框/设备变化时实时刷新预览（不执行）

        可由 vhal_warning_id_input.textChanged / vhal_sub_status_input.textChanged /
        ComboxButton.textActivated 触发。输入非法时静默忽略（不弹错），
        避免用户输入过程中频繁报错干扰。
        """
        try:
            warning_id, sub_status, err = self._vhal_read_inputs()
            if err:
                # 输入未完成或非法，清空预览即可
                preview_widget = getattr(self.main_window, 'vhal_result_preview', None)
                if preview_widget is not None:
                    preview_widget.setPlainText("")
                return
            from Function_Moudle.vhal_warning_inject_thread import VhalWarningInjectThread
            vhal_value = VhalWarningInjectThread.compute_vhal_value(warning_id, sub_status)
            self._vhal_render_preview(warning_id, sub_status, vhal_value)
        except Exception as e:
            logger.warning(f"刷新 VHAL 告警注入预览失败: {e}")
