# ADBTools 云构建版本号管理指南

## 📋 概述

当前云构建已支持三种版本号获取方式，**无需修改云构建流程**。

---

## 🚀 推荐方案（按便捷程度排序）

### 方案 1：快速发布脚本 ⭐⭐⭐（最推荐）

**适用场景：** 日常版本发布

```powershell
# 一行命令完成所有操作
.\quick_release.ps1 1.8.30
```

**自动执行：**
- ✅ 提交代码更改
- ✅ 创建 Git Tag (v1.8.30)
- ✅ 推送到 GitHub
- ✅ 触发自动构建

**优点：**
- 最简单快捷
- 全自动处理
- 适合频繁发布

---

### 方案 2：完整发布脚本 ⭐⭐

**适用场景：** 需要更多控制的正式发布

```powershell
# 交互式发布（有确认步骤）
.\release.ps1 -Version "1.8.30"

# 干跑模式（预览操作，不实际执行）
.\release.ps1 -Version "1.8.30" -DryRun

# 跳过提交确认
.\release.ps1 -Version "1.8.30" -SkipCommit
```

**功能：**
- ✅ 检查 Git 状态
- ✅ 确认分支正确性
- ✅ 拉取最新代码
- ✅ 交互式确认
- ✅ 防止重复 tag

**优点：**
- 更安全
- 有详细提示
- 适合重要版本

---

### 方案 3：手动 Git Tag ⭐

**适用场景：** 熟悉 Git 操作的用户

```bash
# 1. 提交代码
git add .
git commit -m "chore: release v1.8.30"

# 2. 创建并推送 tag
git tag v1.8.30
git push origin main --tags
```

**或者一次性完成：**
```bash
git add . && git commit -m "chore: release v1.8.30" && git tag v1.8.30 && git push origin main --tags
```

---

### 方案 4：GitHub Web 界面

**适用场景：** 测试构建、临时版本

1. 访问：https://github.com/wangke956/ADBTools/actions
2. 点击 **Build and Package ADBTools**
3. 点击 **Run workflow**
4. 填写版本号（如 `1.8.30`）
5. 勾选 **是否创建 Release**
6. 点击 **Run workflow**

**优点：**
- 无需命令行
- 可视化操作
- 适合测试

---

## 📊 版本号规则

### 推荐的版本号格式

```
主版本.次版本.修订号
例如：1.8.30
```

### 版本号优先级

云构建会按以下顺序获取版本号：

1. **Git Tag**（最高优先级）
   - 推送 `v1.8.30` → 版本号 `1.8.30`
   - 适合正式版本发布

2. **手动输入**（workflow_dispatch）
   - 在 GitHub Actions 界面输入
   - 适合测试和临时构建

3. **日期格式**（默认）
   - 自动生成 `2026.06.26`
   - 适合开发版本

---

## 🔄 完整发布流程示例

### 日常发布（使用快速脚本）

```powershell
# 1. 确保代码已修改并提交
git status

# 2. 运行快速发布脚本
.\quick_release.ps1 1.8.30

# 3. 等待构建完成（5-10分钟）
# 访问 https://github.com/wangke956/ADBTools/actions 查看进度

# 4. 构建完成后自动创建 Release
# 访问 https://github.com/wangke956/ADBTools/releases/tag/v1.8.30 下载
```

### 正式发布（使用完整脚本）

```powershell
# 1. 更新本地版本号（如果需要）
# 编辑 adbtools_config.json 等文件

# 2. 运行完整发布脚本
.\release.ps1 -Version "1.8.30"

# 3. 按提示确认操作

# 4. 等待构建完成
```

---

## ⚠️ 注意事项

### 1. Tag 命名规范

- ✅ 正确：`v1.8.30`
- ❌ 错误：`1.8.30`（缺少 v 前缀）
- ❌ 错误：`V1.8.30`（大写 V）

### 2. 避免重复 Tag

如果 tag 已存在，脚本会提示：
```
⚠️  Tag v1.8.30 已存在！
是否删除并重新创建? (y/n)
```

### 3. 分支要求

建议在 `main` 分支上发布版本：
```bash
git checkout main
git pull origin main
```

### 4. 构建时间

- 首次构建：约 10-15 分钟
- 后续构建：约 5-8 分钟（有缓存）

---

## 🔍 查看构建结果

### 1. 查看构建进度

访问：https://github.com/wangke956/ADBTools/actions

### 2. 下载构建产物

构建成功后，可以在以下位置找到：

- **Release 页面**：https://github.com/wangke956/ADBTools/releases
- **Artifacts**：Actions 页面的 Artifacts 部分

### 3. 构建产物包含

- `ADBTools_Setup.exe` - 安装版
- `ADBTools_v1.8.30_Windows.zip` - 便携版

---

## 💡 最佳实践

### 1. 版本号递增规则

- **主版本**：重大架构变更或不兼容更新
- **次版本**：新功能添加
- **修订号**：Bug 修复和小改进

例如：
- `1.8.29` → `1.8.30`（小修复）
- `1.8.30` → `1.9.0`（新功能）
- `1.9.0` → `2.0.0`（重大变更）

### 2. 发布前检查清单

- [ ] 代码已测试通过
- [ ] 版本号已更新
- [ ] CHANGELOG 已更新（如果有）
- [ ] 在 main 分支上
- [ ] 本地构建成功

### 3. 使用 DryRun 模式预览

不确定时先用干跑模式：
```powershell
.\release.ps1 -Version "1.8.30" -DryRun
```

---

## 🆘 常见问题

### Q1: 如何取消已推送的 tag？

```bash
# 删除本地 tag
git tag -d v1.8.30

# 删除远程 tag
git push origin :refs/tags/v1.8.30
```

### Q2: 构建失败了怎么办？

1. 查看 Actions 日志找出错误原因
2. 修复问题后重新推送 tag
3. 或者删除旧 tag 后重新创建

### Q3: 可以修改已发布的版本吗？

不建议。应该发布新版本号：
```powershell
.\quick_release.ps1 1.8.31
```

### Q4: 如何只构建不发布 Release？

使用 GitHub Web 界面，不勾选"是否创建 Release"选项。

---

## 📞 技术支持

如有问题，请查看：
- GitHub Issues: https://github.com/wangke956/ADBTools/issues
- Actions 日志: https://github.com/wangke956/ADBTools/actions
