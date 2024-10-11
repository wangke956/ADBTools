# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'backup0.bak.ui'
#
# Created by: PyQt5 UI code generator 5.15.11
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(883, 830)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setMinimumSize(QtCore.QSize(509, 790))
        MainWindow.setMaximumSize(QtCore.QSize(16777215, 16777215))
        font = QtGui.QFont()
        font.setFamily("Franklin Gothic Medium")
        MainWindow.setFont(font)
        MainWindow.setAcceptDrops(True)
        MainWindow.setStyleSheet("QPushbutton{\n"
"    background-color:#4682b4;\n"
"    color:shite;\n"
"}\n"
"")
        MainWindow.setIconSize(QtCore.QSize(16, 16))
        MainWindow.setAnimated(False)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setObjectName("centralwidget")
        self.formLayout_3 = QtWidgets.QFormLayout(self.centralwidget)
        self.formLayout_3.setObjectName("formLayout_3")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        font.setBold(False)
        font.setWeight(50)
        self.tabWidget.setFont(font)
        self.tabWidget.setAcceptDrops(False)
        self.tabWidget.setStyleSheet("")
        self.tabWidget.setIconSize(QtCore.QSize(20, 20))
        self.tabWidget.setElideMode(QtCore.Qt.ElideRight)
        self.tabWidget.setObjectName("tabWidget")
        self.ADB = QtWidgets.QWidget()
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.ADB.setFont(font)
        self.ADB.setObjectName("ADB")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.ADB)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.gridLayout_3 = QtWidgets.QGridLayout()
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.textBrowser = QtWidgets.QTextBrowser(self.ADB)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.textBrowser.sizePolicy().hasHeightForWidth())
        self.textBrowser.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Franklin Gothic Medium")
        font.setPointSize(12)
        self.textBrowser.setFont(font)
        self.textBrowser.setAcceptDrops(True)
        self.textBrowser.setTabChangesFocus(False)
        self.textBrowser.setObjectName("textBrowser")
        self.gridLayout_3.addWidget(self.textBrowser, 6, 1, 1, 3)
        self.label = QtWidgets.QLabel(self.ADB)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setMaximumSize(QtCore.QSize(398, 28))
        self.label.setObjectName("label")
        self.gridLayout_3.addWidget(self.label, 8, 1, 1, 1)
        self.ComboxButton = QtWidgets.QComboBox(self.ADB)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.ComboxButton.sizePolicy().hasHeightForWidth())
        self.ComboxButton.setSizePolicy(sizePolicy)
        self.ComboxButton.setMinimumSize(QtCore.QSize(0, 35))
        self.ComboxButton.setMaximumSize(QtCore.QSize(16777215, 35))
        self.ComboxButton.setBaseSize(QtCore.QSize(0, 0))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.ComboxButton.setFont(font)
        self.ComboxButton.setEditable(False)
        self.ComboxButton.setCurrentText("请点击刷新设备")
        self.ComboxButton.setMaxVisibleItems(60)
        self.ComboxButton.setIconSize(QtCore.QSize(16, 16))
        self.ComboxButton.setPlaceholderText("")
        self.ComboxButton.setFrame(False)
        self.ComboxButton.setObjectName("ComboxButton")
        self.ComboxButton.addItem("")
        self.gridLayout_3.addWidget(self.ComboxButton, 4, 3, 1, 1)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.adbbutton = QtWidgets.QPushButton(self.ADB)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.adbbutton.sizePolicy().hasHeightForWidth())
        self.adbbutton.setSizePolicy(sizePolicy)
        self.adbbutton.setMinimumSize(QtCore.QSize(0, 24))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.adbbutton.setFont(font)
        self.adbbutton.setObjectName("adbbutton")
        self.gridLayout.addWidget(self.adbbutton, 0, 0, 1, 1)
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.button_reboot = QtWidgets.QPushButton(self.ADB)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.button_reboot.sizePolicy().hasHeightForWidth())
        self.button_reboot.setSizePolicy(sizePolicy)
        self.button_reboot.setMinimumSize(QtCore.QSize(0, 0))
        self.button_reboot.setMaximumSize(QtCore.QSize(16777215, 16777215))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.button_reboot.setFont(font)
        self.button_reboot.setObjectName("button_reboot")
        self.gridLayout_2.addWidget(self.button_reboot, 0, 0, 1, 1)
        self.adb_root = QtWidgets.QPushButton(self.ADB)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.adb_root.sizePolicy().hasHeightForWidth())
        self.adb_root.setSizePolicy(sizePolicy)
        self.adb_root.setMinimumSize(QtCore.QSize(0, 0))
        self.adb_root.setMaximumSize(QtCore.QSize(16777215, 16777215))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.adb_root.setFont(font)
        self.adb_root.setObjectName("adb_root")
        self.gridLayout_2.addWidget(self.adb_root, 1, 0, 1, 1)
        self.adb_pull_file = QtWidgets.QPushButton(self.ADB)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.adb_pull_file.sizePolicy().hasHeightForWidth())
        self.adb_pull_file.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.adb_pull_file.setFont(font)
        self.adb_pull_file.setObjectName("adb_pull_file")
        self.gridLayout_2.addWidget(self.adb_pull_file, 2, 0, 1, 1)
        self.adb_push_file = QtWidgets.QPushButton(self.ADB)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.adb_push_file.sizePolicy().hasHeightForWidth())
        self.adb_push_file.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.adb_push_file.setFont(font)
        self.adb_push_file.setObjectName("adb_push_file")
        self.gridLayout_2.addWidget(self.adb_push_file, 3, 0, 1, 1)
        self.simulate_click = QtWidgets.QPushButton(self.ADB)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.simulate_click.sizePolicy().hasHeightForWidth())
        self.simulate_click.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.simulate_click.setFont(font)
        self.simulate_click.setObjectName("simulate_click")
        self.gridLayout_2.addWidget(self.simulate_click, 4, 0, 1, 1)
        self.simulate_swipe = QtWidgets.QPushButton(self.ADB)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.simulate_swipe.sizePolicy().hasHeightForWidth())
        self.simulate_swipe.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.simulate_swipe.setFont(font)
        self.simulate_swipe.setObjectName("simulate_swipe")
        self.gridLayout_2.addWidget(self.simulate_swipe, 5, 0, 1, 1)
        self.simulate_long_press = QtWidgets.QPushButton(self.ADB)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.simulate_long_press.sizePolicy().hasHeightForWidth())
        self.simulate_long_press.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.simulate_long_press.setFont(font)
        self.simulate_long_press.setObjectName("simulate_long_press")
        self.gridLayout_2.addWidget(self.simulate_long_press, 6, 0, 1, 1)
        self.adb_install = QtWidgets.QPushButton(self.ADB)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.adb_install.sizePolicy().hasHeightForWidth())
        self.adb_install.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.adb_install.setFont(font)
        self.adb_install.setObjectName("adb_install")
        self.gridLayout_2.addWidget(self.adb_install, 7, 0, 1, 1)
        self.adb_uninstall = QtWidgets.QPushButton(self.ADB)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.adb_uninstall.sizePolicy().hasHeightForWidth())
        self.adb_uninstall.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.adb_uninstall.setFont(font)
        self.adb_uninstall.setObjectName("adb_uninstall")
        self.gridLayout_2.addWidget(self.adb_uninstall, 8, 0, 1, 1)
        self.start_app = QtWidgets.QPushButton(self.ADB)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.start_app.sizePolicy().hasHeightForWidth())
        self.start_app.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.start_app.setFont(font)
        self.start_app.setObjectName("start_app")
        self.gridLayout_2.addWidget(self.start_app, 9, 0, 1, 1)
        self.gridLayout.addLayout(self.gridLayout_2, 0, 1, 1, 1)
        self.gridLayout_3.addLayout(self.gridLayout, 5, 1, 1, 1)
        self.gridLayout_5 = QtWidgets.QGridLayout()
        self.gridLayout_5.setContentsMargins(0, -1, -1, 0)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.adb_cpu_info = QtWidgets.QPushButton(self.ADB)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.adb_cpu_info.sizePolicy().hasHeightForWidth())
        self.adb_cpu_info.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.adb_cpu_info.setFont(font)
        self.adb_cpu_info.setObjectName("adb_cpu_info")
        self.gridLayout_5.addWidget(self.adb_cpu_info, 1, 0, 1, 1)
        self.pull_hulog = QtWidgets.QPushButton(self.ADB)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pull_hulog.sizePolicy().hasHeightForWidth())
        self.pull_hulog.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.pull_hulog.setFont(font)
        self.pull_hulog.setObjectName("pull_hulog")
        self.gridLayout_5.addWidget(self.pull_hulog, 1, 1, 1, 1)
        self.get_screenshot = QtWidgets.QPushButton(self.ADB)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.get_screenshot.sizePolicy().hasHeightForWidth())
        self.get_screenshot.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.get_screenshot.setFont(font)
        self.get_screenshot.setObjectName("get_screenshot")
        self.gridLayout_5.addWidget(self.get_screenshot, 2, 0, 1, 1)
        self.view_apk_path = QtWidgets.QPushButton(self.ADB)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.view_apk_path.sizePolicy().hasHeightForWidth())
        self.view_apk_path.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.view_apk_path.setFont(font)
        self.view_apk_path.setDefault(False)
        self.view_apk_path.setObjectName("view_apk_path")
        self.gridLayout_5.addWidget(self.view_apk_path, 2, 1, 1, 1)
        self.input_text_via_adb = QtWidgets.QPushButton(self.ADB)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.input_text_via_adb.sizePolicy().hasHeightForWidth())
        self.input_text_via_adb.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.input_text_via_adb.setFont(font)
        self.input_text_via_adb.setObjectName("input_text_via_adb")
        self.gridLayout_5.addWidget(self.input_text_via_adb, 3, 0, 1, 1)
        self.get_running_app_info_button = QtWidgets.QPushButton(self.ADB)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.get_running_app_info_button.sizePolicy().hasHeightForWidth())
        self.get_running_app_info_button.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.get_running_app_info_button.setFont(font)
        self.get_running_app_info_button.setObjectName("get_running_app_info_button")
        self.gridLayout_5.addWidget(self.get_running_app_info_button, 3, 1, 1, 1)
        self.pull_log_without_clear = QtWidgets.QPushButton(self.ADB)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.pull_log_without_clear.sizePolicy().hasHeightForWidth())
        self.pull_log_without_clear.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.pull_log_without_clear.setFont(font)
        self.pull_log_without_clear.setObjectName("pull_log_without_clear")
        self.gridLayout_5.addWidget(self.pull_log_without_clear, 4, 0, 1, 1)
        self.aapt_getpackagename_button = QtWidgets.QPushButton(self.ADB)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.aapt_getpackagename_button.sizePolicy().hasHeightForWidth())
        self.aapt_getpackagename_button.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.aapt_getpackagename_button.setFont(font)
        self.aapt_getpackagename_button.setObjectName("aapt_getpackagename_button")
        self.gridLayout_5.addWidget(self.aapt_getpackagename_button, 4, 1, 1, 1)
        self.pull_log_with_clear = QtWidgets.QPushButton(self.ADB)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.pull_log_with_clear.sizePolicy().hasHeightForWidth())
        self.pull_log_with_clear.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.pull_log_with_clear.setFont(font)
        self.pull_log_with_clear.setObjectName("pull_log_with_clear")
        self.gridLayout_5.addWidget(self.pull_log_with_clear, 5, 0, 1, 1)
        self.clear_app_cache = QtWidgets.QPushButton(self.ADB)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.clear_app_cache.sizePolicy().hasHeightForWidth())
        self.clear_app_cache.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.clear_app_cache.setFont(font)
        self.clear_app_cache.setObjectName("clear_app_cache")
        self.gridLayout_5.addWidget(self.clear_app_cache, 5, 1, 1, 1)
        self.app_package_and_activity = QtWidgets.QPushButton(self.ADB)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.app_package_and_activity.sizePolicy().hasHeightForWidth())
        self.app_package_and_activity.setSizePolicy(sizePolicy)
        self.app_package_and_activity.setMinimumSize(QtCore.QSize(0, 0))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.app_package_and_activity.setFont(font)
        self.app_package_and_activity.setObjectName("app_package_and_activity")
        self.gridLayout_5.addWidget(self.app_package_and_activity, 6, 0, 1, 1)
        self.force_stop_app = QtWidgets.QPushButton(self.ADB)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.force_stop_app.sizePolicy().hasHeightForWidth())
        self.force_stop_app.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.force_stop_app.setFont(font)
        self.force_stop_app.setObjectName("force_stop_app")
        self.gridLayout_5.addWidget(self.force_stop_app, 6, 1, 1, 1)
        self.close = QtWidgets.QPushButton(self.ADB)
        self.close.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(11)
        sizePolicy.setHeightForWidth(self.close.sizePolicy().hasHeightForWidth())
        self.close.setSizePolicy(sizePolicy)
        self.close.setMinimumSize(QtCore.QSize(0, 0))
        self.close.setMaximumSize(QtCore.QSize(16777215, 83))
        self.close.setBaseSize(QtCore.QSize(0, 10))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        font.setBold(False)
        font.setWeight(50)
        self.close.setFont(font)
        self.close.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        self.close.setMouseTracking(False)
        self.close.setTabletTracking(False)
        self.close.setAcceptDrops(False)
        self.close.setCheckable(False)
        self.close.setAutoDefault(False)
        self.close.setDefault(False)
        self.close.setFlat(False)
        self.close.setObjectName("close")
        self.gridLayout_5.addWidget(self.close, 0, 0, 1, 2)
        self.gridLayout_3.addLayout(self.gridLayout_5, 5, 3, 1, 1)
        self.RefreshButton = QtWidgets.QPushButton(self.ADB)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.RefreshButton.sizePolicy().hasHeightForWidth())
        self.RefreshButton.setSizePolicy(sizePolicy)
        self.RefreshButton.setMinimumSize(QtCore.QSize(160, 35))
        self.RefreshButton.setMaximumSize(QtCore.QSize(16777215, 35))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.RefreshButton.setFont(font)
        self.RefreshButton.setObjectName("RefreshButton")
        self.gridLayout_3.addWidget(self.RefreshButton, 4, 1, 1, 1)
        self.Cleartextbutton = QtWidgets.QPushButton(self.ADB)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Cleartextbutton.sizePolicy().hasHeightForWidth())
        self.Cleartextbutton.setSizePolicy(sizePolicy)
        self.Cleartextbutton.setMinimumSize(QtCore.QSize(0, 50))
        self.Cleartextbutton.setObjectName("Cleartextbutton")
        self.gridLayout_3.addWidget(self.Cleartextbutton, 7, 1, 1, 3)
        self.horizontalLayout_2.addLayout(self.gridLayout_3)
        self.gridLayout_4.addLayout(self.horizontalLayout_2, 0, 0, 1, 1)
        self.tabWidget.addTab(self.ADB, "")
        self.text = QtWidgets.QWidget()
        self.text.setObjectName("text")
        self.formLayout_2 = QtWidgets.QFormLayout(self.text)
        self.formLayout_2.setObjectName("formLayout_2")
        self.textBrowser1 = QtWidgets.QTextBrowser(self.text)
        font = QtGui.QFont()
        font.setFamily("Franklin Gothic Medium")
        font.setPointSize(16)
        self.textBrowser1.setFont(font)
        self.textBrowser1.setAcceptDrops(False)
        self.textBrowser1.setObjectName("textBrowser1")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.SpanningRole, self.textBrowser1)
        self.tabWidget.addTab(self.text, "")
        self.horizontalLayout.addWidget(self.tabWidget)
        self.formLayout_3.setLayout(0, QtWidgets.QFormLayout.SpanningRole, self.horizontalLayout)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        self.ComboxButton.setCurrentIndex(0)
        self.Cleartextbutton.clicked.connect(self.textBrowser.clear) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "ADBTools"))
        self.label.setText(_translate("MainWindow", "作者：王克    微信：2315313745"))
        self.ComboxButton.setItemText(0, _translate("MainWindow", "请点击刷新设备"))
        self.adbbutton.setText(_translate("MainWindow", "执行adb"))
        self.button_reboot.setToolTip(_translate("MainWindow", "<html><head/><body><p>Reboot</p></body></html>"))
        self.button_reboot.setText(_translate("MainWindow", "重启设备"))
        self.adb_root.setText(_translate("MainWindow", "获取Root权限"))
        self.adb_pull_file.setText(_translate("MainWindow", "Pull文件"))
        self.adb_push_file.setText(_translate("MainWindow", "Push文件"))
        self.simulate_click.setText(_translate("MainWindow", "模拟点击"))
        self.simulate_swipe.setText(_translate("MainWindow", "模拟滑动"))
        self.simulate_long_press.setText(_translate("MainWindow", "模拟长按"))
        self.adb_install.setText(_translate("MainWindow", "安装应用"))
        self.adb_uninstall.setText(_translate("MainWindow", "卸载应用"))
        self.start_app.setText(_translate("MainWindow", "启动应用"))
        self.adb_cpu_info.setText(_translate("MainWindow", "显示CPU信息"))
        self.pull_hulog.setText(_translate("MainWindow", "pull Hulog"))
        self.get_screenshot.setText(_translate("MainWindow", "Screen"))
        self.view_apk_path.setText(_translate("MainWindow", "adb shell pm path"))
        self.input_text_via_adb.setText(_translate("MainWindow", "Input text"))
        self.get_running_app_info_button.setText(_translate("MainWindow", "获取应用版本号"))
        self.pull_log_without_clear.setText(_translate("MainWindow", "Pull all log"))
        self.aapt_getpackagename_button.setText(_translate("MainWindow", "获取apk文件的包名"))
        self.pull_log_with_clear.setText(_translate("MainWindow", "Clear-Pull log"))
        self.clear_app_cache.setText(_translate("MainWindow", "Clear App 缓存"))
        self.app_package_and_activity.setText(_translate("MainWindow", "获取包名和活动页名"))
        self.force_stop_app.setText(_translate("MainWindow", "Close App"))
        self.close.setText(_translate("MainWindow", "关闭"))
        self.RefreshButton.setText(_translate("MainWindow", "刷新设备"))
        self.Cleartextbutton.setText(_translate("MainWindow", "清空"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.ADB), _translate("MainWindow", "ADB"))
        self.textBrowser1.setHtml(_translate("MainWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Franklin Gothic Medium\'; font-size:16pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">adb root</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">adb remount remount</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">adb shell &quot;setprop bmi.service.adb.root 1&quot;</p></body></html>"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.text), _translate("MainWindow", "TEXT"))
