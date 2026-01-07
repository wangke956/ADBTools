from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QProgressBar, QPushButton, QMessageBox, QTextEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
import os
import subprocess
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class DownloadDialog(QDialog):
    """下载更新对话框"""
    
    download_canceled = pyqtSignal()
    
    def __init__(self, parent=None, update_info=None):
        super(DownloadDialog, self).__init__(parent)
        self.update_info = update_info
        self.download_thread = None
        self.downloaded_file_path = None
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("下载更新")
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        
        # 主布局
        main_layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("下载新版本")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        # 版本信息
        if self.update_info:
            version_text = f"当前版本: v{self.update_info.get('current_version', '未知')}\n"
            version_text += f"最新版本: v{self.update_info.get('latest_version', '未知')}"
            version_label = QLabel(version_text)
            main_layout.addWidget(version_label)
            
            # 更新说明
            release_body = self.update_info.get('release_body', '')
            if release_body:
                if len(release_body) > 200:
                    release_body = release_body[:200] + "..."
                release_label = QLabel(f"更新说明:\n{release_body}")
                release_label.setWordWrap(True)
                main_layout.addWidget(release_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(True)
        main_layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("准备下载...")
        self.status_label.setWordWrap(True)
        main_layout.addWidget(self.status_label)
        
        # 详细日志
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(100)
        main_layout.addWidget(self.log_text)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.cancel_download)
        
        self.download_button = QPushButton("开始下载")
        self.download_button.clicked.connect(self.start_download)
        
        self.install_button = QPushButton("安装")
        self.install_button.clicked.connect(self.install_update)
        self.install_button.setEnabled(False)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.download_button)
        button_layout.addWidget(self.install_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
    def log_message(self, message):
        """添加日志消息"""
        self.log_text.append(message)
        
    def start_download(self):
        """开始下载"""
        if not self.update_info:
            QMessageBox.warning(self, "错误", "没有更新信息")
            return
            
        setup_file = self.update_info.get('setup_file')
        if not setup_file:
            QMessageBox.warning(self, "错误", "未找到安装文件")
            return
            
        download_url = setup_file.get('browser_download_url')
        if not download_url:
            QMessageBox.warning(self, "错误", "没有下载链接")
            return
            
        # 如果已有下载线程在运行，先停止它
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.cancel()
            self.download_thread.wait()
            
        # 禁用下载按钮，启用取消按钮
        self.download_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.install_button.setEnabled(False)
        
        # 导入下载线程
        from Function_Moudle.download_update_thread import DownloadUpdateThread
        
        # 创建下载线程
        file_name = setup_file.get('name', 'ADBTools_Setup.exe')
        self.download_thread = DownloadUpdateThread(download_url, file_name)
        
        # 连接信号
        self.download_thread.progress_signal.connect(self.update_progress)
        self.download_thread.download_complete_signal.connect(self.download_complete)
        self.download_thread.error_signal.connect(self.download_error)
        self.download_thread.download_canceled_signal.connect(self.download_canceled)
        
        # 启动下载
        self.download_thread.start()
        self.log_message(f"开始下载: {file_name}")
        
    def _disconnect_signals(self):
        """断开所有信号连接"""
        if self.download_thread:
            try:
                self.download_thread.progress_signal.disconnect()
                self.download_thread.download_complete_signal.disconnect()
                self.download_thread.error_signal.disconnect()
                self.download_thread.download_canceled_signal.disconnect()
            except:
                # 忽略断开连接时的错误
                pass
        
    def update_progress(self, current, total, status):
        """更新下载进度"""
        if total > 0:
            percent = int((current / total) * 100)
            self.progress_bar.setValue(percent)
            
            # 格式化大小显示
            def format_size(size):
                if size < 1024:
                    return f"{size} B"
                elif size < 1024 * 1024:
                    return f"{size/1024:.1f} KB"
                elif size < 1024 * 1024 * 1024:
                    return f"{size/(1024*1024):.1f} MB"
                else:
                    return f"{size/(1024*1024*1024):.1f} GB"
                    
            size_text = f"{format_size(current)} / {format_size(total)}"
            self.progress_bar.setFormat(f"%p% ({size_text})")
        else:
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("下载中...")
            
        self.status_label.setText(status)
        
    def download_complete(self, file_path):
        """下载完成"""
        try:
            self.downloaded_file_path = file_path
            self.progress_bar.setValue(100)
            self.progress_bar.setFormat("下载完成！")
            self.status_label.setText("下载完成！")
            
            # 断开信号连接
            self._disconnect_signals()
            
            # 更新按钮状态
            self.download_button.setEnabled(False)
            self.cancel_button.setText("关闭")
            self.install_button.setEnabled(True)
            
            self.log_message(f"下载完成: {os.path.basename(file_path)}")
            self.log_message(f"文件保存到: {file_path}")
            
            # 询问是否立即安装
            reply = QMessageBox.question(self, "下载完成", 
                f"更新文件下载完成！\n\n文件: {os.path.basename(file_path)}\n大小: {self._get_file_size(file_path)}\n\n是否要立即安装？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes)
                
            if reply == QMessageBox.Yes:
                self.install_update()
                
        except Exception as e:
            self.log_message(f"处理下载完成时出错: {str(e)}")
            QMessageBox.warning(self, "错误", f"处理下载完成时发生错误:\n\n{str(e)}")
        
    def download_error(self, error_msg):
        """下载错误"""
        try:
            self.status_label.setText(f"下载失败: {error_msg}")
            self.log_message(f"错误: {error_msg}")
            
            # 断开信号连接
            self._disconnect_signals()
            
            # 重置按钮状态
            self.download_button.setEnabled(True)
            self.cancel_button.setEnabled(True)
            
            QMessageBox.warning(self, "下载失败", f"下载更新失败:\n\n{error_msg}")
            
        except Exception as e:
            self.log_message(f"处理下载错误时出错: {str(e)}")
        
    def download_canceled(self):
        """下载被取消"""
        try:
            self.status_label.setText("下载已取消")
            self.log_message("下载已取消")
            
            # 断开信号连接
            self._disconnect_signals()
            
            # 重置按钮状态
            self.download_button.setEnabled(True)
            self.cancel_button.setEnabled(True)
            self.install_button.setEnabled(False)
            
            # 重置进度条
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("%p%")
            
        except Exception as e:
            self.log_message(f"处理下载取消时出错: {str(e)}")
        
    def cancel_download(self):
        """取消下载"""
        if self.download_thread and self.download_thread.isRunning():
            reply = QMessageBox.question(self, "确认取消", 
                "确定要取消下载吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No)
                
            if reply == QMessageBox.Yes:
                # 先断开信号连接，避免线程结束后仍然触发信号
                self._disconnect_signals()
                
                # 取消下载线程
                self.download_thread.cancel()
                
                # 等待线程结束（最多等待2秒）
                if not self.download_thread.wait(2000):
                    # 如果线程没有正常结束，强制终止
                    self.download_thread.terminate()
                    self.download_thread.wait()
                    
                # 更新UI状态
                self.download_canceled()
                
                # 重新启用下载按钮
                self.download_button.setEnabled(True)
                self.cancel_button.setEnabled(True)
        else:
            self.close()
            
    def install_update(self):
        """安装更新"""
        if not self.downloaded_file_path or not os.path.exists(self.downloaded_file_path):
            QMessageBox.warning(self, "错误", "安装文件不存在")
            return
            
        # 确认安装
        reply = QMessageBox.question(self, "确认安装",
            "即将启动安装程序。当前程序将会关闭。\n\n是否继续？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes)
            
        if reply != QMessageBox.Yes:
            return
            
        try:
            # 获取文件扩展名
            file_ext = os.path.splitext(self.downloaded_file_path)[1].lower()
            
            if file_ext == '.exe':
                # 对于exe文件，直接运行
                subprocess.Popen([self.downloaded_file_path])
            elif file_ext == '.msi':
                # 对于msi文件，使用msiexec
                subprocess.Popen(['msiexec', '/i', self.downloaded_file_path])
            elif file_ext in ['.zip', '.7z', '.rar']:
                # 对于压缩文件，使用系统默认程序打开
                os.startfile(self.downloaded_file_path)
            else:
                # 其他文件类型，尝试直接打开
                os.startfile(self.downloaded_file_path)
                
            self.log_message("正在启动安装程序...")
            
            # 延迟关闭程序，让用户看到日志
            QTimer.singleShot(1000, self._close_application)
            
        except Exception as e:
            QMessageBox.critical(self, "启动安装失败", 
                f"无法启动安装程序:\n\n{str(e)}\n\n请手动运行安装文件: {self.downloaded_file_path}")
                
    def _close_application(self):
        """关闭应用程序"""
        self.log_message("正在关闭ADBTools...")
        # 发送信号给主窗口关闭应用程序
        if self.parent():
            self.parent().close()
            
    def _get_file_size(self, file_path):
        """获取文件大小（格式化）"""
        try:
            size = os.path.getsize(file_path)
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size/1024:.1f} KB"
            elif size < 1024 * 1024 * 1024:
                return f"{size/(1024*1024):.1f} MB"
            else:
                return f"{size/(1024*1024*1024):.1f} GB"
        except:
            return "未知大小"
            
    def closeEvent(self, event):
        """关闭事件"""
        try:
            if self.download_thread and self.download_thread.isRunning():
                reply = QMessageBox.question(self, "确认关闭",
                    "下载正在进行中，确定要关闭吗？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No)
                    
                if reply == QMessageBox.Yes:
                    # 先断开信号连接
                    self._disconnect_signals()
                    
                    # 取消下载线程
                    self.download_thread.cancel()
                    
                    # 等待线程结束（最多等待1秒）
                    if not self.download_thread.wait(1000):
                        # 如果线程没有正常结束，强制终止
                        self.download_thread.terminate()
                        self.download_thread.wait()
                    
                    event.accept()
                else:
                    event.ignore()
            else:
                # 断开信号连接
                self._disconnect_signals()
                event.accept()
                
        except Exception as e:
            self.log_message(f"关闭对话框时出错: {str(e)}")
            event.accept()