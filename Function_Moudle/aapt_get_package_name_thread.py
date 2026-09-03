from PyQt6.QtCore import QThread, pyqtSignal
import os
import re
import shutil
import subprocess
import tempfile


class AaptGetPackageNameThread(QThread):
    """使用 aapt 读取 APK 包名的后台线程。

    兼容含中文 / 特殊 Unicode 字符（如 ƽ）的 APK 路径：
    aapt.exe 内部使用 ANSI fopen，若路径无法映射到当前代码页会报
    "Illegal byte sequence"，此时会先把 APK 复制到 ASCII 临时文件再解析。
    """

    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, apk_path):
        super().__init__()
        self.apk_path = apk_path

    @staticmethod
    def _is_ascii_safe(path: str) -> bool:
        try:
            path.encode('ascii')
            return True
        except (UnicodeEncodeError, AttributeError):
            return False

    @staticmethod
    def _run_aapt(apk_path: str):
        """列表参数直接调用 aapt，避免 shell 解析特殊字符。"""
        return subprocess.run(
            ['aapt', 'dump', 'badging', apk_path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=False,
        )

    @staticmethod
    def _parse_package_name(stdout: str):
        if not stdout:
            return None
        match = re.search(r"package:\s*name='([^']+)'", stdout)
        if match:
            return match.group(1)
        return None

    def run(self):
        temp_dir = None
        try:
            if not self.apk_path or not os.path.isfile(self.apk_path):
                self.error_signal.emit(f"获取包名失败: 文件不存在 {self.apk_path}")
                return

            work_path = self.apk_path
            # 路径含非 ASCII 字符时，复制到临时 ASCII 文件规避 aapt 编码问题
            if not self._is_ascii_safe(self.apk_path):
                temp_dir = tempfile.mkdtemp(prefix='aapt_pkg_')
                work_path = os.path.join(temp_dir, 'temp.apk')
                shutil.copy2(self.apk_path, work_path)

            result = self._run_aapt(work_path)
            package_name = self._parse_package_name(result.stdout)

            if package_name:
                self.result_signal.emit(f"包名: {package_name}")
                return

            err_msg = (result.stderr or '').strip()
            if not err_msg:
                err_msg = '未找到包名信息'
            self.error_signal.emit(f"获取包名失败: {err_msg}")

        except FileNotFoundError:
            self.error_signal.emit("获取包名失败: 未找到 aapt 工具，请确认已加入 PATH")
        except Exception as e:
            self.error_signal.emit(f"发生未知错误: {str(e)}")
        finally:
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)
