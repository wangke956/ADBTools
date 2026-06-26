from PyQt5.QtCore import QThread, pyqtSignal
import os
import subprocess


class RemoveRecordFileThread(QThread):
    """删除录音文件线程 - 支持U2和ADB两种模式"""

    signal_remove_voice_record_file = pyqtSignal(str)
    progress_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)

    def __init__(self, device_id=None, device_record_file_path=None, connection_mode='adb', u2_device=None):
        """
        初始化线程
        
        Args:
            device_id: 设备ID（ADB模式使用）
            device_record_file_path: 设备上的录音文件路径
            connection_mode: 连接模式 ('u2' 或 'adb')
            u2_device: U2设备对象（仅当connection_mode='u2'时使用）
        """
        super().__init__()
        self.device_id = device_id
        self.device_record_file_path = device_record_file_path
        self.connection_mode = connection_mode
        self.u2_device = u2_device
        # 兼容旧版本：如果传入了d参数，判断是U2设备还是其他
        print(f"连接模式: {self.connection_mode}, U2设备: {self.u2_device is not None}")

    def run(self):
        """执行删除录音文件操作"""
        try:
            # 检查设备连接是否有效
            if self.connection_mode == 'u2':
                if not self.u2_device:
                    self.signal_remove_voice_record_file.emit("U2设备连接无效，无法删除录音文件")
                    return
            elif self.connection_mode == 'adb':
                if not self.device_id:
                    self.signal_remove_voice_record_file.emit("设备ID无效，无法删除录音文件")
                    return
            else:
                self.signal_remove_voice_record_file.emit(f"不支持的连接模式: {self.connection_mode}")
                return
            
            self.signal_remove_voice_record_file.emit('正在删除录音文件...')
            
            if self.connection_mode == 'u2' and self.u2_device:
                # U2模式删除文件
                self._remove_file_u2()
            elif self.connection_mode == 'adb':
                # ADB模式删除文件
                self._remove_file_adb()
            
        except Exception as e:
            self.signal_remove_voice_record_file.emit(f'删除录音文件失败！{e}')
    
    def _remove_file_u2(self):
        """U2模式下删除文件"""
        try:
            res = self.u2_device.shell(f'rm -rf {self.device_record_file_path}')
            
            # 处理不同格式的返回值
            if hasattr(res, 'exit_code'):
                # uiautomator2 新版本返回对象
                exit_code = res.exit_code
                output = str(res.output).strip() if hasattr(res, 'output') else ""
            else:
                # 旧版本或其他情况
                exit_code = 0
                output = str(res).strip() if res else ""
            
            if exit_code == 0 or not output:
                self.signal_remove_voice_record_file.emit('录音文件删除成功！')
            else:
                self.signal_remove_voice_record_file.emit(f'删除录音文件失败: {output}')
                
        except Exception as e:
            self.signal_remove_voice_record_file.emit(f'U2模式删除录音文件失败: {str(e)}')
    
    def _remove_file_adb(self):
        """ADB模式下删除文件"""
        try:
            # 使用ADB命令删除文件
            command = f"adb -s {self.device_id} shell rm -rf {self.device_record_file_path}"
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.signal_remove_voice_record_file.emit('录音文件删除成功！')
            else:
                error_msg = result.stderr.strip() if result.stderr else '未知错误'
                self.signal_remove_voice_record_file.emit(f'删除录音文件失败: {error_msg}')
                
        except subprocess.TimeoutExpired:
            self.signal_remove_voice_record_file.emit('删除录音文件超时')
        except Exception as e:
            self.signal_remove_voice_record_file.emit(f'ADB模式删除录音文件失败: {str(e)}')



