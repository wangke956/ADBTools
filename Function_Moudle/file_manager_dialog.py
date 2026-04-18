# -*- coding: utf-8 -*-
"""
文件管理对话框 - 提供设备文件浏览、上传、下载、删除功能
"""

import os
import stat
import subprocess
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QLineEdit, QComboBox, QMessageBox, QProgressBar,
    QHeaderView, QMenu, QAction, QInputDialog, QWidget, QFileDialog,
    QTextEdit, QApplication, QSplitter
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMimeData, QUrl
from PyQt5.QtGui import QIcon, QCursor, QDropEvent, QDrag
from PyQt5 import uic

from Function_Moudle.dialog_styles import apply_dialog_style, DIALOG_STYLE
from logger_manager import get_logger

logger = get_logger("ADBTools.FileManager")


class LocalFileTree(QTreeWidget):
    """本地文件树 - 支持拖拽文件到设备"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setDragDropMode(QTreeWidget.DragOnly)
    
    def startDrag(self, supportedActions):
        """重写拖拽开始事件 - 设置文件URL"""
        selected_items = self.selectedItems()
        if not selected_items:
            return
        
        mime_data = QMimeData()
        urls = []
        
        for item in selected_items:
            data = item.data(0, Qt.UserRole)
            if isinstance(data, dict) and 'path' in data:
                file_path = data['path']
                if os.path.exists(file_path):
                    urls.append(QUrl.fromLocalFile(file_path))
        
        if urls:
            mime_data.setUrls(urls)
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            drag.exec_(Qt.CopyAction)


class DeviceFileTree(QTreeWidget):
    """设备文件树 - 支持拖放上传"""
    
    # 定义信号：拖放文件上传
    files_dropped = pyqtSignal(list)  # 传递文件路径列表
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
    
    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        """拖拽移动事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """拖放事件 - 处理文件上传"""
        if event.mimeData().hasUrls():
            files = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if os.path.exists(file_path):
                    files.append(file_path)
            if files:
                self.files_dropped.emit(files)
            event.acceptProposedAction()
        else:
            event.ignore()


class DeviceListThread(QThread):
    """获取设备文件列表的线程"""
    finished_signal = pyqtSignal(list)  # 返回文件列表
    error_signal = pyqtSignal(str)  # 返回错误信息
    
    def __init__(self, device_id, path, connection_mode='adb', d=None):
        super().__init__()
        self.device_id = device_id
        self.path = path
        self.connection_mode = connection_mode
        self.d = d  # uiautomator2设备对象
    
    def run(self):
        try:
            files = []
            # 确保路径以斜杠结尾，以便正确显示目录内容而非链接本身
            path = self.path.rstrip('/') + '/'
            
            # 判断是否使用U2模式：必须是u2模式且有有效的d对象
            use_u2 = (self.connection_mode == 'u2' and self.d is not None)
            
            logger.info(f"DeviceListThread: device_id={self.device_id}, path={path}, mode={self.connection_mode}, use_u2={use_u2}")
            
            if use_u2:
                # 使用uiautomator2方式，不使用-L避免跟随符号链接导致重复
                result = self.d.shell(f'ls -la "{path}" 2>/dev/null')
                output = result.output if hasattr(result, 'output') else str(result)
            else:
                # 使用ADB命令，不使用-L避免跟随符号链接导致重复
                cmd = f'adb -s {self.device_id} shell ls -la "{path}"'
                logger.info(f"执行命令: {cmd}")
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                output = result.stdout
                logger.info(f"命令输出长度: {len(output)}, stderr: {result.stderr[:100] if result.stderr else 'None'}")
            
            # 解析ls -la输出
            lines = output.strip().split('\n')
            logger.info(f"解析行数: {len(lines)}")
            
            # 用于去重的集合
            seen_names = set()
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('total '):
                    continue
                # Android ls -la 格式: drwxr-xr-x  29 root root 820 2009-01-01 05:30 filename
                # 符号链接格式: lrwxrwxrwx   1 root root   21 2009-01-01 00:00 sdcard -> /storage/self/primary
                # 共8列: 权限 链接数 所有者 组 大小 日期 时间 文件名
                parts = line.split(None, 7)  # 最多分割成8部分，文件名可能含空格
                logger.info(f"解析行: '{line}' -> parts={len(parts)}: {parts}")
                if len(parts) >= 8:
                    is_link = line.startswith('l')
                    is_dir = line.startswith('d')
                    
                    # 解析文件名（可能包含 -> 目标路径）
                    name_part = parts[7] if len(parts) > 7 else ''
                    
                    if is_link and ' -> ' in name_part:
                        # 符号链接: 分离名称和目标
                        name, link_target = name_part.split(' -> ', 1)
                        name = name.strip()
                        link_target = link_target.strip()
                    else:
                        name = name_part
                        link_target = None
                    
                    # 跳过 . 和 ..
                    if name in ['.', '..']:
                        continue
                    
                    # 去重：跳过已存在的文件名
                    if name in seen_names:
                        logger.info(f"跳过重复文件: {name}")
                        continue
                    seen_names.add(name)
                    
                    file_info = {
                        'permissions': parts[0],
                        'owner': parts[2] if len(parts) > 2 else '',
                        'group': parts[3] if len(parts) > 3 else '',
                        'size': parts[4] if len(parts) > 4 else '0',
                        'date': ' '.join(parts[5:7]) if len(parts) > 6 else '',  # 日期+时间
                        'name': name,
                        'is_dir': is_dir,
                        'is_link': is_link,
                        'link_target': link_target,  # 符号链接目标
                    }
                    files.append(file_info)
                    logger.info(f"添加文件: {file_info['name']}")
            
            logger.info(f"最终文件列表数量: {len(files)}")
            self.finished_signal.emit(files)
        except Exception as e:
            self.error_signal.emit(f"获取文件列表失败: {str(e)}")


