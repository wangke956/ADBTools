import time
from PyQt5.QtCore import QThread, pyqtSignal
import os

class VoicePullRecordFileThread(QThread):
    """拉取录音文件线程 - 支持U2和ADB两种模式"""
    
    progress_signal = pyqtSignal(str)  # 进度信号
    result_signal = pyqtSignal(str)    # 结果信号
    signal_voice_pull_record_file = pyqtSignal(str)  # 兼容旧版本的信号

    def __init__(self, device_id=None, file_path=None, device_record_file_path=None, connection_mode='adb', u2_device=None):
        """
        初始化线程
        
        Args:
            device_id: 设备ID（ADB模式使用）
            file_path: 本地保存路径
            device_record_file_path: 设备上的录音文件路径
            connection_mode: 连接模式 ('u2' 或 'adb')
            u2_device: U2设备对象（仅当connection_mode='u2'时使用）
        """
        super().__init__()
        self.device_id = device_id
        self.record_file_path = file_path
        # 设备上的目录路径
        self.remote_dir_path = device_record_file_path
        self.connection_mode = connection_mode
        self.u2_device = u2_device

    def run(self):
        """执行拉取录音文件操作"""
        try:
            # 检查设备连接是否有效
            if self.connection_mode == 'u2':
                if not self.u2_device:
                    self.progress_signal.emit("U2设备连接无效，无法拉取录音文件")
                    return
            elif self.connection_mode == 'adb':
                if not self.device_id:
                    self.progress_signal.emit("设备ID无效，无法拉取录音文件")
                    return
            else:
                self.progress_signal.emit(f"不支持的连接模式: {self.connection_mode}")
                return
            
            # 检查并创建本地目录
            if not os.path.exists(self.record_file_path):
                try:
                    os.makedirs(self.record_file_path)
                    msg = f"已创建目录: {self.record_file_path}"
                    self.progress_signal.emit(msg)
                    self.signal_voice_pull_record_file.emit(msg)
                except OSError as e:
                    error_msg = f"创建目录时出现错误: {e}"
                    self.progress_signal.emit(error_msg)
                    self.signal_voice_pull_record_file.emit(error_msg)
                    return
            
            start_msg = '开始录音文件拉取...'
            self.progress_signal.emit(start_msg)
            self.signal_voice_pull_record_file.emit(start_msg)
            
            if self.connection_mode == 'u2' and self.u2_device:
                # U2模式：使用pull方法拉取文件
                self._pull_file_u2()
            elif self.connection_mode == 'adb':
                # ADB模式：使用adb pull命令
                self._pull_file_adb()
            
        except Exception as e:
            error_msg = f'执行命令失败：{e}'
            self.progress_signal.emit(error_msg)
            self.signal_voice_pull_record_file.emit(error_msg)
    
    def _pull_file_u2(self):
        """U2模式下拉取文件"""
        try:
            # 使用uiautomator2的pull方法
            import tempfile
            import shutil
            
            # 先在设备上确认文件或目录存在
            check_res = self.u2_device.shell(f'test -e {self.remote_dir_path} && echo "exists" || echo "not_exists"')
            if hasattr(check_res, 'output'):
                check_output = str(check_res.output).strip()
            else:
                check_output = str(check_res).strip()
            
            if 'not_exists' in check_output:
                error_msg = f'设备上的路径不存在: {self.remote_dir_path}'
                self.progress_signal.emit(error_msg)
                self.signal_voice_pull_record_file.emit(error_msg)
                return
            
            # 创建临时目录用于中转
            temp_dir = tempfile.mkdtemp()
            try:
                # 使用pull方法拉取文件/目录
                self.u2_device.pull(self.remote_dir_path, temp_dir)
                
                # 将文件移动到目标目录
                temp_contents = os.listdir(temp_dir)
                for item in temp_contents:
                    src = os.path.join(temp_dir, item)
                    dst = os.path.join(self.record_file_path, item)
                    if os.path.isdir(src):
                        if os.path.exists(dst):
                            shutil.rmtree(dst)
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)
                
                success_msg = '录音文件拉取完成！（U2模式）'
                self.result_signal.emit(success_msg)
                self.signal_voice_pull_record_file.emit(success_msg)
            finally:
                # 清理临时目录
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except Exception as e:
            error_msg = f'U2模式拉取文件失败：{str(e)}'
            self.progress_signal.emit(error_msg)
            self.signal_voice_pull_record_file.emit(error_msg)
    
    def _pull_file_adb(self):
        """ADB模式下拉取文件"""
        global subprocess
        try:
            import subprocess
            
            # 使用adb pull命令
            command = f'adb -s {self.device_id} pull {self.remote_dir_path} "{self.record_file_path}"'
            
            cmd_msg = f'执行命令：{command}'
            self.progress_signal.emit(cmd_msg)
            self.signal_voice_pull_record_file.emit(cmd_msg)
            
            res = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
            
            if res.returncode == 0:
                success_msg = '录音文件拉取完成！（ADB模式）'
                self.result_signal.emit(success_msg)
                self.signal_voice_pull_record_file.emit(success_msg)
            else:
                error_msg = res.stderr.strip() if res.stderr else '未知错误'
                self.progress_signal.emit(f'拉取失败：{error_msg}')
                self.signal_voice_pull_record_file.emit(f'拉取失败：{error_msg}')
                
        except subprocess.TimeoutExpired:
            self.progress_signal.emit('拉取文件超时')
            self.signal_voice_pull_record_file.emit('拉取文件超时')
        except Exception as e:
            error_msg = f'ADB模式拉取文件失败：{str(e)}'
            self.progress_signal.emit(error_msg)
            self.signal_voice_pull_record_file.emit(error_msg)
