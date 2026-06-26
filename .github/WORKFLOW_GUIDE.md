# GitHub Actions 自动化构建指南

## 📋 概述

本项目已配置 GitHub Actions 自动构建流程，可以自动编译和打包 ADBTools 为 Windows 可执行文件。

## 🚀 快速开始

### 1. 推送代码触发构建

将代码推送到 `main` 或 `master` 分支时，会自动触发构建：

```bash
git add .
git commit -m "更新代码"
git push origin main
```

### 2. 使用标签创建发布版本

创建带版本号的标签会触发构建并自动创建 Release：

```bash
git tag v1.6.2
git push origin v1.6.2
```

### 3. 手动触发构建（推荐）

在 GitHub 仓库页面操作：

1. 进入 **Actions** 标签页
2. 选择 **Build and Package ADBTools** 工作流
3. 点击 **Run workflow** 按钮
4. 填写参数：
   - **版本号**: 例如 `1.6.2`（留空则使用当前日期）
   - **是否创建 Release**: 勾选则自动创建 GitHub Release
5. 点击 **Run workflow**

## ⚙️ 工作流程说明

### 构建步骤

1. **环境准备**
   - 安装 Python 3.10
   - 安装 Visual C++ Build Tools
   - 安装项目依赖

2. **版本管理**
   - 从标签、输入或日期获取版本号
   - 更新配置文件中的版本号

3. **资源准备**
   - 下载 Android platform-tools
   - 复制 ADB 工具文件到构建目录

4. **Nuitka 编译**
   - 使用 Nuitka 编译为单文件可执行程序
   - 包含所有必要的资源和依赖

5. **打包发布**
   - 创建 ZIP 压缩包
   - 上传为 GitHub Artifact
   - （可选）创建 GitHub Release

### 输出文件

- **Artifact**: `ADBTools_{version}_Windows.zip`
- **保存期限**: 90 天
- **位置**: Actions → Artifacts

## 🔧 配置说明

### 环境变量

在工作流中定义的环境变量：

```yaml
env:
  PYTHON_VERSION: '3.10'
  APP_NAME: ADBTools
```

### Secrets 配置

如需启用通知功能，需要在 GitHub 仓库设置中添加 Secrets：

1. 进入 **Settings** → **Secrets and variables** → **Actions**
2. 添加以下 Secret：

| Secret 名称 | 说明 | 必需 |
|------------|------|------|
| `SERVERCHAN_API_KEY` | Server酱 API Key，用于推送通知 | 否 |

获取 Server酱 API Key：
1. 访问 [Server酱官网](https://sct.ftqq.com/)
2. 登录并获取 SendKey
3. 在 GitHub Secrets 中添加

## 📝 自定义构建

### 修改 Python 版本

编辑 `.github/workflows/build.yml`：

```yaml
env:
  PYTHON_VERSION: '3.11'  # 修改为你需要的版本
```

### 修改构建类型

当前使用 OneFile 模式，如需改为 Standalone 模式：

```yaml
- name: Build with Nuitka (Standalone)
  run: |
    python nuitka_build_fixed_v2.py --build standalone
```

### 添加更多平台

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

## 🐛 故障排除

### 构建失败

1. **查看日志**
   - 进入 Actions 标签页
   - 点击失败的工作流
   - 查看详细日志

2. **常见问题**

| 问题 | 解决方案 |
|------|---------|
| Nuitka 编译错误 | 检查 `requirements_nuitka.txt` 是否完整 |
| 缺少 VC++ Build Tools | 确认工作流中正确安装了 build tools |
| 依赖安装失败 | 清除缓存后重试：Actions → Delete cache |
| 内存不足 | 减少 Nuitka 并行编译核心数 |

### 本地测试

在提交前，建议在本地测试构建：

```bash
# 安装依赖
pip install -r requirements_nuitka.txt

# 清理旧构建
python nuitka_build_fixed_v2.py --clean

# 执行构建
python nuitka_build_fixed_v2.py --build onefile

# 验证输出
ls dist_nuitka/
```

## 📊 构建状态徽章

可以将构建状态徽章添加到 README：

```markdown
![Build Status](https://github.com/用户名/ADBTools/actions/workflows/build.yml/badge.svg)
```

## 🔗 相关链接

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [Nuitka 官方文档](https://nuitka.net/)
- [softprops/action-gh-release](https://github.com/softprops/action-gh-release)

## 💡 最佳实践

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

## 📞 支持

如有问题，请：
1. 查看 Actions 日志
2. 搜索 Issues
3. 创建新的 Issue

---

**最后更新**: 2026-06-26
