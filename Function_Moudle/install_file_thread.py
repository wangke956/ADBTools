from PyQt5.QtCore import QThread, pyqtSignal
import subprocess
import sys
import os

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入日志管理器
from logger_manager import get_logger, log_operation, measure_performance, log_exception

# 创建日志记录器
logger = get_logger("ADBTools.InstallFileThread")

class InstallFileThread(QThread):
    progress_signal = pyqtSignal(int)
    signal_status = pyqtSignal(str)

    def __init__(self, d, package_path):
        super().__init__()
        self.d = d
        self.package_path = package_path
        logger.info(f"安装文件线程初始化: {package_path}")

    def run(self):
        logger.info("=" * 80)
        logger.info("开始安装应用")
        logger.info("=" * 80)
        logger.info(f"APK路径: {self.package_path}")
        logger.info(f"设备: {self.d if self.d else 'N/A'}")
        
        log_operation("install_apk", {
            "package_path": self.package_path,
            "device": str(self.d) if self.d else None
        })
        
        # 使用性能监控
        with measure_performance("install_apk"):
            try:
                self.signal_status.emit("正在开始安装...")
                logger.info("发送状态信号: 正在开始安装...")
                
                # 构建安装命令
                install_cmd = ["adb", "install", "-r", self.package_path]
                logger.info(f"执行安装命令: {' '.join(install_cmd)}")
                
                result = subprocess.run(
                    install_cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                logger.info("=" * 80)
                logger.info("安装命令执行结果")
                logger.info("=" * 80)
                logger.info(f"返回码: {result.returncode}")
                
                if result.stdout:
                    logger.info("标准输出:")
                    for line in result.stdout.strip().split('\n'):
                        logger.info(f"  {line}")
                
                if result.stderr:
                    logger.warning("错误输出:")
                    for line in result.stderr.strip().split('\n'):
                        logger.warning(f"  {line}")
                
                logger.info(f"✓ 安装成功: {self.package_path}")
                self.signal_status.emit(result.stdout)
                
                log_operation("install_apk_success", {
                    "package_path": self.package_path,
                    "returncode": result.returncode,
                    "stdout": result.stdout
                }, result="success")
                
                logger.info("=" * 80)
                logger.info("安装操作完成")
                logger.info("=" * 80)
                
            except subprocess.CalledProcessError as e:
                logger.error("=" * 80)
                logger.error("安装失败（CalledProcessError）")
                logger.error("=" * 80)
                logger.error(f"返回码: {e.returncode}")
                logger.error(f"命令: {' '.join(e.cmd)}")
                
                if e.stdout:
                    logger.error("标准输出:")
                    for line in e.stdout.strip().split('\n'):
                        logger.error(f"  {line}")
                
                if e.stderr:
                    logger.error("错误输出:")
                    for line in e.stderr.strip().split('\n'):
                        logger.error(f"  {line}")
                
                logger.error(f"✗ 安装失败: {self.package_path}")
                self.signal_status.emit(str(e))
                
                log_operation("install_apk_failed", {
                    "package_path": self.package_path,
                    "returncode": e.returncode,
                    "stdout": e.stdout,
                    "stderr": e.stderr
                }, result="failed")
                
                logger.error("=" * 80)
                
            except Exception as e:
                logger.error("=" * 80)
                logger.error("安装失败（异常）")
                logger.error("=" * 80)
                logger.error(f"异常类型: {type(e).__name__}")
                logger.error(f"异常信息: {str(e)}")
                logger.error(f"✗ 安装失败: {self.package_path}")
                log_exception(logger, "install_apk", e)
                self.signal_status.emit(str(e))
                
                log_operation("install_apk_error", {
                    "package_path": self.package_path,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }, result="error")
                
                logger.error("=" * 80)