class FileTransferThread(QThread):
    """文件传输线程（上传/下载）"""
    progress_signal = pyqtSignal(str)  # 进度信息
    progress_percent = pyqtSignal(int)  # 进度百分比 (0-100)
    finished_signal = pyqtSignal(bool, str)  # 完成信号(成功/失败, 消息)
    
    def __init__(self, device_id, src_path, dst_path, transfer_type='download', 
                 connection_mode='adb', d=None):
        super().__init__()
        self.device_id = device_id
        self.src_path = src_path
        self.dst_path = dst_path
        self.transfer_type = transfer_type  # 'download' or 'upload'
        self.connection_mode = connection_mode
        self.d = d
    
    def run(self):
        try:
            if self.transfer_type == 'download':
                self._download_file()
            else:
                self._upload_file()
        except Exception as e:
            self.finished_signal.emit(False, str(e))
    
    def _download_file(self):
        """从设备下载文件"""
        self.progress_signal.emit(f"正在下载: {self.src_path}")
        
        if self.connection_mode == 'u2' and self.d:
            self.d.pull(self.src_path, self.dst_path)
            self.progress_percent.emit(100)
        else:
            # 使用 subprocess 实时读取进度
            cmd = f'adb -s {self.device_id} pull "{self.src_path}" "{self.dst_path}"'
            self._run_with_progress(cmd)
        
        self.finished_signal.emit(True, f"下载成功: {os.path.basename(self.src_path)}")
    
    def _upload_file(self):
        """上传文件到设备"""
        self.progress_signal.emit(f"正在上传: {self.src_path}")
        
        if self.connection_mode == 'u2' and self.d:
            self.d.push(self.src_path, self.dst_path)
            self.progress_percent.emit(100)
        else:
            # 使用 subprocess 实时读取进度
            cmd = f'adb -s {self.device_id} push "{self.src_path}" "{self.dst_path}"'
            self._run_with_progress(cmd)
        
        self.finished_signal.emit(True, f"上传成功: {os.path.basename(self.src_path)}")
    
    def _run_with_progress(self, cmd):
        """运行命令并解析进度"""
        import re
        
        # 获取文件大小（用于计算进度）
        file_size = 0
        if self.transfer_type == 'upload' and os.path.exists(self.src_path):
            file_size = os.path.getsize(self.src_path)
        
        process = subprocess.Popen(
            cmd, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # ADB push/pull 进度格式: [  0%] /path/to/file
        # 或: /path/to/file: 1 file pulled, 0 skipped. 15.2 MB/s (12345678 bytes in 0.800s)
        progress_pattern = re.compile(r'\[\s*(\d+)%\]')
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            
            if line:
                line = line.strip()
                # 解析进度百分比
                match = progress_pattern.search(line)
                if match:
                    percent = int(match.group(1))
                    self.progress_percent.emit(percent)
                    # 计算已传输大小
                    if file_size > 0:
                        transferred = int(file_size * percent / 100)
                        self.progress_signal.emit(
                            f"传输中 {percent}% ({self._format_size(transferred)}/{self._format_size(file_size)})"
                        )
                    else:
                        self.progress_signal.emit(f"传输中 {percent}%")
        
        if process.returncode != 0:
            raise Exception(f"传输失败 (返回码: {process.returncode})")
    
    def _format_size(self, size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


class BatchFileTransferThread(QThread):
    """批量文件传输线程"""
    progress_signal = pyqtSignal(str)  # 进度信息
    progress_percent = pyqtSignal(int)  # 总体进度百分比 (0-100)
    file_progress_signal = pyqtSignal(int, int, str)  # 当前文件索引, 总文件数, 文件名
    finished_signal = pyqtSignal(int, int)  # 完成信号(成功数, 失败数)
    
    def __init__(self, device_id, file_paths, dst_dir, transfer_type='upload', 
                 connection_mode='adb', d=None):
        super().__init__()
        self.device_id = device_id
        self.file_paths = file_paths
        self.dst_dir = dst_dir
        self.transfer_type = transfer_type  # 'upload' or 'download'
        self.connection_mode = connection_mode
        self.d = d
    
    def run(self):
        success_count = 0
        fail_count = 0
        total = len(self.file_paths)
        
        for i, src_path in enumerate(self.file_paths):
            file_name = os.path.basename(src_path)
            
            # 发送当前文件进度
            self.file_progress_signal.emit(i + 1, total, file_name)
            
            # 计算总体进度百分比
            base_percent = int((i / total) * 100)
            self.progress_percent.emit(base_percent)
            
            if self.transfer_type == 'upload':
                # 上传：src_path 是本地文件，dst 是设备路径
                dst_path = self.dst_dir.rstrip('/') + '/' + file_name
                self.progress_signal.emit(f"上传中 ({i+1}/{total}): {file_name}")
                
                try:
                    if self.connection_mode == 'u2' and self.d:
                        self.d.push(src_path, dst_path)
                    else:
                        cmd = f'adb -s {self.device_id} push "{src_path}" "{dst_path}"'
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
                        if result.returncode != 0:
                            raise Exception(result.stderr)
                    success_count += 1
                    logger.info(f"上传成功: {file_name}")
                except Exception as e:
                    fail_count += 1
                    logger.error(f"上传失败: {file_name} - {str(e)}")
            else:
                # 下载：src_path 是设备文件，dst 是本地路径
                dst_path = os.path.join(self.dst_dir, file_name)
                self.progress_signal.emit(f"下载中 ({i+1}/{total}): {file_name}")
                
                try:
                    if self.connection_mode == 'u2' and self.d:
                        self.d.pull(src_path, dst_path)
                    else:
                        cmd = f'adb -s {self.device_id} pull "{src_path}" "{dst_path}"'
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
                        if result.returncode != 0:
                            raise Exception(result.stderr)
                    success_count += 1
                    logger.info(f"下载成功: {file_name}")
                except Exception as e:
                    fail_count += 1
                    logger.error(f"下载失败: {file_name} - {str(e)}")
        
        # 完成时发送100%
        self.progress_percent.emit(100)
        self.finished_signal.emit(success_count, fail_count)


class FileDeleteThread(QThread):
    """文件删除线程"""
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, device_id, path, is_dir=False, connection_mode='adb', d=None):
        super().__init__()
        self.device_id = device_id
        self.path = path
        self.is_dir = is_dir
        self.connection_mode = connection_mode
        self.d = d
    
    def run(self):
        try:
            self.progress_signal.emit(f"正在删除: {self.path}")
            
            if self.is_dir:
                rm_cmd = f'rm -rf "{self.path}"'
            else:
                rm_cmd = f'rm "{self.path}"'
            
            if self.connection_mode == 'u2' and self.d:
                result = self.d.shell(rm_cmd)
            else:
                cmd = f'adb -s {self.device_id} shell {rm_cmd}'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
                if result.returncode != 0:
                    raise Exception(result.stderr)
            
            self.finished_signal.emit(True, f"删除成功: {os.path.basename(self.path)}")
        except Exception as e:
            self.finished_signal.emit(False, f"删除失败: {str(e)}")


class RenameThread(QThread):
    """重命名文件/文件夹线程"""
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, device_id, old_path, new_path, connection_mode='adb', d=None):
        super().__init__()
        self.device_id = device_id
        self.old_path = old_path
        self.new_path = new_path
        self.connection_mode = connection_mode
        self.d = d
    
    def run(self):
        try:
            mv_cmd = f'mv "{self.old_path}" "{self.new_path}"'
            
            if self.connection_mode == 'u2' and self.d:
                self.d.shell(mv_cmd)
            else:
                cmd = f'adb -s {self.device_id} shell {mv_cmd}'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    raise Exception(result.stderr)
            
            self.finished_signal.emit(True, "重命名成功")
        except Exception as e:
            self.finished_signal.emit(False, f"重命名失败: {str(e)}")


class ChmodThread(QThread):
    """修改文件权限线程"""
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, device_id, path, permissions, connection_mode='adb', d=None):
        super().__init__()
        self.device_id = device_id
        self.path = path
        self.permissions = permissions
        self.connection_mode = connection_mode
        self.d = d
    
    def run(self):
        try:
            chmod_cmd = f'chmod "{self.permissions}" "{self.path}"'
            
            if self.connection_mode == 'u2' and self.d:
                result = self.d.shell(chmod_cmd)
            else:
                cmd = f'adb -s {self.device_id} shell {chmod_cmd}'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    raise Exception(result.stderr)
            
            self.finished_signal.emit(True, "权限修改成功")
        except Exception as e:
            self.finished_signal.emit(False, f"权限修改失败: {str(e)}")


class FolderUploadThread(QThread):
    """文件夹上传线程 - 递归上传整个文件夹到设备"""
    progress_signal = pyqtSignal(str)  # 进度信息
    progress_percent = pyqtSignal(int)  # 进度百分比 (0-100)
    file_progress_signal = pyqtSignal(int, int)  # 当前文件数, 总文件数
    finished_signal = pyqtSignal(int, int, int)  # 成功数, 失败数, 跳过数
    
    def __init__(self, device_id, local_folder, device_folder, connection_mode='adb', d=None):
        super().__init__()
        self.device_id = device_id
        self.local_folder = local_folder
        self.device_folder = device_folder
        self.connection_mode = connection_mode
        self.d = d
    
    def run(self):
        success_count = 0
        fail_count = 0
        skip_count = 0
        
        # 获取文件夹名称
        folder_name = os.path.basename(self.local_folder)
        target_folder = self.device_folder.rstrip('/') + '/' + folder_name
        
        # 统计总文件数
        total_files = sum(len(files) for _, _, files in os.walk(self.local_folder))
        current_file = 0
        
        self.progress_signal.emit(f"准备上传文件夹: {folder_name} ({total_files} 个文件)")
        
        # 在设备上创建根目录
        if not self._create_device_dir(target_folder):
            self.finished_signal.emit(0, 0, 0)
            return
        
        # 递归遍历本地文件夹
        for root, dirs, files in os.walk(self.local_folder):
            # 计算相对路径
            rel_path = os.path.relpath(root, self.local_folder)
            if rel_path == '.':
                rel_path = ''
            
            # 在设备上创建子目录
            for dir_name in dirs:
                if rel_path:
                    device_subdir = f"{target_folder}/{rel_path}/{dir_name}".replace('\\', '/')
                else:
                    device_subdir = f"{target_folder}/{dir_name}"
                self._create_device_dir(device_subdir)
            
            # 上传文件
            for file_name in files:
                current_file += 1
                local_file = os.path.join(root, file_name)
                
                if rel_path:
                    device_file = f"{target_folder}/{rel_path}/{file_name}".replace('\\', '/')
                else:
                    device_file = f"{target_folder}/{file_name}"
                
                self.file_progress_signal.emit(current_file, total_files)
                # 计算进度百分比
                percent = int((current_file / total_files) * 100) if total_files > 0 else 0
                self.progress_percent.emit(percent)
                self.progress_signal.emit(f"上传中 ({current_file}/{total_files}): {file_name}")
                
                try:
                    if self.connection_mode == 'u2' and self.d:
                        self.d.push(local_file, device_file)
                    else:
                        cmd = f'adb -s {self.device_id} push "{local_file}" "{device_file}"'
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
                        if result.returncode != 0:
                            raise Exception(result.stderr)
                    success_count += 1
                    logger.info(f"上传成功: {file_name}")
                except Exception as e:
                    fail_count += 1
                    logger.error(f"上传失败: {file_name} - {str(e)}")
        
        self.progress_percent.emit(100)
        self.finished_signal.emit(success_count, fail_count, skip_count)
    
    def _create_device_dir(self, dir_path):
        """在设备上创建目录"""
        try:
            mkdir_cmd = f'mkdir -p "{dir_path}"'
            
            if self.connection_mode == 'u2' and self.d:
                self.d.shell(mkdir_cmd)
            else:
                cmd = f'adb -s {self.device_id} shell {mkdir_cmd}'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    logger.error(f"创建目录失败: {dir_path}")
                    return False
            return True
        except Exception as e:
            logger.error(f"创建目录异常: {dir_path} - {str(e)}")
            return False


