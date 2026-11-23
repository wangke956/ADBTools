#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VHAL 告警注入线程 - ZXD项目 Inbox 告警测试

将用户输入的 WarningID + subStatus 组合为 vhalValue，并通过
    adb shell cmd car_service inject-vhal-event <propertyId> <areaId> <vhalValue>
下发到设备。支持 U2 / ADB 双模式。

固定属性：
    propertyId = 0x21410214
    areaId     = 0
计算公式：
    vhalValue = (warningId << 16) | subStatus
"""

from PyQt6.QtCore import QThread, pyqtSignal
import subprocess


class VhalWarningInjectThread(QThread):
    """VHAL 告警注入线程（支持 ADB / U2 双模式）"""

    # 固定 VHAL 属性
    PROPERTY_ID_HEX = "0x21410214"
    AREA_ID = 0

    # 16 位无符号上限
    MAX_UINT16 = 0xFFFF

    progress_signal = pyqtSignal(str)   # 过程输出
    result_signal = pyqtSignal(str)     # 最终结果输出

    def __init__(self, device_id=None, warning_id=None, sub_status=None,
                 connection_mode='adb', u2_device=None, action='inject'):
        """
        Args:
            device_id: 设备 ID（ADB 模式使用）
            warning_id: WarningID（int，已经解析完成）
            sub_status: subStatus（int，已经解析完成）
            connection_mode: 'adb' 或 'u2'
            u2_device: uiautomator2 设备对象（仅 u2 模式使用）
            action: 'inject'（注入 vhalValue） 或 'clear'（清除告警，vhalValue=0）
        """
        super().__init__()
        self.device_id = device_id
        self.warning_id = warning_id if warning_id is not None else 0
        self.sub_status = sub_status if sub_status is not None else 0
        self.connection_mode = connection_mode
        self.u2_device = u2_device
        self.action = action

    # ---------------------- 工具方法 ----------------------
    @staticmethod
    def parse_number(text, field_name="值"):
        """解析用户输入的数值字符串

        支持：
            - "0x1A26"（带 0x 前缀的十六进制）
            - "1A26"（纯十六进制字符串，包含字母 a-f/A-F 时按十六进制解析）
            - "6694"（纯数字，按十进制解析）

        Returns:
            (int, None) 成功
            (None, str) 失败并返回错误信息
        """
        if text is None:
            return None, f"{field_name}不能为空"
        s = str(text).strip()
        if not s:
            return None, f"{field_name}不能为空"

        # 带 0x/0X 前缀，明确按十六进制解析
        if s.lower().startswith("0x"):
            hex_part = s[2:]
            if not hex_part:
                return None, f"{field_name}格式错误：0x 后必须跟十六进制数字"
            try:
                return int(hex_part, 16), None
            except ValueError:
                return None, f"{field_name}格式错误：非法的十六进制字符串 '{s}'"

        # 纯数字（可能含 a-f/A-F）——先尝试按十六进制解析（若含字母），否则按十进制
        has_alpha = any(c.isalpha() for c in s)
        if has_alpha:
            # 含字母，必须是合法的十六进制
            try:
                return int(s, 16), None
            except ValueError:
                return None, f"{field_name}格式错误：非法的十六进制字符串 '{s}'"
        else:
            # 纯数字：按十进制解析（同时也允许用户手动指定十六进制）
            try:
                return int(s, 10), None
            except ValueError:
                return None, f"{field_name}格式错误：非法的十进制字符串 '{s}'"

    @classmethod
    def validate_range(cls, value, field_name):
        """校验数值是否在 16 位无符号范围内"""
        if value is None:
            return f"{field_name}不能为空"
        if value < 0:
            return f"{field_name}不能为负数（当前值：{value}）"
        if value > cls.MAX_UINT16:
            return (f"{field_name}超出 16 位无符号上限 0xFFFF"
                    f"（当前值：0x{value:X} = {value}）")
        return None

    @classmethod
    def compute_vhal_value(cls, warning_id, sub_status):
        """计算 vhalValue = (warningId << 16) | subStatus"""
        return ((warning_id & 0xFFFF) << 16) | (sub_status & 0xFFFF)

    def build_shell_command(self, vhal_value):
        """构造设备端 shell 命令（不含 'adb -s xxx shell' 前缀）
        
        vhalValue 以十进制格式传递（用户要求）。
        当 vhalValue > 2147483647 (Java int 最大值) 时，转换为有符号整数表示，
        避免设备端报 NumberFormatException。
        例如：2420113408 (0x90400000) -> -1874853888
        """
        # Java int 范围：-2147483648 到 2147483647
        # 超出时转换为有符号表示
        JAVA_INT_MAX = 2147483647
        if vhal_value > JAVA_INT_MAX:
            signed_value = vhal_value - 4294967296  # 2^32
        else:
            signed_value = vhal_value
        return (f"cmd car_service inject-vhal-event "
                f"{self.PROPERTY_ID_HEX} {self.AREA_ID} {signed_value}")

    # ---------------------- 主流程 ----------------------
    def run(self):
        try:
            # 1) 校验设备连接
            if self.connection_mode == 'u2':
                if not self.u2_device:
                    self.result_signal.emit("U2 设备连接无效，无法执行 VHAL 告警注入")
                    return
            elif self.connection_mode == 'adb':
                if not self.device_id:
                    self.result_signal.emit("设备 ID 无效，无法执行 VHAL 告警注入")
                    return
            else:
                self.result_signal.emit(f"不支持的连接模式: {self.connection_mode}")
                return

            # 2) 计算 vhalValue
            if self.action == 'clear':
                vhal_value = 0
                self.progress_signal.emit("[清除告警] vhalValue = 0")
            else:
                # 校验范围
                err = self.validate_range(self.warning_id, "WarningID")
                if err:
                    self.result_signal.emit(err)
                    return
                err = self.validate_range(self.sub_status, "subStatus")
                if err:
                    self.result_signal.emit(err)
                    return

                vhal_value = self.compute_vhal_value(self.warning_id, self.sub_status)
                self.progress_signal.emit(
                    f"[计算] WarningID=0x{self.warning_id:04X}({self.warning_id}) "
                    f"subStatus=0x{self.sub_status:04X}({self.sub_status}) "
                    f"=> vhalValue=0x{vhal_value:08X}({vhal_value})"
                )

            # 3) 构造命令
            shell_cmd = self.build_shell_command(vhal_value)
            if self.connection_mode == 'adb':
                full_cmd = f'adb -s {self.device_id} shell {shell_cmd}'
            else:
                full_cmd = f'[U2 shell] {shell_cmd}'
            self.progress_signal.emit(f"执行命令: {full_cmd}")

            # 4) 执行
            if self.connection_mode == 'u2' and self.u2_device:
                res = self.u2_device.shell(shell_cmd)
                if hasattr(res, 'output'):
                    output = str(res.output).strip() if res.output else ""
                else:
                    output = str(res).strip() if res else ""
                self.result_signal.emit(f"命令返回: {output or '(空)'}")
            else:
                # ADB 模式：使用 subprocess 执行，30s 超时防止阻塞
                # 使用列表参数形式，避免 shell=True 引号解析问题
                # adb 路径走系统 PATH（不写死）
                adb_args = ['adb']
                if self.device_id:
                    adb_args.extend(['-s', self.device_id])
                # 转换为有符号整数表示，避免超出 Java int 范围
                JAVA_INT_MAX = 2147483647
                signed_value = vhal_value - 4294967296 if vhal_value > JAVA_INT_MAX else vhal_value
                adb_args.extend(['shell', 'cmd', 'car_service',
                                 'inject-vhal-event',
                                 self.PROPERTY_ID_HEX,
                                 str(self.AREA_ID),
                                 str(signed_value)])
                res = subprocess.run(
                    adb_args, shell=False,
                    capture_output=True, text=True,
                    encoding='utf-8', errors='replace',
                    timeout=30
                )
                if res.returncode == 0:
                    output = (res.stdout or "").strip()
                    self.result_signal.emit(f"命令返回: {output or '(空)'}")
                else:
                    err = (res.stderr or "").strip() or '未知错误'
                    self.result_signal.emit(f"命令执行失败: {err}")

        except subprocess.TimeoutExpired:
            self.result_signal.emit('VHAL 告警注入命令执行超时（>30s）')
        except FileNotFoundError:
            self.result_signal.emit('未找到 adb 可执行文件，请确认系统 PATH 已配置 adb')
        except Exception as e:
            self.result_signal.emit(f'VHAL 告警注入失败: {e}')
