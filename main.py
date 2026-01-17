import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QThread
import qdarkstyle

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)  # type: ignore
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)  # type: ignore

# 导入日志管理器
from logger_manager import get_logger, log_operation, logger_manager

# 初始化日志记录器
logger = get_logger("ADBTools.Main")


def main():
    try:
        # 记录应用启动
        logger.info("=" * 80)
        logger.info("ADBTools 应用程序启动")
        logger.info(f"Python 版本: {sys.version}")
        logger.info(f"工作目录: {sys.path[0]}")
        logger.info("=" * 80)
        
        app = QApplication(sys.argv)
        app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
        
        logger.info("加载 ADB 主窗口模块...")
        from ADB_module import ADB_Mainwindow
        window = ADB_Mainwindow()
        
        logger.info(f"ADB 主窗口创建成功，版本: {window.VERSION}")
        log_operation("app_start", {"version": window.VERSION, "action": "启动应用程序"})

        def closeevent(event):
            try:
                logger.info("应用程序正在关闭...")
                log_operation("app_close", {"action": "关闭应用程序"})
                
                # Clean up any running threads
                for attr in dir(window):
                    thread = getattr(window, attr)
                    if isinstance(thread, QThread) and thread.isRunning():
                        logger.info(f"终止线程: {attr}")
                        thread.terminate()
                        thread.wait()
                
                logger.info("应用程序已正常关闭")
                logger.info("=" * 80)
                event.accept()
            except Exception as e:
                logger.error(f"清理过程中出错: {e}")
                print(f"Error during cleanup: {e}")
                event.accept()

        window.closeEvent = closeevent
        window.show()
        sys.exit(app.exec())
    except ImportError as e:
        logger.critical(f"导入必需模块失败: {e}")
        logger.critical("请确保已从 environment.yml 安装所有依赖")
        print(f"Failed to import required modules: {e}")
        print("Please ensure all dependencies are installed from environment.yml")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"严重错误: {e}")
        logger.critical(f"异常堆栈:\n{__import__('traceback').format_exc()}")
        print(f"Critical error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
