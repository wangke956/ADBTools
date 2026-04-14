import time
import os
from typing import Dict, Optional

from PyQt5.QtCore import QThread, pyqtSignal
import openpyxl  # 移到顶部，符合PEP8规范
from openpyxl.utils.exceptions import InvalidFileException


class AppVersionCheckThread(QThread):
    """
    应用版本检查线程
    功能：
    1. 读取Excel版本清单文件
    2. 对比设备端已安装应用的版本号
    3. 实时反馈进度/错误/版本对比结果
    """
    # 进度信号：传递当前执行步骤
    progress_signal = pyqtSignal(str)
    # 错误信号：传递错误详情
    error_signal = pyqtSignal(str)
    # 版本清单信号：传递Excel中读取的包名-版本号字典
    release_note_signal = pyqtSignal(dict)
    # 版本对比结果信号：传递{包名: (清单版本, 设备版本, 是否一致)}
    version_compare_signal = pyqtSignal(dict)

    def __init__(self, d, releasenote_file: str):
        """
        初始化线程
        :param d: uiautomator2/ADB设备对象（需已连接）
        :param releasenote_file: 版本清单Excel文件路径
        """
        super().__init__()
        self.d = d  # 设备对象（用于获取设备端应用版本）
        self.releasenote_file = releasenote_file  # 版本清单文件路径
        self.release_note_dict: Dict[str, Optional[str]] = {}  # Excel版本清单
        self.compare_result_dict: Dict[str, tuple] = {}  # 版本对比结果

    def _validate_file(self) -> bool:
        """校验版本清单文件是否有效"""
        self.progress_signal.emit("校验版本清单文件...")
        # 检查文件是否存在
        if not os.path.exists(self.releasenote_file):
            self.error_signal.emit(f"版本清单文件不存在：{self.releasenote_file}")
            return False
        # 检查文件后缀
        if not self.releasenote_file.endswith(('.xlsx', '.xlsm')):
            self.error_signal.emit(f"文件格式错误，仅支持.xlsx/.xlsm：{self.releasenote_file}")
            return False
        return True

    def _read_excel_version(self) -> bool:
        """读取Excel中的版本清单"""
        self.progress_signal.emit("读取版本清单Excel文件...")
        try:
            # 只读模式打开Excel，减少内存占用
            wb = openpyxl.load_workbook(self.releasenote_file, read_only=True, data_only=True)
            # 检查工作表是否存在
            if 'checkversion' not in wb.sheetnames:
                self.error_signal.emit("Excel中不存在checkversion工作表")
                wb.close()
                return False

            ws = wb['checkversion']
            # 校验B8单元格标识
            cell_b8 = ws['B8'].value
            if cell_b8 != "packageName":
                self.error_signal.emit(f"B8单元格值错误（预期：packageName，实际：{cell_b8}）")
                wb.close()
                return False

            # 读取B9开始的包名和D列版本号
            self.progress_signal.emit("解析包名和版本号...")
            row_num = 9
            while row_num <= 100:  # 限制最大行数，防止无限循环
                packagename = ws.cell(row=row_num, column=2).value  # B列：包名
                version = ws.cell(row=row_num, column=4).value  # D列：版本号

                # 包名为空则终止读取
                if packagename is None or str(packagename).strip() == "":
                    break

                # 处理版本号空值
                clean_version = str(version).strip() if version is not None else "未知版本"
                self.release_note_dict[packagename.strip()] = clean_version
                self.progress_signal.emit(f"读取到：{packagename.strip()} - {clean_version}")

                row_num += 1
                time.sleep(0.05)  # 轻微延迟，避免读取过快

            wb.close()

            # 检查是否读取到有效数据
            if not self.release_note_dict:
                self.error_signal.emit("Excel中未读取到任何包名和版本号")
                return False

            self.progress_signal.emit(f"共读取到{len(self.release_note_dict)}个应用的版本清单")
            self.release_note_signal.emit(self.release_note_dict)
            return True

        except InvalidFileException:
            self.error_signal.emit("Excel文件损坏或格式不支持")
            return False
        except PermissionError:
            self.error_signal.emit(f"无权限读取文件：{self.releasenote_file}（可能文件已打开）")
            return False
        except Exception as e:
            self.error_signal.emit(f"读取Excel失败：{str(e)}")
            return False

    def _get_device_app_version(self, packagename: str) -> Optional[str]:
        """获取设备端已安装应用的版本号"""
        try:
            # 通过uiautomator2获取应用版本（适配常见的ADB设备对象）
            app_info = self.d.app_info(packagename)
            return app_info.get('version_name', '未知版本')
        except Exception as e:
            # 应用未安装/获取失败
            self.progress_signal.emit(f"设备端未找到应用：{packagename}（{str(e)}）")
            return None

    def _compare_version(self):
        """对比Excel版本和设备端版本"""
        self.progress_signal.emit("开始对比设备端应用版本...")
        for packagename, excel_version in self.release_note_dict.items():
            time.sleep(0.1)  # 延迟，避免设备操作过快
            self.progress_signal.emit(f"检查应用：{packagename}")

            # 获取设备端版本
            device_version = self._get_device_app_version(packagename)

            # 判定版本是否一致
            if device_version is None:
                is_match = False
                device_version = "未安装"
            else:
                is_match = (excel_version == device_version)

            # 存储对比结果
            self.compare_result_dict[packagename] = (excel_version, device_version, is_match)

        # 发送对比结果
        self.version_compare_signal.emit(self.compare_result_dict)
        self.progress_signal.emit(f"版本对比完成，共检查{len(self.compare_result_dict)}个应用")

    def run(self):
        """线程核心执行逻辑"""
        try:
            # 步骤1：校验文件
            if not self._validate_file():
                return

            # 步骤2：读取Excel版本清单
            if not self._read_excel_version():
                return

            # 步骤3：对比设备端版本
            self._compare_version()

            self.progress_signal.emit("版本检查全部完成！")

        except Exception as e:
            self.error_signal.emit(f"线程执行异常：{str(e)}")


