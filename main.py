import sys
from PyQt5.QtWidgets import QApplication, QTextBrowser
# from ADB_module import ADB_Mainwindow
from ADB_module import ADB_Mainwindow

import qdarkstyle


def main():
    try:
        app = QApplication(sys.argv)
        app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
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