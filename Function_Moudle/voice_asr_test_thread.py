from PyQt6.QtCore import QThread, pyqtSignal
import subprocess


class VoiceAsrTestThread(QThread):
    """语音识别测试线程 - 支持U2和ADB两种模式"""
    
    progress_signal = pyqtSignal(str)   # 进度信号
    result_signal = pyqtSignal(str)     # 结果信号

    def __init__(self, device_id=None, asr_text=None, connection_mode='adb', u2_device=None):
        """
        初始化线程
        
        Args:
            device_id: 设备ID（ADB模式使用）
            asr_text: 语音识别测试文本
            connection_mode: 连接模式 ('u2' 或 'adb')
            u2_device: U2设备对象（仅当connection_mode='u2'时使用）
        """
        super().__init__()
        self.device_id = device_id
        self.asr_text = asr_text
        self.connection_mode = connection_mode
        self.u2_device = u2_device

    def run(self):
        """执行语音识别测试操作"""
        try:
            # 检查设备连接是否有效
            if self.connection_mode == 'u2':
                if not self.u2_device:
                    self.result_signal.emit("U2设备连接无效，无法执行语音识别测试")
                    return
            elif self.connection_mode == 'adb':
                if not self.device_id:
                    self.result_signal.emit("设备ID无效，无法执行语音识别测试")
                    return
            else:
                self.result_signal.emit(f"不支持的连接模式: {self.connection_mode}")
                return
            
            # 构造shell命令
            command = (
                f'am broadcast -n com.microsoft.assistant.client/.VAExtendBroadcastReceiver '
                f'-a com.microsoft.assistant.action.asr_test '
                f'--es asrText "{self.asr_text}"'
            )
            
            self.progress_signal.emit(f"执行命令: {command}")
            
            if self.connection_mode == 'u2' and self.u2_device:
                # U2模式执行命令
                res = self.u2_device.shell(command)
                # 处理不同格式的返回值
                if hasattr(res, 'output'):
                    output = str(res.output).strip() if hasattr(res, 'output') else ""
                else:
                    output = str(res).strip() if res else ""
                self.result_signal.emit(f"命令返回: {output}")
            elif self.connection_mode == 'adb':
                # ADB模式执行命令
                adb_command = f'adb -s {self.device_id} shell {command}'
                res = subprocess.run(adb_command, shell=True, capture_output=True, text=True, timeout=30)
                if res.returncode == 0:
                    output = res.stdout.strip()
                    self.result_signal.emit(f"命令返回: {output}")
                else:
                    error_msg = res.stderr.strip() if res.stderr else '未知错误'
                    self.result_signal.emit(f"命令执行失败: {error_msg}")
                    
        except subprocess.TimeoutExpired:
            self.result_signal.emit('语音识别测试超时')
        except Exception as e:
            self.result_signal.emit(f'语音识别测试失败: {str(e)}')
