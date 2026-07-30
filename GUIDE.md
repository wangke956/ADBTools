# ADBTools 完整使用指南

**最后更新**: 2026-06-26  
**版本**: v1.8.30+

---

## 📋 目录

1. [项目概述](#项目概述)
2. [快速开始](#快速开始)
3. [云构建与自动发布](#云构建与自动发布)
4. [版本号管理](#版本号管理)
5. [本地打包](#本地打包)
6. [故障排除](#故障排除)
7. [高级配置](#高级配置)

---

## 项目概述

ADBTools 是一个功能强大的 Android 设备管理工具，支持：
- ✅ U2 (uiautomator2) 和 ADB 双模式连接
- ✅ VR 设备管理和控制
- ✅ 批量应用安装和管理
- ✅ 截图和日志获取
- ✅ 工程模式访问

### 技术栈
- **语言**: Python 3.10
- **UI框架**: PyQt5
- **编译工具**: Nuitka (OneFile 模式)
- **打包工具**: Inno Setup
- **CI/CD**: GitHub Actions

---

## 快速开始

### 方式 1：下载预编译版本（推荐）

1. 访问 [Releases 页面](https://github.com/wangke956/ADBTools/releases)
2. 下载最新版本：
   - **便携版**: `ADBTools_x.x.x_Windows.zip`
   - **安装版**: `ADBTools_Setup.exe`
3. 解压或安装后运行 `ADBTools_nuitka.exe`

### 方式 2：从源码构建

```powershell
# 克隆仓库
git clone https://github.com/wangke956/ADBTools.git
cd ADBTools

# 创建虚拟环境
python -m venv .venv
.\.venv\Scripts\activate

# 安装依赖
pip install -r requirements_nuitka.txt

# 本地构建
python nuitka_build_fixed_v2.py --build onefile
```

---

## 云构建与自动发布

### 🚀 三种触发方式

#### 方式 1：推送 Git Tag（最常用）⭐⭐⭐

```powershell
# 使用快速脚本（推荐）
.\quick_release.ps1 1.8.30

# 或手动执行
git add .
git commit -m "chore: release v1.8.30"
git tag v1.8.30
git push origin main --tags
```

**效果：**
- ✅ 自动触发云构建
- ✅ 构建完成后**自动创建 Release**
- ✅ 生成便携版 ZIP 和安装版 EXE

---

#### 方式 2：GitHub Web 界面手动触发

1. 访问：https://github.com/wangke956/ADBTools/actions
2. 点击 **Build and Package ADBTools**
3. 点击 **Run workflow**
4. 填写参数：
   - **版本号**: `1.8.30`
   - **是否创建 Release**: ✅ 勾选
5. 点击 **Run workflow**

---

#### 方式 3：仅推送代码（不创建 Release）

```powershell
git add .
git commit -m "fix: some bug"
git push origin main
```

**效果：**
- ✅ 触发云构建
- ❌ 不会创建 Release
- 版本号使用日期格式（如 `2026.06.26`）
- 适合日常开发测试

---

### 📦 构建输出

#### Artifact（临时文件）
- **位置**: Actions → Artifacts
- **文件名**: `ADBTools_{version}_Windows.zip`
- **保存期限**: 90 天

#### Release（正式发布）
- **位置**: https://github.com/wangke956/ADBTools/releases
- **包含文件**:
  - `ADBTools_{version}_Windows.zip` - 便携版
  - `ADBTools_Setup.exe` - 安装版
- **永久保存**

---

### 🔧 工作流配置

工作流文件：`.github/workflows/build.yml`

#### 主要步骤

1. **环境准备**
   - 安装 Python 3.10
   - 安装 Visual C++ Build Tools
   - 安装项目依赖

2. **版本管理**
   - 从 Tag/输入/日期获取版本号
   - 自动更新配置文件

3. **Nuitka 编译**
   - OneFile 模式编译
   - 包含所有资源和依赖

4. **Inno Setup 打包**
   - 创建 Windows 安装程序
   - 设置版本信息和图标

5. **上传产物**
   - 上传 ZIP 到 Artifacts
   - 创建 GitHub Release

---

### ⚙️ Secrets 配置（可选）

如需接收构建通知，配置 Server酱：

1. 进入 **Settings** → **Secrets and variables** → **Actions**
2. 添加 Secret：
   - Name: `SERVERCHAN_API_KEY`
   - Value: 你的 Server酱 SendKey

获取 SendKey：
- 访问 [Server酱官网](https://sct.ftqq.com/)
- 登录并获取

---

## 版本号管理

### ❓ 核心问题

**问：我应该在哪里更新版本号？**

**答：你不需要在本地更新任何文件！云端会自动处理。**

---

### 🎯 完整流程

#### 1️⃣ 本地操作（你只需要做这个）

```powershell
# 修改代码后，一行命令完成发布
.\quick_release.ps1 1.8.30
```

这会自动：
- ✅ 提交代码更改
- ✅ 创建 Git Tag `v1.8.30`
- ✅ 推送到 GitHub

#### 2️⃣ 云端自动处理（无需你操心）

云构建会自动：
1. ✅ 从 Git Tag 提取版本号：`v1.8.30` → `1.8.30`
2. ✅ 更新 `adbtools_config.json` 中的 `version` 和 `file_version`
3. ✅ 更新 `ADBTools_setup.iss` 中的 `MyAppVersion`
4. ✅ Nuitka 构建时使用新版本号
5. ✅ Inno Setup 打包时使用新版本号
6. ✅ 生成带版本号的安装包和 ZIP 文件

---

### 📋 正确 vs 错误做法

#### ❌ 错误做法（不要这样做）

```powershell
# 不要手动修改这些文件！
# adbtools_config.json
# config_manager.py
# ADBTools_setup.iss

git add .
git commit -m "update version to 1.8.30"
git push
```

**问题：**
- 容易遗漏某个文件
- 与云端自动化冲突
- 增加人为错误风险

---

#### ✅ 正确做法（推荐）

```powershell
# 只需推送代码 + 创建 tag
.\quick_release.ps1 1.8.30
```

**优势：**
- 简单快捷
- 完全自动化
- 不会出错

---

### 💡 常见场景

#### 场景 1：日常版本发布

```powershell
# 修复了 Bug，发布新版本
.\quick_release.ps1 1.8.30
```

**结果：**
- 版本号：`1.8.30`
- 自动创建 Release
- 生成正式版安装包

---

#### 场景 2：仅推送代码（不发布版本）

```powershell
# 日常开发，不创建 tag
git add .
git commit -m "fix: some bug"
git push origin main
```

**结果：**
- 版本号：`2026.06.26`（当前日期）
- 不会创建 Release
- 适合内部测试

---

#### 场景 3：重大版本发布

```powershell
# 新功能上线，大版本更新
.\quick_release.ps1 2.0.0
```

**结果：**
- 版本号：`2.0.0`
- 自动创建 Release
- 生成正式版安装包

---

### ⚠️ 注意事项

#### 1. Tag 命名规范

✅ **正确：**
```powershell
git tag v1.8.30
git tag v2.0.0
```

❌ **错误：**
```powershell
git tag 1.8.30      # 缺少 v 前缀
git tag V1.8.30     # 大写 V
git tag v1.8.30.1   # 格式不规范
```

---

#### 2. 避免重复 Tag

如果 tag 已存在，脚本会提示：
```
⚠️  Tag v1.8.30 已存在！
是否删除并重新创建? (y/n)
```

**解决方法：**
```powershell
# 删除旧 tag
git tag -d v1.8.30
git push origin :refs/tags/v1.8.30

# 重新创建
.\quick_release.ps1 1.8.30
```

---

#### 3. 分支要求

建议在 `main` 分支上发布：
```powershell
git checkout main
git pull origin main
.\quick_release.ps1 1.8.30
```

---

## 本地打包

### 🛠️ 使用自动打包脚本

```powershell
# 运行交互式打包工具
python auto_package.py
```

按照提示输入：
1. 版本号（如 `1.8.30`）
2. platform-tools 路径（可选，留空自动下载）

---

### 📦 使用 Nuitka 直接构建

```powershell
# 清理旧构建
python nuitka_build_fixed_v2.py --clean

# 构建 OneFile 版本
python nuitka_build_fixed_v2.py --build onefile

# 验证输出
ls dist_nuitka/
```

---

### 🔧 使用 PowerShell 发布脚本

#### quick_release.ps1（快速发布）

```powershell
# 语法
.\quick_release.ps1 <版本号> [-SkipCommit]

# 示例
.\quick_release.ps1 1.8.30
.\quick_release.ps1 1.8.30 -SkipCommit  # 跳过提交，只创建 tag
```

**功能：**
- 自动检查未提交的更改
- 自动提交代码
- 创建并推送 Git Tag
- 触发云构建

---

#### release.ps1（交互式发布）

```powershell
# 语法
.\release.ps1 [<版本号>] [-DryRun]

# 示例
.\release.ps1                    # 交互式输入版本号
.\release.ps1 1.8.30             # 指定版本号
.\release.ps1 1.8.30 -DryRun     # 预览操作，不实际执行
```

**功能：**
- 交互式确认每个步骤
- 检查 Git 状态
- 检查当前分支
- 检查 Tag 是否已存在
- 支持 DryRun 模式

---

## 故障排除

### 🐛 常见问题

#### Q1: U2 连接失败 - ApplicationSharedMemory not initialized

**现象：**
```
U2连接无法获取设备信息，降级到ADB模式: 192.168.1.38:34567
java.lang.IllegalStateException: ApplicationSharedMemory not initialized
```

**原因：**
设备端 uiautomator2 server 启动需要时间，第一次连接时 server 尚未完全初始化。

**解决方案：**
程序已内置自动重试机制（最多 3 次，间隔 2 秒），通常会自动解决。

如果仍然失败：
1. 重启设备的 uiautomator2 server
2. 检查设备网络连接
3. 尝试使用 ADB 模式

---

#### Q2: GitHub Release 创建失败 - 403 Forbidden

**现象：**
```
GitHub release failed with status: 403
{"message":"Resource not accessible by integration"}
```

**原因：**
工作流中错误地使用了 `token: ${{ secrets.GITHUB_TOKEN }}`

**解决方案：**
已在 `.github/workflows/build.yml` 第 295 行注释掉该行。GITHUB_TOKEN 会自动提供，无需显式指定。

---

#### Q3: Nuitka 编译错误

**可能原因：**
1. 缺少 Visual C++ Build Tools
2. 依赖包不完整
3. 内存不足

**解决方案：**
```powershell
# 确保安装了 VC++ Build Tools
# 从 https://visualstudio.microsoft.com/downloads/ 下载

# 检查依赖
pip install -r requirements_nuitka.txt

# 清理后重新构建
python nuitka_build_fixed_v2.py --clean
python nuitka_build_fixed_v2.py --build onefile
```

---

#### Q4: 构建需要多长时间？

**答案：**
- 首次构建：约 15-20 分钟（需要安装依赖和编译）
- 后续构建：约 10-15 分钟（会使用缓存）

---

#### Q5: Artifact 保存多久？

**答案：**
默认 90 天，可以在 `.github/workflows/build.yml` 中修改 `retention-days` 参数。

---

#### Q6: 如何查看构建日志？

**步骤：**
1. 进入 **Actions** 标签
2. 点击具体的 workflow run
3. 点击 job 名称查看详细日志

---

### 🔍 调试技巧

#### 本地测试构建

在提交前，建议在本地测试构建：

```powershell
# 安装依赖
pip install -r requirements_nuitka.txt

# 清理旧构建
python nuitka_build_fixed_v2.py --clean

# 执行构建
python nuitka_build_fixed_v2.py --build onefile

# 验证输出
ls dist_nuitka/
```

---

#### 检查工作流语法

```powershell
# 使用 actionlint 检查
actionlint .github/workflows/build.yml
```

---

## 高级配置

### 🎨 自定义构建

#### 修改 Python 版本

编辑 `.github/workflows/build.yml`：

```yaml
env:
  PYTHON_VERSION: '3.11'  # 修改为你需要的版本
```

---

#### 修改构建类型

当前使用 OneFile 模式，如需改为 Standalone 模式：

```yaml
- name: Build with Nuitka (Standalone)
  run: |
    python nuitka_build_fixed_v2.py --build standalone
```

**注意：** Standalone 模式会生成独立目录，需要在 Inno Setup 中调整文件引用。

---

#### 添加更多平台

可以在工作流中添加 macOS 和 Linux 构建任务：

```yaml
build-macos:
  name: Build macOS Executable
  runs-on: macos-latest
  # ... 配置步骤
  
build-linux:
  name: Build Linux Executable
  runs-on: ubuntu-latest
  # ... 配置步骤
```

---

### 📊 构建状态徽章

将以下代码添加到 README.md 顶部：

```markdown
![Build Status](https://github.com/wangke956/ADBTools/actions/workflows/build.yml/badge.svg)
[![Release](https://img.shields.io/github/v/release/wangke956/ADBTools)](https://github.com/wangke956/ADBTools/releases)
```

---

### 🔗 相关链接

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [Nuitka 官方文档](https://nuitka.net/)
- [softprops/action-gh-release](https://github.com/softprops/action-gh-release)
- [Inno Setup 文档](https://jrsoftware.org/iss/)

---

### 💡 最佳实践

1. **使用标签发布**
   - 重要版本使用 Git 标签
   - 标签格式：`v主版本.次版本.修订号`

2. **定期清理 Artifact**
   - Artifact 默认保留 90 天
   - 可以手动删除旧的 Artifact 节省空间

3. **保护分支**
   - 为主分支设置保护规则
   - 要求 PR 通过 CI 检查才能合并

4. **通知机制**
   - 配置 Server酱 或其他通知服务
   - 及时了解构建状态

5. **语义化版本**
   - 主版本：重大变更（`1.x.x` → `2.0.0`）
   - 次版本：新功能（`1.8.x` → `1.9.0`）
   - 修订号：Bug 修复（`1.8.29` → `1.8.30`）

---

## 🆘 获得帮助

如有问题，请：
1. 查看 Actions 日志
2. 搜索 Issues
3. 创建新的 Issue

---

**记住这个原则：**

> **只需推送代码 + 创建 Tag，其他都交给云端！**

```powershell
.\quick_release.ps1 1.8.30
```

就这么简单！🎉

---
---

# ADBTools 新功能开发指南

> 本文档详细说明如何在 ADBTools 项目中添加新功能，涵盖 UI 添加、线程编写、ADB/U2 双模式兼容、信号绑定、日志记录等完整流程。

---

## 目录

1. [项目架构总览](#1-项目架构总览)
2. [核心概念](#2-核心概念)
3. [添加功能完整步骤](#3-添加功能完整步骤)
4. [线程编写详解](#4-线程编写详解)
5. [ADB/U2 双模式兼容详解](#5-adbu2-双模式兼容详解)
6. [Manager 编写详解](#6-manager-编写详解)
7. [主窗口信号绑定详解](#7-主窗口信号绑定详解)
8. [日志记录规范](#8-日志记录规范)
9. [完整实战案例](#9-完整实战案例)
10. [常见问题与注意事项](#10-常见问题与注意事项)
11. [文件修改清单](#11-文件修改清单)

---

### 1. 项目架构总览

#### 1.1 目录结构

```
ADBTools/
├── main.py                          # 程序入口
├── ADB_module.py                    # 主窗口类 (Controller)
├── adbtool.ui                       # Qt Designer UI 文件
├── adb_utils.py                     # ADB 底层工具类
├── logger_manager.py                # 日志管理器
├── config_manager.py                # 配置管理器
├── Function_Moudle/                 # 功能模块目录
│   ├── base_thread.py               # ★ 线程基类
│   ├── thread_factory.py            # ★ 线程工厂（注册线程类型）
│   ├── adb_device_utils.py          # 设备连接检查工具
│   │
│   ├── app_operations.py            # 应用操作管理器 (Manager)
│   ├── device_manager.py            # 设备操作管理器 (Manager)
│   ├── file_operations.py           # 文件操作管理器 (Manager)
│   ├── input_operations.py          # 输入操作管理器 (Manager)
│   ├── log_operations.py            # 日志操作管理器 (Manager)
│   ├── vr_controller.py             # VR 功能控制器 (Manager)
│   ├── datong_manager.py            # 大通项目管理器 (Manager)
│   │
│   ├── start_app_thread.py          # 启动应用线程（支持 U2+ADB）
│   ├── force_stop_app_thread.py     # U2 模式停止应用线程
│   ├── adb_force_stop_app_thread.py # ADB 模式停止应用线程
│   ├── app_threads.py               # 应用相关线程集合
│   ├── device_threads.py            # 设备相关线程集合
│   ├── file_threads.py              # 文件相关线程集合
│   ├── vr_threads.py                # VR 相关线程集合
│   └── ...                          # 其他线程文件
```

#### 1.2 架构分层图

```
┌─────────────────────────────────────────────────────────┐
│                    main.py (入口)                        │
│  初始化 QApplication → 加载样式 → 创建主窗口 → 显示      │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│             ADB_module.py (主窗口 Controller)            │
│  ┌──────────────────────────────────────────────────┐   │
│  │  1. 加载 adbtool.ui                              │   │
│  │  2. 初始化各 Manager（功能管理器）                  │   │
│  │  3. 绑定按钮点击信号 → Manager 方法                │   │
│  │  4. 提供公共方法：get_selected_device() 等         │   │
│  └──────────────────────────────────────────────────┘   │
└──────┬──────────┬──────────┬──────────┬────────────────┘
       │          │          │          │
       ▼          ▼          ▼          ▼
┌──────────┐┌──────────┐┌──────────┐┌──────────┐
│AppOps    ││DeviceMgr ││FileOps   ││VRControl │  ← Manager 层
│Manager   ││          ││Manager   ││ler       │
└────┬─────┘└────┬─────┘└────┬─────┘└────┬─────┘
     │           │           │           │
     ▼           ▼           ▼           ▼
┌─────────────────────────────────────────────────────────┐
│                   Thread 层（QThread）                    │
│  继承 BaseThread / DeviceBaseThread / 直接继承 QThread   │
│  通过 pyqtSignal 与 UI 通信                              │
└──────┬──────────────────────────────────┬───────────────┘
       │                                  │
       ▼                                  ▼
┌──────────────┐                ┌──────────────────┐
│ ADB 模式      │                │ U2 模式           │
│ subprocess    │                │ uiautomator2      │
│ / adb_utils   │                │ / self.d          │
└──────────────┘                └──────────────────┘
```

#### 1.3 关键角色职责

| 角色 | 文件 | 职责 |
|------|------|------|
| **主窗口** | `ADB_module.py` | UI 加载、信号绑定、功能调度、提供设备信息 |
| **Manager** | `Function_Moudle/*_operations.py` 等 | 业务逻辑编排：参数校验 → 创建线程 → 连接信号 → 启动线程 |
| **Thread** | `Function_Moudle/*_thread.py` | 在子线程中执行耗时操作（ADB命令/U2调用），通过信号回报结果 |
| **工具类** | `adb_utils.py`、`adb_device_utils.py` | 提供 ADB 命令执行、设备检查等底层能力 |
| **线程工厂** | `thread_factory.py` | 统一管理线程创建（可选使用） |

---

### 2. 核心概念

#### 2.1 双模式连接：ADB 与 U2

ADBTools 支持两种设备连接模式：

| 模式 | 说明 | 适用场景 | 调用方式 |
|------|------|----------|----------|
| **ADB 模式** | 通过 `adb` 命令行工具 | 通用，不需要额外安装 | `subprocess.run("adb -s {device_id} ...")` 或 `ADBUtils.run_adb_command()` |
| **U2 模式** | 通过 `uiautomator2` Python 库 | 高级自动化，支持 UI 操作 | `self.d.app_start()`、`self.d.shell()` 等 |

**关键变量（在主窗口中）：**
- `self.connection_mode`：当前连接模式，值为 `'u2'` 或 `'adb'`
- `self.d`：U2 设备对象（仅 U2 模式有效）
- `self.device_id`：ADB 设备 ID（仅 ADB 模式有效）

#### 2.2 线程模型

所有耗时操作必须在子线程中执行，避免阻塞 UI。项目中存在 **三种线程编写风格**：

| 风格 | 基类 | 适用场景 | 示例 |
|------|------|----------|------|
| **风格 A** | `BaseThread` / `DeviceBaseThread` | 推荐使用，自带日志、超时、重试、取消 | `device_threads.py` 中的线程 |
| **风格 B** | 直接继承 `QThread` | 简单线程，不需要高级功能 | `adb_force_stop_app_thread.py` |
| **风格 C** | `QThread` + 双模式参数 | 需要在单个线程内支持 ADB/U2 切换 | `start_app_thread.py` |

#### 2.3 信号通信机制

线程与 UI 之间通过 `pyqtSignal` 通信，**严禁在线程中直接操作 UI 控件**。

项目中常用的信号定义：

```python
progress_signal = pyqtSignal(str)    # 进度信息（如"正在处理..."）
result_signal = pyqtSignal(str)      # 操作结果（成功/失败的消息）
error_signal = pyqtSignal(str)       # 错误信息
success_signal = pyqtSignal(str)     # 成功信号
finished_signal = pyqtSignal()       # 完成信号（无参数）
```

---

### 3. 添加功能完整步骤

#### 总览流程图

```
步骤1: 在 adbtool.ui 中添加按钮控件
         ↓
步骤2: 创建线程类（在 Function_Moudle/ 下新建或修改已有文件）
         ↓
步骤3: 创建/修改 Manager（编写业务调度逻辑）
         ↓
步骤4: 修改 ADB_module.py（声明变量 + 初始化 Manager + 绑定信号）
         ↓
步骤5:（可选）注册到线程工厂
         ↓
步骤6: 测试运行
```

#### 步骤 1：在 UI 中添加按钮

使用 **Qt Designer** 打开 `adbtool.ui`：

1. 找到合适的页面/Tab
2. 拖入一个 `QPushButton`
3. 设置 `objectName` 属性（非常重要！），例如：`my_new_feature_button`
4. 设置按钮文本，例如：`我的新功能`

> **记住这个 objectName**，后面在代码中要用它来查找控件并绑定信号。

#### 步骤 2：创建线程类

详见 [第 4 节](#4-线程编写详解)。

#### 步骤 3：创建/修改 Manager

详见 [第 6 节](#6-manager-编写详解)。

#### 步骤 4：修改主窗口

详见 [第 7 节](#7-主窗口信号绑定详解)。

---

### 4. 线程编写详解

#### 4.1 风格 A：继承 BaseThread（推荐）

适用于不需要区分 ADB/U2 模式的场景（纯 ADB 操作）。

**基类提供的能力：**
- ✅ 统一的 `run()` 方法，包含异常处理、状态管理
- ✅ 超时控制（`timeout` 参数）
- ✅ 重试机制（`max_retries` 参数）
- ✅ 取消支持（调用 `cancel()` 或 `check_cancelled()`）
- ✅ 自动日志记录
- ✅ 状态信号（`status_changed_signal`）

```python
# Function_Moudle/my_feature_thread.py

from PyQt5.QtCore import pyqtSignal
from Function_Moudle.base_thread import DeviceBaseThread


class MyFeatureThread(DeviceBaseThread):
    """我的新功能线程"""
    
    # 自定义信号（根据需要添加）
    result_signal = pyqtSignal(str)

    def __init__(self, device_id, param1, param2=None):
        """
        初始化
        
        Args:
            device_id: 设备 ID（由 DeviceBaseThread 处理）
            param1: 参数1
            param2: 参数2（可选）
        """
        super().__init__(device_id, thread_name="MyFeatureThread")
        self.param1 = param1
        self.param2 = param2

    def _run_implementation(self):
        """
        ★ 核心方法：必须实现
        在这里编写你的具体业务逻辑
        """
        from adb_utils import ADBUtils
        
        # 1. 发送进度信息（会显示在 UI 的 textBrowser 中）
        self.progress_signal.emit(f"正在处理: {self.param1}...")
        
        # 2. 执行 ADB 命令（使用 ADBUtils 统一管理路径）
        result = ADBUtils.run_adb_command(
            command=f"shell my_command {self.param1}",
            device_id=self.device_id,
            timeout=30
        )
        
        # 3. 长时间操作中间检查是否被取消
        self.check_cancelled()  # 如果用户取消了，这里会抛出 RuntimeError
        
        # 4. 判断命令执行结果
        if result.returncode == 0:
            self.result_signal.emit(f"操作成功: {result.stdout.strip()}")
            self.success_signal.emit("操作完成")
        else:
            self.error_signal.emit(f"操作失败: {result.stderr.strip()}")
```

**DeviceBaseThread 与 BaseThread 的区别：**

```python
# BaseThread：不需要设备信息的线程（如文件处理、版本检查等）
class BaseThread(QThread):
    def __init__(self, thread_name=None, timeout=None, max_retries=0, retry_interval=1):
        ...

# DeviceBaseThread：需要设备 ID 的线程（自动校验 device_id 非空）
class DeviceBaseThread(BaseThread):
    def __init__(self, device_id, thread_name=None):
        super().__init__(thread_name)
        self.device_id = device_id
```

#### 4.2 风格 B：直接继承 QThread（简单场景）

适用于逻辑简单、不需要高级功能的线程。项目中大量 ADB-only 的线程使用这种风格。

```python
# Function_Moudle/adb_my_feature_thread.py

from PyQt5.QtCore import QThread, pyqtSignal
import subprocess


class ADBMyFeatureThread(QThread):
    """ADB 模式下我的新功能线程（简单风格）"""
    
    # ★ 定义信号（这三个是最常用的组合）
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)

    def __init__(self, device_id, my_param=None):
        super().__init__()
        self.device_id = device_id
        self.my_param = my_param

    def run(self):
        """线程执行入口"""
        try:
            # 1. 参数校验
            if not self.my_param:
                self.error_signal.emit("参数不能为空")
                return
            
            # 2. 检查设备连接（推荐）
            from Function_Moudle.adb_device_utils import check_device_connection
            is_connected, error_msg = check_device_connection(self.device_id)
            if not is_connected:
                self.error_signal.emit(error_msg)
                return
            
            # 3. 发送进度
            self.progress_signal.emit("正在处理...")
            
            # 4. 执行 ADB 命令
            command = f"adb -s {self.device_id} shell my_command {self.my_param}"
            result = subprocess.run(
                command, shell=True, check=True,
                capture_output=True, text=True
            )
            
            # 5. 发送结果
            if result.returncode == 0:
                self.result_signal.emit("操作成功！")
            else:
                self.error_signal.emit(f"操作失败: {result.stderr}")
                
        except subprocess.CalledProcessError as e:
            self.error_signal.emit(f"命令执行失败: {str(e)}")
        except Exception as e:
            self.error_signal.emit(f"发生错误: {str(e)}")
```

#### 4.3 风格 C：单线程支持 ADB/U2 双模式

适用于需要同时支持两种模式的场景。线程接收 `connection_mode` 和 `u2_device` 参数，内部根据模式分别执行。

```python
# Function_Moudle/my_dual_mode_thread.py

from PyQt5.QtCore import QThread, pyqtSignal


class MyDualModeThread(QThread):
    """双模式线程 - 同时支持 ADB 和 U2"""
    
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)

    def __init__(self, device_id, my_param, connection_mode='adb', u2_device=None):
        """
        初始化
        
        Args:
            device_id: 设备 ID（ADB 模式使用）
            my_param: 业务参数
            connection_mode: 连接模式 ('u2' 或 'adb')
            u2_device: U2 设备对象（U2 模式使用）
        """
        super().__init__()
        self.device_id = device_id
        self.my_param = my_param
        self.connection_mode = connection_mode
        self.u2_device = u2_device

    def run(self):
        """执行入口 - 根据模式分发"""
        try:
            self.progress_signal.emit(f"正在处理: {self.my_param}...")
            
            if self.connection_mode == 'u2' and self.u2_device:
                self._execute_u2()
            elif self.connection_mode == 'adb':
                self._execute_adb()
            else:
                self.error_signal.emit("设备未连接或连接模式无效")
                
        except Exception as e:
            self.error_signal.emit(f"执行失败: {str(e)}")

    def _execute_u2(self):
        """U2 模式执行逻辑"""
        d = self.u2_device
        
        # U2 方式执行 shell 命令
        result = d.shell(f"my_command {self.my_param}")
        
        # U2 的 shell 返回值处理方式
        output = result.output if hasattr(result, 'output') else str(result)
        
        self.result_signal.emit(f"U2 模式执行成功: {output}")

    def _execute_adb(self):
        """ADB 模式执行逻辑"""
        from adb_utils import ADBUtils
        
        result = ADBUtils.run_adb_command(
            command=f"shell my_command {self.my_param}",
            device_id=self.device_id,
            timeout=30
        )
        
        if result.returncode == 0:
            self.result_signal.emit(f"ADB 模式执行成功: {result.stdout.strip()}")
        else:
            self.error_signal.emit(f"ADB 模式执行失败: {result.stderr.strip()}")
```

#### 4.4 线程编写对比总结

| 特性 | 风格 A (BaseThread) | 风格 B (QThread) | 风格 C (QThread 双模式) |
|------|---------------------|-------------------|------------------------|
| 自动异常处理 | ✅ | ❌ 需手动 try/except | ❌ 需手动 try/except |
| 超时控制 | ✅ | ❌ | ❌ |
| 重试机制 | ✅ | ❌ | ❌ |
| 取消支持 | ✅ | ❌ | ❌ |
| 自动日志 | ✅ | ❌ | ❌ |
| 代码简洁度 | 中等 | 简洁 | 较复杂 |
| 双模式支持 | ❌ | ❌ | ✅ |
| 适用场景 | 纯 ADB 复杂操作 | 纯 ADB 简单操作 | 需要兼容两种模式 |

---

### 5. ADB/U2 双模式兼容详解

#### 5.1 模式判断模板

在 Manager 中，判断当前连接模式的标准模板：

```python
def my_feature_method(self):
    """我的功能入口"""
    # 1. 获取设备信息
    device_id = self.main_window.get_selected_device()
    devices_id_lst = self.main_window.get_new_device_lst()
    
    # 2. 检查设备是否连接
    if device_id not in devices_id_lst:
        self.textBrowser.append("设备未连接！")
        return
    
    # 3. 检查 U2 连接可用性（如果当前是 U2 模式）
    if self.main_window.connection_mode == 'u2':
        if not self.main_window.d:
            # U2 连接失效，降级到 ADB 模式
            self.main_window.connection_mode = 'adb'
            self.textBrowser.append("U2连接不可用，切换到ADB模式")
    
    # 4. 根据模式创建不同的线程
    try:
        if self.main_window.connection_mode == 'u2' and self.main_window.d:
            # U2 模式 → 使用 U2 线程
            from Function_Moudle.my_feature_thread import MyFeatureThread
            self.main_window.my_feature_thread = MyFeatureThread(
                d=self.main_window.d,           # U2 设备对象
                my_param="xxx"
            )
        elif self.main_window.connection_mode == 'adb':
            # ADB 模式 → 使用 ADB 线程
            from Function_Moudle.adb_my_feature_thread import ADBMyFeatureThread
            self.main_window.my_feature_thread = ADBMyFeatureThread(
                device_id=device_id,             # ADB 设备 ID
                my_param="xxx"
            )
        else:
            self.textBrowser.append("设备未连接！")
            return
        
        # 5. 连接信号
        self.main_window.my_feature_thread.progress_signal.connect(self.textBrowser.append)
        self.main_window.my_feature_thread.result_signal.connect(self.textBrowser.append)
        self.main_window.my_feature_thread.error_signal.connect(self.textBrowser.append)
        
        # 6. 启动线程
        self.main_window.my_feature_thread.start()
        
    except Exception as e:
        self.textBrowser.append(f"启动线程失败: {e}")
```

#### 5.2 双模式 vs 分离线程

项目中有两种处理双模式的方式：

**方式一：分离线程文件（推荐简单功能使用）**

```
U2 模式 → force_stop_app_thread.py      （接收 self.d）
ADB 模式 → adb_force_stop_app_thread.py  （接收 device_id）
```

优点：每个线程逻辑简单，职责单一
缺点：需要维护两个文件

**方式二：单线程内部分发（推荐复杂功能使用）**

```
双模式 → start_app_thread.py  （接收 connection_mode + u2_device）
         内部根据模式调用 _execute_u2() 或 _execute_adb()
```

优点：一个文件搞定，逻辑集中
缺点：线程内部稍复杂

#### 5.3 ADB 与 U2 常用 API 对照表

| 操作 | ADB 模式 | U2 模式 |
|------|----------|--------|
| 执行 shell 命令 | `ADBUtils.run_adb_command("shell xxx", device_id)` | `d.shell("xxx")` |
| 启动应用 | `ADBUtils.run_adb_command("shell am start -n pkg/activity", device_id)` | `d.app_start(package)` |
| 停止应用 | `ADBUtils.run_adb_command("shell am force-stop pkg", device_id)` | `d.app_stop(package)` |
| 安装应用 | `ADBUtils.run_adb_command("install apk_path", device_id)` | `d.app_install(apk_path)` |
| 卸载应用 | `ADBUtils.run_adb_command("uninstall pkg", device_id)` | `d.app_uninstall(pkg)` |
| 获取前台应用 | `ADBUtils.run_adb_command("shell dumpsys activity top", device_id)` | `d.app_current()` |
| 截图 | `ADBUtils.run_adb_command("shell screencap ...", device_id)` | `d.screenshot(path)` |
| 推送文件 | `ADBUtils.run_adb_command("push local remote", device_id)` | `d.push(local, remote)` |
| 拉取文件 | `ADBUtils.run_adb_command("pull remote local", device_id)` | `d.pull(remote, local)` |

---

### 6. Manager 编写详解

#### 6.1 Manager 的作用

Manager 是 **业务逻辑编排层**，负责：
1. 获取用户输入（弹窗、对话框）
2. 参数校验
3. 设备连接检查
4. 创建线程、传递参数
5. 连接线程信号到 UI
6. 启动线程
7. 记录操作日志

#### 6.2 在已有 Manager 中添加方法

如果新功能属于已有类别（如应用操作），直接在对应 Manager 中添加方法即可：

```python
# 在 Function_Moudle/app_operations.py 的 AppOperationsManager 类中添加

from logger_manager import log_button_click, log_method_result, get_logger

logger = get_logger("ADBTools.AppOperations")


class AppOperationsManager:
    """应用操作管理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window
    
    @property
    def textBrowser(self):
        return self.main_window.textBrowser

    def my_new_feature(self):
        """我的新功能"""
        # 1. 获取设备信息
        device_id = self.main_window.get_selected_device()
        devices_id_lst = self.main_window.get_new_device_lst()
        
        # 2. 记录按钮点击日志
        log_button_click("my_new_feature_button", "我的新功能")
        
        # 3. 检查设备连接
        if device_id in devices_id_lst:
            try:
                # 4. 检查 U2 连接可用性
                if self.main_window.connection_mode == 'u2':
                    if not self.main_window.d:
                        self.main_window.connection_mode = 'adb'
                        self.textBrowser.append("U2连接不可用，切换到ADB模式")
                
                # 5. 获取用户输入（如果需要）
                from PyQt5.QtWidgets import QInputDialog
                param, ok = QInputDialog.getText(
                    self.main_window, "输入参数", "请输入要处理的参数："
                )
                if not (ok and param):
                    return
                
                # 6. 根据连接模式创建对应线程
                if self.main_window.connection_mode == 'u2' and self.main_window.d:
                    from Function_Moudle.my_feature_thread import MyFeatureThread
                    self.main_window.my_feature_thread = MyFeatureThread(
                        d=self.main_window.d, my_param=param
                    )
                elif self.main_window.connection_mode == 'adb':
                    from Function_Moudle.adb_my_feature_thread import ADBMyFeatureThread
                    self.main_window.my_feature_thread = ADBMyFeatureThread(
                        device_id=device_id, my_param=param
                    )
                else:
                    self.textBrowser.append("设备未连接！")
                    return
                
                # 7. 连接信号（★ 必须连接，否则无法看到输出）
                self.main_window.my_feature_thread.progress_signal.connect(self.textBrowser.append)
                self.main_window.my_feature_thread.result_signal.connect(self.textBrowser.append)
                self.main_window.my_feature_thread.error_signal.connect(self.textBrowser.append)
                
                # 8. 启动线程
                self.main_window.my_feature_thread.start()
                
                # 9. 记录操作结果日志
                log_method_result("my_new_feature", True, "线程已启动")
                
            except Exception as e:
                log_method_result("my_new_feature", False, str(e))
                self.textBrowser.append(f"启动失败: {e}")
        else:
            log_method_result("my_new_feature", False, "设备未连接")
            self.textBrowser.append("设备未连接！")
```

#### 6.3 创建全新 Manager

如果功能是全新的类别，需要创建新的 Manager 文件：

```python
# Function_Moudle/my_feature_operations.py

from logger_manager import log_button_click, log_method_result, get_logger

logger = get_logger("ADBTools.MyFeatureOperations")


class MyFeatureOperationsManager:
    """我的新功能操作管理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window
    
    @property
    def textBrowser(self):
        """快捷访问主窗口的输出文本框"""
        return self.main_window.textBrowser
    
    def my_feature_action(self):
        """功能入口方法"""
        # ... 业务逻辑（同上 6.2 模板）
        pass
```

然后在 `ADB_module.py` 中初始化：

```python
# 在 ADB_module.py 的 __init__ 中
from Function_Moudle.my_feature_operations import MyFeatureOperationsManager
self.my_feature_operations = MyFeatureOperationsManager(self)
```

---

### 7. 主窗口信号绑定详解

修改 `ADB_module.py` 需要改动 **三个位置**：

#### 7.1 位置一：声明线程变量（防止 GC 回收）

在 `__init__` 方法的变量声明区域添加：

```python
# ADB_module.py __init__ 中，约第 119-154 行附近
self.my_feature_thread = None  # ★ 必须声明！否则线程可能被垃圾回收导致意外终止
```

#### 7.2 位置二：初始化 Manager（如果是新 Manager）

```python
# ADB_module.py __init__ 中，约第 198-204 行附近
from Function_Moudle.my_feature_operations import MyFeatureOperationsManager
self.my_feature_operations = MyFeatureOperationsManager(self)
```

#### 7.3 位置三：绑定按钮信号

```python
# ADB_module.py __init__ 中，信号连接区域（约第 220-291 行附近）

# 方式 1：直接绑定（按钮在 UI 文件中有明确的 objectName）
self.my_new_feature_button.clicked.connect(self.app_operations.my_new_feature)

# 方式 2：安全绑定（按钮可能不存在于旧版 UI 中）
try:
    self.my_new_feature_button = self.findChild(QtWidgets.QPushButton, 'my_new_feature_button')
    if self.my_new_feature_button:
        self.my_new_feature_button.clicked.connect(self.app_operations.my_new_feature)
except Exception as e:
    self.textBrowser.append(str(e))
```

> **方式 2 更安全**：如果 UI 文件中没有这个按钮（比如旧版 UI），不会报错崩溃。

---

### 8. 日志记录规范

#### 8.1 可用的日志 API

```python
from logger_manager import (
    get_logger,              # 获取日志记录器
    log_operation,           # 记录操作
    log_button_click,        # 记录按钮点击
    log_method_result,       # 记录方法执行结果
    log_thread_start,        # 记录线程开始
    log_thread_complete,     # 记录线程完成
    log_exception,           # 记录异常
)
```

#### 8.2 在 Manager 中记录日志

```python
from logger_manager import log_button_click, log_method_result, get_logger

logger = get_logger("ADBTools.MyFeature")

def my_feature_action(self):
    # 1. 记录按钮点击
    log_button_click("my_feature_button", "我的新功能", "额外信息（可选）")
    
    # 2. 记录方法执行结果
    log_method_result("my_feature_action", True, "操作成功描述")
    log_method_result("my_feature_action", False, "失败原因")
    
    # 3. 自定义日志
    logger.info("自定义信息日志")
    logger.warning("自定义警告日志")
    logger.error("自定义错误日志")
```

#### 8.3 在线程中记录日志

如果使用 `BaseThread`，日志自动记录。如果使用原生 `QThread`，手动记录：

```python
from logger_manager import get_logger
logger = get_logger("ADBTools.MyThread")

def run(self):
    logger.info("线程开始执行")
    try:
        # ... 业务逻辑
        logger.info("线程执行成功")
    except Exception as e:
        logger.error(f"线程执行失败: {e}")
```

---

### 9. 完整实战案例

#### 案例：添加"获取设备电池信息"功能

##### 9.1 步骤 1：UI 添加按钮

在 `adbtool.ui` 中添加按钮：
- objectName: `get_battery_info_button`
- text: `获取电池信息`

##### 9.2 步骤 2：创建 ADB 模式线程

新建 `Function_Moudle/adb_get_battery_info_thread.py`：

```python
from PyQt5.QtCore import QThread, pyqtSignal
import subprocess


class ADBGetBatteryInfoThread(QThread):
    """ADB 模式下获取电池信息线程"""
    
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)

    def __init__(self, device_id):
        super().__init__()
        self.device_id = device_id

    def run(self):
        try:
            # 检查设备连接
            from Function_Moudle.adb_device_utils import check_device_connection
            is_connected, error_msg = check_device_connection(self.device_id)
            if not is_connected:
                self.error_signal.emit(error_msg)
                return
            
            self.progress_signal.emit("正在获取电池信息...")
            
            # 执行 ADB 命令获取电池信息
            command = f"adb -s {self.device_id} shell dumpsys battery"
            result = subprocess.run(
                command, shell=True, capture_output=True,
                text=True, encoding='utf-8', errors='ignore', timeout=10
            )
            
            if result.returncode == 0:
                # 解析电池信息
                battery_info = self._parse_battery_info(result.stdout)
                self.result_signal.emit(battery_info)
            else:
                self.error_signal.emit(f"获取电池信息失败: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            self.error_signal.emit("获取电池信息超时")
        except Exception as e:
            self.error_signal.emit(f"获取电池信息失败: {str(e)}")

    def _parse_battery_info(self, raw_output):
        """解析电池信息"""
        lines = []
        for line in raw_output.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('Current Battery Service state'):
                lines.append(line)
        return '\n'.join(lines) if lines else raw_output
```

##### 9.3 步骤 3：创建 U2 模式线程

新建 `Function_Moudle/get_battery_info_thread.py`：

```python
from PyQt5.QtCore import QThread, pyqtSignal


class GetBatteryInfoThread(QThread):
    """U2 模式下获取电池信息线程"""
    
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str)

    def __init__(self, d):
        super().__init__()
        self.d = d

    def run(self):
        try:
            if self.d is None:
                self.error_signal.emit("设备连接无效")
                return
            
            self.progress_signal.emit("正在获取电池信息...")
            
            # U2 方式执行 shell 命令
            result = self.d.shell("dumpsys battery")
            output = result.output if hasattr(result, 'output') else str(result)
            
            # 解析并返回
            lines = []
            for line in output.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('Current Battery Service state'):
                    lines.append(line)
            
            self.result_signal.emit('\n'.join(lines))
            
        except Exception as e:
            self.error_signal.emit(f"获取电池信息失败: {str(e)}")
```

##### 9.4 步骤 4：在 Manager 中添加方法

在 `Function_Moudle/device_manager.py` 的 `DeviceManager` 类中添加：

```python
def get_battery_info(self):
    """获取设备电池信息"""
    device_id = self.main_window.get_selected_device()
    devices_id_lst = self.main_window.get_new_device_lst()
    
    log_button_click("get_battery_info_button", "获取电池信息")

    if device_id in devices_id_lst:
        try:
            # 检查 U2 连接可用性
            if self.main_window.connection_mode == 'u2':
                if not self.main_window.d:
                    self.main_window.connection_mode = 'adb'
                    self.textBrowser.append("U2连接不可用，切换到ADB模式")
            
            # 根据模式创建线程
            if self.main_window.connection_mode == 'u2' and self.main_window.d:
                from Function_Moudle.get_battery_info_thread import GetBatteryInfoThread
                self.main_window.battery_info_thread = GetBatteryInfoThread(
                    d=self.main_window.d
                )
            elif self.main_window.connection_mode == 'adb':
                from Function_Moudle.adb_get_battery_info_thread import ADBGetBatteryInfoThread
                self.main_window.battery_info_thread = ADBGetBatteryInfoThread(
                    device_id=device_id
                )
            else:
                self.textBrowser.append("设备未连接！")
                return
            
            # 连接信号
            self.main_window.battery_info_thread.progress_signal.connect(self.textBrowser.append)
            self.main_window.battery_info_thread.result_signal.connect(self.textBrowser.append)
            self.main_window.battery_info_thread.error_signal.connect(self.textBrowser.append)
            
            # 启动线程
            self.main_window.battery_info_thread.start()
            
            log_method_result("get_battery_info", True, "线程已启动")
        except Exception as e:
            log_method_result("get_battery_info", False, str(e))
            self.textBrowser.append(f"获取电池信息失败: {e}")
    else:
        log_method_result("get_battery_info", False, "设备未连接")
        self.textBrowser.append("设备未连接！")
```

##### 9.5 步骤 5：修改主窗口绑定

**5a. 声明线程变量**（`ADB_module.py` 的 `__init__` 中）：

```python
self.battery_info_thread = None
```

**5b. 绑定按钮信号**（`ADB_module.py` 的信号连接区域）：

```python
try:
    self.get_battery_info_button = self.findChild(QtWidgets.QPushButton, 'get_battery_info_button')
    if self.get_battery_info_button:
        self.get_battery_info_button.clicked.connect(self.device_manager.get_battery_info)
except Exception as e:
    self.textBrowser.append(str(e))
```

##### 9.6 完成！运行测试

点击按钮后，执行流程：

```
按钮点击 → DeviceManager.get_battery_info()
         → 检查设备连接
         → 判断 U2/ADB 模式
         → 创建对应线程
         → 连接信号
         → 线程启动
         → 执行 ADB/U2 命令
         → 通过信号将结果显示在 textBrowser 中
```

---

### 10. 常见问题与注意事项

#### 10.1 ★ 线程变量必须挂在 main_window 上

```python
# ✅ 正确：线程引用保存在 main_window 上，生命周期与窗口一致
self.main_window.my_thread = MyThread(...)

# ❌ 错误：局部变量，方法返回后可能被 GC 回收，线程意外终止
my_thread = MyThread(...)
my_thread.start()
```

#### 10.2 ★ 严禁在线程中直接操作 UI

```python
# ✅ 正确：通过信号通信
self.result_signal.emit("操作成功")

# ❌ 错误：直接操作 UI 控件（会导致崩溃）
self.main_window.textBrowser.append("操作成功")
```

#### 10.3 ★ subprocess 必须处理编码

```python
# ✅ 正确
result = subprocess.run(cmd, shell=True, capture_output=True, 
                        text=True, encoding='utf-8', errors='ignore')

# ❌ 可能崩溃：Windows 下中文输出可能导致 UnicodeDecodeError
result = subprocess.run(cmd, shell=True, capture_output=True)
```

#### 10.4 ★ ADB 命令推荐使用 ADBUtils

```python
# ✅ 推荐：自动处理 ADB 路径问题（打包后也能找到 adb.exe）
from adb_utils import ADBUtils
result = ADBUtils.run_adb_command("shell xxx", device_id=self.device_id)

# ❌ 不推荐：直接使用 subprocess（打包后可能找不到 adb）
subprocess.run(f"adb -s {device_id} shell xxx", shell=True)
```

#### 10.5 ★ 操作前必须检查设备连接

```python
# 在 Manager 中检查
device_id = self.main_window.get_selected_device()
devices_id_lst = self.main_window.get_new_device_lst()
if device_id not in devices_id_lst:
    self.textBrowser.append("设备未连接！")
    return

# 在线程中再次检查（因为线程执行时设备可能已断开）
from Function_Moudle.adb_device_utils import check_device_connection
is_connected, error_msg = check_device_connection(self.device_id)
if not is_connected:
    self.error_signal.emit(error_msg)
    return
```

#### 10.6 ★ U2 模式降级处理

```python
# 标准降级逻辑
if self.main_window.connection_mode == 'u2':
    if not self.main_window.d:
        self.main_window.connection_mode = 'adb'
        self.textBrowser.append("U2连接不可用，切换到ADB模式")
```

#### 10.7 ★ 按钮可能不存在于 UI 中

使用 `findChild` 安全获取控件，避免 UI 文件更新不及时导致崩溃：

```python
try:
    self.my_button = self.findChild(QtWidgets.QPushButton, 'my_button')
    if self.my_button:
        self.my_button.clicked.connect(self.my_handler)
except Exception as e:
    self.textBrowser.append(str(e))
```

---

### 11. 文件修改清单

每次添加新功能，按以下清单逐项检查和修改：

| 序号 | 操作 | 文件路径 | 修改内容 | 是否必须 |
|:---:|------|----------|----------|:---:|
| 1 | 修改 | `adbtool.ui` | 添加按钮控件，设置 objectName | ✅ |
| 2 | 新建 | `Function_Moudle/xxx_thread.py` | 创建线程类 | ✅ |
| 3 | 新建/修改 | `Function_Moudle/xxx_operations.py` | 添加 Manager 方法 | ✅ |
| 4 | 修改 | `ADB_module.py` | ① 声明线程变量 `self.xxx_thread = None` | ✅ |
| 5 | 修改 | `ADB_module.py` | ② 初始化新 Manager（如果是新 Manager） | 视情况 |
| 6 | 修改 | `ADB_module.py` | ③ 绑定按钮信号 `button.clicked.connect(...)` | ✅ |
| 7 | 修改 | `Function_Moudle/thread_factory.py` | 注册线程类型到 `_get_thread_class` | 视情况 |

#### 快速开发模板

如果你想快速添加一个纯 ADB 功能，只需要：

1. **UI 加按钮** → objectName: `xxx_button`
2. **新建线程文件** → `Function_Moudle/adb_xxx_thread.py`（复制风格 B 模板）
3. **在 Manager 中加方法** → 检查设备 → 创建线程 → 连信号 → 启动
4. **ADB_module.py 改 3 处** → 声明变量 + 绑定信号

> 💡 **提示**：如果遇到问题，先参考项目中已有的类似功能实现。例如：
> - 简单 ADB 操作 → 参考 `adb_force_stop_app_thread.py`
> - U2 操作 → 参考 `force_stop_app_thread.py`
> - 双模式操作 → 参考 `start_app_thread.py`
> - 复杂 Manager → 参考 `app_operations.py`
