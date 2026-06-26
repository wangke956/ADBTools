from PyQt5.QtCore import QThread, pyqtSignal
import subprocess

class VoiceStopRecordThread(QThread):
    """停止语音录制线程 - 支持U2和ADB两种模式"""
    
    voice_stop_record_signal = pyqtSignal(str)

    def __init__(self, device_id=None, connection_mode='adb', u2_device=None):
        """
        初始化线程
        
        Args:
            device_id: 设备ID（ADB模式使用）
            connection_mode: 连接模式 ('u2' 或 'adb')
            u2_device: U2设备对象（仅当connection_mode='u2'时使用）
        """
        super().__init__()
        self.device_id = device_id
        self.connection_mode = connection_mode
        self.u2_device = u2_device

    def run(self):
        """执行停止录音操作"""
        try:
            # 检查设备连接是否有效
            if self.connection_mode == 'u2':
                if not self.u2_device:
                    self.voice_stop_record_signal.emit("U2设备连接无效，无法停止录音")
                    return
            elif self.connection_mode == 'adb':
                if not self.device_id:
                    self.voice_stop_record_signal.emit("设备ID无效，无法停止录音")
                    return
            else:
                self.voice_stop_record_signal.emit(f"不支持的连接模式: {self.connection_mode}")
                return
            
            command = 'am broadcast -n com.microsoft.assistant.client/.VAExtendBroadcastReceiver --es cmd "DisableAudioDump"'
            
            if self.connection_mode == 'u2' and self.u2_device:
                # U2模式执行命令
                res = self.u2_device.shell(command)
                # 处理不同格式的返回值
                if hasattr(res, 'output'):
                    output = str(res.output).strip() if hasattr(res, 'output') else ""
                else:
                    output = str(res).strip() if res else ""
                self.voice_stop_record_signal.emit(f'录音停止成功：{output}')
            elif self.connection_mode == 'adb':
                # ADB模式执行命令
                adb_command = f'adb -s {self.device_id} shell {command}'
                res = subprocess.run(adb_command, shell=True, capture_output=True, text=True, timeout=30)
                if res.returncode == 0:
                    self.voice_stop_record_signal.emit(f'录音停止成功：{res.stdout.strip()}')
                else:
                    error_msg = res.stderr.strip() if res.stderr else '未知错误'
                    self.voice_stop_record_signal.emit(f'录音停止失败：{error_msg}')
                    
        except subprocess.TimeoutExpired:
            self.voice_stop_record_signal.emit('录音停止超时')
        except Exception as e:
            self.voice_stop_record_signal.emit(f'录音停止失败：{str(e)}')