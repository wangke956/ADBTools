# ADBTools 自动发布指南

## 概述

本项目提供了两个自动发布脚本，用于将新版本发布到 GitHub：

1. **release.py** - 功能完整的发布脚本（推荐）
2. **release_simple.py** - 简化的发布脚本

## 前置要求

### 1. GitHub CLI
确保已安装 GitHub CLI：
- 下载地址：https://cli.github.com/
- 安装后验证：`gh --version`

### 2. Inno Setup
确保已安装 Inno Setup 编译器：
- 下载地址：https://jrsoftware.org/isinfo.php
- 安装后确保 `iscc.exe` 在系统 PATH 中

### 3. Python 依赖
确保已安装所有必要的 Python 包：
```bash
pip install nuitka PyQt5 qdarkstyle uiautomator2 adbutils openpyxl psutil lxml
```

### 4. Git 配置
确保已配置 Git 用户信息：
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## 使用方法

### 方法一：使用完整版发布脚本（推荐）

```bash
python release.py [版本号]
```

**示例：**
```bash
# 交互式输入版本号
python release.py

# 直接指定版本号
python release.py 1.6.3
```

### 方法二：使用简化版发布脚本

```bash
python release_simple.py [版本号]
```

**示例：**
```bash
# 交互式输入版本号
python release_simple.py

# 直接指定版本号
python release_simple.py 1.6.3
```

## 发布流程

### 1. 版本号更新
- 自动更新 `config_manager.py` 中的版本号
- 自动更新 `adbtools_config.json` 中的版本号
- 自动更新 `ADBTools_setup.iss` 中的版本号

### 2. 打包流程
- 执行 Nuitka 构建（生成单文件可执行程序）
- 复制必要的配置文件到构建目录
- 使用 Inno Setup 编译生成安装包

### 3. Git 操作
- 添加所有更改到暂存区
- 创建提交（commit）
- 创建 Git 标签（tag）
- 推送到远程仓库

### 4. GitHub 发布
- 使用 `gh release create` 命令创建 GitHub 发布
- 上传生成的安装包作为发布附件
- 推送标签到远程仓库

## 脚本功能对比

| 功能 | release.py | release_simple.py |
|------|------------|-------------------|
| 版本号更新 | ✅ 完整 | ✅ 完整 |
| Nuitka 构建 | ✅ 完整 | ✅ 完整 |
| 文件复制 | ✅ 完整 | ✅ 完整 |
| Inno Setup | ✅ 完整 | ✅ 完整 |
| Git 操作 | ✅ 完整 | ✅ 完整 |
| GitHub 发布 | ✅ 完整 | ✅ 完整 |
| 用户交互 | ✅ 详细 | ✅ 基础 |
| 错误处理 | ✅ 详细 | ✅ 基础 |
| 代码复杂度 | 中等 | 简单 |

## 输出文件

发布完成后，将在以下位置生成文件：

- **安装包**：`D:\Personal files\ADBTools\Output\ADBTools_Setup.exe`
- **可执行程序**：`D:\Personal files\ADBTools\dist_nuitka\ADBTools_nuitka.exe`

## 常见问题

### Q: gh 命令未找到怎么办？
A: 请安装 GitHub CLI：
1. 访问 https://cli.github.com/
2. 下载并安装
3. 重启终端
4. 验证安装：`gh --version`

### Q: iscc 命令未找到怎么办？
A: 请安装 Inno Setup：
1. 访问 https://jrsoftware.org/isinfo.php
2. 下载并安装 Inno Setup
3. 确保安装路径已添加到系统 PATH

### Q: 版本号格式错误怎么办？
A: 版本号必须使用 `主版本.次版本.修订号` 格式，如 `1.6.3`。

### Q: 发布失败如何处理？
A: 
1. 检查所有前置要求是否满足
2. 查看脚本输出的错误信息
3. 手动执行失败的步骤
4. 确保 Git 已正确配置

## 自动化发布

可以将发布脚本集成到 CI/CD 流程中，实现自动化发布：

### GitHub Actions 示例

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
          
      - name: Install dependencies
        run: |
          pip install nuitka PyQt5 qdarkstyle uiautomator2 adbutils openpyxl psutil lxml
          
      - name: Build
        run: |
          python nuitka_build.py --build onefile
          python auto_package.py --non-interactive
          
      - name: Release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python release.py ${{ github.ref_name }}
```

## 联系信息

如有问题或建议，请通过以下方式联系：
- GitHub Issues: https://github.com/wangke956/ADBTools/issues
- 邮箱: wangke956@example.com

## 更新日志

### v1.0.0 (2024-01-28)
- 初始版本发布
- 支持完整的自动发布流程
- 提供两个版本的发布脚本

---

**注意**：请确保在发布前进行充分测试，确保安装包正常工作。