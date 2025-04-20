import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import qdarkstyle

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)  # type: ignore
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)  # type: ignore


def main():
    try:
        app = QApplication(sys.argv)
        app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
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
        print(e)


if __name__ == '__main__':
    main()
