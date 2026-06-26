# GitHub Actions 自动化构建 - 快速开始

## 🎯 三步完成自动化构建

### 第一步：提交代码到 GitHub

```bash
git add .
git commit -m "添加 GitHub Actions 配置"
git push origin main
```

### 第二步：触发构建

**方式 1：推送标签（推荐用于发布）**
```bash
git tag v1.6.2
git push origin v1.6.2
```

**方式 2：手动触发**
1. 访问你的 GitHub 仓库
2. 点击 **Actions** 标签
3. 选择 **Build and Package ADBTools**
4. 点击 **Run workflow**
5. 输入版本号（可选）
6. 勾选 **是否创建 Release**（可选）
7. 点击 **Run workflow**

### 第三步：下载构建产物

1. 等待构建完成（约 10-20 分钟）
2. 在 Actions 页面查看状态
3. 构建成功后：
   - **Artifact**: 在 workflow 详情页底部下载
   - **Release**: 如果勾选了创建 Release，会在 Releases 页面找到

## 📁 创建的文件

```
.github/
├── workflows/
│   └── build.yml          # GitHub Actions 工作流配置
└── WORKFLOW_GUIDE.md      # 详细使用指南

ci_build.py                # CI/CD 专用构建脚本
GITHUB_ACTIONS_GUIDE.md    # 本文件
```

## ⚙️ 首次设置

### 1. 启用 GitHub Actions

如果是首次使用：
1. 进入仓库的 **Actions** 标签
2. 点击 **I understand my workflows, go ahead and enable them**

### 2. 配置 Secrets（可选）

如需接收构建通知：

1. 进入 **Settings** → **Secrets and variables** → **Actions**
2. 点击 **New repository secret**
3. 添加：
   - Name: `SERVERCHAN_API_KEY`
   - Value: 你的 Server酱 API Key

### 3. 验证构建

推送一个测试提交：
```bash
git commit --allow-empty -m "测试 GitHub Actions"
git push
```

然后在 Actions 页面查看构建状态。

## 🔍 常见问题

### Q: 构建需要多长时间？
A: 首次构建约 15-20 分钟（需要安装依赖和编译），后续构建会使用缓存，约 10-15 分钟。

### Q: 如何查看构建日志？
A: 
1. 进入 **Actions** 标签
2. 点击具体的 workflow run
3. 点击 job 名称查看详细日志

### Q: 构建失败怎么办？
A:
1. 查看错误日志
2. 检查 `requirements_nuitka.txt` 是否完整
3. 确认所有必要的文件都已提交
4. 尝试在本地运行 `python ci_build.py` 测试

### Q: Artifact 保存多久？
A: 默认 90 天，可以在 `build.yml` 中修改 `retention-days` 参数。

### Q: 如何自定义版本号？
A:
- **标签方式**: `git tag v1.6.2`
- **手动触发**: 在 Run workflow 时输入
- **自动**: 使用当前日期（格式：YYYY.MM.DD）

## 📊 构建状态徽章

将以下代码添加到 README.md 顶部：

```markdown
![Build Status](https://github.com/你的用户名/ADBTools/actions/workflows/build.yml/badge.svg)
[![Release](https://img.shields.io/github/v/release/你的用户名/ADBTools)](https://github.com/你的用户名/ADBTools/releases)
```

替换 `你的用户名` 为你的 GitHub 用户名。

## 🚀 下一步

- 阅读 [WORKFLOW_GUIDE.md](.github/WORKFLOW_GUIDE.md) 了解详细配置
- 查看 [nuitka_build_fixed_v2.py](nuitka_build_fixed_v2.py) 了解构建细节
- 探索其他 GitHub Actions 功能

## 💡 提示

1. **使用标签管理版本**: 重要版本使用 Git 标签
2. **定期检查构建**: 确保每次提交都能成功构建
3. **保护主分支**: 要求 PR 通过 CI 检查
4. **清理旧 Artifact**: 定期删除不需要的构建产物

---

**有问题？** 查看 [WORKFLOW_GUIDE.md](.github/WORKFLOW_GUIDE.md) 或创建 Issue。
