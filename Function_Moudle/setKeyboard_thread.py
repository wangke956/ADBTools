# -*- coding: utf-8 -*-
"""
设置输入法线程 - 支持 U2 和 ADB 两种模式

功能：
1. 列出设备上所有可用的输入法
2. 设置设备默认输入法
3. 获取当前默认输入法
"""

from PyQt5.QtCore import QThread, pyqtSignal
import subprocess
import logging

logger = logging.getLogger("ADBTools.SetKeyboard")


class SetKeyboardThread(QThread):
    """设置输入法线程 - 支持 U2 和 ADB 双模式"""

    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)
    # 列出输入法时发送的列表信号
    input_methods_signal = pyqtSignal(list)
    # 当前输入法信号
    current_method_signal = pyqtSignal(str)

    def __init__(self, device_id, mode='list', target_method=None,
                 connection_mode='adb', u2_device=None):
        """
        初始化线程

        Args:
            device_id: 设备 ID（ADB 模式使用）
            mode: 操作模式
                  'list'  - 列出所有可用输入法
                  'set'   - 设置指定输入法为默认
                  'get'   - 获取当前默认输入法
            target_method: 要设置的输入法（mode='set' 时使用）
            connection_mode: 连接模式 ('u2' 或 'adb')
            u2_device: U2 设备对象（仅 U2 模式使用）
        """
        super().__init__()
        self.device_id = device_id
        self.mode = mode
        self.target_method = target_method
        self.connection_mode = connection_mode
        self.u2_device = u2_device

    def run(self):
        """执行入口 - 根据模式分发"""
        try:
            logger.info(f"线程启动: mode={self.mode}, connection_mode={self.connection_mode}, "
                        f"device_id={self.device_id}, has_u2={self.u2_device is not None}")
            if self.connection_mode == 'u2' and self.u2_device:
                self._run_u2()
            elif self.connection_mode == 'adb':
                self._run_adb()
            else:
                logger.error(f"无效的连接模式: connection_mode={self.connection_mode}, u2_device={self.u2_device}")
                self.error_signal.emit(f"设备未连接或连接模式无效 (mode={self.connection_mode})")
        except Exception as e:
            logger.error(f"执行异常: {e}", exc_info=True)
            self.error_signal.emit(f"执行失败: {str(e)}")

    # ==================== U2 模式 ====================

    def _run_u2(self):
        """U2 模式下执行"""
        d = self.u2_device
        if d is None:
            self.error_signal.emit("U2 设备连接无效")
            return

        if self.mode == 'list':
            self._list_methods_u2(d)
        elif self.mode == 'set':
            self._set_method_u2(d)
        elif self.mode == 'get':
            self._get_current_method_u2(d)

    def _list_methods_u2(self, d):
        """U2 模式：列出所有可用输入法"""
        self.progress_signal.emit("[U2] 正在获取设备输入法列表...")
        result = d.shell("ime list -s")
        output = result.output if hasattr(result, 'output') else str(result)
        methods = self._parse_methods_output(output)

        if methods:
            self.progress_signal.emit(f"[U2] 找到 {len(methods)} 个输入法")
            self.input_methods_signal.emit(methods)
        else:
            self.error_signal.emit("[U2] 未找到任何输入法")

    def _set_method_u2(self, d):
        """U2 模式：设置默认输入法"""
        if not self.target_method:
            self.error_signal.emit("未指定要设置的输入法")
            return

        self.progress_signal.emit(f"[U2] 正在设置输入法: {self.target_method}")
        d.shell(f"ime set {self.target_method}")

        # 验证设置结果
        result = d.shell("settings get secure default_input_method")
        output = result.output if hasattr(result, 'output') else str(result)
        current = output.strip()

        if self.target_method in current:
            self.result_signal.emit(f"[U2] 输入法已设置为: {self.target_method}")
        else:
            self.result_signal.emit(
                f"[U2] 已发送设置命令，当前默认输入法: {current}"
            )

    def _get_current_method_u2(self, d):
        """U2 模式：获取当前默认输入法"""
        self.progress_signal.emit("[U2] 正在获取当前输入法...")
        result = d.shell("settings get secure default_input_method")
        output = result.output if hasattr(result, 'output') else str(result)
        current = output.strip()
        self.current_method_signal.emit(current)
        self.result_signal.emit(f"[U2] 当前默认输入法: {current}")

    # ==================== ADB 模式 ====================

    def _run_adb(self):
        """ADB 模式下执行"""
        # 检查设备连接
        from Function_Moudle.adb_device_utils import check_device_connection
        is_connected, error_msg = check_device_connection(self.device_id)
        if not is_connected:
            self.error_signal.emit(error_msg)
            return

        if self.mode == 'list':
            self._list_methods_adb()
        elif self.mode == 'set':
            self._set_method_adb()
        elif self.mode == 'get':
            self._get_current_method_adb()

    def _list_methods_adb(self):
        """ADB 模式：列出所有可用输入法"""
        self.progress_signal.emit("[ADB] 正在获取设备输入法列表...")
        command = f"adb -s {self.device_id} shell ime list -s"
        logger.debug(f"执行命令: {command}")
        result = subprocess.run(
            command, shell=True, capture_output=True,
            text=True, encoding='utf-8', errors='ignore', timeout=15
        )

        logger.debug(f"returncode={result.returncode}, stdout={result.stdout.strip()!r}, stderr={result.stderr.strip()!r}")

        # 优先从 stdout 解析（ADB 有时返回非零退出码但 stdout 仍有有效数据）
        stdout_text = result.stdout.strip()
        if stdout_text:
            methods = self._parse_methods_output(stdout_text)
            if methods:
                self.progress_signal.emit(f"[ADB] 找到 {len(methods)} 个输入法")
                self.input_methods_signal.emit(methods)
                return

        # stdout 无有效数据时，检查 returncode 和 stderr
        if result.returncode != 0:
            stderr_text = result.stderr.strip()
            error_detail = stderr_text if stderr_text else stdout_text
            self.error_signal.emit(f"[ADB] 获取输入法列表失败(returncode={result.returncode}): {error_detail}")
        else:
            self.error_signal.emit("[ADB] 未找到任何输入法（设备可能未安装输入法）")

    def _set_method_adb(self):
        """ADB 模式：设置默认输入法"""
        if not self.target_method:
            self.error_signal.emit("未指定要设置的输入法")
            return

        self.progress_signal.emit(f"[ADB] 正在设置输入法: {self.target_method}")
        command = f"adb -s {self.device_id} shell ime set {self.target_method}"
        logger.debug(f"执行命令: {command}")
        result = subprocess.run(
            command, shell=True, capture_output=True,
            text=True, encoding='utf-8', errors='ignore', timeout=15
        )

        logger.debug(f"set returncode={result.returncode}, stdout={result.stdout.strip()!r}, stderr={result.stderr.strip()!r}")

        # 验证设置结果（无论 returncode 如何都尝试验证）
        verify_cmd = f"adb -s {self.device_id} shell settings get secure default_input_method"
        verify_result = subprocess.run(
            verify_cmd, shell=True, capture_output=True,
            text=True, encoding='utf-8', errors='ignore', timeout=10
        )
        current = verify_result.stdout.strip() if verify_result.stdout.strip() else "未知"

        if self.target_method in current:
            self.result_signal.emit(f"[ADB] 输入法已设置为: {self.target_method}")
        elif result.returncode == 0:
            self.result_signal.emit(
                f"[ADB] 已发送设置命令，当前默认输入法: {current}"
            )
        else:
            stderr_text = result.stderr.strip() if result.stderr else "未知错误"
            self.error_signal.emit(f"[ADB] 设置输入法失败: {stderr_text}")

    def _get_current_method_adb(self):
        """ADB 模式：获取当前默认输入法"""
        self.progress_signal.emit("[ADB] 正在获取当前输入法...")
        command = f"adb -s {self.device_id} shell settings get secure default_input_method"
        result = subprocess.run(
            command, shell=True, capture_output=True,
            text=True, encoding='utf-8', errors='ignore', timeout=10
        )

        current = result.stdout.strip()
        if current:
            self.current_method_signal.emit(current)
            self.result_signal.emit(f"[ADB] 当前默认输入法: {current}")
        else:
            stderr_text = result.stderr.strip() if result.stderr else "无输出"
            self.error_signal.emit(f"[ADB] 获取当前输入法失败: {stderr_text}")

    # ==================== 公共工具方法 ====================

    @staticmethod
    def _parse_methods_output(output):
        """
        解析 ime list -s 的输出为输入法列表

        Args:
            output: adb shell ime list -s 的输出文本

        Returns:
            list: 输入法包名/组件名列表
        """
        methods = []
        if not output:
            return methods
        for line in output.strip().split('\n'):
            line = line.strip()
            if line and '/' in line:
                methods.append(line)
        return methods
