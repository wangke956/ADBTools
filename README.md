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

### 使用PyInstaller打包：
1. 在项目文件根目录下运行命令：pyinstaller --onefile --noconsole --add-data "[u2.jar文件路径];uiautomator2\assets" main.py

### 使用Nuitka打包（推荐）：
Nuitka可以将Python代码编译为本地可执行文件，提供更好的性能和安全性。

#### 快速开始：
```bash
# 1. 安装依赖
pip install -r requirements_nuitka.txt

# 2. 使用打包脚本（推荐）
python nuitka_build.py --build onefile

# 3. 或手动使用Nuitka命令
python -m nuitka --standalone --onefile --windows-disable-console --plugin-enable=pyqt5 --windows-icon-from-ico=icon.ico --include-data-files=adbtool.ui=. --include-data-files=adbtools_config.json=. --include-package-data=Function_Moudle --output-dir=build_nuitka --output-filename=ADBTools_nuitka main.py
```

#### 详细说明：
1. **环境准备**：
   - 安装Python 3.7+
   - 安装Visual Studio Build Tools（C编译器）
   - 安装项目依赖：`pip install -r requirements_nuitka.txt`

2. **打包选项**：
   - 单文件版本：`python nuitka_build.py --build onefile`
   - 独立目录版本：`python nuitka_build.py --build standalone`
   - 清理构建文件：`python nuitka_build.py --clean`
   - 检查依赖：`python nuitka_build.py --check`

3. **输出文件**：
   - 单文件：`dist_nuitka/ADBTools_nuitka.exe`
   - 独立目录：`dist_nuitka/` 目录包含所有必要文件

4. **优势对比**：
   - **Nuitka**：性能更好、体积更小、反编译更难
   - **PyInstaller**：打包速度更快、配置更简单

详细打包说明请参考：[Nuitka打包说明.md](Nuitka打包说明.md)
