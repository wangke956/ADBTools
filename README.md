# ADBTools
一、前提条件：
1. 系统变量增加adb路径。

二、使用说明：
1. 创建python虚拟环境python=3.11，并安装依赖包:environment.yml
2. 运行main.py文件

三、UI设计说明：
1. 使用Qt Designer打开UI文件
2. 修改界面元素
3. 在项目文件根目录下运行命令：pyuic5 -x [UI文件名] -o [UI模块文件名]

四、编译说明：
1. 在项目文件根目录下运行命令：pyinstaller --onefile --noconsole --add-data "[u2.jar文件路径];uiautomator2\assets" main.py