class FolderDownloadThread(QThread):
    """文件夹下载线程 - 从设备递归下载文件夹到本地"""
    progress_signal = pyqtSignal(str)  # 进度信息
    progress_percent = pyqtSignal(int)  # 进度百分比 (0-100)
    file_progress_signal = pyqtSignal(int, int)  # 当前文件数, 总文件数
    finished_signal = pyqtSignal(int, int, int)  # 成功数, 失败数, 跳过数
    
    def __init__(self, device_id, device_folder, local_folder, connection_mode='adb', d=None):
        super().__init__()
        self.device_id = device_id
        self.device_folder = device_folder
        self.local_folder = local_folder
        self.connection_mode = connection_mode
        self.d = d
    
    def run(self):
        success_count = 0
        fail_count = 0
        skip_count = 0
        
        # 获取文件夹名称
        folder_name = self.device_folder.rstrip('/').split('/')[-1]
        target_folder = os.path.join(self.local_folder, folder_name)
        
        # 统计总文件数
        total_files = self._count_files_recursive(self.device_folder)
        current_file = 0
        
        self.progress_signal.emit(f"准备下载文件夹: {folder_name} ({total_files} 个文件)")
        
        # 在本地创建根目录
        os.makedirs(target_folder, exist_ok=True)
        
        # 递归下载
        success_count, fail_count, skip_count, current_file = self._download_recursive(
            self.device_folder, target_folder, current_file, total_files
        )
        
        self.progress_percent.emit(100)
        self.finished_signal.emit(success_count, fail_count, skip_count)
    
    def _count_files_recursive(self, device_path):
        """递归统计设备文件夹中的文件数量"""
        count = 0
        try:
            if self.connection_mode == 'u2' and self.d:
                result = self.d.shell(f'ls -la "{device_path}"')
                output = result.output if hasattr(result, 'output') else str(result)
            else:
                cmd = f'adb -s {self.device_id} shell ls -la "{device_path}"'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                output = result.stdout
            
            lines = output.strip().split('\n')
            for line in lines:
                line = line.strip()
                if not line or line.startswith('total '):
                    continue
                
                parts = line.split(None, 7)
                if len(parts) >= 8:
                    is_dir = line.startswith('d')
                    name_part = parts[7] if len(parts) > 7 else ''
                    
                    # 处理符号链接
                    if ' -> ' in name_part:
                        name = name_part.split(' -> ')[0].strip()
                    else:
                        name = name_part
                    
                    if name in ['.', '..']:
                        continue
                    
                    full_path = f"{device_path.rstrip('/')}/{name}"
                    
                    if is_dir:
                        count += self._count_files_recursive(full_path)
                    else:
                        count += 1
        except Exception as e:
            logger.error(f"统计文件数失败: {device_path} - {str(e)}")
        
        return count
    
    def _download_recursive(self, device_path, local_path, current_file, total_files):
        """递归下载文件夹"""
        success_count = 0
        fail_count = 0
        skip_count = 0
        
        try:
            if self.connection_mode == 'u2' and self.d:
                result = self.d.shell(f'ls -la "{device_path}"')
                output = result.output if hasattr(result, 'output') else str(result)
            else:
                cmd = f'adb -s {self.device_id} shell ls -la "{device_path}"'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                output = result.stdout
            
            lines = output.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('total '):
                    continue
                
                parts = line.split(None, 7)
                if len(parts) >= 8:
                    is_dir = line.startswith('d')
                    is_link = line.startswith('l')
                    name_part = parts[7] if len(parts) > 7 else ''
                    
                    # 处理符号链接
                    if ' -> ' in name_part:
                        name = name_part.split(' -> ')[0].strip()
                    else:
                        name = name_part
                    
                    if name in ['.', '..']:
                        continue
                    
                    device_full_path = f"{device_path.rstrip('/')}/{name}"
                    local_full_path = os.path.join(local_path, name)
                    
                    if is_dir:
                        # 创建本地目录并递归下载
                        os.makedirs(local_full_path, exist_ok=True)
                        s, f, sk, current_file = self._download_recursive(
                            device_full_path, local_full_path, current_file, total_files
                        )
                        success_count += s
                        fail_count += f
                        skip_count += sk
                    elif not is_link:  # 跳过符号链接
                        # 下载文件
                        current_file += 1
                        self.file_progress_signal.emit(current_file, total_files)
                        # 计算进度百分比
                        percent = int((current_file / total_files) * 100) if total_files > 0 else 0
                        self.progress_percent.emit(percent)
                        self.progress_signal.emit(f"下载中 ({current_file}/{total_files}): {name}")
                        
                        try:
                            if self.connection_mode == 'u2' and self.d:
                                self.d.pull(device_full_path, local_full_path)
                            else:
                                cmd = f'adb -s {self.device_id} pull "{device_full_path}" "{local_full_path}"'
                                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
                                if result.returncode != 0:
                                    raise Exception(result.stderr)
                            success_count += 1
                            logger.info(f"下载成功: {name}")
                        except Exception as e:
                            fail_count += 1
                            logger.error(f"下载失败: {name} - {str(e)}")
                    else:
                        # 符号链接跳过
                        skip_count += 1
        except Exception as e:
            logger.error(f"遍历目录失败: {device_path} - {str(e)}")
        
        return success_count, fail_count, skip_count, current_file


class TextReadThread(QThread):
    """读取设备文本文件线程"""
    finished_signal = pyqtSignal(bool, str, str)  # success, content, error_msg
    
    def __init__(self, device_id, path, connection_mode='adb', d=None):
        super().__init__()
        self.device_id = device_id
        self.path = path
        self.connection_mode = connection_mode
        self.d = d
    
    def run(self):
        try:
            if self.connection_mode == 'u2' and self.d:
                result = self.d.shell(f'cat "{self.path}"')
                # ShellResponse 对象需要提取 output 属性或转换为字符串
                if hasattr(result, 'output'):
                    content = result.output
                else:
                    content = str(result)
            else:
                cmd = f'adb -s {self.device_id} shell cat "{self.path}"'
                result = subprocess.run(cmd, shell=True, capture_output=True, timeout=60)
                # 尝试多种编码
                for encoding in ['utf-8', 'gbk', 'latin-1']:
                    try:
                        content = result.stdout.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    content = result.stdout.decode('utf-8', errors='replace')
            
            self.finished_signal.emit(True, content, "")
        except Exception as e:
            self.finished_signal.emit(False, "", str(e))


class TextWriteThread(QThread):
    """写入设备文本文件线程"""
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, device_id, path, content, connection_mode='adb', d=None):
        super().__init__()
        self.device_id = device_id
        self.path = path
        self.content = content
        self.connection_mode = connection_mode
        self.d = d
    
    def run(self):
        try:
            # 创建临时文件
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(self.content)
                temp_path = f.name
            
            try:
                # 先上传临时文件到设备临时位置
                temp_device_path = '/data/local/tmp/temp_edit.txt'
                
                if self.connection_mode == 'u2' and self.d:
                    self.d.push(temp_path, temp_device_path)
                    self.d.shell(f'cat "{temp_device_path}" > "{self.path}"')
                    self.d.shell(f'rm "{temp_device_path}"')
                else:
                    # 上传临时文件
                    cmd = f'adb -s {self.device_id} push "{temp_path}" "{temp_device_path}"'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                    if result.returncode != 0:
                        raise Exception(result.stderr)
                    
                    # 复制到目标位置
                    cmd = f'adb -s {self.device_id} shell cp "{temp_device_path}" "{self.path}"'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                    if result.returncode != 0:
                        raise Exception(result.stderr)
                    
                    # 清理临时文件
                    subprocess.run(f'adb -s {self.device_id} shell rm "{temp_device_path}"', shell=True, timeout=10)
            finally:
                # 删除本地临时文件
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
            self.finished_signal.emit(True, "保存成功")
        except Exception as e:
            self.finished_signal.emit(False, f"保存失败: {str(e)}")


