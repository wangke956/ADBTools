import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtCore import Qt
import qdarkstyle
import logging

# 配置日志记录
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)  # type: ignore
# QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)  # type: ignore
app = QApplication(sys.argv)
QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
)

def main():
    try:
        app = QApplication(sys.argv)
        app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        from ADB_module import ADB_Mainwindow
        window = ADB_Mainwindow()

        # 添加窗口关闭事件记录
        # noinspection SpellCheckingInspection
        def closeevent(event):
            event.accept()

        window.closeEvent = closeevent
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logging.error(f"程序运行出错: {e}", exc_info=True)

if __name__ == '__main__':
    main()
