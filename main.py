import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QThread
import qdarkstyle

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)  # type: ignore
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)  # type: ignore


def main():
    try:
        app = QApplication(sys.argv)
        app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
        from ADB_module import ADB_Mainwindow
        window = ADB_Mainwindow()

        def closeevent(event):
            try:
                # Clean up any running threads
                for attr in dir(window):
                    thread = getattr(window, attr)
                    if isinstance(thread, QThread) and thread.isRunning():
                        thread.terminate()
                        thread.wait()
                event.accept()
            except Exception as e:
                print(f"Error during cleanup: {e}")
                event.accept()

        window.closeEvent = closeevent
        window.show()
        sys.exit(app.exec())
    except ImportError as e:
        print(f"Failed to import required modules: {e}")
        print("Please ensure all dependencies are installed from environment.yml")
        sys.exit(1)
    except Exception as e:
        print(f"Critical error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
