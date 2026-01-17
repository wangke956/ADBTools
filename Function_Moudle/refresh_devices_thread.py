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
logger = get_logger("ADBTools.RefreshDevicesThread")

try:
    from adb_utils import ADBUtils
except ImportError:
    # 如果直接导入失败，尝试相对导入
    import importlib.util
    spec = importlib.util.spec_from_file_location("adb_utils", os.path.join(project_root, "adb_utils.py"))
    adb_utils_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adb_utils_module)
    ADBUtils = adb_utils_module.ADBUtils

class RefreshDevicesThread(QThread):
    """刷新设备列表线程（多线程执行，避免阻塞主界面）"""
    progress_signal = pyqtSignal(str)
    devices_signal = pyqtSignal(list)  # 发送设备列表
    error_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.device_ids = []
        logger.info("刷新设备列表线程初始化")
        
    def run(self):
        """执行刷新设备列表操作"""
        logger.info("=" * 80)
        logger.info("开始执行刷新设备列表操作")
        logger.info("=" * 80)
        
        log_operation("refresh_devices_thread", {"action": "刷新设备列表"})
        
        # 使用性能监控
        with measure_performance("refresh_devices"):
            try:
                self.progress_signal.emit("正在刷新设备列表...")
                logger.info("发送进度信号: 正在刷新设备列表...")
                
                # 使用项目统一的ADB工具类执行命令
                logger.info("准备执行 ADB 命令: devices")
                result = ADBUtils.run_adb_command(
                    command="devices",
                    timeout=10  # 设置10秒超时
                )
                
                logger.info("ADB 命令执行完成，开始解析结果...")
                
                if result.returncode != 0:
                    logger.error(f"ADB命令执行失败，返回码: {result.returncode}")
                    logger.error(f"错误输出: {result.stderr}")
                    self.error_signal.emit(f"ADB命令执行失败: {result.stderr}")
                    self.devices_signal.emit([])
                    log_operation("refresh_devices_failed", {
                        "reason": "adb_command_failed",
                        "returncode": result.returncode,
                        "stderr": result.stderr
                    }, result="failed")
                    return
                
                # 解析设备列表
                output = result.stdout.strip()
                logger.info(f"ADB 命令返回内容长度: {len(output)} 字符")
                
                if not output:
                    logger.warning("ADB命令返回空结果")
                    self.progress_signal.emit("ADB命令返回空结果")
                    self.devices_signal.emit([])
                    log_operation("refresh_devices_empty", {
                        "reason": "empty_output"
                    }, result="failed")
                    return
                
                # 解析设备列表输出
                lines = output.split('\n')
                logger.info(f"ADB命令返回 {len(lines)} 行内容")
                
                device_ids = []
                
                for i, line in enumerate(lines):
                    line = line.strip()
                    logger.debug(f"解析第 {i+1} 行: {line}")
                    
                    if line and not line.startswith("List of devices"):
                        parts = line.split()
                        if len(parts) >= 2 and parts[1] in ["device", "offline"]:
                            device_ids.append(parts[0])
                            logger.info(f"✓ 发现设备: {parts[0]} (状态: {parts[1]})")
                        else:
                            logger.debug(f"  跳过无效行: {line}")
                
                self.device_ids = device_ids
                
                logger.info(f"设备解析完成，共找到 {len(device_ids)} 个设备")
                
                if device_ids:
                    device_count = len(device_ids)
                    device_ids_str = "\n".join(device_ids)
                    logger.info(f"设备列表:")
                    for dev_id in device_ids:
                        logger.info(f"  - {dev_id}")
                    
                    self.progress_signal.emit(f"找到 {device_count} 个设备：")
                    self.progress_signal.emit(device_ids_str)
                    self.devices_signal.emit(device_ids)
                    
                    log_operation("refresh_devices_success", {
                        "device_count": device_count,
                        "device_ids": device_ids
                    }, result="success")
                else:
                    logger.info("未检测到任何已连接的设备")
                    self.progress_signal.emit("未检测到任何已连接的设备")
                    self.devices_signal.emit([])
                    
                    log_operation("refresh_devices_no_device", {
                        "reason": "no_devices_found"
                    }, result="success")
                
                logger.info("=" * 80)
                logger.info("刷新设备列表操作完成")
                logger.info("=" * 80)
                    
            except subprocess.TimeoutExpired:
                logger.error("刷新设备列表超时")
                self.error_signal.emit("刷新设备列表超时，请检查ADB连接")
                self.devices_signal.emit([])
                log_operation("refresh_devices_timeout", {
                    "reason": "timeout"
                }, result="failed")
            except Exception as e:
                logger.error(f"刷新设备列表时发生错误: {str(e)}")
                log_exception(logger, "refresh_devices_thread", e)
                self.error_signal.emit(f"刷新设备列表时发生错误: {str(e)}")
                self.devices_signal.emit([])
                log_operation("refresh_devices_error", {
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }, result="error")