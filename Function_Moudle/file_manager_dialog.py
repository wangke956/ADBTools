# -*- coding: utf-8 -*-
"""
文件管理对话框 - 提供设备文件浏览、上传、下载、删除、权限管理功能
"""

import os
import stat
import subprocess
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QLineEdit, QComboBox, QMessageBox, QProgressBar,
    QHeaderView, QMenu, QAction, QInputDialog, QWidget, QFileDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QCursor

from Function_Moudle.dialog_styles import apply_dialog_style, DIALOG_STYLE
from logger_manager import get_logger

logger = get_logger("ADBTools.FileManager")


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
                # 使用uiautomator2方式，使用-L跟随符号链接
                result = self.d.shell(f'ls -laL "{path}" 2>/dev/null || ls -la "{path}"')
                output = result.output if hasattr(result, 'output') else str(result)
            else:
                # 使用ADB命令，使用-L跟随符号链接
                cmd = f'adb -s {self.device_id} shell ls -laL "{path}"'
                logger.info(f"执行命令: {cmd}")
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                output = result.stdout
                logger.info(f"命令输出长度: {len(output)}, stderr: {result.stderr[:100] if result.stderr else 'None'}")
            
            # 解析ls -la输出
            lines = output.strip().split('\n')
            logger.info(f"解析行数: {len(lines)}")
            for line in lines:
                line = line.strip()
                if not line or line.startswith('total '):
                    continue
                # Android ls -laL 格式: drwxr-xr-x  29 root root 820 2009-01-01 05:30 .
                # 共8列: 权限 链接数 所有者 组 大小 日期 时间 文件名
                parts = line.split(None, 7)  # 最多分割成8部分，文件名可能含空格
                logger.info(f"解析行: '{line}' -> parts={len(parts)}: {parts}")
                if len(parts) >= 8:
                    file_info = {
                        'permissions': parts[0],
                        'owner': parts[2] if len(parts) > 2 else '',
                        'group': parts[3] if len(parts) > 3 else '',
                        'size': parts[4] if len(parts) > 4 else '0',
                        'date': ' '.join(parts[5:7]) if len(parts) > 6 else '',  # 日期+时间
                        'name': parts[7] if len(parts) > 7 else '',
                        'is_dir': line.startswith('d'),
                        'is_link': line.startswith('l'),
                    }
                    # 跳过 . 和 ..
                    if file_info['name'] not in ['.', '..']:
                        files.append(file_info)
                        logger.info(f"添加文件: {file_info['name']}")
            
            logger.info(f"最终文件列表数量: {len(files)}")
            self.finished_signal.emit(files)
        except Exception as e:
            self.error_signal.emit(f"获取文件列表失败: {str(e)}")


class FileTransferThread(QThread):
    """文件传输线程（上传/下载）"""
    progress_signal = pyqtSignal(str)  # 进度信息
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
        else:
            cmd = f'adb -s {self.device_id} pull "{self.src_path}" "{self.dst_path}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                raise Exception(result.stderr)
        
        self.finished_signal.emit(True, f"下载成功: {os.path.basename(self.src_path)}")
    
    def _upload_file(self):
        """上传文件到设备"""
        self.progress_signal.emit(f"正在上传: {self.src_path}")
        
        if self.connection_mode == 'u2' and self.d:
            self.d.push(self.src_path, self.dst_path)
        else:
            cmd = f'adb -s {self.device_id} push "{self.src_path}" "{self.dst_path}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                raise Exception(result.stderr)
        
        self.finished_signal.emit(True, f"上传成功: {os.path.basename(self.src_path)}")


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


