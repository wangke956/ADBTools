from PyQt5.QtCore import QThread, pyqtSignal
import uiautomator2 as u2


class UpdateThread(QThread):
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, d):
        super().__init__()
        self.d = d

    def run(self):

        try:
            self.progress_signal.emit("正在尝试启动更新页面...")
            result = self.d.app_start("com.saicmotor.update", ".view.MainActivity")
            # result = self.d.app_start("com.tencent.mm", ".ui.LauncherUI")
            #  微信包名: com.tencent.mm, 活动名: .ui.LauncherUI
            if result:
                self.progress_signal.emit(f"更新页面启动成功！")
            else:
                self.error_signal.emit(f"更新页面启动失败: {result}")
        except Exception as e:
            self.error_signal.emit(f"更新页面启动失败: {str(e)}")