# -------------------------- 测试示例（可直接运行） --------------------------
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit
    import uiautomator2 as u2


    class TestWindow(QWidget):
        def __init__(self):
            super().__init__()
            self.init_ui()
            # 连接测试设备（替换为你的设备IP/序列号）
            self.d = u2.connect("127.0.0.1:62001")  # 夜神模拟器示例

        def init_ui(self):
            self.setWindowTitle("版本检查测试")
            self.resize(800, 600)

            # 控件
            self.start_btn = QPushButton("开始版本检查")
            self.log_text = QTextEdit()

            # 布局
            layout = QVBoxLayout()
            layout.addWidget(self.start_btn)
            layout.addWidget(self.log_text)
            self.setLayout(layout)

            # 绑定事件
            self.start_btn.clicked.connect(self.start_check)

        def start_check(self):
            """启动版本检查线程"""
            # 替换为你的版本清单Excel路径
            excel_path = "版本清单.xlsx"

            # 创建线程
            self.check_thread = AppVersionCheckThread(self.d, excel_path)

            # 绑定信号
            self.check_thread.progress_signal.connect(self.log)
            self.check_thread.error_signal.connect(self.log)
            self.check_thread.release_note_signal.connect(lambda d: self.log(f"版本清单：{d}"))
            self.check_thread.version_compare_signal.connect(lambda d: self.log(f"对比结果：{d}"))

            # 启动线程
            self.check_thread.start()

        def log(self, msg):
            """日志输出"""
            self.log_text.append(f"[{time.strftime('%H:%M:%S')}] {msg}")


    # 运行测试
    app = QApplication(sys.argv)
    win = TestWindow()
    win.show()
    sys.exit(app.exec_())