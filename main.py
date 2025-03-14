import sys
import logging
import platform
import traceback
import psutil
from datetime import datetime
from PyQt5.QtWidgets import QApplication
from ADB_module import ADB_Mainwindow
import qdarkstyle
from PyQt5.QtCore import Qt

def get_system_info():
    """获取系统详细信息"""
    info = []
    info.append(f"操作系统: {platform.platform()}")
    info.append(f"Python版本: {sys.version}")
    info.append(f"CPU信息: {platform.processor()}")
    info.append(f"内存使用: {psutil.virtual_memory().percent}%")
    info.append(f"磁盘使用: {psutil.disk_usage('/').percent}%")
    return "\n".join(info)

def setup_logging():
    import os
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    log_filename = f'logs/adbtools_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    
    logger = logging.getLogger('ADBTools')
    logger.setLevel(logging.DEBUG)
    
    # 更详细的日志格式
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    detailed_formatter = logging.Formatter(
        '[%(asctime)s.%(msecs)03d] %(levelname)-8s '
        '[%(name)s] [%(threadName)s] '
        '%(module)s.%(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # 记录系统信息
    logger.info('='*50)
    logger.info('程序启动')
    logger.info('系统信息:\n%s', get_system_info())
    logger.info('='*50)
    
    # 设置全局异常处理器
    sys.excepthook = lambda exctype, value, tb: \
        logger.critical('未捕获的异常:\n%s', ''.join(traceback.format_exception(exctype, value, tb)))
    
    return logger

def main():
    logger = setup_logging()
    logger.info('启动 ADBTools 应用程序')
    
    try:
        # 启用高DPI缩放支持
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

        app = QApplication(sys.argv)
        logger.debug('初始化 QApplication')
        
        app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
        logger.debug('应用深色主题样式')
        
        window = ADB_Mainwindow()
        logger.debug('创建主窗口')
        # 添加窗口关闭事件记录
        def closeEvent(event):
            logger.info('应用程序正在关闭')
            logger.info(f'最终内存使用: {psutil.Process().memory_info().rss / 1024 / 1024:.2f} MB')
            event.accept()
        
        window.closeEvent = closeEvent
        
        window.show()
        logger.info('显示主窗口')
        
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f'程序运行出错: {str(e)}', exc_info=True)
        logger.error(f'错误堆栈:\n{"".join(traceback.format_exc())}')
        raise

if __name__ == '__main__':
    main()