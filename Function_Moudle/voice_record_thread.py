from PyQt5.QtCore import QThread, pyqtSignal
import subprocess

class VoiceRecordThread(QThread):
    """开始语音录制线程 - 支持U2和ADB两种模式"""
    
    progress_signal = pyqtSignal(int)
    record_signal = pyqtSignal(str)

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
        """执行开始录音操作"""
        try:
            # 检查设备连接是否有效
            if self.connection_mode == 'u2':
                if not self.u2_device:
                    self.record_signal.emit("U2设备连接无效，无法启动录音")
                    return
            elif self.connection_mode == 'adb':
                if not self.device_id:
                    self.record_signal.emit("设备ID无效，无法启动录音")
                    return
            else:
                self.record_signal.emit(f"不支持的连接模式: {self.connection_mode}")
                return
            
            command = 'am broadcast -n com.microsoft.assistant.client/.VAExtendBroadcastReceiver --es cmd "EnableAudioDump"'
            
            if self.connection_mode == 'u2' and self.u2_device:
                # U2模式执行命令
                res = self.u2_device.shell(command)
                # 处理不同格式的返回值
                if hasattr(res, 'output'):
                    output = str(res.output).strip() if hasattr(res, 'output') else ""
                else:
                    output = str(res).strip() if res else ""
                self.record_signal.emit(f'录音启动成功：{output}')
            elif self.connection_mode == 'adb':
                # ADB模式执行命令
                adb_command = f'adb -s {self.device_id} shell {command}'
                res = subprocess.run(adb_command, shell=True, capture_output=True, text=True, timeout=30)
                if res.returncode == 0:
                    self.record_signal.emit(f'录音启动成功：{res.stdout.strip()}')
                else:
                    error_msg = res.stderr.strip() if res.stderr else '未知错误'
                    self.record_signal.emit(f'录音启动失败：{error_msg}')
                    
        except subprocess.TimeoutExpired:
            self.record_signal.emit('录音启动超时')
        except Exception as e:
            self.record_signal.emit(f'录音启动失败：{str(e)}')