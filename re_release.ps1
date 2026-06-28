# ADBTools 重新发布脚本（用于修复已推送但未创建 Release 的情况）
# 用法: .\re_release.ps1 1.8.30
#
# 说明：
# - 删除本地和远程的旧 tag
# - 重新创建并推送 tag 以触发云构建
# - 这次会正确创建 Release

param(
    [Parameter(Mandatory=$true)]
    [string]$Version
)

Write-Host "🔄 重新发布 ADBTools v$Version" -ForegroundColor Cyan
Write-Host ""

# 确认操作
$confirm = Read-Host "⚠️  这将删除现有的 tag v$Version 并重新创建，是否继续？(y/n)"
if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "❌ 操作已取消" -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "📝 步骤 1/4: 删除本地 tag..." -ForegroundColor Cyan
git tag -d "v$Version" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 本地 tag 已删除" -ForegroundColor Green
} else {
    Write-Host "⚠️  本地 tag 不存在" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📝 步骤 2/4: 删除远程 tag..." -ForegroundColor Cyan
git push origin :refs/tags/v$Version 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 远程 tag 已删除" -ForegroundColor Green
} else {
    Write-Host "⚠️  远程 tag 不存在或无法删除" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📝 步骤 3/4: 确保代码是最新的..." -ForegroundColor Cyan
git pull origin main --rebase

Write-Host ""
Write-Host "📝 步骤 4/4: 重新创建并推送 tag..." -ForegroundColor Cyan
git tag "v$Version"
git push origin main --tags

Write-Host ""
Write-Host "✅ 重新发布成功！" -ForegroundColor Green
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
