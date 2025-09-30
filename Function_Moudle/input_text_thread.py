from PyQt5.QtCore import QThread, pyqtSignal
import subprocess

class InputTextThread(QThread):
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, d, text_to_input):
        super().__init__()
        self.d = d
        self.text = str(text_to_input)


    def run(self):
        try:
            # self.d.send_keys(self.text)
            result = subprocess.run(
                ["adb", "shell", "input", "text", str(self.text)],
                capture_output=True,
                text=True,
                check=True
            )
            self.progress_signal.emit(result.stdout)
        except Exception as e:
            self.error_signal.emit(str(e))