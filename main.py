import sys
from PyQt5.QtWidgets import QApplication, QTextBrowser
from PyQt5 import uic
from PyQt5.QtCore import Qt
import qdarkstyle

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)


def main():
    try:
        app = QApplication(sys.argv)
        app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
        from ADB_module import ADB_Mainwindow
        window = ADB_Mainwindow()

        # 添加窗口关闭事件记录
        def closeEvent(event):
            event.accept()

        window.closeEvent = closeEvent
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(e)


if __name__ == '__main__':
    main()
