# ADBTools 版本发布脚本
# 用法: .\release.ps1 -Version "1.8.30"

param(
    [Parameter(Mandatory=$true)]
    [string]$Version,
    
    [switch]$SkipCommit = $false,
    [switch]$DryRun = $false
)

# 颜色输出函数
function Write-Success { param($msg); Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Info { param($msg); Write-Host "ℹ️  $msg" -ForegroundColor Cyan }
function Write-Warning { param($msg); Write-Host "⚠️  $msg" -ForegroundColor Yellow }
function Write-Error { param($msg); Write-Host "❌ $msg" -ForegroundColor Red }

Write-Info "=========================================="
Write-Info "ADBTools 版本发布工具"
Write-Info "=========================================="
Write-Info "目标版本: $Version"
Write-Info ""

# 检查 git 状态
Write-Info "检查 Git 状态..."
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Warning "工作区有未提交的更改："
    git status --short
    
    if (-not $SkipCommit) {
        $confirm = Read-Host "是否提交这些更改? (y/n)"
        if ($confirm -eq 'y') {
            git add .
            git commit -m "chore: 准备发布版本 $Version"
            Write-Success "已提交更改"
        } else {
            Write-Error "请先提交或暂存更改后重试"
            exit 1
        }
    }
} else {
    Write-Success "工作区干净"
}

# 检查当前分支
$currentBranch = git branch --show-current
Write-Info "当前分支: $currentBranch"
if ($currentBranch -ne "main") {
    Write-Warning "不在 main 分支上，建议切换到 main 分支后再发布"
    $confirm = Read-Host "是否继续? (y/n)"
    if ($confirm -ne 'y') {
        exit 1
    }
}

# 拉取最新代码
Write-Info "拉取最新代码..."
git pull origin $currentBranch
Write-Success "代码已更新"

# 显示将要创建的 tag
$tagName = "v$Version"
Write-Info ""
Write-Info "即将执行的操作:"
Write-Info "  1. 创建 tag: $tagName"
Write-Info "  2. 推送到远程仓库"
Write-Info "  3. 触发 GitHub Actions 自动构建"
Write-Info ""

if ($DryRun) {
    Write-Warning "[干跑模式] 不会实际执行操作"
    exit 0
}

$confirm = Read-Host "确认执行? (y/n)"
if ($confirm -ne 'y') {
    Write-Info "已取消"
    exit 0
}

# 创建 tag
Write-Info ""
Write-Info "创建 tag: $tagName ..."
if (git tag | Select-String -Pattern "^$tagName$") {
    Write-Warning "Tag $tagName 已存在！"
    $confirm = Read-Host "是否删除并重新创建? (y/n)"
    if ($confirm -eq 'y') {
        git tag -d $tagName
        git push origin :refs/tags/$tagName
        Write-Success "已删除旧 tag"
    } else {
        Write-Error "已取消"
        exit 1
    }
}

git tag $tagName
Write-Success "Tag 创建成功: $tagName"

# 推送 tag
Write-Info "推送 tag 到远程仓库..."
git push origin $tagName
Write-Success "Tag 已推送"

# 推送主分支（如果有新提交）
if ($gitStatus -or -not $SkipCommit) {
    Write-Info "推送主分支..."
    git push origin $currentBranch
    Write-Success "主分支已推送"
}

Write-Info ""
Write-Success "=========================================="
Write-Success "发布流程启动成功！"
Write-Success "=========================================="
Write-Info ""
Write-Info "下一步："
Write-Info "  1. 访问 GitHub Actions 查看构建进度"
Write-Info "     https://github.com/wangke956/ADBTools/actions"
Write-Info ""
Write-Info "  2. 构建完成后会自动创建 Release"
Write-Info "     https://github.com/wangke956/ADBTools/releases/tag/$tagName"
Write-Info ""
Write-Info "预计耗时: 5-10 分钟"
Write-Info ""
