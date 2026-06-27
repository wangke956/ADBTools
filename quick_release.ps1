# ADBTools 快速发布脚本
# 用法: .\quick_release.ps1 1.8.30
#
# 说明：
# - 自动提交代码更改
# - 创建 Git Tag (v1.8.30)
# - 推送到 GitHub 触发云构建
# - 云端会自动更新版本号，无需手动修改任何文件

param(
    [Parameter(Mandatory=$true)]
    [string]$Version,
    
    [switch]$SkipCommit = $false
)

Write-Host "🚀 快速发布 ADBTools v$Version" -ForegroundColor Cyan
Write-Host ""
Write-Host "ℹ️  云端会自动更新版本号，无需手动修改配置文件" -ForegroundColor Yellow
Write-Host ""

# 检查是否有未提交的更改
$gitStatus = git status --porcelain
if ($gitStatus -and -not $SkipCommit) {
    Write-Host "📝 检测到未提交的更改，正在提交..." -ForegroundColor Cyan
    git add .
    git commit -m "chore: release v$Version"
    Write-Host "✅ 代码已提交" -ForegroundColor Green
} elseif ($gitStatus) {
    Write-Host "⚠️  有未提交的更改但使用了 -SkipCommit 参数" -ForegroundColor Yellow
}

# 拉取最新代码
Write-Host "📥 拉取最新代码..." -ForegroundColor Cyan
git pull origin main --rebase

# 创建并推送 tag
Write-Host "🏷️  创建 Git Tag: v$Version" -ForegroundColor Cyan
git tag "v$Version"

Write-Host "📤 推送到 GitHub..." -ForegroundColor Cyan
git push origin main --tags

Write-Host ""
Write-Host "✅ 发布成功！" -ForegroundColor Green
Write-Host ""
Write-Host "📦 云构建正在进行中..." -ForegroundColor Yellow
Write-Host "   • 云端会自动更新版本号" -ForegroundColor Gray
Write-Host "   • 预计耗时: 5-10 分钟" -ForegroundColor Gray
Write-Host ""
Write-Host "🔗 查看构建进度:" -ForegroundColor Cyan
Write-Host "   https://github.com/wangke956/ADBTools/actions" -ForegroundColor Blue
Write-Host ""
Write-Host "🔗 构建完成后下载:" -ForegroundColor Cyan
Write-Host "   https://github.com/wangke956/ADBTools/releases/tag/v$Version" -ForegroundColor Blue
Write-Host ""
