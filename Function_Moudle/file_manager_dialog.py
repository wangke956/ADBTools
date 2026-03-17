# -*- coding: utf-8 -*-
"""
文件管理对话框 - 提供设备文件浏览、上传、下载、删除功能
"""

import os
import stat
import subprocess
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QLineEdit, QComboBox, QMessageBox, QProgressBar,
    QHeaderView, QMenu, QAction, QInputDialog, QWidget, QFileDialog,
    QTextEdit, QApplication
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMimeData, QUrl
from PyQt5.QtGui import QIcon, QCursor, QDropEvent, QDrag

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
        self.delete_thread = None
        self.rename_thread = None
        self.text_read_thread = None
        self.text_write_thread = None
        
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
        
        self.device_tree = DeviceFileTree()
        self.device_tree.setHeaderLabels(['名称', '大小', '权限', '修改日期'])
        self.device_tree.setColumnWidth(0, 200)
        self.device_tree.setSortingEnabled(True)
        self.device_tree.setSelectionMode(QTreeWidget.ExtendedSelection)  # 多选模式
        self.device_tree.itemDoubleClicked.connect(self._on_device_item_double_clicked)
        self.device_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.device_tree.customContextMenuRequested.connect(self._show_device_context_menu)
        self.device_tree.files_dropped.connect(self._on_files_dropped)  # 拖放上传信号
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
        
        self.local_tree = LocalFileTree()
        self.local_tree.setHeaderLabels(['名称', '大小', '类型', '修改日期'])
        self.local_tree.setColumnWidth(0, 200)
        self.local_tree.setSortingEnabled(True)
        self.local_tree.setSelectionMode(QTreeWidget.ExtendedSelection)  # 多选模式
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
        selected_items = self.device_tree.selectedItems()
        if not selected_items:
            return
        
        menu = QMenu(self)
        
        # 单选模式
        if len(selected_items) == 1:
            item = selected_items[0]
            data = item.data(0, Qt.UserRole)
            if not isinstance(data, dict):
                return
            
            # 下载
            download_action = QAction("⬇ 下载到本地", self)
            download_action.triggered.connect(lambda: self._download_item(data))
            menu.addAction(download_action)
            
            menu.addSeparator()
            
            # 重命名
            rename_action = QAction("✏ 重命名", self)
            rename_action.triggered.connect(lambda: self._rename_item(data))
            menu.addAction(rename_action)
            
            # 文本预览/编辑（仅文件）
            if not data.get('is_dir'):
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
    
    def _on_files_dropped(self, file_paths):
        """处理拖放文件上传"""
        if not file_paths:
            return
        
        # 确认上传
        reply = QMessageBox.question(
            self, '确认上传',
            f"确定要上传 {len(file_paths)} 个文件/文件夹到设备吗？\n目标路径: {self.device_current_path}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            self._upload_files_batch(file_paths)
    
    def _upload_files_batch(self, file_paths):
        """批量上传文件"""
        self.progress_bar.setVisible(True)
        total = len(file_paths)
        
        for i, src_path in enumerate(file_paths):
            file_name = os.path.basename(src_path)
            dst_path = self._join_device_path(self.device_current_path, file_name)
            
            self.status_label.setText(f"上传中 ({i+1}/{total}): {file_name}")
            
            try:
                if self.connection_mode == 'u2' and self.d:
                    self.d.push(src_path, dst_path)
                else:
                    cmd = f'adb -s {self.device_id} push "{src_path}" "{dst_path}"'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
                    if result.returncode != 0:
                        raise Exception(result.stderr)
                
                logger.info(f"上传成功: {file_name}")
            except Exception as e:
                logger.error(f"上传失败: {file_name} - {str(e)}")
                self.status_label.setText(f"上传失败: {file_name}")
        
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"上传完成: {total} 个文件")
        self._refresh_device_files()
    
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
    
    def _rename_item(self, file_info):
        """重命名文件/文件夹"""
        old_name = file_info.get('name', '')
        new_name, ok = QInputDialog.getText(self, "重命名", "请输入新名称:", text=old_name)
        
        if ok and new_name and new_name != old_name:
            old_path = self._join_device_path(self.device_current_path, old_name)
            new_path = self._join_device_path(self.device_current_path, new_name)
            
            self.status_label.setText(f"正在重命名: {old_name} -> {new_name}")
            
            self.rename_thread = RenameThread(
                self.device_id, old_path, new_path,
                self.connection_mode, self.d
            )
            self.rename_thread.finished_signal.connect(self._on_rename_finished)
            self.rename_thread.start()
    
    def _on_rename_finished(self, success, message):
        """重命名完成"""
        self.status_label.setText(message)
        if success:
            self._refresh_device_files()
        else:
            QMessageBox.warning(self, "重命名失败", message)
    
    def _delete_selected_device_items(self):
        """批量删除选中的设备文件"""
        selected_items = self.device_tree.selectedItems()
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
            
            self.status_label.setText(f"正在删除: {file_name}")
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
        
        self.status_label.setText(f"删除完成: 成功 {success_count} 个, 失败 {fail_count} 个")
        self._refresh_device_files()
    
    def _preview_text_file(self, file_info):
        """预览/编辑文本文件"""
        file_name = file_info.get('name', '')
        file_path = self._join_device_path(self.device_current_path, file_name)
        
        self.status_label.setText(f"正在读取文件: {file_name}")
        
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
            self.status_label.setText(f"读取失败: {error}")
            QMessageBox.warning(self, "读取失败", f"无法读取文件: {error}")
            return
        
        self.status_label.setText(f"已加载: {file_name}")
        
        # 显示文本编辑对话框
        dialog = TextPreviewDialog(self, file_path, file_name, content, 
                                   self.device_id, self.connection_mode, self.d)
        dialog.saved_signal.connect(self._refresh_device_files)
        dialog.exec_()
    
    def closeEvent(self, event):
        """关闭事件"""
        # 确保线程结束
        for thread in [self.list_thread, self.transfer_thread, self.delete_thread,
                       self.rename_thread, self.text_read_thread, self.text_write_thread]:
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
