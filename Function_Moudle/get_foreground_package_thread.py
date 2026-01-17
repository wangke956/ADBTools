from PyQt5.QtCore import QThread, pyqtSignal
import sys
import os

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入日志管理器
from logger_manager import get_logger, log_thread_start, log_thread_complete

# 创建日志记录器
logger = get_logger("ADBTools.GetForegroundPackageThread")


class GetForegroundPackageThread(QThread):
    """获取前台应用包名线程"""
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)

    def __init__(self, d):
        super().__init__()
        self.d = d
        log_thread_start("GetForegroundPackageThread", {"action": "获取前台应用"})
        
    def run(self):
        """执行获取前台应用操作"""
        logger.info("开始获取前台应用信息")
        
        try:
            self.progress_signal.emit("正在获取前台应用...")
            
            current_app = self.d.app_current()  # 获取当前正在运行的应用
            
            if current_app:
                package_name = current_app['package']
                activity_name = current_app['activity']
                result = f"包名: {package_name}, 活动名: {activity_name}"
                self.result_signal.emit(result)
                logger.info(f"获取前台应用成功: {result}")
                log_thread_complete("GetForegroundPackageThread", "success", {
                    "package": package_name,
                    "activity": activity_name
                })
            else:
                result = "当前没有正在运行的应用"
                self.result_signal.emit(result)
                logger.warning(result)
                log_thread_complete("GetForegroundPackageThread", "success", {"result": "no_app"})
                
        except Exception as e:
            error_msg = f"获取前台应用失败: {str(e)}"
            self.error_signal.emit(error_msg)
            logger.error(error_msg)
            log_thread_complete("GetForegroundPackageThread", "failed", {"error": str(e)})