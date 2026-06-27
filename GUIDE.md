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
