# ADBTools

一个功能强大的 Android 调试桥（ADB）工具，提供图形化界面来管理 Android 设备、安装应用、查看日志等功能。

## 目录

- [功能特性](#功能特性)
- [系统要求](#系统要求)
- [安装说明](#安装说明)
- [使用说明](#使用说明)
- [配置管理](#配置管理)
- [日志功能](#日志功能)
- [打包说明](#打包说明)
- [常见问题](#常见问题)

---

## 功能特性

### 核心功能
- ✅ 设备管理和连接（支持 ADB 和 uiautomator2 两种模式）
- ✅ 应用安装、卸载、启动
- ✅ 批量安装和版本验证
- ✅ 设备日志拉取
- ✅ 文件传输
- ✅ 工程模式访问
- ✅ VR 激活
- ✅ 应用版本检查

### 高级功能
- 📊 完整的日志记录系统
- ⚙️ 增强版配置管理器
- 🔄 配置备份和恢复
- 📈 性能监控
- 🎯 操作历史记录
- 🔧 自动打包工具

---

## 系统要求

### 必需软件
- **Python 3.7+** - 项目运行环境
- **ADB 工具** - Android 调试桥（需要添加到系统 PATH）

### 可选软件
- **Visual Studio Build Tools** - 用于 Nuitka 打包
- **Inno Setup 6+** - 用于制作 Windows 安装包

---

## 安装说明

### 1. 创建虚拟环境

```bash
# 创建 Python 虚拟环境
python -m venv .venv

# 激活虚拟环境（Windows）
.venv\Scripts\activate

# 激活虚拟环境（Linux/Mac）
source .venv/bin/activate
```

### 2. 安装依赖

```bash
# 安装基础依赖
pip install -r environment.yml

# 或安装打包依赖
pip install -r requirements_nuitka.txt
```

### 3. 运行程序

```bash
python main.py
```

---

## 使用说明

### UI 设计说明

如需修改界面：

1. 使用 Qt Designer 打开 `adbtool.ui` 文件
2. 修改界面元素
3. 在项目根目录运行命令：
   ```bash
   pyuic5 -x adbtool.ui -o adbtool.ui
   ```

### 连接模式

ADBTools 支持两种连接模式：

1. **ADB 模式** - 使用标准 ADB 命令
2. **uiautomator2 模式** - 使用 uiautomator2 库（功能更强大）

两种模式可以自动切换，当 u2 无法连接时会自动使用 ADB 模式。

---

## 配置管理

### 配置文件

配置文件位于 `adbtools_config.json`，包含以下主要部分：

```json
{
  "version": { ... },           // 版本信息
  "adb": { ... },               // ADB 设置
  "ui": { ... },                // 界面设置
  "devices": { ... },           // 设备设置
  "logging": { ... },           // 日志设置
  "batch_install": { ... },     // 批量安装设置
  "network": { ... },           // 网络设置
  "performance": { ... },       // 性能设置
  "backup": { ... },            // 备份设置
  "shortcuts": { ... }          // 快捷键设置
}
```

### 配置管理器

ADBTools 提供了增强版配置管理器，支持：

- **树形配置浏览** - 按分类浏览所有配置项
- **多种编辑方式** - 表单编辑、JSON 直接编辑
- **实时验证** - 编辑时实时验证配置有效性
- **配置备份** - 自动备份和手动恢复
- **导入导出** - 配置文件的导入和导出

### 配置验证

配置管理器提供完整的验证功能：

- **语法验证** - 验证 JSON 格式正确性
- **值域验证** - 验证配置值的有效范围
- **类型验证** - 验证配置值的类型正确性
- **自动修复** - 提供自动修复建议

---

## 日志功能

### 日志文件位置

所有日志文件存储在 `logs/` 目录下：

```
logs/
├── adbtools.log              # 主日志文件
├── operation_history.log     # 操作历史记录
├── performance.log            # 性能监控日志
├── adbtools.log.1             # 日志轮转备份
└── ...
```

### 日志配置

日志配置位于 `adbtools_config.json`：

```json
{
  "logging": {
    "level": "DEBUG",
    "file": "adbtools.log",
    "max_size": 10485760,
    "backup_count": 5,
    "console_output": true,
    "log_dir": "logs",
    "enable_operation_history": true,
    "enable_performance_monitoring": true
  }
}
```

### 日志内容

#### 主日志文件 (adbtools.log)
记录所有详细的系统日志，包括：
- 应用启动和关闭
- 设备连接状态
- ADB 命令执行
- 线程操作
- 错误和异常

#### 操作历史记录 (operation_history.log)
记录所有用户操作的详细历史，以 JSON 格式存储：

```json
{
  "timestamp": "2026-01-16 10:30:50",
  "operation_type": "refresh_devices",
  "device_id": null,
  "details": {
    "action": "刷新设备列表"
  },
  "result": "success",
  "thread_id": 12345
}
```

#### 性能监控日志 (performance.log)
记录每个操作的执行时间，用于性能分析：

```json
{
  "timestamp": "2026-01-16 10:30:50",
  "operation": "refresh_devices",
  "device_id": null,
  "elapsed_time": 1.234,
  "thread_id": 12345
}
```

### 日志查看工具

提供了 `log_viewer.py` 命令行工具来查看和分析日志：

```bash
# 查看日志摘要
python log_viewer.py --view

# 导出日志到文件
python log_viewer.py --export logs_export.txt

# 搜索日志
python log_viewer.py --search "ERROR" --file logs/adbtools.log
```

### 在代码中使用日志

```python
from logger_manager import get_logger, log_operation, measure_performance

# 创建日志记录器
logger = get_logger("YourModuleName")

# 记录不同级别的日志
logger.debug("调试信息")
logger.info("操作成功")
logger.warning("警告信息")
logger.error("操作失败")

# 记录操作历史
log_operation(
    operation_type="install_apk",
    details={"package_name": "com.example.app"},
    device_id="12345678",
    result="success"
)

# 性能监控
with measure_performance("install_apk", device_id="12345678"):
    install_app("com.example.app")
```

---

## 打包说明

### 使用 PyInstaller 打包

```bash
pyinstaller --onefile --noconsole \
  --add-data "[u2.jar文件路径];uiautomator2\assets" \
  main.py
```

### 使用 Nuitka 打包（推荐）

Nuitka 可以将 Python 代码编译为本地可执行文件，提供更好的性能和安全性。

#### 快速开始

```bash
# 1. 安装依赖
pip install -r requirements_nuitka.txt

# 2. 使用打包脚本（推荐）
python nuitka_build.py --build onefile

# 3. 或手动使用 Nuitka 命令
python -m nuitka --standalone --onefile \
  --windows-disable-console \
  --plugin-enable=pyqt5 \
  --windows-icon-from-ico=icon.ico \
  --include-data-files=adbtool.ui=. \
  --include-data-files=adbtools_config.json=. \
  --include-package-data=Function_Moudle \
  --output-dir=build_nuitka \
  --output-filename=ADBTools_nuitka \
  main.py
```

#### 自动打包脚本

提供了 `auto_package.py` 自动打包脚本，支持：

1. **版本号更新** - 自动更新版本号
2. **ADB 工具文件配置** - 支持三种方式配置 ADB 文件路径
3. **Nuitka 构建** - 自动生成单文件可执行程序
4. **文件复制** - 自动复制必要的文件到构建目录
5. **Inno Setup 打包** - 生成 Windows 安装包

```bash
# 运行自动打包脚本
python auto_package.py
```

脚本将引导您完成以下步骤：

1. 输入版本号（如：1.6.2）
2. 选择 ADB 工具文件来源：
   - 手动输入 platform-tools 文件夹路径
   - 使用默认路径（D:\work_tools\platform-tools）
   - 跳过 ADB 文件复制（后续手动处理）
3. 自动更新版本号
4. 执行 Nuitka 构建
5. 复制文件到构建目录
6. Inno Setup 打包

#### 输出文件

打包完成后，生成的文件位于：

1. **build_nuitka/** - Nuitka 构建的中间文件
2. **dist_nuitka/** - Nuitka 生成的可执行文件和相关文件
3. **Output/** - Inno Setup 生成的安装包
   - `ADBTools_Setup.exe` - 最终安装程序

#### 优势对比

| 特性 | Nuitka | PyInstaller |
|------|--------|-------------|
| 性能 | 更好 | 一般 |
| 体积 | 更小 | 较大 |
| 反编译难度 | 更难 | 较易 |
| 打包速度 | 较慢 | 更快 |
| 配置复杂度 | 较高 | 较低 |

---

## 常见问题

### 1. iscc 命令未找到

**问题**：运行 Inno Setup 时提示 "iscc 命令未找到"

**解决**：
- 确保已安装 Inno Setup 6+
- 将 Inno Setup 安装目录添加到系统 PATH
- 或修改 auto_package.py 中的 iscc 路径

### 2. Nuitka 构建失败

**问题**：Nuitka 构建过程中出现错误

**解决**：
- 检查 Python 依赖是否完整安装
- 运行 `python nuitka_build.py --check` 检查依赖
- 确保有足够的磁盘空间

### 3. 日志文件过大

**问题**：日志文件占用过多磁盘空间

**解决**：
- 减少 `max_size` 配置值
- 减少 `backup_count` 配置值
- 将日志级别从 `DEBUG` 改为 `INFO`
- 定期清理日志文件

### 4. 配置文件损坏

**问题**：配置文件损坏无法加载

**解决**：
- 检查备份目录中的备份文件
- 手动恢复最近的备份
- 使用配置管理器的恢复功能

### 5. u2 无法连接

**问题**：uiautomator2 模式无法连接设备

**解决**：
- 检查设备是否已启用 USB 调试
- 尝试切换到 ADB 模式
- 检查 u2 是否正确初始化

---

## 项目结构

```
ADBTools/
├── main.py                      # 主程序入口
├── ADB_module.py                # 主窗口模块
├── adb_utils.py                 # ADB 工具类
├── config_manager.py            # 配置管理器
├── config_manager_enhanced.py   # 增强版配置管理器
├── logger_manager.py            # 日志管理器
├── log_viewer.py                # 日志查看工具
├── adbtool.ui                   # UI 文件
├── adbtools_config.json         # 配置文件
├── icon.ico                     # 程序图标
├── nuitka_build.py              # Nuitka 构建脚本
├── auto_package.py              # 自动打包脚本
├── ADBTools_setup.iss           # Inno Setup 安装脚本
├── environment.yml              # 基础依赖
├── requirements_nuitka.txt      # 打包依赖
├── Function_Moudle/             # 功能模块目录
│   ├── adb_*.py                 # ADB 相关线程
│   ├── app_*.py                 # 应用相关线程
│   └── ...
├── logs/                        # 日志目录
├── backups/                     # 配置备份目录
├── build_nuitka/                # Nuitka 构建目录
├── dist_nuitka/                 # Nuitka 分发目录
└── Output/                      # 安装包输出目录
```

---

## 技术支持

如有问题或建议，请通过以下方式联系：

- **GitHub 仓库**: https://github.com/wangke956/ADBTools
- **问题反馈**: 创建 GitHub Issue
- **查看日志**: 使用日志查看工具获取详细的错误信息

---

## 许可证

本项目采用 MIT 许可证。

---

## 贡献

欢迎贡献代码、报告问题或提出建议！

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

**最后更新**: 2026-01-19