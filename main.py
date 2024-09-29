import sys
from PyQt5.QtWidgets import QApplication
from ADB_module import ADB_Mainwindow
import qdarkstyle
"""功能完整，已测试"""

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    # app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
    window = ADB_Mainwindow()  # 创建窗口
    window.show()  # 显示窗口
    sys.exit(app.exec())  # 退出时关闭窗口
if __name__ == '__main__':  # 主函数
    main()