class FileManagerDialog(QDialog):
    """文件管理对话框"""
    
    def __init__(self, parent=None, device_id=None, connection_mode='adb', d=None):
        super().__init__(parent)
        self.device_id = device_id
        self.connection_mode = connection_mode
        self.d = d  # uiautomator2设备对象
        
        # 当前路径
        self.device_current_path = '/sdcard'
        self.local_current_path = os.path.expanduser('~')
        
        # 线程引用
        self.list_thread = None
        self.transfer_thread = None
        self.batch_transfer_thread = None
        self.delete_thread = None
        self.rename_thread = None
        self.chmod_thread = None
        self.text_read_thread = None
        self.text_write_thread = None
        self.folder_upload_thread = None
        self.folder_download_thread = None
        
        # 动态加载UI文件
        import sys
        
        ui_file = None
        
        # 方法1：从程序所在目录加载（onedir模式下，程序在安装目录）
        try:
            executable_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            ui_file = os.path.join(executable_dir, 'file_manager_ui.ui')
        except:
            pass
        
        # 方法2：从项目根目录加载（开发环境）
        if not ui_file or not os.path.exists(ui_file):
            try:
                ui_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'file_manager_ui.ui')
            except:
                pass
        
        # 方法3：从当前模块目录加载（兼容旧版本）
        if not ui_file or not os.path.exists(ui_file):
            try:
                ui_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'file_manager_ui.ui')
            except:
                pass
        
        # 最终检查
        if not ui_file or not os.path.exists(ui_file):
            # 提供调试信息
            error_msg = f"找不到UI文件\n\n"
            error_msg += f"尝试的路径:\n"
            try:
                error_msg += f"  1. {os.path.dirname(os.path.abspath(sys.argv[0]))}/file_manager_ui.ui\n"
                error_msg += f"  2. {os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/file_manager_ui.ui\n"
                error_msg += f"  3. {os.path.dirname(os.path.abspath(__file__))}/file_manager_ui.ui\n"
            except:
                pass
            if ui_file:
                error_msg += f"\n最后尝试: {ui_file}\n"
            error_msg += f"\n请确保 file_manager_ui.ui 文件存在于程序安装目录中。"
            raise FileNotFoundError(error_msg)
        
        logger.info(f"加载UI文件: {ui_file}")
        uic.loadUi(ui_file, self)
        
        # 应用样式
        apply_dialog_style(self)
        
        # 设置窗口标题
        if device_id:
            self.setWindowTitle(f"文件管理器 - 设备: {device_id}")
        
        # 初始化控件属性
        self._init_controls()
        
        # 连接信号槽
        self._connect_signals()
        
        # 刷新文件列表
        self._refresh_device_files()
        self._refresh_local_files()
    
    def _init_controls(self):
        """初始化控件属性（从UI文件加载后）"""
        # 设置初始路径
        self.devicePathEdit.setText(self.device_current_path)
        self.localPathEdit.setText(self.local_current_path)
        
        # 设置树形控件属性
        self.deviceTree.setHeaderLabels(['名称', '大小', '权限', '修改日期'])
        self.deviceTree.setColumnWidth(0, 200)
        self.deviceTree.setSortingEnabled(True)
        self.deviceTree.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.deviceTree.setContextMenuPolicy(Qt.CustomContextMenu)
        
        self.localTree.setHeaderLabels(['名称', '大小', '类型', '修改日期'])
        self.localTree.setColumnWidth(0, 200)
        self.localTree.setSortingEnabled(True)
        self.localTree.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.localTree.setContextMenuPolicy(Qt.CustomContextMenu)
        
        # 设置分割器比例
        self.splitter.setSizes([500, 500])
        
        # 隐藏进度条
        self.progressBar.setVisible(False)
        self.progressBar.setFixedHeight(16)
        
        # 设置状态栏样式
        self.statusLabel.setStyleSheet("color: #909090; font-size: 11px;")
        
        # 统一两个面板的背景色
        panel_style = """
            QWidget#deviceWidget {
                background-color: #1a1a2e;
            }
            QWidget#localWidget {
                background-color: #1a1a2e;
            }
        """
        self.deviceWidget.setStyleSheet(panel_style)
        self.localWidget.setStyleSheet(panel_style)
        
        # 设置按钮提示文本
        self.btnDeviceUp.setToolTip("返回上级目录")
        self.btnRefreshDevice.setToolTip("刷新文件列表")
        self.btnDownload.setToolTip("下载选中的文件到本地")
        self.btnNewFolderDevice.setToolTip("在设备上新建文件夹")
        self.btnLocalUp.setToolTip("返回上级目录")
        self.btnRefreshLocal.setToolTip("刷新文件列表")
        self.btnUpload.setToolTip("上传选中的文件或文件夹到设备")
        self.btnSelectFile.setToolTip("选择要上传的文件")
        self.btnBrowseDir.setToolTip("浏览选择本地目录")
        
        # 统一所有工具栏按钮的样式（颜色、大小、悬停效果）
        from PyQt5.QtCore import QSize
        
        # 统一定义按钮样式
        button_style = """
            QPushButton {
                background-color: #2c3e50;
                color: #ffffff;
                border: 1px solid #34495e;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 13px;
                font-weight: bold;
                min-width: 80px;
                min-height: 32px;
            }
            QPushButton:hover {
                background-color: #34495e;
                border: 1px solid #5a6c7d;
            }
            QPushButton:pressed {
                background-color: #1a252f;
                border: 1px solid #2c3e50;
            }
        """
        
        # 应用到所有工具栏按钮
        toolbar_buttons = [
            self.btnDeviceUp, self.btnRefreshDevice, self.btnDownload, self.btnNewFolderDevice,
            self.btnLocalUp, self.btnRefreshLocal, self.btnUpload, self.btnSelectFile, self.btnBrowseDir
        ]
        
        for btn in toolbar_buttons:
            btn.setStyleSheet(button_style)
            btn.setSizePolicy(btn.sizePolicy().horizontalPolicy(), btn.sizePolicy().verticalPolicy())
            btn.setMinimumSize(QSize(80, 32))
    
    def _connect_signals(self):
        """连接信号槽"""
        # 路径导航
        self.devicePathEdit.returnPressed.connect(self._navigate_device_path)
        self.btnDeviceGo.clicked.connect(self._navigate_device_path)
        self.localPathEdit.returnPressed.connect(self._navigate_local_path)
        self.btnLocalGo.clicked.connect(self._navigate_local_path)
        
        # 设备文件操作
        self.btnDeviceUp.clicked.connect(self._device_go_up)
        self.btnRefreshDevice.clicked.connect(self._refresh_device_files)
        self.btnDownload.clicked.connect(self._download_selected)
        self.btnNewFolderDevice.clicked.connect(self._create_folder_on_device)
        
        # 本地文件操作
        self.btnLocalUp.clicked.connect(self._local_go_up)
        self.btnRefreshLocal.clicked.connect(self._refresh_local_files)
        self.btnUpload.clicked.connect(self._upload_selected)
        self.btnSelectFile.clicked.connect(self._select_local_file)
        self.btnBrowseDir.clicked.connect(self._browse_local_directory)
        
        # 树形控件事件
        self.deviceTree.itemDoubleClicked.connect(self._on_device_item_double_clicked)
        self.deviceTree.customContextMenuRequested.connect(self._show_device_context_menu)
        self.deviceTree.files_dropped.connect(self._on_files_dropped)
        
        self.localTree.itemDoubleClicked.connect(self._on_local_item_double_clicked)
        self.localTree.customContextMenuRequested.connect(self._show_local_context_menu)
    
    def _refresh_device_files(self):
        """刷新设备文件列表"""
        self.deviceTree.clear()
        self.statusLabel.setText("正在获取设备文件列表...")
        
        self.list_thread = DeviceListThread(
            self.device_id, 
            self.device_current_path,
            self.connection_mode,
            self.d
        )
        self.list_thread.finished_signal.connect(self._on_device_list_ready)
        self.list_thread.error_signal.connect(self._on_list_error)
        self.list_thread.start()
    
    def _on_device_list_ready(self, files):
        """设备文件列表准备好"""
        logger.info(f"_on_device_list_ready 被调用，文件数量: {len(files)}")
        self.deviceTree.clear()
        
        for file_info in files:
            name = file_info['name']
            is_dir = file_info['is_dir']
            is_link = file_info['is_link']
            link_target = file_info.get('link_target')
            
            # 显示名称：符号链接显示为 name -> target
            display_name = f"{name} -> {link_target}" if is_link and link_target else name
            
            # 符号链接的大小通常很小，如果是链接到目录，显示 <LINK>
            if is_link:
                size_str = '<LINK>' if not file_info['size'].isdigit() or int(file_info['size']) < 100 else self._format_size(int(file_info['size']))
            else:
                size_str = '<DIR>' if is_dir else self._format_size(int(file_info['size']) if file_info['size'].isdigit() else 0)
            
            item = QTreeWidgetItem([
                display_name,
                size_str,
                file_info['permissions'],
                file_info['date']
            ])
            item.setData(0, Qt.UserRole, file_info)
            
            # 设置图标
            if is_link:
                # 符号链接使用链接图标
                item.setIcon(0, self.style().standardIcon(self.style().SP_FileLinkIcon))
            elif is_dir:
                item.setIcon(0, self.style().standardIcon(self.style().SP_DirIcon))
            else:
                item.setIcon(0, self.style().standardIcon(self.style().SP_FileIcon))
            
            self.deviceTree.addTopLevelItem(item)
        
        self.devicePathEdit.setText(self.device_current_path)
        self.statusLabel.setText(f"已加载 {len(files)} 个项目")
    
    def _on_list_error(self, error_msg):
        """列表获取错误"""
        self.statusLabel.setText(error_msg)
        QMessageBox.warning(self, "错误", error_msg)
    
    def _refresh_local_files(self):
        """刷新本地文件列表"""
        self.localTree.clear()
        
        try:
            # 添加返回上级目录
            # if self.local_current_path != os.path.dirname(self.local_current_path):
            #     parent_item = QTreeWidgetItem(['.. (上级目录)', '', '', ''])
            #     parent_item.setData(0, Qt.UserRole, 'parent')
            #     parent_item.setIcon(0, self.style().standardIcon(self.style().SP_DirIcon))
            #     self.localTree.addTopLevelItem(parent_item)
            
            items = os.listdir(self.local_current_path)
            for item_name in items:
                item_path = os.path.join(self.local_current_path, item_name)
                try:
                    stat_info = os.stat(item_path)
                    is_dir = stat.S_ISDIR(stat_info.st_mode)
                    size = stat_info.st_size if not is_dir else 0
                    mod_time = datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M')
                    
                    size_str = '<DIR>' if is_dir else self._format_size(size)
                    file_type = '文件夹' if is_dir else os.path.splitext(item_name)[1] or '文件'
                    
                    item = QTreeWidgetItem([
                        item_name,
                        size_str,
                        file_type,
                        mod_time
                    ])
                    item.setData(0, Qt.UserRole, {'path': item_path, 'is_dir': is_dir, 'name': item_name})
                    
                    if is_dir:
                        item.setIcon(0, self.style().standardIcon(self.style().SP_DirIcon))
                    else:
                        item.setIcon(0, self.style().standardIcon(self.style().SP_FileIcon))
                    
                    self.localTree.addTopLevelItem(item)
                except PermissionError:
                    continue
            
            self.localPathEdit.setText(self.local_current_path)
            self.statusLabel.setText(f"本地: {len(items)} 个项目")
        except Exception as e:
            self.statusLabel.setText(f"读取本地目录失败: {str(e)}")
    
    def _format_size(self, size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def _join_device_path(self, *args):
        """拼接设备路径（使用正斜杠）"""
        parts = [str(p).strip('/') for p in args if p]
        return '/' + '/'.join(parts) if parts else '/'
    
    def _navigate_device_path(self):
        """导航到设备指定路径"""
        path = self.devicePathEdit.text().strip()
        if path:
            self.device_current_path = path
            self._refresh_device_files()
    
    def _navigate_local_path(self):
        """导航到本地指定路径"""
        path = self.localPathEdit.text().strip()
        if path and os.path.isdir(path):
            self.local_current_path = path
            self._refresh_local_files()
    
    def _device_go_up(self):
        """设备返回上一级目录"""
        if self.device_current_path != '/':
            parent = self.device_current_path.rsplit('/', 1)[0]
            self.device_current_path = parent if parent else '/'
            self._refresh_device_files()
    
    def _local_go_up(self):
        """本地返回上一级目录"""
        parent = os.path.dirname(self.local_current_path)
        if parent and parent != self.local_current_path:
            self.local_current_path = parent
            self._refresh_local_files()
    
    def _browse_local_directory(self):
        """浏览选择本地目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择目录", self.local_current_path
        )
        if dir_path:
            self.local_current_path = dir_path
            self.localPathEdit.setText(dir_path)
            self._refresh_local_files()
    
    def _on_device_item_double_clicked(self, item, column):
        """设备文件双击事件"""
        data = item.data(0, Qt.UserRole)
        
        if isinstance(data, dict):
            is_dir = data.get('is_dir')
            is_link = data.get('is_link')
            
            # 目录或符号链接（可能指向目录）都可以尝试进入
            if is_dir or is_link:
                # 进入目录 - 使用正斜杠拼接
                if self.device_current_path.endswith('/'):
                    self.device_current_path = self.device_current_path + data['name']
                else:
                    self.device_current_path = self.device_current_path + '/' + data['name']
                self._refresh_device_files()
    
    def _on_local_item_double_clicked(self, item, column):
        """本地文件双击事件"""
        data = item.data(0, Qt.UserRole)
        
        if isinstance(data, dict) and data.get('is_dir'):
            # 进入目录
            self.local_current_path = data['path']
            self._refresh_local_files()
    
    def _show_device_context_menu(self, pos):
        """显示设备文件右键菜单"""
        selected_items = self.deviceTree.selectedItems()
        
        menu = QMenu(self)
        
        # 置顶：返回上级目录
        if self.device_current_path != '/':
            go_up_action = QAction("⬆ 返回上级目录", self)
            go_up_action.triggered.connect(self._device_go_up)
            menu.addAction(go_up_action)
            menu.addSeparator()
        
        if not selected_items:
            menu.exec_(self.deviceTree.viewport().mapToGlobal(pos))
            return
        
        # 单选模式
        if len(selected_items) == 1:
            item = selected_items[0]
            data = item.data(0, Qt.UserRole)
            if not isinstance(data, dict):
                return
            
            is_dir = data.get('is_dir')
            
            # 下载（自动判断文件/文件夹）
            download_action = QAction("⬇ 下载", self)
            download_action.triggered.connect(lambda: self._download_selected())
            menu.addAction(download_action)
            
            menu.addSeparator()
            
            # 重命名
            rename_action = QAction("✏ 重命名", self)
            rename_action.triggered.connect(lambda: self._rename_item(data))
            menu.addAction(rename_action)
            
            # 文本预览/编辑（仅文件）
            if not is_dir:
                # 判断是否为文本文件
                name = data.get('name', '')
                text_exts = ['.txt', '.log', '.xml', '.json', '.properties', '.conf', 
                            '.cfg', '.ini', '.sh', '.bat', '.cmd', '.py', '.js', 
                            '.html', '.css', '.md', '.yml', '.yaml', '.csv']
                if any(name.lower().endswith(ext) for ext in text_exts) or True:
                    preview_action = QAction("📝 预览/编辑", self)
                    preview_action.triggered.connect(lambda: self._preview_text_file(data))
                    menu.addAction(preview_action)
            
            menu.addSeparator()
            
            # 权限管理
            chmod_action = QAction("🔒 权限管理", self)
            chmod_action.triggered.connect(lambda: self._chmod_item(data))
            menu.addAction(chmod_action)
            
            # 删除
            delete_action = QAction("🗑 删除", self)
            delete_action.triggered.connect(lambda: self._delete_device_item(data))
            menu.addAction(delete_action)
        else:
            # 多选模式
            # 批量下载
            batch_download_action = QAction(f"⬇ 批量下载 ({len(selected_items)}项)", self)
            batch_download_action.triggered.connect(self._download_selected)
            menu.addAction(batch_download_action)
            
            menu.addSeparator()
            
            # 批量删除
            batch_delete_action = QAction(f"🗑 批量删除 ({len(selected_items)}项)", self)
            batch_delete_action.triggered.connect(self._delete_selected_device_items)
            menu.addAction(batch_delete_action)
        
        menu.exec_(self.deviceTree.viewport().mapToGlobal(pos))
    
    def _show_local_context_menu(self, pos):
        """显示本地文件右键菜单"""
        item = self.localTree.itemAt(pos)
        
        menu = QMenu(self)
        
        # 置顶：返回上级目录
        parent_path = os.path.dirname(self.local_current_path)
        if parent_path and parent_path != self.local_current_path:
            go_up_action = QAction("⬆ 返回上级目录", self)
            go_up_action.triggered.connect(self._local_go_up)
            menu.addAction(go_up_action)
            menu.addSeparator()
        
        if not item:
            # 空白处右键 - 显示新建选项
            new_folder_action = QAction("📁 新建文件夹", self)
            new_folder_action.triggered.connect(self._create_local_folder)
            menu.addAction(new_folder_action)
            
            new_file_action = QAction("📄 新建文本文件", self)
            new_file_action.triggered.connect(self._create_local_text_file)
            menu.addAction(new_file_action)
            
            paste_action = QAction("📋 粘贴", self)
            paste_action.triggered.connect(self._paste_local_files)
            # 检查剪贴板是否有内容
            if not hasattr(self, '_clipboard_files') or not self._clipboard_files:
                paste_action.setEnabled(False)
            menu.addAction(paste_action)
            
            menu.exec_(self.localTree.viewport().mapToGlobal(pos))
            return
        
        data = item.data(0, Qt.UserRole)
        if data == 'parent':
            return
        
        if isinstance(data, dict):
            is_dir = data.get('is_dir', False)
            file_path = data.get('path', '')
            
            # 上传到设备（文件和文件夹都可以）
            upload_action = QAction("⬆ 上传", self)
            upload_action.triggered.connect(lambda: self._upload_item(data))
            menu.addAction(upload_action)
            
            menu.addSeparator()
            
            # 打开文件/文件夹
            open_action = QAction("📂 打开", self)
            open_action.triggered.connect(lambda: self._open_local_item(data))
            menu.addAction(open_action)
            
            # 复制
            copy_action = QAction("📋 复制", self)
            copy_action.triggered.connect(lambda: self._copy_local_files([data]))
            menu.addAction(copy_action)
            
            # 剪切
            cut_action = QAction("✂️ 剪切", self)
            cut_action.triggered.connect(lambda: self._cut_local_files([data]))
            menu.addAction(cut_action)
            
            menu.addSeparator()
            
            # 重命名
            rename_action = QAction("✏ 重命名", self)
            rename_action.triggered.connect(lambda: self._rename_local_item(data))
            menu.addAction(rename_action)
            
            # 删除
            delete_action = QAction("🗑 删除", self)
            delete_action.triggered.connect(lambda: self._delete_local_item(data))
            menu.addAction(delete_action)
            
            # 如果是文件，添加编辑选项
            if not is_dir:
                menu.addSeparator()
                edit_action = QAction("📝 编辑文本", self)
                edit_action.triggered.connect(lambda: self._edit_local_text_file(data))
                menu.addAction(edit_action)
        
        menu.exec_(self.localTree.viewport().mapToGlobal(pos))
    
    def _download_selected(self):
        """下载选中的设备文件或文件夹"""
        selected_items = self.deviceTree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择要下载的文件或文件夹")
            return
        
        # 分离文件和文件夹
        file_paths = []
        folder_items = []
        for item in selected_items:
            data = item.data(0, Qt.UserRole)
            if isinstance(data, dict):
                if data.get('is_dir'):
                    folder_items.append(data)
                else:
                    src_path = self._join_device_path(self.device_current_path, data['name'])
                    file_paths.append(src_path)
        
        if not file_paths and not folder_items:
            QMessageBox.information(self, "提示", "请选择有效的文件或文件夹")
            return
        
        # 构建确认消息
        msg_parts = []
        if file_paths:
            msg_parts.append(f"{len(file_paths)} 个文件")
        if folder_items:
            msg_parts.append(f"{len(folder_items)} 个文件夹")
        
        reply = QMessageBox.question(
            self, '确认下载',
            f"确定要下载 {' 和 '.join(msg_parts)} 到本地吗？\n保存位置: {self.local_current_path}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            # 下载文件
            if file_paths:
                if len(file_paths) == 1:
                    # 单文件使用单文件下载
                    self._download_item(selected_items[0].data(0, Qt.UserRole))
                else:
                    # 多文件批量下载
                    self._download_files_batch(file_paths)
            # 下载文件夹
            for folder_info in folder_items:
                device_folder = self._join_device_path(self.device_current_path, folder_info['name'])
                self._do_download_folder(device_folder, self.local_current_path)
    
    def _download_files_batch(self, file_paths):
        """批量下载文件（使用线程，不阻塞界面）"""
        self.progressBar.setVisible(True)
        self.progressBar.setRange(0, 100)  # 设置进度条范围
        self.progressBar.setValue(0)
        self.statusLabel.setText(f"准备下载 {len(file_paths)} 个文件...")
        
        self.batch_transfer_thread = BatchFileTransferThread(
            self.device_id, file_paths, self.local_current_path,
            'download', self.connection_mode, self.d
        )
        self.batch_transfer_thread.progress_signal.connect(self.statusLabel.setText)
        self.batch_transfer_thread.progress_percent.connect(self.progressBar.setValue)
        self.batch_transfer_thread.finished_signal.connect(self._on_batch_transfer_finished)
        self.batch_transfer_thread.start()
    
    def _download_item(self, file_info):
        """下载单个文件"""
        src_path = self._join_device_path(self.device_current_path, file_info['name'])
        dst_path = os.path.join(self.local_current_path, file_info['name'])
        
        self.progressBar.setVisible(True)
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.statusLabel.setText(f"正在下载: {file_info['name']}")
        
        self.transfer_thread = FileTransferThread(
            self.device_id, src_path, dst_path,
            'download', self.connection_mode, self.d
        )
        self.transfer_thread.progress_signal.connect(self.statusLabel.setText)
        self.transfer_thread.progress_percent.connect(self.progressBar.setValue)
        self.transfer_thread.finished_signal.connect(self._on_transfer_finished)
        self.transfer_thread.start()
    
    def _upload_selected(self):
        """上传选中的本地文件或文件夹"""
        selected_items = self.localTree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择要上传的文件或文件夹")
            return
        
        # 分离文件和文件夹
        file_paths = []
        folder_paths = []
        for item in selected_items:
            data = item.data(0, Qt.UserRole)
            if isinstance(data, dict):
                if data.get('is_dir'):
                    folder_paths.append(data['path'])
                else:
                    file_paths.append(data['path'])
        
        if not file_paths and not folder_paths:
            QMessageBox.information(self, "提示", "请选择有效的文件或文件夹")
            return
        
        # 构建确认消息
        msg_parts = []
        if file_paths:
            msg_parts.append(f"{len(file_paths)} 个文件")
        if folder_paths:
            msg_parts.append(f"{len(folder_paths)} 个文件夹")
        
        reply = QMessageBox.question(
            self, '确认上传',
            f"确定要上传 {' 和 '.join(msg_parts)} 到设备吗？\n目标路径: {self.device_current_path}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            # 上传文件
            if file_paths:
                self._upload_files_batch(file_paths)
            # 上传文件夹
            for folder_path in folder_paths:
                self._do_upload_folder(folder_path)
    
    def _upload_item(self, file_info):
        """上传单个文件"""
        src_path = file_info['path']
        dst_path = self._join_device_path(self.device_current_path, file_info['name'])
        
        self.progressBar.setVisible(True)
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.statusLabel.setText(f"正在上传: {file_info['name']}")
        
        self.transfer_thread = FileTransferThread(
            self.device_id, src_path, dst_path,
            'upload', self.connection_mode, self.d
        )
        self.transfer_thread.progress_signal.connect(self.statusLabel.setText)
        self.transfer_thread.progress_percent.connect(self.progressBar.setValue)
        self.transfer_thread.finished_signal.connect(self._on_transfer_finished)
        self.transfer_thread.start()
    
    def _on_files_dropped(self, file_paths):
        """处理拖放文件上传"""
        if not file_paths:
            return
        
        # 分离文件和文件夹
        files = []
        folders = []
        for path in file_paths:
            if os.path.isdir(path):
                folders.append(path)
            elif os.path.isfile(path):
                files.append(path)
        
        # 显示确认对话框
        msg_parts = []
        if files:
            msg_parts.append(f"{len(files)} 个文件")
        if folders:
            msg_parts.append(f"{len(folders)} 个文件夹")
        
        msg = f"确定要上传 {' 和 '.join(msg_parts)} 到设备吗？\n目标路径: {self.device_current_path}"
        
        reply = QMessageBox.question(
            self, '确认上传', msg,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # 上传文件
        if files:
            self._upload_files_batch(files)
        
        # 上传文件夹（需要在文件上传完成后处理）
        if folders:
            # 如果有文件正在上传，等待完成后再上传文件夹
            # 简单起见，我们依次上传文件夹
            for folder_path in folders:
                self._do_upload_folder(folder_path)
    
    def _upload_files_batch(self, file_paths):
        """批量上传文件（使用线程，不阻塞界面）"""
        self.progressBar.setVisible(True)
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.statusLabel.setText(f"准备上传 {len(file_paths)} 个文件...")
        
        self.batch_transfer_thread = BatchFileTransferThread(
            self.device_id, file_paths, self.device_current_path,
            'upload', self.connection_mode, self.d
        )
        self.batch_transfer_thread.progress_signal.connect(self.statusLabel.setText)
        self.batch_transfer_thread.progress_percent.connect(self.progressBar.setValue)
        self.batch_transfer_thread.finished_signal.connect(self._on_batch_upload_finished)
        self.batch_transfer_thread.start()
    
    def _do_upload_folder(self, folder_path):
        """执行文件夹上传"""
        self.progressBar.setVisible(True)
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.statusLabel.setText(f"正在上传文件夹...")
        
        self.folder_upload_thread = FolderUploadThread(
            self.device_id, folder_path, self.device_current_path,
            self.connection_mode, self.d
        )
        self.folder_upload_thread.progress_signal.connect(self.statusLabel.setText)
        self.folder_upload_thread.progress_percent.connect(self.progressBar.setValue)
        self.folder_upload_thread.finished_signal.connect(self._on_folder_upload_finished)
        self.folder_upload_thread.start()
    
    def _on_folder_upload_finished(self, success_count, fail_count, skip_count):
        """文件夹上传完成"""
        self.progressBar.setVisible(False)
        self.statusLabel.setText(f"文件夹上传完成: 成功 {success_count} 个, 失败 {fail_count} 个")
        self._refresh_device_files()
    
    def _do_download_folder(self, device_folder, local_folder):
        """执行文件夹下载"""
        self.progressBar.setVisible(True)
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.statusLabel.setText(f"正在下载文件夹...")
        
        self.folder_download_thread = FolderDownloadThread(
            self.device_id, device_folder, local_folder,
            self.connection_mode, self.d
        )
        self.folder_download_thread.progress_signal.connect(self.statusLabel.setText)
        self.folder_download_thread.progress_percent.connect(self.progressBar.setValue)
        self.folder_download_thread.finished_signal.connect(self._on_folder_download_finished)
        self.folder_download_thread.start()
    
    def _on_folder_download_finished(self, success_count, fail_count, skip_count):
        """文件夹下载完成"""
        self.progressBar.setVisible(False)
        self.statusLabel.setText(f"文件夹下载完成: 成功 {success_count} 个, 失败 {fail_count} 个, 跳过 {skip_count} 个")
        self._refresh_local_files()
    
    def _on_batch_upload_finished(self, success_count, fail_count):
        """批量上传完成"""
        self.progressBar.setVisible(False)
        self.statusLabel.setText(f"上传完成: 成功 {success_count} 个, 失败 {fail_count} 个")
        self._refresh_device_files()
    
    def _on_batch_transfer_finished(self, success_count, fail_count):
        """批量下载完成"""
        self.progressBar.setVisible(False)
        self.statusLabel.setText(f"下载完成: 成功 {success_count} 个, 失败 {fail_count} 个")
        self._refresh_local_files()
    
    def _select_local_file(self):
        """选择本地文件或文件夹"""
        # 先询问用户是要选择文件还是文件夹
        menu = QMenu(self)
        file_action = menu.addAction("选择文件")
        folder_action = menu.addAction("选择文件夹")
        
        # 在按钮位置显示菜单
        sender = self.sender()
        if sender:
            pos = sender.mapToGlobal(sender.rect().bottomLeft())
            action = menu.exec_(pos)
        else:
            action = file_action
        
        if action == file_action:
            # 选择文件
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择要上传的文件", self.local_current_path, "所有文件 (*)"
            )
            if file_path:
                self.local_current_path = os.path.dirname(file_path)
                self._refresh_local_files()
                # 选中刚选择的文件
                for i in range(self.localTree.topLevelItemCount()):
                    item = self.localTree.topLevelItem(i)
                    if item.text(0) == os.path.basename(file_path):
                        self.localTree.setCurrentItem(item)
                        break
        elif action == folder_action:
            # 选择文件夹
            folder_path = QFileDialog.getExistingDirectory(
                self, "选择要上传的文件夹", self.local_current_path
            )
            if folder_path:
                # 直接上传选择的文件夹
                reply = QMessageBox.question(
                    self, '确认上传',
                    f"确定要上传文件夹到设备吗？\n文件夹: {os.path.basename(folder_path)}\n目标路径: {self.device_current_path}",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
                )
                if reply == QMessageBox.Yes:
                    self._do_upload_folder(folder_path)
    
    def _on_transfer_finished(self, success, message):
        """传输完成"""
        self.progressBar.setVisible(False)
        self.statusLabel.setText(message)
        
        if success:
            self._refresh_local_files()
        else:
            QMessageBox.warning(self, "传输失败", message)
    
    # ==================== 本地文件管理功能 ====================
    
    def _open_local_item(self, file_info):
        """打开本地文件或文件夹"""
        path = file_info.get('path', '')
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "错误", "文件不存在")
            return
        
        try:
            if os.path.isdir(path):
                # 打开文件夹
                os.startfile(path)  # Windows
            else:
                # 打开文件（使用默认程序）
                os.startfile(path)
        except Exception as e:
            QMessageBox.warning(self, "打开失败", f"无法打开: {str(e)}")
    
    def _copy_local_files(self, file_infos):
        """复制本地文件到剪贴板"""
        if not hasattr(self, '_clipboard_files'):
            self._clipboard_files = []
        
        self._clipboard_files = [(info.get('path'), 'copy') for info in file_infos]
        self.statusLabel.setText(f"已复制 {len(file_infos)} 个项目")
    
    def _cut_local_files(self, file_infos):
        """剪切本地文件到剪贴板"""
        if not hasattr(self, '_clipboard_files'):
            self._clipboard_files = []
        
        self._clipboard_files = [(info.get('path'), 'cut') for info in file_infos]
        self.statusLabel.setText(f"已剪切 {len(file_infos)} 个项目")
    
    def _paste_local_files(self):
        """粘贴本地文件"""
        if not hasattr(self, '_clipboard_files') or not self._clipboard_files:
            QMessageBox.information(self, "提示", "剪贴板为空")
            return
        
        try:
            success_count = 0
            fail_count = 0
            
            for src_path, operation in self._clipboard_files:
                if not os.path.exists(src_path):
                    fail_count += 1
                    continue
                
                filename = os.path.basename(src_path)
                dst_path = os.path.join(self.local_current_path, filename)
                
                # 如果目标已存在，添加序号
                if os.path.exists(dst_path):
                    name, ext = os.path.splitext(filename)
                    counter = 1
                    while os.path.exists(dst_path):
                        dst_path = os.path.join(self.local_current_path, f"{name}_{counter}{ext}")
                        counter += 1
                
                try:
                    if os.path.isdir(src_path):
                        # 复制文件夹
                        import shutil
                        shutil.copytree(src_path, dst_path)
                    else:
                        # 复制文件
                        import shutil
                        shutil.copy2(src_path, dst_path)
                    
                    # 如果是剪切操作，删除源文件
                    if operation == 'cut':
                        if os.path.isdir(src_path):
                            import shutil
                            shutil.rmtree(src_path)
                        else:
                            os.remove(src_path)
                    
                    success_count += 1
                except Exception as e:
                    fail_count += 1
                    logger.error(f"粘贴失败: {filename} - {str(e)}")
            
            # 清空剪贴板
            if all(op == 'cut' for _, op in self._clipboard_files):
                self._clipboard_files = []
            
            self.statusLabel.setText(f"粘贴完成: 成功 {success_count} 个, 失败 {fail_count} 个")
            self._refresh_local_files()
        except Exception as e:
            QMessageBox.warning(self, "粘贴失败", str(e))
    
    def _rename_local_item(self, file_info):
        """重命名本地文件/文件夹"""
        old_name = file_info.get('name', '')
        new_name, ok = QInputDialog.getText(self, "重命名", "请输入新名称:", text=old_name)
        
        if ok and new_name and new_name != old_name:
            old_path = file_info.get('path', '')
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            
            try:
                os.rename(old_path, new_path)
                self.statusLabel.setText(f"重命名成功: {old_name} -> {new_name}")
                self._refresh_local_files()
            except Exception as e:
                QMessageBox.warning(self, "重命名失败", f"无法重命名: {str(e)}")
    
    def _delete_local_item(self, file_info):
        """删除本地文件/文件夹"""
        name = file_info.get('name', '')
        is_dir = file_info.get('is_dir', False)
        
        reply = QMessageBox.question(
            self, '确认删除',
            f"确定要删除 '{name}' 吗？\n此操作不可撤销！",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            path = file_info.get('path', '')
            try:
                if is_dir:
                    import shutil
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                
                self.statusLabel.setText(f"删除成功: {name}")
                self._refresh_local_files()
            except Exception as e:
                QMessageBox.warning(self, "删除失败", f"无法删除: {str(e)}")
    
    def _create_local_folder(self):
        """在当前目录创建新文件夹"""
        folder_name, ok = QInputDialog.getText(self, "新建文件夹", "请输入文件夹名称:")
        
        if ok and folder_name:
            folder_path = os.path.join(self.local_current_path, folder_name)
            
            try:
                os.makedirs(folder_path, exist_ok=False)
                self.statusLabel.setText(f"文件夹创建成功: {folder_name}")
                self._refresh_local_files()
            except FileExistsError:
                QMessageBox.warning(self, "创建失败", f"文件夹已存在: {folder_name}")
            except Exception as e:
                QMessageBox.warning(self, "创建失败", f"无法创建文件夹: {str(e)}")
    
    def _create_local_text_file(self):
        """在当前目录创建新文本文件"""
        file_name, ok = QInputDialog.getText(self, "新建文本文件", "请输入文件名:", text="新建文本文档.txt")
        
        if ok and file_name:
            # 如果没有扩展名，添加 .txt
            if not os.path.splitext(file_name)[1]:
                file_name += '.txt'
            
            file_path = os.path.join(self.local_current_path, file_name)
            
            try:
                # 创建空文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    pass
                
                self.statusLabel.setText(f"文件创建成功: {file_name}")
                self._refresh_local_files()
                
                # 自动打开编辑
                file_info = {'path': file_path, 'name': file_name, 'is_dir': False}
                self._edit_local_text_file(file_info)
            except FileExistsError:
                QMessageBox.warning(self, "创建失败", f"文件已存在: {file_name}")
            except Exception as e:
                QMessageBox.warning(self, "创建失败", f"无法创建文件: {str(e)}")
    
    def _edit_local_text_file(self, file_info):
        """编辑本地文本文件"""
        file_path = file_info.get('path', '')
        file_name = file_info.get('name', '')
        
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # 显示编辑对话框
            dialog = LocalTextEditorDialog(self, file_path, file_name, content)
            dialog.saved_signal.connect(self._refresh_local_files)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "打开失败", f"无法打开文件: {str(e)}")
    
    def _delete_device_item(self, file_info):
        """删除设备文件"""
        reply = QMessageBox.question(
            self, '确认删除',
            f"确定要删除 '{file_info['name']}' 吗？\n此操作不可撤销！",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            path = self._join_device_path(self.device_current_path, file_info['name'])
            
            self.delete_thread = FileDeleteThread(
                self.device_id, path, file_info.get('is_dir', False),
                self.connection_mode, self.d
            )
            self.delete_thread.progress_signal.connect(self.statusLabel.setText)
            self.delete_thread.finished_signal.connect(self._on_delete_finished)
            self.delete_thread.start()
    
    def _on_delete_finished(self, success, message):
        """删除完成"""
        self.statusLabel.setText(message)
        if success:
            self._refresh_device_files()
        else:
            QMessageBox.warning(self, "删除失败", message)
    
    def _chmod_item(self, file_info):
        """修改文件权限"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
        
        # 创建权限管理对话框
        dialog = QDialog(self)
        dialog.setWindowTitle(f"权限管理 - {file_info['name']}")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # 当前权限显示
        current_perm = file_info.get('permissions', '???')
        layout.addWidget(QLabel(f"当前权限: <b>{current_perm}</b>"))
        
        # 权限输入
        perm_layout = QHBoxLayout()
        perm_layout.addWidget(QLabel("新权限 (如: 755):"))
        perm_edit = QLineEdit()
        perm_edit.setPlaceholderText("输入权限值 (数字或符号模式)")
        perm_layout.addWidget(perm_edit, 1)
        layout.addLayout(perm_layout)
        
        # 常用权限预设
        presets_layout = QHBoxLayout()
        presets_layout.addWidget(QLabel("常用权限:"))
        
        common_perms = [
            ("755", "所有者读写执行，组和其他读执行"),
            ("777", "所有人读写执行"),
            ("644", "所有者读写，组和其他只读"),
            ("600", "只有所有者读写"),
            ("700", "只有所有者读写执行"),
            ("775", "所有者和组读写执行，其他读执行")
        ]
        
        for perm, desc in common_perms:
            btn = QPushButton(perm)
            btn.setToolTip(desc)
            btn.clicked.connect(lambda checked, p=perm: perm_edit.setText(p))
            presets_layout.addWidget(btn)
        
        layout.addLayout(presets_layout)
        
        # 说明
        layout.addWidget(QLabel("<small>数字权限解释:<br>"
                               "第一位: 特殊权限<br>"
                               "第二位: 所有者权限 (4=读, 2=写, 1=执行)<br>"
                               "第三位: 组权限<br>"
                               "第四位: 其他用户权限</small>"))
        
        # 按钮布局
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("确定")
        btn_cancel = QPushButton("取消")
        
        def on_ok():
            permissions = perm_edit.text().strip()
            if not permissions:
                QMessageBox.warning(dialog, "输入错误", "请输入权限值")
                return
            
            # 执行权限修改
            path = self._join_device_path(self.device_current_path, file_info['name'])
            
            self.chmod_thread = ChmodThread(
                self.device_id, path, permissions,
                self.connection_mode, self.d
            )
            self.chmod_thread.finished_signal.connect(self._on_chmod_finished)
            self.chmod_thread.start()
            
            dialog.accept()
        
        btn_ok.clicked.connect(on_ok)
        btn_cancel.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
        dialog.exec_()
    
    def _on_chmod_finished(self, success, message):
        """权限修改完成"""
        self.statusLabel.setText(message)
        if success:
            self._refresh_device_files()
            QMessageBox.information(self, "操作成功", message)
        else:
            QMessageBox.warning(self, "权限修改失败", message)
    
    def _create_folder_on_device(self):
        """在设备上创建文件夹"""
        folder_name, ok = QInputDialog.getText(self, "新建文件夹", "请输入文件夹名称:")
        if ok and folder_name:
            folder_path = self._join_device_path(self.device_current_path, folder_name)
            
            try:
                mkdir_cmd = f'mkdir "{folder_path}"'
                
                if self.connection_mode == 'u2' and self.d:
                    self.d.shell(mkdir_cmd)
                else:
                    cmd = f'adb -s {self.device_id} shell {mkdir_cmd}'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                    if result.returncode != 0:
                        raise Exception(result.stderr)
                
                self.statusLabel.setText(f"文件夹创建成功: {folder_name}")
                self._refresh_device_files()
            except Exception as e:
                QMessageBox.warning(self, "创建失败", f"创建文件夹失败: {str(e)}")
    
    def _rename_item(self, file_info):
        """重命名文件/文件夹"""
        old_name = file_info.get('name', '')
        new_name, ok = QInputDialog.getText(self, "重命名", "请输入新名称:", text=old_name)
        
        if ok and new_name and new_name != old_name:
            old_path = self._join_device_path(self.device_current_path, old_name)
            new_path = self._join_device_path(self.device_current_path, new_name)
            
            self.statusLabel.setText(f"正在重命名: {old_name} -> {new_name}")
            
            self.rename_thread = RenameThread(
                self.device_id, old_path, new_path,
                self.connection_mode, self.d
            )
            self.rename_thread.finished_signal.connect(self._on_rename_finished)
            self.rename_thread.start()
    
    def _on_rename_finished(self, success, message):
        """重命名完成"""
        self.statusLabel.setText(message)
        if success:
            self._refresh_device_files()
        else:
            QMessageBox.warning(self, "重命名失败", message)
    
    def _delete_selected_device_items(self):
        """批量删除选中的设备文件"""
        selected_items = self.deviceTree.selectedItems()
        if not selected_items:
            return
        
        # 确认删除
        count = len(selected_items)
        reply = QMessageBox.question(
            self, '确认批量删除',
            f"确定要删除选中的 {count} 个项目吗？\n此操作不可撤销！",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # 批量删除
        success_count = 0
        fail_count = 0
        
        for item in selected_items:
            data = item.data(0, Qt.UserRole)
            if not isinstance(data, dict):
                continue
            
            file_name = data.get('name', '')
            path = self._join_device_path(self.device_current_path, file_name)
            
            self.statusLabel.setText(f"正在删除: {file_name}")
            QApplication.processEvents()  # 更新UI
            
            try:
                if data.get('is_dir'):
                    rm_cmd = f'rm -rf "{path}"'
                else:
                    rm_cmd = f'rm "{path}"'
                
                if self.connection_mode == 'u2' and self.d:
                    self.d.shell(rm_cmd)
                else:
                    cmd = f'adb -s {self.device_id} shell {rm_cmd}'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
                    if result.returncode != 0:
                        raise Exception(result.stderr)
                
                success_count += 1
            except Exception as e:
                fail_count += 1
                logger.error(f"删除失败: {file_name} - {str(e)}")
        
        self.statusLabel.setText(f"删除完成: 成功 {success_count} 个, 失败 {fail_count} 个")
        self._refresh_device_files()
    
    def _preview_text_file(self, file_info):
        """预览/编辑文本文件"""
        file_name = file_info.get('name', '')
        file_path = self._join_device_path(self.device_current_path, file_name)
        
        self.statusLabel.setText(f"正在读取文件: {file_name}")
        
        self.text_read_thread = TextReadThread(
            self.device_id, file_path,
            self.connection_mode, self.d
        )
        self.text_read_thread.finished_signal.connect(
            lambda success, content, error: self._on_text_read_finished(
                success, content, error, file_path, file_name
            )
        )
        self.text_read_thread.start()
    
    def _on_text_read_finished(self, success, content, error, file_path, file_name):
        """文本读取完成"""
        if not success:
            self.statusLabel.setText(f"读取失败: {error}")
            QMessageBox.warning(self, "读取失败", f"无法读取文件: {error}")
            return
        
        self.statusLabel.setText(f"已加载: {file_name}")
        
        # 显示文本编辑对话框
        dialog = TextPreviewDialog(self, file_path, file_name, content, 
                                   self.device_id, self.connection_mode, self.d)
        dialog.saved_signal.connect(self._refresh_device_files)
        dialog.exec_()
    
    def closeEvent(self, event):
        """关闭事件"""
        # 确保线程结束
        for thread in [self.list_thread, self.transfer_thread, self.batch_transfer_thread,
                       self.delete_thread, self.rename_thread, self.chmod_thread, self.text_read_thread, 
                       self.text_write_thread, self.folder_upload_thread, self.folder_download_thread]:
            if thread and thread.isRunning():
                thread.wait(1000)
        event.accept()


class TextPreviewDialog(QDialog):
    """文本预览/编辑对话框"""
    
    saved_signal = pyqtSignal()  # 保存成功信号
    
    def __init__(self, parent, file_path, file_name, content, 
                 device_id, connection_mode, d):
        super().__init__(parent)
        self.file_path = file_path
        self.file_name = file_name
        self.original_content = content
        self.device_id = device_id
        self.connection_mode = connection_mode
        self.d = d
        self.write_thread = None
        
        self.setWindowTitle(f"编辑: {file_name}")
        self.setMinimumSize(700, 500)
        self.resize(900, 600)
        apply_dialog_style(self)
        
        from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout
        layout = QVBoxLayout(self)
        
        # 文件路径显示
        path_label = QLabel(f"📄 {file_path}")
        path_label.setStyleSheet("color: #5a9bd5; font-size: 11px;")
        layout.addWidget(path_label)
        
        # 文本编辑器
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(content)
        self.text_edit.setFontFamily("Consolas")
        self.text_edit.setFontPointSize(10)
        layout.addWidget(self.text_edit, 1)
        
        # 状态栏
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #909090;")
        layout.addWidget(self.status_label)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        btn_save = QPushButton("💾 保存")
        btn_save.clicked.connect(self._save_file)
        btn_layout.addWidget(btn_save)
        
        btn_save_as = QPushButton("💾 另存为...")
        btn_save_as.clicked.connect(self._save_as)
        btn_layout.addWidget(btn_save_as)
        
        btn_layout.addStretch()
        
        btn_cancel = QPushButton("关闭")
        btn_cancel.clicked.connect(self.close)
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)
    
    def _save_file(self):
        """保存文件"""
        content = self.text_edit.toPlainText()
        
        if content == self.original_content:
            self.status_label.setText("内容未更改")
            return
        
        self.status_label.setText("正在保存...")
        self.write_thread = TextWriteThread(
            self.device_id, self.file_path, content,
            self.connection_mode, self.d
        )
        self.write_thread.finished_signal.connect(self._on_save_finished)
        self.write_thread.start()
    
    def _on_save_finished(self, success, message):
        """保存完成"""
        self.status_label.setText(message)
        if success:
            self.original_content = self.text_edit.toPlainText()
            self.saved_signal.emit()
            QMessageBox.information(self, "保存成功", message)
        else:
            QMessageBox.warning(self, "保存失败", message)
    
    def _save_as(self):
        """另存为本地文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "另存为", self.file_name, "文本文件 (*.txt);;所有文件 (*)"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.text_edit.toPlainText())
                self.status_label.setText(f"已保存到: {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "保存失败", str(e))
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.write_thread and self.write_thread.isRunning():
            self.write_thread.wait(1000)
        event.accept()


class LocalTextEditorDialog(QDialog):
    """本地文本文件编辑对话框"""
    
    saved_signal = pyqtSignal()  # 保存成功信号
    
    def __init__(self, parent, file_path, file_name, content):
        super().__init__(parent)
        self.file_path = file_path
        self.file_name = file_name
        self.original_content = content
        
        self.setWindowTitle(f"编辑: {file_name}")
        self.setMinimumSize(700, 500)
        self.resize(900, 600)
        apply_dialog_style(self)
        
        from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout
        layout = QVBoxLayout(self)
        
        # 文件路径显示
        path_label = QLabel(f"📄 {file_path}")
        path_label.setStyleSheet("color: #5a9bd5; font-size: 11px;")
        layout.addWidget(path_label)
        
        # 文本编辑器
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(content)
        self.text_edit.setFontFamily("Consolas")
        self.text_edit.setFontPointSize(10)
        layout.addWidget(self.text_edit, 1)
        
        # 状态栏
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #909090;")
        layout.addWidget(self.status_label)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        btn_save = QPushButton("💾 保存")
        btn_save.clicked.connect(self._save_file)
        btn_layout.addWidget(btn_save)
        
        btn_save_as = QPushButton("💾 另存为...")
        btn_save_as.clicked.connect(self._save_as)
        btn_layout.addWidget(btn_save_as)
        
        btn_layout.addStretch()
        
        btn_cancel = QPushButton("关闭")
        btn_cancel.clicked.connect(self.close)
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)
    
    def _save_file(self):
        """保存文件"""
        content = self.text_edit.toPlainText()
        
        if content == self.original_content:
            self.status_label.setText("内容未更改")
            return
        
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.original_content = content
            self.status_label.setText("保存成功")
            self.saved_signal.emit()
            QMessageBox.information(self, "保存成功", "文件已保存")
        except Exception as e:
            QMessageBox.warning(self, "保存失败", f"无法保存文件: {str(e)}")
    
    def _save_as(self):
        """另存为"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "另存为", self.file_name, "文本文件 (*.txt);;所有文件 (*)"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.text_edit.toPlainText())
                self.status_label.setText(f"已保存到: {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "保存失败", str(e))
