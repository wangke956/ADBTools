import sys
import threading

from PyQt5.QtWidgets import QApplication
from ADB_module import ADB_Mainwindow
# from qt_material import apply_stylesheet
# from qt_material import list_themes
# list_themes()
# import qdarkstyle
"""功能完整，已测试"""

def main():
    def inner_main():
        app = QApplication(sys.argv)
        # app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        # app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
        # apply_stylesheet(app, theme = 'dark_teal.xml')
        window = ADB_Mainwindow()  # 创建窗口
        window.show()  # 显示窗口
        # ADB_Mainwindow.d_list(ADB_Mainwindow())
        sys.exit(app.exec())  # 退出时关闭窗口
    thread = threading.Thread(target=inner_main)
    thread.start()  # 启动线程
if __name__ == '__main__':  # 主函数
    main()