class PermissionChangeThread(QThread):
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
            chmod_cmd = f'chmod {self.permissions} "{self.path}"'
            
            if self.connection_mode == 'u2' and self.d:
                self.d.shell(chmod_cmd)
            else:
                cmd = f'adb -s {self.device_id} shell {chmod_cmd}'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    raise Exception(result.stderr)
            
            self.finished_signal.emit(True, f"权限修改成功: {self.permissions}")
        except Exception as e:
            self.finished_signal.emit(False, f"权限修改失败: {str(e)}")


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
        self.delete_thread = None
        self.permission_thread = None
        
        self._init_ui()
        self._refresh_device_files()
        self._refresh_local_files()
    
    def _init_ui(self):
        """初始化界面"""
        self.setWindowTitle(f"文件管理器 - 设备: {self.device_id}")
        self.setMinimumSize(900, 500)
        self.resize(1200, 700)  # 设置更大的默认尺寸
        apply_dialog_style(self)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(6, 6, 6, 6)
        
        # 顶部路径栏（紧凑）
        path_layout = QHBoxLayout()
        path_layout.setSpacing(4)
        
        # 设备路径
        path_layout.addWidget(QLabel("设备:"))
        self.device_path_edit = QLineEdit(self.device_current_path)
        self.device_path_edit.returnPressed.connect(self._navigate_device_path)
        path_layout.addWidget(self.device_path_edit, 1)
        
        btn_device_go = QPushButton("转到")
        btn_device_go.clicked.connect(self._navigate_device_path)
        path_layout.addWidget(btn_device_go)
        
        path_layout.addSpacing(12)
        
        # 本地路径
        path_layout.addWidget(QLabel("本地:"))
        self.local_path_edit = QLineEdit(self.local_current_path)
        self.local_path_edit.returnPressed.connect(self._navigate_local_path)
        path_layout.addWidget(self.local_path_edit, 1)
        
        btn_local_go = QPushButton("转到")
        btn_local_go.clicked.connect(self._navigate_local_path)
        path_layout.addWidget(btn_local_go)
        
        layout.addLayout(path_layout)
        
        # 中间文件浏览区域
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：设备文件列表
        device_widget = QWidget()
        device_layout = QVBoxLayout(device_widget)
        device_layout.setContentsMargins(4, 4, 4, 4)
        device_layout.setSpacing(4)
        
        # 设备头部：标题+按钮合并为一行
        device_header = QHBoxLayout()
        device_header.setSpacing(4)
        device_header.addWidget(QLabel("📱 设备"))
        btn_device_up = QPushButton("⬆ 上级")
        btn_device_up.setToolTip("返回上级目录")
        btn_device_up.clicked.connect(self._device_go_up)
        device_header.addWidget(btn_device_up)
        btn_refresh_device = QPushButton("🔄 刷新")
        btn_refresh_device.setToolTip("刷新文件列表")
        btn_refresh_device.clicked.connect(self._refresh_device_files)
        device_header.addWidget(btn_refresh_device)
        btn_download = QPushButton("⬇ 下载")
        btn_download.setToolTip("下载选中的文件到本地")
        btn_download.clicked.connect(self._download_selected)
        device_header.addWidget(btn_download)
        btn_new_folder_device = QPushButton("📁 新建")
        btn_new_folder_device.setToolTip("在设备上新建文件夹")
        btn_new_folder_device.clicked.connect(self._create_folder_on_device)
        device_header.addWidget(btn_new_folder_device)
        device_header.addStretch()
        device_layout.addLayout(device_header)
        
        self.device_tree = QTreeWidget()
        self.device_tree.setHeaderLabels(['名称', '大小', '权限', '修改日期'])
        self.device_tree.setColumnWidth(0, 200)
        self.device_tree.setSortingEnabled(True)
        self.device_tree.itemDoubleClicked.connect(self._on_device_item_double_clicked)
        self.device_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.device_tree.customContextMenuRequested.connect(self._show_device_context_menu)
        device_layout.addWidget(self.device_tree, 1)  # stretch=1
        
        splitter.addWidget(device_widget)
        
        # 右侧：本地文件列表
        local_widget = QWidget()
        local_layout = QVBoxLayout(local_widget)
        local_layout.setContentsMargins(4, 4, 4, 4)
        local_layout.setSpacing(4)
        
        # 本地头部：标题+按钮合并为一行
        local_header = QHBoxLayout()
        local_header.setSpacing(4)
        local_header.addWidget(QLabel("💻 本地"))
        btn_local_up = QPushButton("⬆ 上级")
        btn_local_up.setToolTip("返回上级目录")
        btn_local_up.clicked.connect(self._local_go_up)
        local_header.addWidget(btn_local_up)
        btn_refresh_local = QPushButton("🔄 刷新")
        btn_refresh_local.setToolTip("刷新文件列表")
        btn_refresh_local.clicked.connect(self._refresh_local_files)
        local_header.addWidget(btn_refresh_local)
        btn_upload = QPushButton("⬆ 上传")
        btn_upload.setToolTip("上传选中的文件到设备")
        btn_upload.clicked.connect(self._upload_selected)
        local_header.addWidget(btn_upload)
        btn_select_file = QPushButton("📂 选择文件")
        btn_select_file.setToolTip("选择要上传的文件")
        btn_select_file.clicked.connect(self._select_local_file)
        local_header.addWidget(btn_select_file)
        btn_browse_dir = QPushButton("📁 浏览目录")
        btn_browse_dir.setToolTip("浏览选择本地目录")
        btn_browse_dir.clicked.connect(self._browse_local_directory)
        local_header.addWidget(btn_browse_dir)
        local_header.addStretch()
        local_layout.addLayout(local_header)
        
        self.local_tree = QTreeWidget()
        self.local_tree.setHeaderLabels(['名称', '大小', '类型', '修改日期'])
        self.local_tree.setColumnWidth(0, 200)
        self.local_tree.setSortingEnabled(True)
        self.local_tree.itemDoubleClicked.connect(self._on_local_item_double_clicked)
        self.local_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.local_tree.customContextMenuRequested.connect(self._show_local_context_menu)
        local_layout.addWidget(self.local_tree, 1)  # stretch=1
        
        splitter.addWidget(local_widget)
        
        splitter.setSizes([500, 500])
        layout.addWidget(splitter, 1)  # stretch=1
        
        # 底部状态栏（紧凑）
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(8)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(16)
        bottom_layout.addWidget(self.progress_bar)
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #909090; font-size: 11px;")
        bottom_layout.addWidget(self.status_label)
        bottom_layout.addStretch()
        layout.addLayout(bottom_layout)
    
    def _refresh_device_files(self):
        """刷新设备文件列表"""
        self.device_tree.clear()
        self.status_label.setText("正在获取设备文件列表...")
        
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
        self.device_tree.clear()
        
        for file_info in files:
            name = file_info['name']
            is_dir = file_info['is_dir']
            is_link = file_info['is_link']
            
            size_str = '<DIR>' if is_dir else self._format_size(int(file_info['size']) if file_info['size'].isdigit() else 0)
            
            item = QTreeWidgetItem([
                name,
                size_str,
                file_info['permissions'],
                file_info['date']
            ])
            item.setData(0, Qt.UserRole, file_info)
            
            # 设置图标
            if is_dir:
                item.setIcon(0, self.style().standardIcon(self.style().SP_DirIcon))
            elif is_link:
                item.setIcon(0, self.style().standardIcon(self.style().SP_FileLinkIcon))
            else:
                item.setIcon(0, self.style().standardIcon(self.style().SP_FileIcon))
            
            self.device_tree.addTopLevelItem(item)
        
        self.device_path_edit.setText(self.device_current_path)
        self.status_label.setText(f"已加载 {len(files)} 个项目")
    
    def _on_list_error(self, error_msg):
        """列表获取错误"""
        self.status_label.setText(error_msg)
        QMessageBox.warning(self, "错误", error_msg)
    
    def _refresh_local_files(self):
        """刷新本地文件列表"""
        self.local_tree.clear()
        
        try:
            # 添加返回上级目录
            if self.local_current_path != os.path.dirname(self.local_current_path):
                parent_item = QTreeWidgetItem(['.. (上级目录)', '', '', ''])
                parent_item.setData(0, Qt.UserRole, 'parent')
                parent_item.setIcon(0, self.style().standardIcon(self.style().SP_DirIcon))
                self.local_tree.addTopLevelItem(parent_item)
            
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
                    
                    self.local_tree.addTopLevelItem(item)
                except PermissionError:
                    continue
            
            self.local_path_edit.setText(self.local_current_path)
            self.status_label.setText(f"本地: {len(items)} 个项目")
        except Exception as e:
            self.status_label.setText(f"读取本地目录失败: {str(e)}")
    
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
        path = self.device_path_edit.text().strip()
        if path:
            self.device_current_path = path
            self._refresh_device_files()
    
    def _navigate_local_path(self):
        """导航到本地指定路径"""
        path = self.local_path_edit.text().strip()
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
            self.local_path_edit.setText(dir_path)
            self._refresh_local_files()
    
    def _on_device_item_double_clicked(self, item, column):
        """设备文件双击事件"""
        data = item.data(0, Qt.UserRole)
        
        if isinstance(data, dict) and data.get('is_dir'):
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
        item = self.device_tree.itemAt(pos)
        if not item:
            return
        
        data = item.data(0, Qt.UserRole)
        if data == 'parent':
            return
        
        menu = QMenu(self)
        
        if isinstance(data, dict):
            # 下载
            download_action = QAction("⬇ 下载到本地", self)
            download_action.triggered.connect(lambda: self._download_item(data))
            menu.addAction(download_action)
            
            menu.addSeparator()
            
            # 删除
            delete_action = QAction("🗑 删除", self)
            delete_action.triggered.connect(lambda: self._delete_device_item(data))
            menu.addAction(delete_action)
            
            # 权限管理
            if not data.get('is_dir'):
                menu.addSeparator()
                perm_action = QAction("🔒 修改权限", self)
                perm_action.triggered.connect(lambda: self._show_permission_dialog(data))
                menu.addAction(perm_action)
        
        menu.exec_(self.device_tree.viewport().mapToGlobal(pos))
    
    def _show_local_context_menu(self, pos):
        """显示本地文件右键菜单"""
        item = self.local_tree.itemAt(pos)
        if not item:
            return
        
        data = item.data(0, Qt.UserRole)
        if data == 'parent':
            return
        
        menu = QMenu(self)
        
        if isinstance(data, dict) and not data.get('is_dir'):
            # 上传
            upload_action = QAction("⬆ 上传到设备", self)
            upload_action.triggered.connect(lambda: self._upload_item(data))
            menu.addAction(upload_action)
        
        menu.exec_(self.local_tree.viewport().mapToGlobal(pos))
    
    def _download_selected(self):
        """下载选中的设备文件"""
        selected_items = self.device_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择要下载的文件")
            return
        
        for item in selected_items:
            data = item.data(0, Qt.UserRole)
            if isinstance(data, dict):
                self._download_item(data)
    
    def _download_item(self, file_info):
        """下载单个文件"""
        src_path = self._join_device_path(self.device_current_path, file_info['name'])
        dst_path = os.path.join(self.local_current_path, file_info['name'])
        
        self.progress_bar.setVisible(True)
        self.status_label.setText(f"正在下载: {file_info['name']}")
        
        self.transfer_thread = FileTransferThread(
            self.device_id, src_path, dst_path,
            'download', self.connection_mode, self.d
        )
        self.transfer_thread.progress_signal.connect(self.status_label.setText)
        self.transfer_thread.finished_signal.connect(self._on_transfer_finished)
        self.transfer_thread.start()
    
    def _upload_selected(self):
        """上传选中的本地文件"""
        selected_items = self.local_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择要上传的文件")
            return
        
        for item in selected_items:
            data = item.data(0, Qt.UserRole)
            if isinstance(data, dict) and not data.get('is_dir'):
                self._upload_item(data)
    
    def _upload_item(self, file_info):
        """上传单个文件"""
        src_path = file_info['path']
        dst_path = self._join_device_path(self.device_current_path, file_info['name'])
        
        self.progress_bar.setVisible(True)
        self.status_label.setText(f"正在上传: {file_info['name']}")
        
        self.transfer_thread = FileTransferThread(
            self.device_id, src_path, dst_path,
            'upload', self.connection_mode, self.d
        )
        self.transfer_thread.progress_signal.connect(self.status_label.setText)
        self.transfer_thread.finished_signal.connect(self._on_transfer_finished)
        self.transfer_thread.start()
    
    def _select_local_file(self):
        """选择本地文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择要上传的文件", self.local_current_path, "所有文件 (*)"
        )
        if file_path:
            self.local_current_path = os.path.dirname(file_path)
            self._refresh_local_files()
            # 选中刚选择的文件
            for i in range(self.local_tree.topLevelItemCount()):
                item = self.local_tree.topLevelItem(i)
                if item.text(0) == os.path.basename(file_path):
                    self.local_tree.setCurrentItem(item)
                    break
    
    def _on_transfer_finished(self, success, message):
        """传输完成"""
        self.progress_bar.setVisible(False)
        self.status_label.setText(message)
        
        if success:
            self._refresh_local_files()
        else:
            QMessageBox.warning(self, "传输失败", message)
    
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
            self.delete_thread.progress_signal.connect(self.status_label.setText)
            self.delete_thread.finished_signal.connect(self._on_delete_finished)
            self.delete_thread.start()
    
    def _on_delete_finished(self, success, message):
        """删除完成"""
        self.status_label.setText(message)
        if success:
            self._refresh_device_files()
        else:
            QMessageBox.warning(self, "删除失败", message)
    
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
                
                self.status_label.setText(f"文件夹创建成功: {folder_name}")
                self._refresh_device_files()
            except Exception as e:
                QMessageBox.warning(self, "创建失败", f"创建文件夹失败: {str(e)}")
    
    def _show_permission_dialog(self, file_info):
        """显示权限修改对话框"""
        current_perm = file_info.get('permissions', '-rw-r--r--')
        # 提取数字权限
        perm_str = current_perm[1:] if current_perm.startswith('-') else current_perm
        
        dialog = PermissionDialog(self, perm_str, file_info['name'])
        if dialog.exec_() == QDialog.Accepted:
            new_perm = dialog.get_permissions()
            self._change_permission(file_info, new_perm)
    
    def _change_permission(self, file_info, permissions):
        """修改文件权限"""
        path = self._join_device_path(self.device_current_path, file_info['name'])
        
        self.permission_thread = PermissionChangeThread(
            self.device_id, path, permissions,
            self.connection_mode, self.d
        )
        self.permission_thread.finished_signal.connect(self._on_permission_changed)
        self.permission_thread.start()
    
    def _on_permission_changed(self, success, message):
        """权限修改完成"""
        self.status_label.setText(message)
        if not success:
            QMessageBox.warning(self, "权限修改失败", message)
        else:
            self._refresh_device_files()
    
    def closeEvent(self, event):
        """关闭事件"""
        # 确保线程结束
        for thread in [self.list_thread, self.transfer_thread, 
                       self.delete_thread, self.permission_thread]:
            if thread and thread.isRunning():
                thread.wait(1000)
        event.accept()


class PermissionDialog(QDialog):
    """权限修改对话框"""
    
    def __init__(self, parent=None, current_perms="", file_name=""):
        super().__init__(parent)
        self.setWindowTitle(f"修改权限 - {file_name}")
        self.setMinimumWidth(350)
        apply_dialog_style(self)
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("请选择新的权限设置:"))
        
        # 权限复选框
        self.perm_checks = {}
        perm_names = {
            'ur': '用户读', 'uw': '用户写', 'ux': '用户执行',
            'gr': '组读', 'gw': '组写', 'gx': '组执行',
            'or': '其他读', 'ow': '其他写', 'ox': '其他执行'
        }
        
        grid_layout = QVBoxLayout()
        
        for group, group_name in [('u', '用户'), ('g', '组'), ('o', '其他')]:
            group_layout = QHBoxLayout()
            group_layout.addWidget(QLabel(f"{group_name}:"))
            
            for perm, perm_name in [('r', '读'), ('w', '写'), ('x', '执行')]:
                key = f"{group}{perm}"
                check = QCheckBox(perm_name)
                self.perm_checks[key] = check
                group_layout.addWidget(check)
            
            grid_layout.addLayout(group_layout)
        
        layout.addLayout(grid_layout)
        
        # 常用权限预设
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("预设:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "自定义",
            "644 (rw-r--r--)",
            "755 (rwxr-xr-x)",
            "777 (rwxrwxrwx)",
            "600 (rw-------)",
            "700 (rwx------)"
        ])
        self.preset_combo.currentIndexChanged.connect(self._apply_preset)
        preset_layout.addWidget(self.preset_combo)
        layout.addLayout(preset_layout)
        
        # 数字权限显示
        self.perm_label = QLabel("数字权限: 000")
        self.perm_label.setStyleSheet("font-weight: bold; color: #5a9bd5;")
        layout.addWidget(self.perm_label)
        
        # 连接信号更新显示
        for check in self.perm_checks.values():
            check.stateChanged.connect(self._update_perm_display)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("确定")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
    
    def _apply_preset(self, index):
        """应用预设权限"""
        presets = {
            0: None,  # 自定义
            1: '644',
            2: '755',
            3: '777',
            4: '600',
            5: '700'
        }
        
        perm = presets.get(index)
        if perm:
            self._set_from_octal(perm)
    
    def _set_from_octal(self, octal_str):
        """从八进制设置权限"""
        if len(octal_str) != 3:
            return
        
        for i, group in enumerate(['u', 'g', 'o']):
            val = int(octal_str[i])
            self.perm_checks[f"{group}r"].setChecked(bool(val & 4))
            self.perm_checks[f"{group}w"].setChecked(bool(val & 2))
            self.perm_checks[f"{group}x"].setChecked(bool(val & 1))
    
    def _update_perm_display(self):
        """更新权限数字显示"""
        self.perm_label.setText(f"数字权限: {self.get_permissions()}")
    
    def get_permissions(self):
        """获取权限数字字符串"""
        result = ""
        for group in ['u', 'g', 'o']:
            val = 0
            if self.perm_checks[f"{group}r"].isChecked():
                val += 4
            if self.perm_checks[f"{group}w"].isChecked():
                val += 2
            if self.perm_checks[f"{group}x"].isChecked():
                val += 1
            result += str(val)
        return result
