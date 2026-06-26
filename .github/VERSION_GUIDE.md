# GitHub Actions 版本号管理指南

## 📌 版本号的三种获取方式

GitHub Actions 工作流会自动确定版本号，优先级如下：

### 1️⃣ **Git Tag（推荐）- 正式版本发布**

这是最推荐的版本发布方式，适合正式版本。

#### 使用步骤：

```bash
# 1. 确保代码已提交并推送到 main 分支
git add .
git commit -m "准备发布 v1.0.0"
git push origin main

# 2. 创建并推送 tag
git tag v1.0.0
git push origin v1.0.0
```

或者使用 GitHub Web 界面：
1. 进入仓库页面
2. 点击 **Releases** → **Draft a new release**
3. 在 **Tag version** 输入框中输入 `v1.0.0`
4. 点击 **Publish release**

✅ **优点**：
- 自动触发构建
- 自动创建 GitHub Release
- 版本号清晰明确
- 符合语义化版本规范

---

### 2️⃣ **手动触发（workflow_dispatch）- 测试用**

适合测试构建或临时版本。

#### 使用步骤：

1. 进入 GitHub 仓库的 **Actions** 标签页
2. 选择 **Build and Package ADBTools** 工作流
3. 点击 **Run workflow** 按钮
4. 填写参数：
   - **版本号**：输入你想要的版本号（如 `1.0.0-test`），留空则使用日期
   - **是否创建 Release**：勾选则会创建 Release
5. 点击 **Run workflow**

✅ **优点**：
- 灵活控制版本号
- 可以指定任意版本号
- 适合测试和调试

 **缺点**：
- 需要手动操作
- 不适合自动化流程

---

### 3️⃣ **自动日期版本 - 开发版本**

当推送代码到 main 分支时，如果没有 tag 且不是手动触发，会使用当前日期作为版本号。

#### 触发条件：

```bash
# 只需正常推送代码即可
git add .
git commit -m "修复某个bug"
git push origin main
```

版本号格式：`YYYY.MM.DD`（如 `2026.06.26`）

✅ **优点**：
- 完全自动化
- 每次推送都有唯一版本号
- 适合持续集成

❌ **缺点**：
- 版本号不具语义
- 不适合正式发布

---

## 🎯 最佳实践

### 日常开发流程

```bash
# 1. 日常开发，直接推送（自动生成日期版本）
git add .
git commit -m "添加新功能"
git push origin main

# 2. 功能完成，准备发布正式版本
git tag v1.1.0
git push origin v1.1.0
```

### 版本管理规范

建议使用**语义化版本**（SemVer）：

- **主版本号**：不兼容的 API 修改（如 `2.0.0`）
- **次版本号**：向下兼容的功能性新增（如 `1.1.0`）
- **修订号**：向下兼容的问题修正（如 `1.0.1`）

示例：
- `v1.0.0` - 第一个稳定版本
- `v1.0.1` - 修复 bug
- `v1.1.0` - 新增功能
- `v2.0.0` - 重大更新

---

## 🔍 如何查看构建结果

### 查看构建日志

1. 进入 **Actions** 标签页
2. 点击最近的工作流运行
3. 查看 **Build Windows Executable** 步骤的输出
4. 找到类似这样的日志：

```
Using tag version: 1.0.0
Final version: 1.0.0
Updated version to: 1.0.0
```

### 下载构建产物

#### 方式1：从 Artifacts 下载（所有构建）

1. 在工作流运行页面
2. 滚动到底部的 **Artifacts** 部分
3. 点击 `ADBTools-Windows-{version}` 下载 ZIP 文件

#### 方式2：从 Releases 下载（仅 Tag 触发）

1. 进入仓库的 **Releases** 页面
2. 找到对应的版本
3. 下载附件中的 ZIP 文件

---

## ⚠️ 常见问题

### Q1: 为什么我的版本号没有更新？

**可能原因**：
1. 使用了错误的 tag 格式（必须是 `v*` 开头，如 `v1.0.0`）
2. 手动触发时没有填写版本号（会使用日期）
3. 配置文件更新失败（检查构建日志）

**解决方法**：
- 确认 tag 格式正确：`git tag v1.0.0`
- 检查构建日志中的 `Get version from tag or input` 步骤

### Q2: 如何修改已有的 tag？

```bash
# 删除本地 tag
git tag -d v1.0.0

# 删除远程 tag
git push origin :refs/tags/v1.0.0

# 重新创建并推送
git tag v1.0.1
git push origin v1.0.1
```

### Q3: 可以同时构建多个版本吗？

可以！每个 tag 都会触发一次独立的构建。你可以快速连续推送多个 tag：

```bash
git tag v1.0.0 && git push origin v1.0.0
git tag v1.0.1 && git push origin v1.0.1
git tag v1.1.0 && git push origin v1.1.0
```

---

## 📊 版本对比表

| 触发方式 | 版本号来源 | 适用场景 | 是否创建 Release |
|---------|-----------|---------|-----------------|
| Git Tag | Tag 名称（去掉 v） | 正式版本发布 | ✅ 是 |
| 手动触发 | 用户输入 / 日期 | 测试、临时版本 | 可选 |
| 推送 main | 当前日期 | 开发版本、CI | ❌ 否 |

---

## 🚀 快速开始

### 第一次发布正式版本

```bash
# 1. 确保代码已提交
git add .
git commit -m "准备发布第一个正式版本"
git push origin main

# 2. 创建 tag
git tag v1.0.0
git push origin v1.0.0

# 3. 等待 GitHub Actions 自动构建（约 5-10 分钟）

# 4. 查看 Releases 页面下载构建产物
```

### 后续版本更新

```bash
# 修复 bug 后
git add .
git commit -m "修复重要bug"
git push origin main
git tag v1.0.1
git push origin v1.0.1

# 或者添加新功能后
git add .
git commit -m "添加新功能"
git push origin main
git tag v1.1.0
git push origin v1.1.0
```

---

## 💡 提示

- 版本号会自动写入 `adbtools_config.json` 文件中
- 构建产物会保留 90 天（Artifacts）
- Release 会永久保存
- 建议在打 tag 前确保代码已经过充分测试
