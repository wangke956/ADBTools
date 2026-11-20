from PyQt6.QtCore import QThread, pyqtSignal
import subprocess


class Voice3QueryThread(QThread):
    """语音3.0 指令下发线程 - 支持 ADB 和 U2 两种模式

    将用户输入的普通文本指令转换为 VOICELESS_QUERY 广播命令：
        am broadcast -n com.saicmotor.voiceservice/com.google.cloud.ml.api.cca.sample.debug.RemoteCommandReceiver
                     -a com.google.cloud.ml.api.cca.sample.VOICELESS_QUERY
                     --es query "<escaped_text>"

    其中 escaped_text 会把空格替换为 "\\ "（反斜杠+空格），以适配 Android shell 的参数解析。
    """

    # 目标广播接收器与动作
    BROADCAST_COMPONENT = (
        "com.saicmotor.voiceservice/"
        "com.google.cloud.ml.api.cca.sample.debug.RemoteCommandReceiver"
    )
    BROADCAST_ACTION = "com.google.cloud.ml.api.cca.sample.VOICELESS_QUERY"

    progress_signal = pyqtSignal(str)   # 进度/中间态输出
    result_signal = pyqtSignal(str)     # 最终结果输出

    def __init__(self, device_id=None, query_text=None,
                 connection_mode='adb', u2_device=None):
        """
        Args:
            device_id: 设备ID（ADB模式使用）
            query_text: 用户输入的原始指令文本（如 "play online music"）
            connection_mode: 'adb' 或 'u2'
            u2_device: uiautomator2 设备对象（仅 u2 模式使用）
        """
        super().__init__()
        self.device_id = device_id
        self.query_text = query_text or ""
        self.connection_mode = connection_mode
        self.u2_device = u2_device

    @staticmethod
    def escape_query(text: str) -> str:
        """按 Android shell 转义规则处理指令文本

        规则：把空格替换为 "\\ "（反斜杠+空格），确保 am broadcast 把整段文本作为单个 --es 值接收。
        其他字符保持原样（外层由双引号包裹，已能兼容大多数常见字符）。
        """
        if not text:
            return ""
        # 仅按用户示例做空格转义；制表符等空白也一并处理，防止多空白导致的分词异常
        return text.replace(" ", "\\ ")

    def build_shell_command(self) -> str:
        """构造设备端 shell 命令（不含 'adb -s xxx shell' 前缀）"""
        escaped = self.escape_query(self.query_text)
        return (
            f'am broadcast -n {self.BROADCAST_COMPONENT} '
            f'-a {self.BROADCAST_ACTION} '
            f'--es query "{escaped}"'
        )

    def run(self):
        """执行广播下发"""
        try:
            # 校验设备连接
            if self.connection_mode == 'u2':
                if not self.u2_device:
                    self.result_signal.emit("U2设备连接无效，无法执行语音3.0指令下发")
                    return
            elif self.connection_mode == 'adb':
                if not self.device_id:
                    self.result_signal.emit("设备ID无效，无法执行语音3.0指令下发")
                    return
            else:
                self.result_signal.emit(f"不支持的连接模式: {self.connection_mode}")
                return

            if not self.query_text.strip():
                self.result_signal.emit("指令文本不能为空")
                return

            shell_cmd = self.build_shell_command()

            if self.connection_mode == 'adb':
                full_cmd = f'adb -s {self.device_id} shell {shell_cmd}'
            else:
                full_cmd = f'[U2 shell] {shell_cmd}'
            self.progress_signal.emit(f"执行命令: {full_cmd}")

            if self.connection_mode == 'u2' and self.u2_device:
                # U2 模式：直接下发 shell 命令，无需拼 adb -s 前缀
                res = self.u2_device.shell(shell_cmd)
                if hasattr(res, 'output'):
                    output = str(res.output).strip() if res.output else ""
                else:
                    output = str(res).strip() if res else ""
                self.result_signal.emit(f"命令返回: {output or '(空)'}")
            else:
                # ADB 模式：使用 subprocess 执行，30s 超时防止阻塞
                adb_command = f'adb -s {self.device_id} shell {shell_cmd}'
                res = subprocess.run(
                    adb_command, shell=True,
                    capture_output=True, text=True, timeout=30
                )
                if res.returncode == 0:
                    output = (res.stdout or "").strip()
                    self.result_signal.emit(f"命令返回: {output or '(空)'}")
                else:
                    err = (res.stderr or "").strip() or '未知错误'
                    self.result_signal.emit(f"命令执行失败: {err}")

        except subprocess.TimeoutExpired:
            self.result_signal.emit('语音3.0指令下发超时')
        except Exception as e:
            self.result_signal.emit(f'语音3.0指令下发失败: {e}')
